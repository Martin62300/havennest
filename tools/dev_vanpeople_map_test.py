import re
import sys

import cloudscraper
from bs4 import BeautifulSoup


def main():
    url = "https://c.vanpeople.com/zufang/item-3454919.html"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        url = sys.argv[1].strip()
    s = cloudscraper.create_scraper()
    r = s.get(url, timeout=20)
    r.encoding = "utf-8"
    html = r.text or ""
    soup = BeautifulSoup(html, "html.parser")

    iframe = soup.select_one('iframe[src*="lat="][src*="lng="]')
    src = (iframe.get("src") or "").strip() if iframe else ""
    if src.startswith("/"):
        src = "https://c.vanpeople.com" + src

    src2 = src
    if not src2:
        m = re.search(r'(?i)https?://[^\s"\']*googlemap\.html\?[^\s"\']*', html)
        if m:
            src2 = m.group(0)
        else:
            m2 = re.search(r'(?i)["\'](/googlemap\.html\?[^"\']+)["\']', html)
            if m2:
                src2 = m2.group(1)
                if src2.startswith("/"):
                    src2 = "https://c.vanpeople.com" + src2

    mlat = re.search(r"(?i)[?&]lat=([-\d.]+)", src2)
    mlng = re.search(r"(?i)[?&]lng=([-\d.]+)", src2)

    print("src2:", src2)
    if mlat and mlng:
        print("lat:", mlat.group(1))
        print("lng:", mlng.group(1))
    else:
        print("lat/lng not found")
        all_iframes = [x.get("src") for x in soup.find_all("iframe") if x.get("src")]
        if all_iframes:
            print("iframes:")
            for u in all_iframes[:10]:
                print(" -", u[:200])
        else:
            print("no iframes")
        m = re.search(r'(?i)https?://[^\s"\']*(?:googlemap\.html|google\.com/maps|google\.com/maps/embed)[^\s"\']*', html)
        if m:
            print("html_map_url:", m.group(0)[:250])


if __name__ == "__main__":
    main()
