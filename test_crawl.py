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
        # 🏙️ 核心修正：只识别以下标准城市
        self.valid_cities = ["Vancouver", "Richmond", "Burnaby", "Surrey", "Coquitlam", "New Westminster", "North Vancouver", "West Vancouver", "Langley", "Delta", "Port Coquitlam", "Port Moody"]

    def clean_loc(self, raw):
        if not raw: return "Vancouver"
        raw = raw.strip().title()
        for city in self.valid_cities:
            if city in raw: return city
        return "Vancouver"

    def crawl_craigslist(self, limit=30):
        print("🔍 正在提取 Craigslist 高清图片源...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            results = []
            for item in items[:limit]:
                # 🚀 核心修复：通过 ID 合成 CDN 链接，这种链接存活率最高 [cite: 2026-02-28]
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
        except: return []

    def crawl_zumper(self, limit=30):
        print("🔍 正在同步 Zumper 实景图...")
        url = "https://www.zumper.com/apartments-for-rent/vancouver-bc"
        try:
            res = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('[data-testid="listing-card"]')
            results = []
            for item in items[:limit]:
                img_el = item.find('img')
                img_url = img_el['src'] if (img_el and 'src' in img_el.attrs) else ""
                title_el = item.select_one('[class*="Title"]')
                title = title_el.text.strip() if title_el else "Vancouver Suite"
                results.append({
                    "source": "Zumper",
                    "title": title,
                    "title_cn": self.translator.translate(title[:200]),
                    "price": item.select_one('[class*="Price"]').text if item.select_one('[class*="Price"]') else "N/A",
                    "url": "https://www.zumper.com" + item.select_one('a')['href'],
                    "location": "Vancouver",
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
            return results
        except: return []

    def run(self):
        data = self.crawl_craigslist() + self.crawl_zumper()
        # 🚀 物理去重并保存
        unique_data = {x['url']: x for x in data}.values()
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(list(unique_data), f, ensure_ascii=False, indent=4)
        print(f"✅ 成功积攒 {len(unique_data)} 条带图房源。")

if __name__ == "__main__":
    HavenNestCrawler().run()