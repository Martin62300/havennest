import re
import sys

import cloudscraper
from bs4 import BeautifulSoup


def main():
    url = "https://vancouver.craigslist.org/rch/apa/d/richmond-waterview-2bedden3bath-condo/7918638551.html"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        url = sys.argv[1].strip()

    s = cloudscraper.create_scraper()
    r = s.get(url, timeout=20)
    print("status:", r.status_code)
    html = r.text or ""

    print("has_data_latitude:", "data-latitude" in html)
    m = re.search(r'data-latitude="([^"]+)"[^>]*data-longitude="([^"]+)"', html)
    print("regex_latlng:", m.groups() if m else None)

    soup = BeautifulSoup(html, "html.parser")
    map_el = soup.select_one("#map[data-latitude][data-longitude]")
    if map_el:
        print("soup_latlng:", (map_el.get("data-latitude"), map_el.get("data-longitude")))
    else:
        print("soup_latlng:", None)

    mapaddr = soup.select_one(".mapaddress")
    print("mapaddress:", mapaddr.get_text(" ", strip=True) if mapaddr else None)

    body = soup.select_one("#postingbody")
    desc = body.get_text("\n", strip=True) if body else ""
    mm = re.search(r"(?im)^\s*(?:address|addr|location)\s*:\s*(.+?)\s*$", desc)
    print("desc_addr:", mm.group(1).strip() if mm else None)


if __name__ == "__main__":
    main()

