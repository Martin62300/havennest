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
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def force_clean(self, text):
        """终极清理：彻底移除导致 VS Code 报错的所有非法字符"""
        if not text: return ""
        # 移除 LS (\u2028), PS (\u2029) 以及控制字符
        clean_text = re.sub(r'[\u2028\u2029\u0000-\u001f\u007f-\u009f]', '', text)
        return " ".join(clean_text.split())

    def ai_translate(self, text):
        if not text: return ""
        try:
            return self.translator.translate(self.force_clean(text)[:300])
        except:
            return self.force_clean(text)

    def crawl_craigslist(self, limit=10):
        print("🔍 正在抓取 Craigslist 并进行 AI 汉化...")
        url = "https://vancouver.craigslist.org/search/apa"
        try:
            res = self.scraper.get(url, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('li', class_='cl-static-search-result')[:limit]
            
            for item in items:
                link = item.find('a')['href']
                title = self.force_clean(item.find('div', class_='title').text)
                
                # 深度抓图
                d_res = self.scraper.get(link, timeout=30)
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
                    "location": self.force_clean(item.find('div', class_='location').text) if item.find('div', class_='location') else "Vancouver",
                    "image": img_url
                })
                print(f"✅ [Craigslist] 已翻译: {title[:15]}...")
                time.sleep(1)
        except Exception as e:
            print(f"❌ Craigslist 异常: {e}")

    def crawl_zumper(self, limit=10):
        print("🔍 正在转向抓取 Zumper 高质量房源...")
        url = "https://www.zumper.com/apartments-for-rent/vancouver-bc"
        try:
            res = self.scraper.get(url, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Zumper 的房源卡片通常在特定的 Feed 类中
            items = soup.select('[data-testid="listing-card"]')[:limit]
            
            for item in items:
                title_el = item.select_one('[class*="Title"]')
                link_el = item.select_one('a[href*="/apartments-for-rent/"]')
                price_el = item.select_one('[class*="Price"]')
                
                if title_el and link_el:
                    title = self.force_clean(title_el.text)
                    self.all_listings.append({
                        "source": "Zumper",
                        "native_lang": "en",
                        "title": title,
                        "title_cn": self.ai_translate(title),
                        "price": price_el.text if price_el else "面议",
                        "url": "https://www.zumper.com" + link_el['href'],
                        "location": "Vancouver",
                        "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800" # Zumper 需特殊处理图片流，先用高清占位
                    })
                    print(f"✅ [Zumper] 已处理: {title[:15]}...")
            
            print(f"✨ Zumper 获取成功，增加 {len(self.all_listings)} 条精选房源。")
        except Exception as e:
            print(f"❌ Zumper 抓取失败: {e}")

    def save(self):
        with open('listings.json', 'w', encoding='utf-8') as f:
            json_str = json.dumps(self.all_listings, ensure_ascii=False, indent=4)
            # 物理级剔除异常行终止符
            cleaned_json = re.sub(r'[\u2028\u2029]', '', json_str)
            f.write(cleaned_json)
        print(f"📊 任务结束：JSON 文件已彻底清洗并存入 {len(self.all_listings)} 条数据。")

if __name__ == "__main__":
    crawler = HavenNestCrawler()
    crawler.crawl_craigslist(limit=10) 
    crawler.crawl_zumper(limit=10)
    crawler.save()