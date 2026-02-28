import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import re
from deep_translator import GoogleTranslator

class HavenNestCrawler:
    def __init__(self):
        self.all_listings = []
        self.seen_urls = set() # 👈 强化去重逻辑
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def clean_text(self, text):
        if not text: return ""
        # 彻底解决异常行终止符报错
        text = re.sub(r'[\u2028\u2029\u0000-\u001f\u007f-\u009f]', '', text)
        return " ".join(text.split())

    def ai_translate(self, text):
        if not text: return ""
        try:
            # 这里的汉化会更注重意译
            return self.translator.translate(self.clean_text(text)[:300])
        except:
            return text

    def crawl_source(self, name, url, item_selector, limit=12):
        print(f"🔍 正在同步 {name} 房源...")
        try:
            res = self.scraper.get(url, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 根据来源选择不同的解析逻辑
            if name == "Craigslist":
                items = soup.find_all('li', class_='cl-static-search-result')
            else: # Zumper
                items = soup.select('[data-testid="listing-card"]')
            
            count = 0
            for item in items:
                link_el = item.find('a', href=True)
                if not link_el: continue
                full_url = link_el['href'] if link_el['href'].startswith('http') else f"https://www.{name.lower()}.com{link_el['href']}"
                
                if full_url in self.seen_urls: continue # 👈 物理去重
                
                title_text = item.find('div', class_='title').text if name == "Craigslist" else item.select_one('[class*="Title"]').text
                title = self.clean_text(title_text)

                self.all_listings.append({
                    "source": name,
                    "title": title,
                    "title_cn": self.ai_translate(title), # 👈 汉化标题
                    "price": self.clean_text(item.find('div', class_='price').text if name == "Craigslist" else item.select_one('[class*="Price"]').text),
                    "url": full_url,
                    "location": self.clean_text(item.find('div', class_='location').text if name == "Craigslist" else "Vancouver"),
                    "image": item.find('img')['src'] if item.find('img') else "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800"
                })
                self.seen_urls.add(full_url)
                count += 1
                if count >= limit: break
                time.sleep(1)
        except Exception as e:
            print(f"❌ {name} 异常: {e}")

    def save(self):
        with open('listings.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_listings, f, ensure_ascii=False, indent=4)
        print(f"📊 任务结束：Havennest 已存入 {len(self.all_listings)} 条数据。")

if __name__ == "__main__":
    crawler = HavenNestCrawler()
    crawler.crawl_source("Craigslist", "https://vancouver.craigslist.org/search/apa", None)
    crawler.crawl_source("Zumper", "https://www.zumper.com/apartments-for-rent/vancouver-bc", None)
    crawler.save()