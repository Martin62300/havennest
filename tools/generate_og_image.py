import os
import io
import json
import random
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_listings():
    listings = []
    try:
        listings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'listings.json')
        if os.path.exists(listings_file):
            with open(listings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                owners = [x for x in data if x.get('source') == 'owner' and x.get('image')]
                others = [x for x in data if x.get('source') != 'owner' and x.get('image')]
                
                if owners: listings.append(owners[0])
                for src in ['Rentals.ca', 'VanPeople', 'Craigslist']:
                    items = [x for x in others if x.get('source') == src]
                    if items: listings.append(items[0])
                    if len(listings) >= 4: break
                    
                while len(listings) < 4 and others:
                    item = random.choice(others)
                    if item not in listings:
                        listings.append(item)
    except Exception as e:
        print(f"Error loading listings: {e}")
    
    # Fallback dummy data
    while len(listings) < 4:
        listings.append({
            'source': 'System',
            'price': 2500,
            'city': 'Vancouver',
            'beds': 1,
            'image': ''
        })
    return listings[:4]

def crop_center(img, target_w, target_h):
    w, h = img.size
    ratio_w = target_w / w
    ratio_h = target_h / h
    ratio = max(ratio_w, ratio_h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def download_image(url):
    if not url: return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert('RGB')
    except Exception:
        return None

def main():
    # 使用 1080x1440 这种更适合小红书/朋友圈竖屏浏览的比例，或者保持 1200x630 但做满内容
    # 按照用户要求：“作为图片有些小了”，可能是指之前内容在中间缩成一小块。现在做全屏铺满设计。
    width, height = 1200, 630
    navy = (0x00, 0x21, 0x47)
    gold = (0xD4, 0xAF, 0x37)
    slate = (0x33, 0x41, 0x55)

    img = Image.new("RGB", (width, height), "#ffffff")
    d = ImageDraw.Draw(img)

    header_h = 120
    d.rectangle([0, 0, width, header_h], fill=navy)

    logo_x, logo_y = 60, 30
    d.line([(logo_x + 28, logo_y), (logo_x, logo_y + 26)], fill=(255, 255, 255), width=6)
    d.line([(logo_x + 28, logo_y), (logo_x + 56, logo_y + 26)], fill=(255, 255, 255), width=6)
    d.line([(logo_x + 10, logo_y + 28), (logo_x + 10, logo_y + 62)], fill=(255, 255, 255), width=10)
    d.line([(logo_x + 46, logo_y + 28), (logo_x + 46, logo_y + 62)], fill=(255, 255, 255), width=10)
    d.line([(logo_x + 10, logo_y + 48), (logo_x + 46, logo_y + 48)], fill=(255, 255, 255), width=10)
    d.line([(logo_x + 10, logo_y + 34), (logo_x + 10, logo_y + 58)], fill=gold, width=3)
    d.line([(logo_x + 46, logo_y + 34), (logo_x + 46, logo_y + 58)], fill=gold, width=3)

    try:
        font_brand = ImageFont.truetype("arialbd.ttf", 36)
        font_title_cn = ImageFont.truetype("msyhbd.ttc", 46)
        font_sub_cn = ImageFont.truetype("msyh.ttc", 26)
        font_price = ImageFont.truetype("arialbd.ttf", 32)
        font_meta_cn = ImageFont.truetype("msyh.ttc", 20)
        font_tag_cn = ImageFont.truetype("msyhbd.ttc", 16)
        font_qr_cn = ImageFont.truetype("msyhbd.ttc", 22)
    except Exception:
        font_brand = ImageFont.load_default()
        font_title_cn = ImageFont.load_default()
        font_sub_cn = ImageFont.load_default()
        font_price = ImageFont.load_default()
        font_meta_cn = ImageFont.load_default()
        font_tag_cn = ImageFont.load_default()
        font_qr_cn = ImageFont.load_default()

    d.text((logo_x + 80, 40), "HAVENNEST 安家居", fill=(255, 255, 255), font=font_brand)
    
    # 居中大标题
    title = "大温全量房源聚合门户"
    sub = "真实屋主直发 · 全网房源追踪 · 一站式安家服务"
    title_w = d.textlength(title, font=font_title_cn)
    sub_w = d.textlength(sub, font=font_sub_cn)
    
    d.text(((width - title_w) // 2, header_h + 30), title, fill=(11, 27, 51), font=font_title_cn)
    d.text(((width - sub_w) // 2, header_h + 90), sub, fill=slate, font=font_sub_cn)

    # 绘制 4 个房源卡片
    listings = get_listings()
    
    grid_y = header_h + 160
    card_w = 230
    card_h = 260
    gap = 30
    start_x = 50

    for i, item in enumerate(listings):
        x = start_x + i * (card_w + gap)
        y = grid_y
        
        # 背景
        d.rounded_rectangle([x, y, x + card_w, y + card_h], radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=2)
        
        # 图片
        img_h = 140
        cover = download_image(item.get('image'))
        if cover:
            cover = crop_center(cover, card_w, img_h)
            # Create rounded mask for top corners
            mask = Image.new("L", (card_w, img_h), 0)
            mask_d = ImageDraw.Draw(mask)
            mask_d.rounded_rectangle([0, 0, card_w, img_h + 16], radius=16, fill=255)
            img.paste(cover, (x, y), mask)
        else:
            d.rounded_rectangle([x, y, x + card_w, y + img_h], radius=16, fill=(226, 232, 240))
        
        # 遮盖下半部分的圆角，让图片只在上面有圆角
        d.rectangle([x, y + img_h - 16, x + card_w, y + img_h], fill=(255,255,255) if cover else (226, 232, 240))
        if cover:
            cover_bottom_strip = cover.crop((0, img_h-16, card_w, img_h))
            img.paste(cover_bottom_strip, (x, y + img_h - 16))

        # 标签
        tag = "屋主直发" if item.get('source') == 'owner' else item.get('source', 'System')
        tag_w = d.textlength(tag, font=font_tag_cn)
        d.rounded_rectangle([x + 10, y + 10, x + 10 + tag_w + 16, y + 36], radius=13, fill=(11, 27, 51, 200))
        d.text((x + 18, y + 15), tag, fill=(255, 255, 255), font=font_tag_cn)
        
        # 价格与信息
        price = f"${item.get('price', 0):,}"
        city = item.get('city', 'Vancouver')
        beds = item.get('beds', 1)
        meta = f"{city} | {beds} Bed{'s' if beds > 1 else ''}"
        
        d.text((x + 16, y + img_h + 20), price, fill=navy, font=font_price)
        d.text((x + 16, y + img_h + 65), meta, fill=slate, font=font_meta_cn)

    # 二维码区域 (放在右侧)
    qr_data = "https://havennestapp.com"
    try:
        qs = urllib.parse.urlencode({"size": "300x300", "data": qr_data})
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?{qs}"
        with urllib.request.urlopen(qr_url, timeout=10) as resp:
            qr_png = resp.read()
        qr = Image.open(io.BytesIO(qr_png)).convert("RGB")
        qr_size = 200
        qr = qr.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

        qr_x = width - qr_size - 60
        qr_y = header_h + 160
        
        # 画二维码背景框
        d.rounded_rectangle([qr_x - 15, qr_y - 15, qr_x + qr_size + 15, qr_y + qr_size + 60], radius=20, fill=(255, 255, 255), outline=gold, width=3)
        img.paste(qr, (qr_x, qr_y))
        
        # 二维码下方文字
        d.text((qr_x + 35, qr_y + qr_size + 15), "长按扫码选房", fill=navy, font=font_qr_cn)
        
    except Exception as e:
        print(f"QR Error: {e}")

    # 底部服务保障
    footer_y = height - 60
    d.rectangle([0, footer_y, width, height], fill=(241, 245, 249))
    footer_text = "✅ 免费发布房源   ✅ 全网租房抓取   ✅ 权威租客保险   ✅ 专业搬家清洁"
    fw = d.textlength(footer_text, font=font_sub_cn)
    d.text(((width - fw) // 2, footer_y + 12), footer_text, fill=navy, font=font_sub_cn)

    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "og-image.jpg")
    img.save(out_path, "JPEG", quality=95)

if __name__ == "__main__":
    main()
