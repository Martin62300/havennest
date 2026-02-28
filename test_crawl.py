import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import re
from deep_translator import GoogleTranslator

class HavenNestCrawler:
    def __init__(self):
        self.all_listings = []
        self.seen_urls = set() # 👈 第一道防线：物理去重
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def clean_text(self, text):
        if not text: return ""
        # 彻底移除导致 VS Code 报错的异常行终止符
        text = re.sub(r'[\u2028\u2029\u0000-\u001f\u007f-\u009f]', '', text)
        return " ".join(text.split())

    def ai_translate(self, text):
        if not text: return ""
        try:
            # 采用“意译”逻辑，只翻译标题
            return self.translator.translate(self.clean_text(text)[:200])
        except:
            return text

    def crawl_craigslist(self, limit=10):
        print("🔍 正在同步 Craigslist...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            count = 0
            for item in items:
                link = item.find('a')['href']
                if link in self.seen_urls: continue
                
                title = self.clean_text(item.find('div', class_='title').text)
                self.all_listings.append({
                    "source": "Craigslist",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": self.clean_text(item.find('div', class_='price').text) if item.find('div', class_='price') else "面议",
                    "url": link,
                    "location": self.clean_text(item.find('div', class_='location').text) if item.find('div', class_='location') else "Vancouver",
                    "image": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800"
                })
                self.seen_urls.add(link)
                count += 1
                if count >= limit: break
        except Exception as e:
            print(f"❌ Craigslist 异常: {e}")

    def crawl_zumper(self, limit=10):
        print("🔍 正在同步 Zumper...")
        url = "https://www.zumper.com/apartments-for-rent/vancouver-bc"
        try:
            res = self.scraper.get(url, timeout=25)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 🚀 修复 NoneType 报错：增加判空逻辑
            items = soup.select('[data-testid="listing-card"]')
            count = 0
            for item in items:
                link_el = item.select_one('a[href*="/apartments-for-rent/"]')
                if not link_el: continue
                full_url = "https://www.zumper.com" + link_el['href']
                
                if full_url in self.seen_urls: continue

                title_el = item.select_one('[class*="Title"]')
                price_el = item.select_one('[class*="Price"]')
                title = self.clean_text(title_el.text) if title_el else "Vancouver Suite"

                self.all_listings.append({
                    "source": "Zumper",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": price_el.text if price_el else "面议",
                    "url": full_url,
                    "location": "Vancouver",
                    "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800"
                })
                self.seen_urls.add(full_url)
                count += 1
                if count >= limit: break
        except Exception as e:
            print(f"❌ Zumper 引擎异常: {e}")

    def save(self):
        with open('listings.json', 'w', encoding='utf-8') as f:
            json_data = json.dumps(self.all_listings, ensure_ascii=False, indent=4)
            f.write(re.sub(r'[\u2028\u2029]', '', json_data)) # 彻底清洗
        print(f"📊 任务结束：共存入 {len(self.all_listings)} 条纯净房源。")

if __name__ == "__main__":
    c = HavenNestCrawler(); c.crawl_craigslist(); c.crawl_zumper(); c.save()