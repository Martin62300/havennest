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
        # 🚀 强制初始化为空列表，实现你要求的“删除重抓”逻辑
        self.all_listings = [] 
        self.seen_urls = set()
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        self.translator = GoogleTranslator(source='auto', target='zh-CN')
        
        # 🏙️ 大温地区城市映射表（防止出现门牌号筛选）
        self.city_map = ["Vancouver", "Richmond", "Burnaby", "Surrey", "Coquitlam", "New Westminster", "North Vancouver", "West Vancouver", "Langley", "Delta", "Port Coquitlam", "Port Moody"]

    def clean_location(self, loc_str):
        # 🚀 核心优化：从乱七八糟的地址中提取标准城市名
        if not loc_str: return "Vancouver"
        loc_str = loc_str.strip().title()
        for city in self.city_map:
            if city in loc_str: return city
        return "Greater Vancouver"

    def ai_translate(self, text):
        if not text: return ""
        try: return self.translator.translate(text[:200])
        except: return text

    def crawl_craigslist(self, limit=30):
        print(f"🔍 正在抓取 Craigslist 最新房源并合成高清图片...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            count = 0
            for item in items:
                link = item.find('a')['href']
                if link in self.seen_urls: continue
                
                # 🚀 修正图片逻辑：直接从 data-ids 合成官方 CDN 链接，永不失效 [cite: 2026-02-28]
                img_ids = item.get('data-ids', '').split(',')
                img_url = ""
                if img_ids and img_ids[0]:
                    clean_id = img_ids[0].replace('1:', '').split(':')[-1]
                    img_url = f"https://images.craigslist.org/{clean_id}_300x225.jpg"

                title = item.find('div', class_='title').text.strip()
                raw_loc = item.find('div', class_='location').text if item.find('div', class_='location') else "Vancouver"
                
                self.all_listings.append({
                    "source": "Craigslist",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": item.find('div', class_='price').text if item.find('div', class_='price') else "N/A",
                    "url": link,
                    "location": self.clean_location(raw_loc), # 🚀 城市清洗
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                self.seen_urls.add(link)
                count += 1
                if count >= limit: break
        except Exception as e: print(f"❌ Craigslist 异常: {e}")

    def crawl_zumper(self, limit=30):
        print(f"🔍 正在同步 Zumper (提取实拍环境图)...")
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
                # 🚀 提取 Zumper 封面大图
                img_url = img_el.get('src') or ""

                self.all_listings.append({
                    "source": "Zumper",
                    "title": item.select_one('[class*="Title"]').text.strip() if item.select_one('[class*="Title"]') else "Vancouver Suite",
                    "title_cn": self.ai_translate(item.select_one('[class*="Title"]').text) if item.select_one('[class*="Title"]') else "精选套房",
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
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, ensure_ascii=False, indent=4)
        print(f"✅ 清洗完毕：数据库已重置，当前共抓取 {len(self.all_listings)} 条干净房源。")

if __name__ == "__main__":
    c = HavenNestCrawler()
    c.crawl_craigslist(30)
    time.sleep(3)
    c.crawl_zumper(30)
    c.save()