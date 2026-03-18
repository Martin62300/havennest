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
        # Airtable Config
        self.airtable_token = 'pat2AFw6PJ7WRwGTy.11c7c578063429d1757a89ca9abb523e122370c8f13ede3990c7b090bde6b364'
        self.airtable_base = 'appfs8aXtirNbrbWa'
        self.airtable_table = 'Table 1'

    def process_airtable_listings(self):
        """从 Airtable 获取屋主发布的房源并进行地理编码解析"""
        print("Fetching Airtable listings...")
        url = f"https://api.airtable.com/v0/{self.airtable_base}/{self.airtable_table}"
        headers = {"Authorization": f"Bearer {self.airtable_token}"}
        
        results = []
        try:
            res = requests.get(url, headers=headers, timeout=15)
            data = res.json()
            
            for r in data.get('records', []):
                f = r.get('fields', {})
                addr = f.get('房源具体地址 (Address)', "Vancouver")
                title = f.get('房源标题 (Listing Title)', "Rental Listing")
                photos = [p['url'] for p in f.get('房源照片 / Property Photos', [])]
                
                # 城市识别
                city = f.get('所在城市 (City)', "")
                if not city:
                    search_str = (title + " " + addr).lower()
                    if any(k in search_str for k in ['richmond', '列治文', 'lansdowne']):
                        city = "Richmond"
                    else:
                        city = "Vancouver"

                # 卧室数量识别
                beds = f.get('卧室数量 (Beds)')
                try: beds = int(beds)
                except:
                    desc = f.get('房源描述 (Description)', "")
                    beds = self.extract_beds(title + " " + desc)

                # 地理编码解析 (核心修复：由爬虫统一解析地址)
                lat, lng = self.get_lat_lng(addr)
                if not lat or not lng:
                    # 如果解析失败，根据城市分配默认坐标
                    if city == "Richmond":
                        lat, lng = 49.1666, -123.1336
                    else:
                        lat, lng = 49.2827, -123.1207

                item = {
                    "id": r['id'],
                    "source": "owner",
                    "title": title,
                    "price": int(f.get('月租金 (Monthly Rent)', 0)),
                    "url": f"https://havennestapp.com/listing/{r['id']}", # 伪链接，详情由前端Modal展示
                    "address": addr,
                    "city": city,
                    "beds": beds,
                    "lat": lat,
                    "lng": lng,
                    "image": photos[0] if photos else "",
                    "images": photos,
                    "desc": f.get('房源描述 (Description)', "No description."),
                    "phone": f.get('联系电话 (Phone)'),
                    "email": f.get('电子邮箱 (Email)'),
                    "isPromo": True, # 屋主发布的房源默认为推广房源
                    "date": datetime.now().strftime('%Y-%m-%d')
                }
                results.append(item)
            print(f"DONE: Processed {len(results)} Airtable listings.")
        except Exception as e:
            print(f"ERROR: Airtable processing failed: {e}")
        return results

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

                    # 提取卧室
                    beds_match = re.search(r'"bedroomCount":\s*(\d+)', block)
                    beds = int(beds_match.group(1)) if beds_match else self.extract_beds(title)

                    # 提取图片 (改进：寻找多种可能的图片字段)
                    img_url = ""
                    # 尝试从 gallery 提取
                    img_match = re.search(r'"url":\s*"(https://assets\.rentsync\.com/.*?)"', block)
                    if img_match:
                        img_url = img_match.group(1)
                    else:
                        # 尝试从 thumbnail 提取
                        thumb_match = re.search(r'"thumbnail":\s*"(.*?)"', block)
                        if thumb_match: img_url = thumb_match.group(1)

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
        """改进版 Craigslist 抓取：获取图片和描述"""
        print(f"Crawling Craigslist via Web (limit {limit})... ")
        results = []
        scraper = cloudscraper.create_scraper()
        try:
            url = "https://vancouver.craigslist.org/search/apa"
            res = scraper.get(url, timeout=20)
            if res.status_code != 200: return []
            
            soup = BeautifulSoup(res.text, 'html.parser')
            posts = soup.find_all('li', class_='cl-static-search-result')
            
            for post in posts[:limit]:
                try:
                    title_el = post.find('div', class_='title')
                    if not title_el: continue
                    title = title_el.text.strip()
                    
                    link_el = post.find('a')
                    detail_url = link_el.get('href', '')
                    
                    price_el = post.find('div', class_='price')
                    price = int(re.sub(r'[^\d]', '', price_el.text)) if price_el else 0
                    
                    # 深度抓取详情页获取图片集和描述
                    print(f"  Deep crawling Craigslist: {title[:20]}...")
                    d_res = scraper.get(detail_url, timeout=15)
                    d_soup = BeautifulSoup(d_res.text, 'html.parser')
                    
                    images = []
                    for img in d_soup.select('.gallery img'):
                        src = img.get('src')
                        if src: images.append(src)
                    
                    desc_el = d_soup.select_one('#postingbody')
                    desc = desc_el.text.replace('QR Code Link to This Post', '').strip() if desc_el else ""

                    loc_el = post.find('div', class_='location')
                    loc = loc_el.text.strip() if loc_el else "Vancouver"
                    
                    city = "Vancouver"
                    if any(kw in loc.lower() for kw in ['richmond', '列治文']): city = "Richmond"
                    elif any(kw in loc.lower() for kw in ['burnaby', '本拿比']): city = "Burnaby"
                    
                    results.append({
                        "source": "Craigslist",
                        "title": title,
                        "price": price,
                        "url": detail_url,
                        "address": loc,
                        "city": city,
                        "beds": self.extract_beds(title + " " + desc),
                        "lat": None,
                        "lng": None,
                        "image": images[0] if images else "",
                        "images": images,
                        "desc": desc,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                    time.sleep(1)
                except: continue
            
            # 补充坐标
            print(f"Geocoding {len(results)} Craigslist items...")
            for item in results:
                item['lat'], item['lng'] = self.get_lat_lng(item['address'] + ", " + item['city'])

            return results
        except Exception as e:
            print(f"WARNING: Craigslist Web crawl failed: {e}")
            return self.crawl_craigslist_rss(limit)
        return results

    def crawl_craigslist_rss(self, limit=40):
        print(f"Fallback: Crawling Craigslist via RSS...")
        # ... (保留原有的 RSS 逻辑作为备份)
        results = []
        try:
            rss_url = "https://vancouver.craigslist.org/search/apa?format=rss"
            res = requests.get(rss_url, headers={'User-Agent': 'HavenNest_Bot_v2.5.0'}, timeout=15)
            soup = BeautifulSoup(res.text, 'xml')
            items = soup.find_all('item')
            for item in items[:limit]:
                try:
                    title = item.find('title').text
                    url = item.find('link').text
                    price_match = re.search(r'\$(\d+,?\d*)', title)
                    price = int(price_match.group(1).replace(',', '')) if price_match else 0
                    beds = self.extract_beds(title)
                    lat = float(item.find('geo:lat').text) if item.find('geo:lat') else None
                    lng = float(item.find('geo:long').text) if item.find('geo:long') else None
                    loc_match = re.search(r'\((.*?)\)$', title)
                    loc = loc_match.group(1) if loc_match else "Vancouver"
                    city = "Vancouver"
                    if "richmond" in loc.lower(): city = "Richmond"
                    
                    results.append({
                        "source": "Craigslist", "title": title, "price": price, "url": url,
                        "address": loc, "city": city, "beds": beds, "lat": lat, "lng": lng,
                        "image": "", "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except: continue
        except: pass
        return results

    def crawl_vanpeople(self, limit=30):
        """抓取 VanPeople (人在温哥华) 房源信息，深度抓取详情页获取图片和描述"""
        print(f"Crawling VanPeople (limit {limit})... ")
        results = []
        scraper = cloudscraper.create_scraper()
        
        ad_keywords = ['搬家', '清洁', '接送', '教练', '维修', '垃圾', '快递', '求职', '招聘', '服务', '公司', '专业', '诚聘', '货运', '物流', '修车']
        
        try:
            url = "https://c.vanpeople.com/zufang/"
            res = scraper.get(url, timeout=20)
            res.encoding = 'utf-8'
            if res.status_code != 200: return []
            
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('div', class_='c-list-contxt')
            
            count = 0
            for item in items:
                if count >= limit: break
                try:
                    title_el = item.find('a', class_='c-list-title')
                    if not title_el: continue
                    title = title_el.text.strip()
                    
                    # 增强过滤逻辑：标题关键词过滤
                    if any(kw in title for kw in ad_keywords): continue
                    
                    detail_url = title_el.get('href', '')
                    if detail_url and not detail_url.startswith('http'): detail_url = "https://c.vanpeople.com" + detail_url
                    
                    price_el = item.find('span', class_='money')
                    price = int(re.sub(r'[^\d]', '', price_el.text)) if price_el else 0
                    
                    # 增强过滤逻辑：价格为0且包含特定词汇
                    if price == 0 and any(kw in title for kw in ['公司', '专业', '华人', '优惠', '电话', '特惠']): 
                        continue

                    # 深度抓取详情页
                    print(f"  Deep crawling: {title[:20]}...")
                    detail_res = scraper.get(detail_url, timeout=15)
                    detail_res.encoding = 'utf-8'
                    detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    
                    # 1. 提取所有图片 (深度暴力搜索：JSON, 脚本, 以及各种属性)
                    images = []
                    
                    # 方式 A: 搜索源代码中的图片 JSON 数组 (VanPeople 常用格式)
                    photo_matches = re.findall(r'https?://[^\s"\'<>]+?\.(?:jpg|jpeg|png|webp)', detail_res.text)
                    for p in photo_matches:
                        if 'vanpeople.com' in p and ('/ad/' in p or '/images/' in p) and 'avatar' not in p and 'logo' not in p:
                            if p not in images: images.append(p)

                    # 方式 B: 如果方式 A 没找到，使用 DOM 选择器
                    if not images:
                        img_els = detail_soup.select('img[data-src], img[lazy-src], .view-gallery img, .swiper-slide img, .img-box img')
                        for img in img_els:
                            src = img.get('data-src') or img.get('lazy-src') or img.get('swiper-lazy') or img.get('src')
                            if src:
                                if src.startswith('//'): src = "https:" + src
                                elif src.startswith('/'): src = "https://c.vanpeople.com" + src
                                if 'vanpeople.com' in src and 'avatar' not in src and 'logo' not in src:
                                    if src not in images: images.append(src)
                    
                    # 2. 提取描述并深度清洗
                    desc_el = detail_soup.select_one('.detail-desc, .info-content, .description, #info-content, .text-content, .ad-detail-content')
                    desc = desc_el.text.strip() if desc_el else ""
                    
                    # 移除描述中的垃圾信息
                    junk_patterns = [
                        r'微信扫二维码分享到朋友圈', r'联系我时请说明是在vanpeople看到的', r'重要警示：不法骗子.*',
                        r'谨慎租房防诈骗.*', r'扫码添加微信客服', r'点击下载协议', r'我要举报', r'相关广告'
                    ]
                    for pattern in junk_patterns:
                        desc = re.sub(pattern, '', desc, flags=re.DOTALL)
                    
                    desc = re.sub(r'\n\s*\n', '\n', desc).strip()

                    # 提取区域
                    loc_el = item.find('span', class_='class')
                    loc = loc_el.text.strip() if loc_el else "Vancouver"
                    
                    city = "Vancouver"
                    if any(kw in loc.lower() or kw in title.lower() for kw in ['richmond', '列治文']): city = "Richmond"
                    elif any(kw in loc.lower() or kw in title.lower() for kw in ['burnaby', '本拿比']): city = "Burnaby"

                    results.append({
                        "source": "VanPeople",
                        "title": title,
                        "price": price,
                        "url": detail_url,
                        "address": loc,
                        "city": city,
                        "beds": self.extract_beds(title + " " + desc),
                        "lat": None,
                        "lng": None,
                        "image": images[0] if images else "",
                        "images": images,
                        "desc": desc if desc else "请点击'查看原房源'获取更多详细信息。",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                    count += 1
                    time.sleep(1) # 礼貌抓取
                except Exception as e:
                    print(f"  Error crawling detail: {e}")
                    continue
            
            # 补充坐标
            print(f"Geocoding {len(results)} VanPeople items...")
            for i, item in enumerate(results):
                item['lat'], item['lng'] = self.get_lat_lng(item['address'] + ", " + item['city'])

            return results
        except Exception as e:
            print(f"WARNING: VanPeople crawl failed: {e}")
        return results

    def run(self):
        # 加载旧数据
        old_data = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                try: old_data = json.load(f)
                except: old_data = []
        
        # 爬取新数据
        new_data = self.process_airtable_listings() + self.process_manual_rentals() + \
                   self.crawl_craigslist() + self.crawl_vanpeople()
        
        # 合并并去重
        data_map = {}
        for x in old_data:
            key = x.get('url') or x.get('id')
            if key: data_map[key] = x

        for item in new_data:
            key = item.get('url') or item.get('id')
            if key: data_map[key] = item
        
        # 清理旧房源逻辑改进：
        # 1. 屋主发布的推广房源 (isPromo) 永久保留
        # 2. 抓取的房源如果超过 60 天（约2个月）则彻底删除
        # 3. 抓取的房源建议展示近 4 周的（由前端或爬虫控制，这里执行删除逻辑）
        
        cutoff_delete = datetime.now() - timedelta(days=60) # 2个月强制删除
        
        final = []
        for item in data_map.values():
            if item.get('isPromo'):
                final.append(item)
                continue
            
            try:
                item_date = datetime.strptime(item.get('date', '2026-01-01'), '%Y-%m-%d')
                if item_date > cutoff_delete:
                    final.append(item)
            except:
                final.append(item)

        # 排序：推广房源置顶
        final.sort(key=lambda x: x.get('isPromo', False), reverse=True)

        print(f"Saving {len(final)} items (cleaned old listings)...")
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=4)
        print(f"FINISH: Total {len(final)} items.")

if __name__ == "__main__":
    HavenNestCrawler().run()
