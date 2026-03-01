import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

class HavenNestCrawler:
    def __init__(self):
        self.filename = 'listings.json'
        self.all_listings = self.load_existing_data()
        self.seen_urls = {item['url'] for item in self.all_listings}
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def load_existing_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except: return []
        return []

    def clean_old_data(self, days=45):
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.all_listings)
        self.all_listings = [
            item for item in self.all_listings 
            if datetime.strptime(item.get('date', datetime.now().strftime("%Y-%m-%d")), '%Y-%m-%d') > cutoff_date
        ]
        print(f"🧹 自动清理：已移除 {initial_count - len(self.all_listings)} 条过期房源。")

    def ai_translate(self, text):
        if not text: return ""
        try: return self.translator.translate(text[:200])
        except: return text

    def crawl_craigslist(self, limit=25):
        print(f"🔍 正在抓取 Craigslist (增强图片解析逻辑)...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            count = 0
            for item in items:
                link = item.find('a')['href']
                if link in self.seen_urls: continue
                
                # 🚀 深度图片合成逻辑：使用 7A 格式提升加载成功率 [cite: 2026-02-28]
                img_ids = item.get('data-ids', '').split(',')
                img_url = ""
                if img_ids and img_ids[0]:
                    clean_id = img_ids[0].replace('1:', '').split(':')[-1]
                    img_url = f"https://images.craigslist.org/{clean_id}_300x225.jpg"

                title = item.find('div', class_='title').text.strip()
                self.all_listings.insert(0, {
                    "source": "Craigslist",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": item.find('div', class_='price').text if item.find('div', class_='price') else "N/A",
                    "url": link,
                    "location": "Vancouver",
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                self.seen_urls.add(link)
                count += 1
                if count >= limit: break
        except Exception as e: print(f"❌ Craigslist 异常: {e}")

    def crawl_zumper(self, limit=25):
        print(f"🔍 正在同步 Zumper (增强选择器稳定性)...")
        url = "https://www.zumper.com/apartments-for-rent/vancouver-bc"
        try:
            res = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('[data-testid="listing-card"]')
            count = 0
            for item in items:
                link_el = item.select_one('a[href*="/apartments-for-rent/"]')
                if not link_el: continue
                full_url = "https://www.zumper.com" + link_el['href']
                if full_url in self.seen_urls: continue

                img_el = item.find('img')
                # 🚀 尝试抓取高清大图源
                img_url = img_el.get('data-src') or img_el.get('src') or ""

                self.all_listings.insert(0, {
                    "source": "Zumper",
                    "title": item.select_one('[class*="Title"]').text.strip() if item.select_one('[class*="Title"]') else "Vancouver Suite",
                    "title_cn": self.ai_translate(item.select_one('[class*="Title"]').text) if item.select_one('[class*="Title"]') else "精选公寓",
                    "price": item.select_one('[class*="Price"]').text if item.select_one('[class*="Price"]') else "N/A",
                    "url": full_url,
                    "location": "Vancouver",
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                self.seen_urls.add(full_url)
                count += 1
                if count >= limit: break
        except Exception as e: print(f"❌ Zumper 异常: {e}")

    def save(self):
        self.clean_old_data() 
        # 强制按日期排序，确保最新的在网页最上方 [cite: 2026-02-28]
        self.all_listings.sort(key=lambda x: x.get('date', ''), reverse=True)
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, ensure_ascii=False, indent=4)
        print(f"📊 同步结束：数据库共积攒 {len(self.all_listings)} 条带图房源。")

if __name__ == "__main__":
    c = HavenNestCrawler()
    c.crawl_craigslist(25)
    time.sleep(5)
    c.crawl_zumper(25)
    c.save()