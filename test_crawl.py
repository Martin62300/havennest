import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

class HavenNestCrawler:
    def __init__(self):
        self.filename = 'listings.json'
        self.all_listings = self.load_existing_data()
        self.seen_urls = {item['url'] for item in self.all_listings}
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def load_existing_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return []
        return []

    def clean_old_data(self, days=45):
        # 🚀 自动清理逻辑：物理删除 45 天前的陈旧房源
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.all_listings)
        self.all_listings = [
            item for item in self.all_listings 
            if datetime.strptime(item.get('date', datetime.now().strftime("%Y-%m-%d")), '%Y-%m-%d') > cutoff_date
        ]
        print(f"🧹 自动清理：已移除 {initial_count - len(self.all_listings)} 条陈旧房源。")

    def ai_translate(self, text):
        if not text: return ""
        try:
            clean_t = re.sub(r'[\u2028\u2029\u0000-\u001f\u007f-\u009f]', '', text)
            return self.translator.translate(clean_t[:200])
        except: return text

    def crawl_craigslist(self, limit=20):
        print(f"🔍 正在抓取 Craigslist 实拍大图房源...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            count = 0
            for item in items:
                link = item.find('a')['href']
                if link in self.seen_urls: continue
                
                # 🚀 提取真实图片逻辑
                # Craigslist 搜索页通常包含图片 ID
                img_id = item.get('data-ids', '').split(',')[0].replace('1:', '')
                img_url = f"https://images.craigslist.org/{img_id}_300x225.jpg" if img_id else "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800"

                title = item.find('div', class_='title').text.strip()
                self.all_listings.insert(0, {
                    "source": "Craigslist",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": item.find('div', class_='price').text if item.find('div', class_='price') else "N/A",
                    "url": link,
                    "location": item.find('div', class_='location').text.strip() if item.find('div', class_='location') else "Vancouver",
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                self.seen_urls.add(link)
                count += 1
                if count >= limit: break
        except Exception as e: print(f"❌ Craigslist 异常: {e}")

    def crawl_zumper(self, limit=20):
        print(f"🔍 正在抓取 Zumper 真实实景房源...")
        url = "https://www.zumper.com/apartments-for-rent/vancouver-bc"
        try:
            res = self.scraper.get(url, timeout=25)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('[data-testid="listing-card"]')
            count = 0
            for item in items:
                link_el = item.select_one('a[href*="/apartments-for-rent/"]')
                if not link_el: continue
                full_url = "https://www.zumper.com" + link_el['href']
                if full_url in self.seen_urls: continue

                title_el = item.select_one('[class*="Title"]')
                img_el = item.find('img')
                # 🚀 抓取 Zumper 真实图片
                real_img = img_el['src'] if (img_el and img_el.has_attr('src')) else "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800"

                self.all_listings.insert(0, {
                    "source": "Zumper",
                    "title": title_el.text.strip() if title_el else "Vancouver Suite",
                    "title_cn": self.ai_translate(title_el.text) if title_el else "精选套房",
                    "price": item.select_one('[class*="Price"]').text if item.select_one('[class*="Price"]') else "N/A",
                    "url": full_url,
                    "location": "Vancouver",
                    "image": real_img,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                self.seen_urls.add(full_url)
                count += 1
                if count >= limit: break
        except Exception as e: print(f"❌ Zumper 异常: {e}")

    def save(self):
        self.clean_old_data() 
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, ensure_ascii=False, indent=4)
        print(f"📊 任务结束：当前数据库共积攒 {len(self.all_listings)} 条带真实图片的房源。")

if __name__ == "__main__":
    c = HavenNestCrawler()
    c.crawl_craigslist(limit=20)
    c.crawl_zumper(limit=20)
    c.save()