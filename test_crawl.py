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
        # 🚀 自动清理逻辑：删除45天前的陈旧房源 [cite: 2026-02-28]
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.all_listings)
        self.all_listings = [
            item for item in self.all_listings 
            if datetime.strptime(item.get('date', '2026-01-01'), '%Y-%m-%d') > cutoff_date
        ]
        print(f"🧹 已清理 {initial_count - len(self.all_listings)} 条陈旧房源。")

    def ai_translate(self, text):
        if not text: return ""
        try:
            clean_t = re.sub(r'[\u2028\u2029\u0000-\u001f\u007f-\u009f]', '', text)
            return self.translator.translate(clean_t[:200])
        except: return text

    def crawl_craigslist(self, limit=20):
        print(f"🔍 正在追加 Craigslist 最新房源 (上限 {limit})...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            count = 0
            for item in items:
                link = item.find('a')['href']
                if link in self.seen_urls: continue
                
                title = item.find('div', class_='title').text.strip()
                self.all_listings.insert(0, { # 🚀 新房源放在最前面
                    "source": "Craigslist",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": item.find('div', class_='price').text if item.find('div', class_='price') else "N/A",
                    "url": link,
                    "location": item.find('div', class_='location').text.strip() if item.find('div', class_='location') else "Vancouver",
                    "image": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800",
                    "date": datetime.now().strftime("%Y-%m-%d") # 🚀 记录抓取日期用于清理
                })
                self.seen_urls.add(link)
                count += 1
                if count >= limit: break
        except Exception as e: print(f"❌ Craigslist 异常: {e}")

    def save(self):
        self.clean_old_data() # 🚀 保存前先清理
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, ensure_ascii=False, indent=4)
        print(f"📊 数据库已更新：当前共积攒 {len(self.all_listings)} 条优质房源。")

if __name__ == "__main__":
    c = HavenNestCrawler(); c.crawl_craigslist(); c.save()