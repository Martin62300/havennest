import cloudscraper
from bs4 import BeautifulSoup
import json, os, re, time
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

class HavenNestCrawler:
    def __init__(self):
        self.filename = 'listings.json'
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
        self.translator = GoogleTranslator(source='auto', target='zh-CN')
        self.valid_cities = ["Vancouver", "Richmond", "Burnaby", "Surrey", "Coquitlam", "New Westminster", "North Vancouver", "West Vancouver", "Langley", "Delta", "Port Coquitlam", "Port Moody"]

    def clean_loc(self, raw):
        if not raw: return "Vancouver"
        raw = raw.strip().title()
        for city in self.valid_cities:
            if city in raw: return city
        return "Vancouver"

    def crawl_craigslist(self, limit=30):
        print("🔍 正在通过官方 CDN 合成 Craigslist 实拍图...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            results = []
            for item in items[:limit]:
                # 🚀 核心优化：直接提取 ID 合成 CDN 链接，绕过防盗链 [cite: 2026-02-28]
                img_ids = item.get('data-ids', '').split(',')
                img_url = ""
                if img_ids and img_ids[0]:
                    clean_id = img_ids[0].replace('1:', '').split(':')[-1]
                    img_url = f"https://images.craigslist.org/{clean_id}_600x450.jpg"

                title = item.find('div', class_='title').text.strip()
                results.append({
                    "source": "Craigslist",
                    "title": title,
                    "title_cn": self.translator.translate(title[:200]),
                    "price": item.find('div', class_='price').text if item.find('div', class_='price') else "N/A",
                    "url": item.find('a')['href'],
                    "location": self.clean_loc(item.find('div', class_='location').text if item.find('div', class_='location') else ""),
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
            return results
        except Exception as e:
            print(f"❌ Craigslist 报错: {e}")
            return []

    def crawl_zumper(self, limit=30):
        print("🔍 正在抓取 Zumper 高清封面...")
        url = "https://www.zumper.com/apartments-for-rent/vancouver-bc"
        try:
            res = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('[data-testid="listing-card"]')
            results = []
            for item in items[:limit]:
                img_el = item.find('img')
                # 🚀 抓取 Zumper 原始图片源 [cite: 2026-02-28]
                img_url = img_el.get('data-src') or img_el.get('src') or ""
                title_el = item.select_one('[class*="Title"]')
                results.append({
                    "source": "Zumper",
                    "title": title_el.text.strip() if title_el else "Vancouver Suite",
                    "title_cn": self.translator.translate(title_el.text[:200]) if title_el else "精选公寓",
                    "price": item.select_one('[class*="Price"]').text if item.select_one('[class*="Price"]') else "N/A",
                    "url": "https://www.zumper.com" + item.select_one('a')['href'],
                    "location": "Vancouver",
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
            return results
        except Exception as e:
            print(f"❌ Zumper 报错: {e}")
            return []

    def run(self):
        # 🚀 增量合并逻辑：读取旧数据并合并 [cite: 2026-02-28]
        old_data = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        
        new_data = self.crawl_craigslist() + self.crawl_zumper()
        combined = new_data + old_data
        
        # 按 URL 去重并保留最新
        unique_data = {x['url']: x for x in combined}.values()
        # 清理 45 天前的陈旧数据
        cutoff = datetime.now() - timedelta(days=45)
        final_list = [x for x in unique_data if datetime.strptime(x.get('date', '2026-01-01'), '%Y-%m-%d') > cutoff]

        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(final_list, f, ensure_ascii=False, indent=4)
        print(f"✅ 任务成功：数据库当前共积攒 {len(final_list)} 条优质房源。")

if __name__ == "__main__":
    HavenNestCrawler().run()