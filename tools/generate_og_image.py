import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def main():
    width, height = 1200, 630
    navy = (0x00, 0x21, 0x47)
    gold = (0xD4, 0xAF, 0x37)
    slate = (0x33, 0x41, 0x55)

    img = Image.new("RGB", (width, height), "#f6f8fb")

    margin = 52
    screen_x0, screen_y0 = margin, 36
    screen_x1, screen_y1 = width - margin, height - 26

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sh = ImageDraw.Draw(shadow)
    sh.rounded_rectangle(
        [screen_x0 - 6, screen_y0 - 6, screen_x1 + 6, screen_y1 + 12],
        radius=34,
        fill=(11, 27, 51, 35),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        [screen_x0 - 10, screen_y0 - 10, screen_x1 + 10, screen_y1 + 10],
        radius=34,
        fill=(255, 255, 255),
    )
    d.rounded_rectangle(
        [screen_x0, screen_y0, screen_x1, screen_y1],
        radius=28,
        fill=(249, 250, 251),
    )

    header_h = 110
    d.rectangle([screen_x0, screen_y0, screen_x1, screen_y0 + header_h], fill=navy)

    logo_x, logo_y = screen_x0 + 32, screen_y0 + 28
    d.line([(logo_x + 28, logo_y), (logo_x, logo_y + 26)], fill=(255, 255, 255), width=6)
    d.line([(logo_x + 28, logo_y), (logo_x + 56, logo_y + 26)], fill=(255, 255, 255), width=6)
    d.line([(logo_x + 10, logo_y + 28), (logo_x + 10, logo_y + 62)], fill=(255, 255, 255), width=10)
    d.line([(logo_x + 46, logo_y + 28), (logo_x + 46, logo_y + 62)], fill=(255, 255, 255), width=10)
    d.line([(logo_x + 10, logo_y + 48), (logo_x + 46, logo_y + 48)], fill=(255, 255, 255), width=10)
    d.line([(logo_x + 10, logo_y + 34), (logo_x + 10, logo_y + 58)], fill=gold, width=3)
    d.line([(logo_x + 46, logo_y + 34), (logo_x + 46, logo_y + 58)], fill=gold, width=3)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 38)
        font_sub = ImageFont.truetype("arial.ttf", 22)
        font_brand = ImageFont.truetype("arialbd.ttf", 26)
        font_tag = ImageFont.truetype("arialbd.ttf", 13)
        font_price = ImageFont.truetype("arialbd.ttf", 22)
        font_meta = ImageFont.truetype("arialbd.ttf", 14)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_brand = ImageFont.load_default()
        font_tag = ImageFont.load_default()
        font_price = ImageFont.load_default()
        font_meta = ImageFont.load_default()

    d.text((logo_x + 74, screen_y0 + 34), "HAVENNEST", fill=(255, 255, 255), font=font_brand)

    text_x = screen_x0 + 32
    title_y = screen_y0 + header_h + 26
    sub_y = title_y + 44
    d.text((text_x, title_y), "HavenNest 安家居 | 大温全量房源聚合", fill=(11, 27, 51), font=font_title)
    d.text((text_x, sub_y), "聚合各大平台房源，从保险到搬家省时省心", fill=slate, font=font_sub)

    container_y = sub_y + 80
    container_x0 = screen_x0 + 70
    container_x1 = screen_x1 - 70
    container_y1 = container_y + 260

    shadow2 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow2)
    sd.rounded_rectangle([container_x0, container_y, container_x1, container_y1], radius=26, fill=(11, 27, 51, 40))
    shadow2 = shadow2.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img.convert("RGBA"), shadow2).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([container_x0, container_y, container_x1, container_y1], radius=26, fill=(255, 255, 255))

    pad = 22
    grid_x0 = container_x0 + pad
    grid_y0 = container_y + pad
    col_gap = 20
    row_gap = 18
    cell_w = (container_x1 - container_x0 - pad * 2 - col_gap) // 2
    cell_h_top = 140
    cell_h_bottom = 120

    def draw_card(x, y, w, h, tag, price, meta, featured=False):
        if featured:
            d.rounded_rectangle([x - 4, y - 4, x + w + 4, y + h + 4], radius=22, outline=gold, width=6)
        d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        img_h = int(h * 0.62)
        d.rounded_rectangle([x, y, x + w, y + img_h], radius=18, fill=(203, 213, 225))
        pill_w = max(72, 10 + int(d.textlength(tag, font=font_tag)))
        d.rounded_rectangle([x + 14, y + 12, x + 14 + pill_w, y + 34], radius=11, fill=(11, 18, 32, 180))
        d.text((x + 22, y + 16), tag, fill=(255, 255, 255), font=font_tag)
        d.text((x + 16, y + img_h + 18), price, fill=(11, 27, 51), font=font_price)
        d.text((x + 16, y + img_h + 44), meta, fill=slate, font=font_meta)

    x1 = grid_x0
    x2 = grid_x0 + cell_w + col_gap
    y1 = grid_y0
    y2 = grid_y0 + cell_h_top + row_gap

    draw_card(x1, y1, cell_w, cell_h_top, "屋主直发", "$3,100", "Downtown 1BR", featured=True)
    draw_card(x2, y1, cell_w, cell_h_top, "Rentals.ca", "$2,250", "Burnaby 2BR")
    draw_card(x1, y2, cell_w, cell_h_bottom, "VanPeople", "$2,900", "Richmond 2BR")
    draw_card(x2, y2, cell_w, cell_h_bottom, "Craigslist", "$2,480", "Surrey 1BR")

    icons_y = screen_y1 - 56
    d.rounded_rectangle([container_x0, icons_y, container_x1, icons_y + 44], radius=18, fill=(255, 255, 255))
    d.text((container_x0 + 80, icons_y + 12), "🛡️ 租客保险", fill=(11, 27, 51), font=font_meta)
    d.text((container_x0 + 340, icons_y + 12), "📦 搬家服务", fill=(11, 27, 51), font=font_meta)
    d.text((container_x0 + 590, icons_y + 12), "🧹 清洁服务", fill=(11, 27, 51), font=font_meta)

    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "og-image.jpg")
    img.save(out_path, "JPEG", quality=92, optimize=True, progressive=True)


if __name__ == "__main__":
    main()
