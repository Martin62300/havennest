import json
import os
import re
import time
import requests
from datetime import datetime, timedelta
import cloudscraper
from bs4 import BeautifulSoup

class HavenNestCrawler:
    def __init__(self):
        self.filename = 'listings.json'
        self.raw_rentals_file = 'rentals_raw.json'
        self.cache_file = 'coords_cache.json'
        self.coords_cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.coords_cache, f, ensure_ascii=False, indent=4)

    def get_lat_lng(self, address):
        """地址转坐标，带缓存机制 [cite: 2026-03-03]"""
        if not address: return None, None
        
        # 缓存键名处理
        clean_addr = re.sub(r'[^\w\s,.-]', '', address).strip()
        search_query = f"{clean_addr}, BC, Canada"
        
        if search_query in self.coords_cache:
            return self.coords_cache[search_query]

        try:
            if len(clean_addr) < 3: return None, None
            # Nominatim 规定请求频率不能超过 1次/秒
            time.sleep(1.2)
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(search_query)}"
            res = requests.get(url, headers={'User-Agent': 'HavenNest_Bot_v2.5.0 (contact: support@havennestapp.com)'}, timeout=10)
            data = res.json()
            if data:
                coords = [float(data[0]['lat']), float(data[0]['lon'])]
                self.coords_cache[search_query] = coords
                self._save_cache()
                return coords
        except Exception as e:
            print(f"📍 Geocoding error for {address}: {e}")
        return None, None

    def extract_beds(self, text):
        """通用卧室数量提取逻辑"""
        if not text: return 1
        text = text.lower()
        # 匹配 "2 beds", "2br", "2室", "2房"
        match = re.search(r'(\d+)\s*(?:室|房|br|bed|bedroom)', text)
        if match:
            return int(match.group(1))
        # 匹配 "studio", "bachelor"
        if "studio" in text or "bachelor" in text:
            return 0
        return 1

    def process_manual_rentals(self):
        """优化版 Rentals.ca 片段提取逻辑"""
        if not os.path.exists(self.raw_rentals_file):
            print("INFO: No rentals_raw.json found.")
            return []
        
        print(f"Scanning rentals_raw.json for Rentals.ca listings...")
        results = []
        try:
            with open(self.raw_rentals_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 匹配 Rentals.ca 的 GraphQL 节点结构
            blocks = re.findall(r'\{"node":\s*(\{.*?"__typename":\s*"RentalListing".*?\})\s*\}', content, re.DOTALL)
            if not blocks:
                blocks = re.findall(r'(\{.*?"rentalListingName":\s*".*?".*?\})', content, re.DOTALL)

            for block in blocks:
                try:
                    title = re.search(r'"rentalListingName":\s*"(.*?)"', block).group(1)
                    path = re.search(r'"path":\s*"(.*?)"', block).group(1)
                    
                    # 提取坐标：Rentals 是 [lng, lat]
                    loc_match = re.search(r'"rentalListingLocation":\s*\[(.*?),(.*?)\]', block)
                    lat = float(loc_match.group(2)) if loc_match else None
                    lng = float(loc_match.group(1)) if loc_match else None
                    
                    # 提取价格
                    rent_match = re.search(r'"rentRange":\s*\[(.*?)(?:,|$)', block)
                    price = int(float(rent_match.group(1))) if rent_match else 0
                    
                    # 提取地址和城市
                    street_match = re.search(r'"street":\s*"(.*?)"', block)
                    street = street_match.group(1) if street_match else ""
                    city_match = re.search(r'"cityName":\s*"(.*?)"', block)
                    city = city_match.group(1) if city_match else "Vancouver"
                    full_address = f"{street}, {city}" if street else city

                    # 提取卧室 (从字段或标题)
                    beds_match = re.search(r'"bedroomCount":\s*(\d+)', block)
                    beds = int(beds_match.group(1)) if beds_match else self.extract_beds(title)

                    # 提取图片
                    img_match = re.search(r'"url":\s*"(https://assets\.rentsync\.com/.*?)"', block)
                    img_url = img_match.group(1) if img_match else ""

                    results.append({
                        "source": "Rentals.ca",
                        "title": title,
                        "price": price,
                        "url": "https://rentals.ca/" + path,
                        "address": full_address,
                        "city": city,
                        "beds": beds,
                        "lat": lat,
                        "lng": lng,
                        "image": img_url,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except: continue

            print(f"DONE: Extracted {len(results)} Rentals listings.")
            return results
        except Exception as e:
            print(f"WARNING: Rentals extraction failed: {e}")
            return []

    def crawl_craigslist(self, limit=40):
        print(f"Crawling Craigslist via RSS (limit {limit})...")
        results = []
        try:
            # 使用 RSS 更加稳定，不易被封禁
            rss_url = "https://vancouver.craigslist.org/search/apa?format=rss"
            res = requests.get(rss_url, headers={'User-Agent': 'HavenNest_Bot_v2.5.0'}, timeout=15)
            if res.status_code != 200:
                print(f"Craigslist RSS Error: {res.status_code}")
                return []
            
            soup = BeautifulSoup(res.text, 'html.parser') # 使用内置解析器
            items = soup.find_all('item')
            print(f"Found {len(items)} items in Craigslist RSS.")
            
            for i, item in enumerate(items[:limit]):
                try:
                    title = item.find('title').text
                    url = item.find('link').text
                    
                    # 价格通常在标题里，如 "$2,500 / 1br - 700ft2 - (Vancouver)"
                    price_match = re.search(r'\$(\d+,?\d*)', title)
                    price = 0
                    if price_match:
                        price = int(price_match.group(1).replace(',', ''))
                    
                    # 卧室数量通常也在标题里
                    beds = self.extract_beds(title)
                    
                    # 地址/区域
                    desc = item.find('description').text if item.find('description') else ""
                    # RSS 里的描述通常较短，或者包含坐标
                    
                    lat = float(item.find('geo:lat').text) if item.find('geo:lat') else None
                    lng = float(item.find('geo:long').text) if item.find('geo:long') else None
                    
                    # 如果没有坐标，尝试从标题提取区域
                    city = "Vancouver"
                    loc_match = re.search(r'\((.*?)\)$', title)
                    loc = loc_match.group(1) if loc_match else "Vancouver"
                    
                    if any(kw in loc.lower() for kw in ['richmond', '列治文']): city = "Richmond"
                    elif any(kw in loc.lower() for kw in ['burnaby', '本拿比']): city = "Burnaby"
                    
                    results.append({
                        "source": "Craigslist",
                        "title": title,
                        "price": price,
                        "url": url,
                        "address": loc,
                        "city": city,
                        "beds": beds,
                        "lat": lat,
                        "lng": lng,
                        "image": "",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except Exception as e:
                    continue
            
            print(f"DONE: Synced {len(results)} Craigslist listings via RSS.")
        except Exception as e:
            print(f"WARNING: Craigslist RSS crawl failed: {e}")
        return results

    def run(self):
        old_data = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                try: old_data = json.load(f)
                except: old_data = []
        
        # 爬取新数据
        new_data = self.process_manual_rentals() + self.crawl_craigslist()
        
        # 合并并去重 (以 URL 为准)
        data_map = {x['url']: x for x in old_data}
        for item in new_data:
            data_map[item['url']] = item # 新数据覆盖旧数据，更新日期
        
        # 过滤掉 45 天以前的数据
        cutoff = datetime.now() - timedelta(days=45)
        final = []
        for item in data_map.values():
            try:
                item_date = datetime.strptime(item.get('date', '2026-01-01'), '%Y-%m-%d')
                if item_date > cutoff:
                    final.append(item)
            except:
                final.append(item)

        # 保存
        print(f"Saving {len(final)} items to {self.filename}...")
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=4)
            
        print(f"FINISH: Listings task completed! Total {len(final)} items in listings.json.")

if __name__ == "__main__":
    HavenNestCrawler().run()
