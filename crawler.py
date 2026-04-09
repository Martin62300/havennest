import json
import os
import re
import time
import glob
import requests
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote_plus, urlparse
import cloudscraper
from bs4 import BeautifulSoup

class HavenNestCrawler:
    def __init__(self):
        self.filename = 'listings.json'
        self.raw_rentals_file = 'rentals_raw.json'
        self.cache_file = 'coords_cache.json'
        self.coords_cache = self._load_cache()
        self.owner_media_dir = 'owner_media'
        self.owner_media_max_photos = 5
        self.media_backend = (os.getenv('HAVENNEST_MEDIA_BACKEND') or '').strip().lower()
        self.r2_endpoint = (os.getenv('R2_ENDPOINT') or '').strip()
        self.r2_bucket = (os.getenv('R2_BUCKET') or '').strip()
        self.r2_access_key_id = (os.getenv('R2_ACCESS_KEY_ID') or '').strip()
        self.r2_secret_access_key = (os.getenv('R2_SECRET_ACCESS_KEY') or '').strip()
        self.r2_public_base_url = (os.getenv('R2_PUBLIC_BASE_URL') or '').strip().rstrip('/')
        if not self.media_backend:
            self.media_backend = 'r2' if (self.r2_bucket and self.r2_access_key_id and self.r2_secret_access_key and self.r2_public_base_url) else 'local'
        # Airtable Config
        self.airtable_token = (os.getenv('AIRTABLE_TOKEN') or '').strip()
        self.airtable_base = 'appfs8aXtirNbrbWa'
        self.airtable_table = 'Table 1'

        if os.getenv('GITHUB_ACTIONS') == 'true':
            print(f"Media backend: {self.media_backend}")
            if self.media_backend == 'r2':
                ok = all([self.r2_bucket, self.r2_access_key_id, self.r2_secret_access_key, self.r2_public_base_url])
                print(f"R2 config present: {ok}")
            print(f"Airtable token present: {bool(self.airtable_token)}")

    def infer_city_info(self, text):
        if not text:
            return {"city": "", "key": "", "strength": 0}
        s = str(text).lower()
        s_strip = s.strip()

        starts = [
            ("rmd", "Richmond"),
            ("richmond", "Richmond"),
            ("列治文", "Richmond"),
            ("coquitlam", "Coquitlam"),
            ("高贵林", "Coquitlam"),
            ("bby", "Burnaby"),
            ("burnaby", "Burnaby"),
            ("本拿比", "Burnaby"),
            ("surrey", "Surrey"),
            ("素里", "Surrey"),
            ("vancouver", "Vancouver"),
            ("温哥华", "Vancouver"),
        ]
        for key, city in starts:
            if s_strip.startswith(key):
                return {"city": city, "key": key, "strength": 2}

        def has_token(token):
            return re.search(rf'(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])', s) is not None

        rules = [
            ("west coquitlam", "Coquitlam", 4),
            ("coquitlam west", "Coquitlam", 4),
            ("高贵林西", "Coquitlam", 4),
            ("burqitlam", "Coquitlam", 4),
            ("burquitlam", "Coquitlam", 3),
            ("coquitlam centre", "Coquitlam", 3),
            ("westwood plateau", "Coquitlam", 3),
            ("burke mountain", "Coquitlam", 3),

            ("lansdowne", "Richmond", 3),
            ("brighouse", "Richmond", 3),
            ("steveston", "Richmond", 3),

            ("metrotown", "Burnaby", 3),
            ("brentwood", "Burnaby", 3),
            ("lougheed", "Burnaby", 3),
            ("edmonds", "Burnaby", 3),
            ("edmond", "Burnaby", 3),

            ("guildford", "Surrey", 3),
            ("whalley", "Surrey", 3),
            ("newton", "Surrey", 3),
            ("central city", "Surrey", 3),

            ("ubc", "Vancouver", 3),
            ("downtown", "Vancouver", 3),
            ("yaletown", "Vancouver", 3),
            ("marine dr", "Vancouver", 3),
            ("温西", "Vancouver", 3),
            ("温东", "Vancouver", 3),

            ("rmd", "Richmond", 2),
            ("bby", "Burnaby", 2),
            ("poco", "Port Coquitlam", 2),

            ("richmond", "Richmond", 1),
            ("列治文", "Richmond", 1),
            ("burnaby", "Burnaby", 1),
            ("本拿比", "Burnaby", 1),
            ("coquitlam", "Coquitlam", 1),
            ("高贵林", "Coquitlam", 1),
            ("surrey", "Surrey", 1),
            ("素里", "Surrey", 1),
            ("vancouver", "Vancouver", 1),
            ("温哥华", "Vancouver", 1),
            ("new westminster", "New Westminster", 1),
            ("新西敏", "New Westminster", 1),
            ("delta", "Delta", 1),
            ("三角洲", "Delta", 1),
            ("langley", "Langley", 1),
            ("兰里", "Langley", 1),
            ("north vancouver", "North Vancouver", 1),
            ("北温", "North Vancouver", 1),
            ("west vancouver", "West Vancouver", 1),
            ("西温", "West Vancouver", 1),
            ("port coquitlam", "Port Coquitlam", 1),
            ("高贵林港", "Port Coquitlam", 1),
            ("port moody", "Port Moody", 1),
            ("满地宝", "Port Moody", 1),
            ("maple ridge", "Maple Ridge", 1),
            ("枫树岭", "Maple Ridge", 1),
        ]

        for key, city, strength in rules:
            if " " in key:
                if key in s:
                    return {"city": city, "key": key, "strength": strength}
            else:
                if has_token(key) or key in s:
                    return {"city": city, "key": key, "strength": strength}
        return {"city": "", "key": "", "strength": 0}

    def infer_city(self, text):
        return self.infer_city_info(text).get("city", "")

    def build_geocode_query(self, address, city):
        a = (address or "").strip()
        c = (city or "").strip()
        a = re.sub(r"\s+", " ", a)
        c = re.sub(r"\s+", " ", c)

        city_from_a = self.infer_city(a)
        city_from_all = self.infer_city(" ".join([a, c]))
        if not c and city_from_a:
            c = city_from_a
        if c and city_from_a and city_from_a != c and city_from_all:
            c = city_from_all

        if city_from_a and a.lower() == city_from_a.lower():
            a = ""
            if not c:
                c = city_from_a

        if "-" in a and city_from_a and a.lower().startswith(city_from_a.lower() + " -"):
            tail = a.split("-", 1)[1].strip()
            if tail:
                a = tail
                if not c:
                    c = city_from_a

        if a and c and (c.lower() in a.lower()):
            return a
        return (a + ", " + c).strip(", ").strip() if (a or c) else "Vancouver"

    def geocode_item(self, item):
        lat = item.get("lat")
        lng = item.get("lng")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            return lat, lng
        q = self.build_geocode_query(item.get("address", ""), item.get("city", ""))
        return self.get_lat_lng(q)

    def is_suspicious_coordinate(self, item):
        try:
            lat = item.get('lat')
            lng = item.get('lng')
            if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                return False
            text = " ".join([str(item.get('title', '')), str(item.get('address', '')), str(item.get('desc', ''))]).lower()
            inferred = self.infer_city(text)
            yvr = (49.17 < lat < 49.21) and (-123.22 < lng < -123.14)
            if yvr and inferred == "Richmond" and not any(k in text for k in ['yvr', 'airport', 'sea island', 'templeton']):
                q = self.build_geocode_query(item.get('address', ''), item.get('city', ''))
                clean_addr = re.sub(r'[^\w\s,.-]', '', q).strip()
                k = f"{clean_addr}, BC, Canada"
                if k in self.coords_cache:
                    try:
                        del self.coords_cache[k]
                        self._save_cache()
                    except:
                        pass
                return True
            return False
        except:
            return False

    def _store_owner_media(self, record_id, idx, url):
        try:
            ext = 'jpg'
            r = requests.get(url, timeout=20, headers={'User-Agent': 'HavenNest_Bot_v2.5.0'})
            ct = (r.headers.get('content-type') or '').lower()
            if 'image/png' in ct:
                ext = 'png'
            elif 'image/webp' in ct:
                ext = 'webp'
            elif 'image/jpeg' in ct or 'image/jpg' in ct:
                ext = 'jpg'
            if r.status_code != 200:
                return ''

            if self.media_backend == 'r2':
                try:
                    import boto3
                    s3 = boto3.client(
                        's3',
                        endpoint_url=self.r2_endpoint or None,
                        aws_access_key_id=self.r2_access_key_id,
                        aws_secret_access_key=self.r2_secret_access_key,
                        region_name='auto'
                    )
                    key = f"owner/{record_id}/{idx}.{ext}"
                    s3.put_object(
                        Bucket=self.r2_bucket,
                        Key=key,
                        Body=r.content,
                        ContentType=ct.split(';')[0] if ct else None,
                        CacheControl='public, max-age=31536000, immutable'
                    )
                    return f"{self.r2_public_base_url}/{key}"
                except Exception as e:
                    if os.getenv('GITHUB_ACTIONS') == 'true':
                        print(f"R2 upload failed ({record_id} #{idx}): {type(e).__name__}: {e}")
                    return url

            os.makedirs(self.owner_media_dir, exist_ok=True)
            filename = f"{record_id}_{idx}.{ext}"
            path = os.path.join(self.owner_media_dir, filename)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path.replace('\\', '/')
            with open(path, 'wb') as f:
                f.write(r.content)
            return path.replace('\\', '/')
        except:
            return ''

    def _cleanup_owner_media(self, keep_paths):
        try:
            if not os.path.exists(self.owner_media_dir):
                return
            keep = set([p.replace('\\', '/') for p in keep_paths if p])
            for name in os.listdir(self.owner_media_dir):
                path = os.path.join(self.owner_media_dir, name)
                if not os.path.isfile(path):
                    continue
                rel = path.replace('\\', '/')
                if rel not in keep:
                    try:
                        os.remove(path)
                    except:
                        pass
        except:
            pass

    def process_airtable_listings(self):
        """从 Airtable 获取屋主发布的房源并进行地理编码解析"""
        print("Fetching Airtable listings...")
        if not self.airtable_token:
            print("ERROR: AIRTABLE_TOKEN not set.")
            return []
        url = f"https://api.airtable.com/v0/{self.airtable_base}/{self.airtable_table}"
        headers = {"Authorization": f"Bearer {self.airtable_token}"}
        
        results = []
        try:
            res = requests.get(url, headers=headers, timeout=15)
            data = res.json()
            
            for r in data.get('records', []):
                f = r.get('fields', {})
                status = (f.get('Status') or f.get('status') or f.get('状态 (Status)') or '').strip().lower()
                if status in ['inactive', 'deleted', 'off', 'disabled']:
                    continue
                addr_raw = (f.get('房源具体地址 (Address)') or '').strip()
                title = f.get('房源标题 (Listing Title)', "Rental Listing")
                raw_photos = [p.get('url') for p in f.get('房源照片 / Property Photos', []) if p.get('url')]
                photos = []
                for idx, purl in enumerate(raw_photos[:self.owner_media_max_photos]):
                    stored = self._store_owner_media(r['id'], idx, purl)
                    if stored:
                        photos.append(stored)
                
                community = ""
                try:
                    for k, v in f.items():
                        lk = str(k).lower()
                        if not any(s in lk for s in ['community', 'neighbourhood', 'neighborhood', '社区']):
                            continue
                        if isinstance(v, str) and v.strip():
                            community = v.strip()
                            break
                        if isinstance(v, list) and v and isinstance(v[0], str) and v[0].strip():
                            community = v[0].strip()
                            break
                except:
                    community = ""
 
                # 城市识别
                city = f.get('所属城市 (City)') or f.get('所在城市 (City)') or ""
                inferred = self.infer_city(title + " " + addr_raw + " " + community)
                if inferred and (not city or city.strip().lower() == "vancouver"):
                    city = inferred
                if not city:
                    city = "Vancouver"
 
                addr = addr_raw
                if not addr:
                    addr = f"{community}, {city}".strip(", ").strip() if community else city

                # 卧室数量识别
                beds = f.get('卧室数量 (Beds)')
                try: beds = int(beds)
                except:
                    desc = f.get('房源描述 (Description)', "")
                    beds = self.extract_beds(title + " " + desc)

                lat, lng = None, None

                item = {
                    "id": r['id'],
                    "source": "owner",
                    "title": title,
                    "price": int(f.get('月租金 (Monthly Rent)', 0)),
                    "url": f"https://havennestapp.com/listing/{r['id']}", # 伪链接，详情由前端Modal展示
                    "address": addr,
                    "city": city,
                    "community": community,
                    "beds": beds,
                    "lat": lat,
                    "lng": lng,
                    "image": photos[0] if photos else "",
                    "images": photos,
                    "desc": f.get('房源描述 (Description)', "No description."),
                    "isPromo": True, # 屋主发布的房源默认为推广房源
                    "date": datetime.now().strftime('%Y-%m-%d')
                }
                results.append(item)
            if os.getenv('GITHUB_ACTIONS') == 'true':
                r2_count = sum(1 for it in results for u in (it.get('images') or []) if isinstance(u, str) and self.r2_public_base_url and u.startswith(self.r2_public_base_url))
                airtable_count = sum(1 for it in results for u in (it.get('images') or []) if isinstance(u, str) and 'airtableusercontent.com' in u)
                empty_count = sum(1 for it in results if not (it.get('image') or '').strip())
                print(f"Airtable images summary: r2={r2_count}, airtable_fallback={airtable_count}, empty_cover={empty_count}")
            print(f"DONE: Processed {len(results)} Airtable listings.")
        except Exception as e:
            print(f"ERROR: Airtable processing failed: {e}")
        return results

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.coords_cache, f, ensure_ascii=False, indent=4)

    def get_lat_lng(self, address):
        """地址转坐标，带缓存机制 [cite: 2026-03-03]"""
        if not address: return None, None
        
        # 缓存键名处理
        clean_addr = re.sub(r'[^\w\s,.-]', '', address).strip()
        search_query = f"{clean_addr}, BC, Canada"
        
        if search_query in self.coords_cache:
            return self.coords_cache[search_query]

        try:
            if len(clean_addr) < 3: return None, None
            # Nominatim 规定请求频率不能超过 1次/秒
            time.sleep(1.2)
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(search_query)}"
            res = requests.get(url, headers={'User-Agent': 'HavenNest_Bot_v2.5.0 (contact: support@havennestapp.com)'}, timeout=10)
            data = res.json()
            if data:
                coords = [float(data[0]['lat']), float(data[0]['lon'])]
                self.coords_cache[search_query] = coords
                self._save_cache()
                return coords
        except Exception as e:
            print(f"📍 Geocoding error for {address}: {e}")
        return None, None

    def extract_beds(self, text):
        """通用卧室数量提取逻辑"""
        # 匹配 "studio", "bachelor"
        if not text:
            return 1
        text = str(text).lower()
        if "studio" in text or "bachelor" in text:
            return 0
        # 匹配 "2 beds", "2br", "2室", "2房", "2卧"
        match = re.search(r'(\d+)\s*(?:bed(?:room)?s?|br|室|房|卧)', text)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        # 匹配 "2b2b" / "2bd2ba"
        match = re.search(r'(\d+)\s*b(?:d|ed)?\s*(\d+)\s*b(?:a|ath)?', text)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        # 匹配中文数字："两房"、"二室"、"三卧"
        cn_map = {
            "零": 0, "〇": 0,
            "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10
        }
        m = re.search(r'([零〇一二两三四五六七八九十])\s*(?:室|房|卧)', text)
        if m:
            v = cn_map.get(m.group(1))
            if isinstance(v, int):
                return v
        return 1

    def process_manual_rentals(self):
        """处理 Rentals.ca 的原始数据 (从 rentals_raw.json 读取)"""
        print("Processing Rentals.ca from rentals_raw.json...")
        if not os.path.exists(self.raw_rentals_file):
            print("  rentals_raw.json not found. Skipping.")
            return []
        
        try:
            with open(self.raw_rentals_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 增强匹配逻辑：支持更多字段和容错
            blocks = re.findall(r'\{"node":\s*(\{.*?"__typename":\s*"RentalListing".*?\})\s*\}', content, re.DOTALL)
            if not blocks:
                blocks = re.findall(r'(\{.*?"rentalListingName":\s*".*?".*?\})', content, re.DOTALL)
            
            results = []
            for block in blocks:
                try:
                    # 1. 提取基础信息
                    title_match = re.search(r'"rentalListingName":\s*"(.*?)"', block)
                    if not title_match: continue
                    title = title_match.group(1)
                    
                    path_match = re.search(r'"path":\s*"(.*?)"', block)
                    if not path_match: continue
                    path = path_match.group(1)
                    url = "https://rentals.ca/" + path
                    
                    # 2. 价格过滤：Rentals.ca 的 rentRange 可能是 [2500, 3000]
                    rent_match = re.search(r'"rentRange":\s*\[(.*?)(?:,|$)', block)
                    price = int(float(rent_match.group(1))) if rent_match else 0
                    if price < 300: continue # 剔除低价广告/车位

                    # 3. 广告关键词过滤
                    ad_keywords = ['parking', 'storage', 'locker', 'garage', '车位', '储物']
                    if any(kw in title.lower() for kw in ad_keywords): continue

                    # 4. 提取坐标
                    loc_match = re.search(r'"rentalListingLocation":\s*\[(.*?),(.*?)\]', block)
                    lat = float(loc_match.group(2)) if loc_match else None
                    lng = float(loc_match.group(1)) if loc_match else None
                    
                    # 5. 提取地址
                    street_match = re.search(r'"street":\s*"(.*?)"', block)
                    street = street_match.group(1) if street_match else ""
                    city_match = re.search(r'"cityName":\s*"(.*?)"', block)
                    city = city_match.group(1) if city_match else "Vancouver"
                    full_address = f"{street}, {city}" if street else city
                    info = self.infer_city_info(" ".join([title, full_address]))
                    inferred_city = info.get("city") or ""
                    strength = int(info.get("strength") or 0)
                    if inferred_city and (not city or city.strip().lower() == "vancouver" or (strength >= 2 and city.strip().lower() != inferred_city.lower())):
                        city = inferred_city
                        full_address = f"{street}, {city}" if street else city

                    # 6. 提取卧室
                    beds_match = re.search(r'"bedroomCount":\s*(\d+)', block)
                    beds = int(beds_match.group(1)) if beds_match else self.extract_beds(title)

                    # 7. 提取图片 (改进：深度寻找所有可能的图片)
                    images = []
                    # 寻找所有匹配 assets.rentsync.com 的 URL
                    img_matches = re.findall(r'"url":\s*"(https://assets\.rentsync\.com/.*?)"', block)
                    for img in img_matches:
                        if img not in images: images.append(img)
                    
                    # 如果 gallery 没找到，尝试 thumbnail
                    if not images:
                        thumb_match = re.search(r'"thumbnail":\s*"(.*?)"', block)
                        if thumb_match: images.append(thumb_match.group(1))

                    # 8. 尝试提取简短描述 (如果存在)
                    desc_match = re.search(r'"shortDescription":\s*"(.*?)"', block)
                    desc = desc_match.group(1) if desc_match else ""
                    # 处理 unicode 转义字符
                    if desc:
                        try:
                            desc = desc.encode().decode('unicode_escape')
                        except:
                            pass
                    else:
                        desc = "请点击'查看原房源'获取更多详细信息。"

                    results.append({
                        "source": "Rentals.ca",
                        "title": title,
                        "price": price,
                        "url": url,
                        "address": full_address,
                        "city": city,
                        "beds": beds,
                        "lat": lat,
                        "lng": lng,
                        "image": images[0] if images else "",
                        "images": images,
                        "desc": desc,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except: continue

            if not results:
                def _extract_json_object(s, start_idx):
                    i = start_idx
                    while i < len(s) and s[i] != '{':
                        i += 1
                    if i >= len(s) or s[i] != '{':
                        return None
                    depth = 0
                    in_str = False
                    esc = False
                    for j in range(i, len(s)):
                        ch = s[j]
                        if in_str:
                            if esc:
                                esc = False
                            elif ch == '\\':
                                esc = True
                            elif ch == '"':
                                in_str = False
                        else:
                            if ch == '"':
                                in_str = True
                            elif ch == '{':
                                depth += 1
                            elif ch == '}':
                                depth -= 1
                                if depth == 0:
                                    return s[i:j + 1]
                    return None

                marker_idx = content.find('response:')
                if marker_idx != -1:
                    json_str = _extract_json_object(content, marker_idx)
                    if json_str:
                        try:
                            payload = json.loads(json_str)
                            data = (payload.get('data') or {})
                            edges = data.get('edges') or []
                            for edge in edges:
                                node = (edge or {}).get('node') or {}
                                if node.get('__typename') != 'RentalListing':
                                    continue

                                title = node.get('rentalListingName') or ''
                                path = node.get('path') or ''
                                if not title or not path:
                                    continue
                                url = "https://rentals.ca/" + path.lstrip('/')

                                rent_range = node.get('rentRange') or []
                                price = 0
                                if isinstance(rent_range, list) and rent_range:
                                    try:
                                        price = int(float(rent_range[0]))
                                    except:
                                        price = 0
                                if price < 300:
                                    continue

                                loc = node.get('rentalListingLocation') or []
                                lat = None
                                lng = None
                                if isinstance(loc, list) and len(loc) == 2:
                                    try:
                                        lng = float(loc[0])
                                        lat = float(loc[1])
                                    except:
                                        lat = None
                                        lng = None

                                address = node.get('address') or {}
                                street = address.get('street') or ''
                                city_obj = (address.get('city') or {})
                                city = city_obj.get('cityName') or "Vancouver"
                                full_address = f"{street}, {city}" if street else city
                                info = self.infer_city_info(" ".join([title, full_address]))
                                inferred_city = info.get("city") or ""
                                strength = int(info.get("strength") or 0)
                                if inferred_city and (not city or city.strip().lower() == "vancouver" or (strength >= 2 and city.strip().lower() != inferred_city.lower())):
                                    city = inferred_city
                                    full_address = f"{street}, {city}" if street else city

                                beds_range = node.get('bedsRange') or []
                                beds = self.extract_beds(title)
                                if isinstance(beds_range, list) and beds_range:
                                    try:
                                        beds = int(float(beds_range[0]))
                                    except:
                                        pass

                                images = []
                                for img in (node.get('images') or []):
                                    scales = (img or {}).get('scales') or []
                                    for sc in scales:
                                        u = (sc or {}).get('url')
                                        if u and u not in images:
                                            images.append(u)

                                if not images:
                                    thumb = node.get('thumbnail')
                                    if isinstance(thumb, str) and thumb:
                                        images.append(thumb)

                                results.append({
                                    "source": "Rentals.ca",
                                    "title": title,
                                    "price": price,
                                    "url": url,
                                    "address": full_address,
                                    "city": city,
                                    "beds": beds,
                                    "lat": lat,
                                    "lng": lng,
                                    "image": images[0] if images else "",
                                    "images": images,
                                    "desc": "请点击'查看原房源'获取更多详细信息。",
                                    "date": datetime.now().strftime("%Y-%m-%d")
                                })
                            if results:
                                print(f"INFO: Rentals fallback parser extracted {len(results)} listings.")
                        except Exception as e:
                            print(f"WARNING: Rentals fallback parser failed: {e}")

            print(f"DONE: Extracted {len(results)} Rentals listings.")
            return results
        except Exception as e:
            print(f"WARNING: Rentals extraction failed: {e}")
            return []

    def crawl_craigslist(self, limit=40):
        """改进版 Craigslist 抓取：获取图片和描述"""
        print(f"Crawling Craigslist via Web (limit {limit})... ")
        results = []
        scraper = cloudscraper.create_scraper()
        try:
            url = "https://vancouver.craigslist.org/search/apa"
            res = scraper.get(url, timeout=20)
            if res.status_code != 200: return []
            
            soup = BeautifulSoup(res.text, 'html.parser')
            posts = soup.find_all('li', class_='cl-static-search-result')
            
            for post in posts[:limit]:
                try:
                    title_el = post.find('div', class_='title')
                    if not title_el: continue
                    title = title_el.text.strip()
                    
                    link_el = post.find('a')
                    detail_url = link_el.get('href', '')
                    
                    price_el = post.find('div', class_='price')
                    price = int(re.sub(r'[^\d]', '', price_el.text)) if price_el else 0
                    
                    # 深度抓取详情页获取图片集和描述
                    print(f"  Deep crawling Craigslist: {title[:20]}...")
                    d_res = scraper.get(detail_url, timeout=15)
                    if d_res.status_code != 200:
                        continue
                    if re.search(r'(?i)this posting has been deleted|flagged for removal|posting has expired|has expired', d_res.text or ""):
                        continue
                    d_soup = BeautifulSoup(d_res.text, 'html.parser')
                    
                    images = []
                    for img in d_soup.select('.gallery img'):
                        src = img.get('src')
                        if src: images.append(src)
                    
                    desc_el = d_soup.select_one('#postingbody')
                    desc = desc_el.text.replace('QR Code Link to This Post', '').strip() if desc_el else ""

                    loc_el = post.find('div', class_='location')
                    loc = loc_el.text.strip() if loc_el else "Vancouver"
                    
                    city = self.infer_city(loc + " " + title) or "Vancouver"

                    coord_source = ""
                    lat, lng = None, None
                    try:
                        m = d_soup.select_one('#map[data-latitude][data-longitude]')
                        if m:
                            lat = float(m.get('data-latitude'))
                            lng = float(m.get('data-longitude'))
                            coord_source = "source_map"
                    except:
                        lat, lng = None, None

                    address = ""
                    try:
                        a = d_soup.select_one('.mapaddress')
                        address = a.get_text(" ", strip=True) if a else ""
                    except:
                        address = ""
                    if not address:
                        try:
                            page_text = d_soup.get_text("\n", strip=True)
                            m = re.search(
                                r"(?im)^\s*(\d{3,6}\s+[^\n,]{2,}(?:\s+[^\n,]{2,})*,\s*[A-Za-z\s]+,\s*BC\b[^\n]*)\s*$",
                                page_text,
                            )
                            if m:
                                address = m.group(1).strip()
                        except:
                            address = ""
                    if not address:
                        m = re.search(r'(?im)^\s*(?:address|addr|location)\s*:\s*(.+?)\s*$', desc)
                        if m:
                            address = m.group(1).strip()
                    if not address:
                        address = loc
                    
                    results.append({
                        "source": "Craigslist",
                        "title": title,
                        "price": price,
                        "url": detail_url,
                        "address": address,
                        "city": city,
                        "beds": self.extract_beds(title + " " + desc),
                        "lat": lat,
                        "lng": lng,
                        "coord_source": coord_source,
                        "image": images[0] if images else "",
                        "images": images,
                        "desc": desc,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                    time.sleep(1)
                except: continue
            
            # 补充坐标
            print(f"Geocoding {len(results)} Craigslist items...")
            for item in results:
                item['lat'], item['lng'] = self.geocode_item(item)

            return results
        except Exception as e:
            print(f"WARNING: Craigslist Web crawl failed: {e}")
            return self.crawl_craigslist_rss(limit)
        return results

    def crawl_craigslist_rss(self, limit=40):
        print(f"Fallback: Crawling Craigslist via RSS...")
        # ... (保留原有的 RSS 逻辑作为备份)
        results = []
        try:
            rss_url = "https://vancouver.craigslist.org/search/apa?format=rss"
            res = requests.get(rss_url, headers={'User-Agent': 'HavenNest_Bot_v2.5.0'}, timeout=15)
            soup = BeautifulSoup(res.text, 'xml')
            items = soup.find_all('item')
            for item in items[:limit]:
                try:
                    title = item.find('title').text
                    url = item.find('link').text
                    price_match = re.search(r'\$(\d+,?\d*)', title)
                    price = int(price_match.group(1).replace(',', '')) if price_match else 0
                    beds = self.extract_beds(title)
                    lat = float(item.find('geo:lat').text) if item.find('geo:lat') else None
                    lng = float(item.find('geo:long').text) if item.find('geo:long') else None
                    loc_match = re.search(r'\((.*?)\)$', title)
                    loc = loc_match.group(1) if loc_match else "Vancouver"
                    city = self.infer_city(loc + " " + title) or "Vancouver"
                    
                    results.append({
                        "source": "Craigslist", "title": title, "price": price, "url": url,
                        "address": loc, "city": city, "beds": beds, "lat": lat, "lng": lng,
                        "image": "", "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except: continue
        except: pass
        return results

    def crawl_vanpeople(self, limit=60):
        """抓取 VanPeople (人在温哥华) 房源信息，支持多页抓取"""
        print(f"Crawling VanPeople (limit {limit})... ")
        results = []
        scraper = cloudscraper.create_scraper()
        
        ad_keywords = [
            '搬家', '清洁', '接送', '教练', '维修', '垃圾', '快递', '求职', '招聘', '服务', '公司', '专业', '诚聘', '货运', '物流', '修车',
            '回收', '安装', '疏通', '月子', '法律', '会计', '翻译', '补习', '宠物', '美容', '美发', '按摩', '中医', '牙医', '保险', '贷款',
            '地产', '房产经纪', '理财', '移民', '留学', '旅游', '机票', '租车', '手机', '电脑', '网络', '卫浴', '地板', '油漆', '屋顶', '花园',
            '除虫', '锁匠', '玻璃', '窗帘', '地毯', '家电', '家具', '钢琴', '小提琴', '吉他', '绘画', '数学', '英语', '法语', '驾校', '保姆',
            '月嫂', '开锁', '打车', '私厨', '外卖', '团购', '二手', '闲置', '收银', '帮厨', '洗碗', '服务员', '前台', '文员', '销售', '客服'
        ]
        
        page = 1
        while len(results) < limit:
            try:
                url = "https://c.vanpeople.com/zufang/" if page == 1 else f"https://c.vanpeople.com/zufang/?page={page}"
                print(f"  Fetching page {page}...")
                res = scraper.get(url, timeout=20)
                res.encoding = 'utf-8'
                
                if res.status_code != 200: break
                
                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.find_all('div', class_='c-list-contxt')
                
                # print(f"  Found {len(items)} raw items on page {page}")
                
                if not items:
                    print(f"  No items found on page {page} using primary selector. Trying alternative...")
                    items = soup.select('a[href*="/zufang/"]')
                    if not items: break
                
                for item in items:
                    if len(results) >= limit: break
                    try:
                        # 兼容处理：如果是 select 出来的 a 标签
                        if item.name == 'a' and '/zufang/' in item.get('href', ''):
                            title_el = item
                            parent = item.find_parent('div', class_='c-list-contxt') or item.parent
                            price_el = parent.find('span', class_='money') if parent else None
                        else:
                            title_el = item.find('a', class_='c-list-title')
                            price_el = item.find('span', class_='money')
                        
                        if not title_el: continue
                        title = title_el.text.strip()
                        if not title: continue
                        
                        # 增强过滤逻辑：标题关键词过滤
                        if any(kw in title for kw in ad_keywords):
                            # print(f"    Filtered by keyword: {title[:20]}")
                            continue
                        
                        detail_url = title_el.get('href', '')
                        if not detail_url: continue
                        if not detail_url.startswith('http'): detail_url = "https://c.vanpeople.com" + detail_url
                        
                        # 再次确认是租房链接
                        if '/zufang/' not in detail_url and 'zufang' not in detail_url: continue

                        price_str = re.sub(r'[^\d]', '', price_el.text) if price_el else "0"
                        price = int(price_str) if price_str else 0
                        
                        # 增强过滤逻辑：价格太低过滤
                        if price < 100:
                            # print(f"    Filtered by price: {title[:20]} (${price})")
                            continue

                        # 深度抓取详情页
                        detail_res = scraper.get(detail_url, timeout=15)
                        detail_res.encoding = 'utf-8'
                        if detail_res.status_code != 200:
                            continue
                        if re.search(r'您想访问的信息已经被删除|信息已经被删除|已经被删除', detail_res.text or ""):
                            continue
                        detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                        
                        # 1. 提取房源实拍图片
                        images = []
                        mobile_url = detail_url.replace("https://c.vanpeople.com/zufang/", "https://c.vanpeople.com/m/zufang/")
                        try:
                            m_res = scraper.get(mobile_url, timeout=15)
                            m_res.encoding = 'utf-8'
                            m_soup = BeautifulSoup(m_res.text, 'html.parser')
                            for img in m_soup.find_all('img'):
                                src = img.get('data-src') or img.get('data-original') or img.get('lazy-src') or img.get('src')
                                if not src: 
                                    continue
                                if src.startswith('//'):
                                    src = "https:" + src
                                elif src.startswith('/'):
                                    src = "https://c.vanpeople.com" + src
                                s = src.lower()
                                if not re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', s):
                                    continue
                                if any(bad in s for bad in ['gg/images', '/gg/', '/gp/', 'nopic', 'wechat', 'vpp_new', 'info_more', 'logo', 'avatar', 'icon', 'banner', 'ad_image', 'recommend']):
                                    continue
                                if not any(host in s for host in ['thumb.vancdn.com', 'img.vancdn.com', 'static.vancdn.com', 'vanpeople.com']):
                                    continue
                                if src not in images:
                                    images.append(src)
                        except:
                            pass

                        if not images:
                            photo_area = detail_soup.select_one('.detail-left, .view-gallery, .swiper-container, #photo-list, .img-box')
                            if photo_area:
                                img_els = photo_area.select('img')
                                for img in img_els:
                                    src = img.get('data-src') or img.get('data-original') or img.get('lazy-src') or img.get('src')
                                    if not src:
                                        continue
                                    if src.startswith('//'):
                                        src = "https:" + src
                                    elif src.startswith('/'):
                                        src = "https://c.vanpeople.com" + src
                                    s = src.lower()
                                    if not re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', s):
                                        continue
                                    if any(bad in s for bad in ['gg/images', '/gg/', '/gp/', 'nopic', 'wechat', 'vpp_new', 'info_more', 'logo', 'avatar', 'icon', 'banner', 'ad_image', 'recommend']):
                                        continue
                                    if src not in images:
                                        images.append(src)

                        if not images:
                            continue
                        
                        # 2. 提取描述并深度清洗
                        desc_el = detail_soup.select_one('.detail-desc, .info-content, .description, #info-content, .text-content, .ad-detail-content')
                        desc = desc_el.text.strip() if desc_el else ""
                        
                        junk_patterns = [
                            r'微信扫二维码分享到朋友圈', r'联系我时请说明是在vanpeople看到的', r'重要警示：不法骗子.*',
                            r'谨慎租房防诈骗.*', r'扫码添加微信客服', r'点击下载协议', r'我要举报', r'相关广告'
                        ]
                        for pattern in junk_patterns:
                            desc = re.sub(pattern, '', desc, flags=re.DOTALL)
                        
                        desc = re.sub(r'^\s*(联系人|联系人[:：]|联\s*系\s*人)\s*[:：].*$', '', desc, flags=re.MULTILINE | re.IGNORECASE)
                        desc = re.sub(r'^\s*(电话|联系电话|手机|手机号码|联\s*系\s*电\s*话)\s*[:：].*$', '', desc, flags=re.MULTILINE | re.IGNORECASE)
                        desc = re.sub(r'^\s*(微信|微信号|WeChat|wechat)\s*[:：].*$', '', desc, flags=re.MULTILINE | re.IGNORECASE)
                        desc = re.sub(r'^\s*(邮箱|电子邮箱|Email|E-mail)\s*[:：].*$', '', desc, flags=re.MULTILINE | re.IGNORECASE)
                        desc = re.sub(r'(\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}', '', desc)
                        desc = re.sub(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', '', desc, flags=re.IGNORECASE)

                        desc = re.sub(r'\n\s*\n', '\n', desc).strip()

                        loc_el = item.find('span', class_='class')
                        loc = loc_el.text.strip() if loc_el else ""

                        detail_text = detail_soup.get_text("\n", strip=True)
                        addr2 = ""
                        m = re.search(r'(?m)^(?:联系地址|地址)\s*[:：]?\s*(?:\n\s*)?([^\n]+)', detail_text)
                        if m:
                            addr2 = m.group(1)
                        addr2 = re.sub(r'\s*查看地图.*$', '', addr2).strip()
                        addr2 = re.sub(r'\s+', ' ', addr2)
 
                        community = ""
                        for candidate in [addr2, loc]:
                            if candidate and "-" in candidate:
                                parts = [p.strip() for p in candidate.split("-", 1)]
                                if len(parts) == 2 and parts[0] in ["Vancouver", "Richmond", "Burnaby", "Surrey", "Coquitlam"]:
                                    community = parts[1]
                                    break
                        if not community:
                            m = re.search(r'\b(Vancouver|Richmond|Burnaby|Surrey|Coquitlam)\s*-\s*([A-Za-z][A-Za-z\s]+)', detail_text)
                            if m:
                                community = m.group(2).strip()
 
                        map_lat, map_lng = None, None
                        coord_source = ""
                        map_query = ""
                        try:
                            iframe = detail_soup.select_one('iframe[src*="lat="][src*="lng="]')
                            src = (iframe.get('src') or '').strip() if iframe else ''
                            if src and src.startswith('/'):
                                src = "https://c.vanpeople.com" + src
                            src2 = src
                            if not src2:
                                raw_html = detail_res.text or ""
                                msrc = re.search(r'(?i)https?://[^\s"\']*googlemap\.html\?[^\s"\']*', raw_html)
                                if msrc:
                                    src2 = msrc.group(0)
                                else:
                                    msrc2 = re.search(r'(?i)["\'](/googlemap\.html\?[^"\']+)["\']', raw_html)
                                    if msrc2:
                                        src2 = msrc2.group(1)
                                        if src2.startswith('/'):
                                            src2 = "https://c.vanpeople.com" + src2
                            mlat = re.search(r'(?i)[?&]lat=([-\d.]+)', src2)
                            mlng = re.search(r'(?i)[?&]lng=([-\d.]+)', src2)
                            if mlat and mlng:
                                map_lat = float(mlat.group(1))
                                map_lng = float(mlng.group(1))
                                coord_source = "source_map"
                            else:
                                iframe2 = detail_soup.select_one('iframe[src*="maps.google.com/maps/embed"], iframe[src*="google.com/maps/embed"], iframe[src*="maps/embed/v1/place"]')
                                src3 = (iframe2.get('src') or '').strip() if iframe2 else ''
                                if src3:
                                    q = parse_qs(urlparse(src3).query).get('q', [''])[0]
                                    q = unquote_plus(q or '').strip()
                                    if q:
                                        q2 = re.sub(r'(?i),?\s*canada\s*$', '', q).strip().strip(',')
                                        map_query = q2 or q
                                        coord_source = "source_map_query"
                        except:
                            map_lat, map_lng = None, None

                        raw_html2 = detail_res.text or ""
                        open_maps_q = ""
                        try:
                            mm = re.search(r'(?i)https?://(?:www\.)?google\.com/maps/\?q=([^\s"\'<>]+)', raw_html2)
                            if mm:
                                open_maps_q = unquote_plus(mm.group(1) or '').strip()
                        except:
                            open_maps_q = ""

                        city = self.infer_city(" ".join([title, loc, addr2, detail_text, map_query, open_maps_q])) or "Vancouver"
                        address = addr2 or loc or open_maps_q or map_query or city

                        results.append({
                            "source": "VanPeople",
                            "title": title,
                            "price": price,
                            "url": detail_url,
                            "address": address,
                            "city": city,
                            "community": community,
                            "beds": self.extract_beds(title + " " + desc),
                            "lat": map_lat,
                            "lng": map_lng,
                            "coord_source": coord_source,
                            "image": images[0] if images else "",
                            "images": images,
                            "desc": desc if desc else "请点击'查看原房源'获取更多详细信息。",
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
                        time.sleep(0.5) # 稍微加快一点速度
                    except Exception as e:
                        print(f"    Error crawling detail: {e}")
                        continue
                
                page += 1
                if page > 5: break # 最多抓取5页，防止任务太久
            except Exception as e:
                print(f"WARNING: VanPeople crawl failed on page {page}: {e}")
                break
        
        # 补充坐标
        print(f"Geocoding {len(results)} VanPeople items...")
        for i, item in enumerate(results):
            item['lat'], item['lng'] = self.geocode_item(item)

        return results

    def run(self):
        # 加载旧数据
        old_data = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                try: old_data = json.load(f)
                except: old_data = []
        
        # 移除旧数据中的 owner 房源，因为我们将完全依赖本次 Airtable 的抓取结果
        # 这样如果 Airtable 中删除了房源，网站上也会同步删除
        old_data = [x for x in old_data if x.get('source') != 'owner']
        
        # 爬取新数据
        airtable_data = self.process_airtable_listings()
        new_data = airtable_data + self.process_manual_rentals() + \
                   self.crawl_craigslist()
        
        # VanPeople 抓取增加异常处理
        try:
            vp_data = self.crawl_vanpeople()
            if vp_data:
                new_data += vp_data
        except Exception as e:
            print(f"CRITICAL: VanPeople crawl method failed: {e}")
        
        # 补充坐标并确保所有房源都有位置 (仅对新房源中缺失坐标的进行补充)
        print(f"Final geocoding check for {len(new_data)} new items...")
        for item in new_data:
            inferred = self.infer_city(" ".join([str(item.get('title','')), str(item.get('address','')), str(item.get('desc',''))]))
            if inferred and (not item.get('city') or str(item.get('city')).strip().lower() == "vancouver"):
                item['city'] = inferred
            if self.is_suspicious_coordinate(item):
                item['lat'] = None
                item['lng'] = None
            if not item.get('lat') or not item.get('lng'):
                # 只有当地址不在缓存中时才调用 API
                addr_query = self.build_geocode_query(item.get('address', ''), item.get('city', 'Vancouver'))
                if addr_query + ", BC, Canada" not in self.coords_cache:
                    print(f"  Geocoding missing: {item.get('title')[:20]}...")
                item['lat'], item['lng'] = self.get_lat_lng(addr_query)
            
            # 兜底逻辑：依然没有坐标，分配一个中心点
            if not item.get('lat') or not item.get('lng'):
                centers = {
                    "Vancouver": (49.2827, -123.1207),
                    "Richmond": (49.1666, -123.1336),
                    "Burnaby": (49.2488, -122.9805),
                    "Coquitlam": (49.2830, -122.7932),
                    "Surrey": (49.1913, -122.8490),
                }
                base_lat, base_lng = centers.get(item.get('city')) or centers["Vancouver"]
                item['lat'] = base_lat + (time.time() % 1 - 0.5) * 0.005
                item['lng'] = base_lng + (time.time() % 1 - 0.5) * 0.005

        # 合并并去重
        data_map = {}
        for x in old_data:
            if not x.get('isPromo'):
                continue
            key = x.get('url') or x.get('id')
            if key:
                data_map[key] = x

        for item in new_data:
            key = item.get('url') or item.get('id')
            if key: data_map[key] = item

        if self.media_backend != 'local':
            for item in data_map.values():
                if item.get('source') != 'owner':
                    continue
                imgs = item.get('images') or []
                if isinstance(imgs, list):
                    imgs = [u for u in imgs if isinstance(u, str) and not u.startswith('owner_media/')]
                else:
                    imgs = []
                item['images'] = imgs
                img0 = item.get('image')
                if isinstance(img0, str) and img0.startswith('owner_media/'):
                    item['image'] = imgs[0] if imgs else ''

        if self.media_backend == 'local':
            for key, item in data_map.items():
                if item.get('source') != 'owner':
                    continue
                rid = item.get('id') or ''
                files = sorted(glob.glob(os.path.join(self.owner_media_dir, f"{rid}_*.*")))[:self.owner_media_max_photos]
                files = [p.replace('\\', '/') for p in files]
                if files:
                    item['images'] = files
                    item['image'] = files[0]

            keep_owner_media = []
            for item in data_map.values():
                if item.get('source') != 'owner':
                    continue
                keep_owner_media.extend(item.get('images') or [])
                if item.get('image'):
                    keep_owner_media.append(item.get('image'))
            self._cleanup_owner_media(keep_owner_media)
        
        # 清理逻辑：
        # 1. 屋主发布的推广房源 (isPromo) 永久保留
        # 2. 抓取的房源如果超过 45 天则删除
        # 3. 强制过滤掉价格为 0 或低于 100 的房源（除非是屋主发布的）
        # 4. 强制过滤包含广告关键词的房源
        
        ad_keywords = [
            '搬家', '清洁', '接送', '服务', '维修', '快递', '货运', '物流', '求职', '招聘', '公司', '专业', '教练',
            '回收', '安装', '疏通', '月子', '法律', '会计', '翻译', '补习', '宠物', '美容', '美发', '按摩', '中医', '牙医', '保险', '贷款',
            '地产', '房产经纪', '理财', '移民', '留学', '旅游', '机票', '租车', '手机', '电脑', '网络', '卫浴', '地板', '油漆', '屋顶', '花园'
        ]
        cutoff_delete = datetime.now() - timedelta(days=45)
        
        final = []
        for item in data_map.values():
            if item.get('isPromo'):
                final.append(item)
                continue
            
            # 强化过滤：价格为0或包含搬家等关键词的旧数据也要删掉
            title = (item.get('title') or '').lower()
            url = (item.get('url') or '').lower()
            
            # 处理价格：可能是字符串 "$1,500" 或数字
            price_raw = item.get('price')
            if isinstance(price_raw, str):
                price = int(re.sub(r'[^\d]', '', price_raw)) if re.sub(r'[^\d]', '', price_raw) else 0
            else:
                price = int(price_raw or 0)
            
            # 1. 价格过滤：温哥华租房通常不低于300，抓取到的低价必是广告
            if price < 300: 
                continue
            
            # 2. 关键词过滤
            if any(kw in title for kw in ad_keywords):
                continue
            
            # 3. URL 关键词过滤
            if any(kw in url for kw in ['/banyun/', '/jiesong/', '/service/', '/repair/', '/moving/']):
                continue

            # 4. 无图片过滤 (抓取到的房源如果没有图片，质量太低，不予显示)
            if item.get('source') == 'VanPeople':
                img0 = (item.get('image') or '').lower()
                if any(bad in img0 for bad in ['gg/images', '/gg/', '/gp/', 'nopic']):
                    continue

            if not item.get('image') and not item.get('images'):
                continue

            try:
                item_date = datetime.strptime(item.get('date', '2026-01-01'), '%Y-%m-%d')
                if item_date > cutoff_delete:
                    final.append(item)
            except:
                final.append(item)

        # 排序：推广房源置顶
        final.sort(key=lambda x: x.get('isPromo', False), reverse=True)

        print(f"Cleaning summary: {len(data_map)} raw items -> {len(final)} final items.")
        print(f"Saving {len(final)} items (cleaned old listings)...")
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=4)
        print(f"FINISH: Total {len(final)} items.")

if __name__ == "__main__":
    HavenNestCrawler().run()
