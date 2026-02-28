import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from deep_translator import GoogleTranslator

class HavenNestCrawler:
    def __init__(self):
        self.all_listings = []
        self.seen_urls = set() # 👈 物理去重：确保不出现重复房源
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def clean_illegal_chars(self, text):
        """杀掉所有导致 JSON 报错的不可见字符"""
        if not text: return ""
        text = re.sub(r'[\u2028\u2029\u0000-\u001f\u007f-\u009f]', '', text)
        return " ".join(text.split())

    def ai_translate(self, text):
        """真正好用的 AI 汉化，不只是单词替换"""
        if not text: return ""
        try:
            cleaned = self.clean_illegal_chars(text)
            return self.translator.translate(cleaned[:350])
        except:
            return cleaned

    def crawl_craigslist(self, limit=12):
        print("🔍 正在同步 Craigslist 深度汉化数据...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')
            
            count = 0
            for item in items:
                link = item.find('a')['href']
                if link in self.seen_urls: continue # 👈 拦截重复
                
                title = self.clean_illegal_chars(item.find('div', class_='title').text)
                
                # 抓取详情图
                d_res = self.scraper.get(link, timeout=10)
                d_soup = BeautifulSoup(d_res.text, 'html.parser')
                img_el = d_soup.find('img')
                img_url = img_el['src'] if img_el else "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800"

                self.all_listings.append({
                    "source": "Craigslist",
                    "native_lang": "en",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": item.find('div', class_='price').text if item.find('div', class_='price') else "面议",
                    "url": link,
                    "location": self.clean_illegal_chars(item.find('div', class_='location').text) if item.find('div', class_='location') else "Vancouver",
                    "image": img_url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                self.seen_urls.add(link)
                count += 1
                if count >= limit: break
                time.sleep(1)
        except Exception as e:
            print(f"❌ Craigslist 引擎异常: {e}")

    def crawl_zumper(self, limit=12):
        print("🔍 正在同步 Zumper 高质量数据源...")
        url = "https://www.zumper.com/apartments-for-rent/vancouver-bc"
        try:
            res = self.scraper.get(url, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('[data-testid="listing-card"]')
            
            count = 0
            for item in items:
                link_el = item.select_one('a[href*="/apartments-for-rent/"]')
                if not link_el: continue
                full_url = "https://www.zumper.com" + link_el['href']
                
                if full_url in self.seen_urls: continue 

                title_el = item.select_one('[class*="Title"]')
                title = self.clean_illegal_chars(title_el.text) if title_el else "Vancouver Suite"
                price_el = item.select_one('[class*="Price"]')

                self.all_listings.append({
                    "source": "Zumper",
                    "native_lang": "en",
                    "title": title,
                    "title_cn": self.ai_translate(title),
                    "price": price_el.text if price_el else "面议",
                    "url": full_url,
                    "location": "Vancouver",
                    "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800",
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                self.seen_urls.add(full_url)
                count += 1
                if count >= limit: break
        except Exception as e:
            print(f"❌ Zumper 引擎异常: {e}")

    def save(self):
        with open('listings.json', 'w', encoding='utf-8') as f:
            json_str = json.dumps(self.all_listings, ensure_ascii=False, indent=4)
            # 最后的双重清理，确保无 LS/PS 符号
            cleaned_json = re.sub(r'[\u2028\u2029]', '', json_str)
            f.write(cleaned_json)
        print(f"📊 任务结束：Havennest 已同步 {len(self.all_listings)} 条最新服务数据。")

if __name__ == "__main__":
    crawler = HavenNestCrawler()
    crawler.crawl_craigslist() 
    crawler.crawl_zumper()
    crawler.save()