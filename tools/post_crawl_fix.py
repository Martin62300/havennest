import json
import os
import random
import re
import sys
from typing import Any, Dict, Tuple
 
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
 
from crawler import HavenNestCrawler
 
 
CITY_CENTERS = {
    "Vancouver": (49.2827, -123.1207),
    "Richmond": (49.1666, -123.1336),
    "Burnaby": (49.2488, -122.9805),
    "Coquitlam": (49.2830, -122.7932),
    "Surrey": (49.1913, -122.8490),
}
 
CITY_BBOX = {
    "Vancouver": (49.20, 49.34, -123.27, -123.00),
    "Richmond": (49.08, 49.23, -123.25, -123.02),
    "Burnaby": (49.20, 49.32, -123.10, -122.88),
    "Coquitlam": (49.20, 49.35, -122.93, -122.74),
    "Surrey": (49.03, 49.30, -122.98, -122.65),
}
 
 
def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)
 
 
def _in_bbox(city: str, lat: float, lng: float) -> bool:
    box = CITY_BBOX.get(city)
    if not box:
        return True
    lat_min, lat_max, lng_min, lng_max = box
    return (lat_min <= lat <= lat_max) and (lng_min <= lng <= lng_max)
 
 
def _cache_key_from_query(query: str) -> str:
    clean_addr = re.sub(r"[^\w\s,.-]", "", (query or "")).strip()
    return f"{clean_addr}, BC, Canada"
 
 
def _fallback_coords(city: str) -> Tuple[float, float]:
    base = CITY_CENTERS.get(city) or CITY_CENTERS["Vancouver"]
    return (base[0] + random.uniform(-0.004, 0.004), base[1] + random.uniform(-0.004, 0.004))
 
 
def main():
    listings_path = os.path.join(ROOT, "listings.json")
    if not os.path.exists(listings_path):
        raise SystemExit(f"listings.json not found: {listings_path}")
 
    max_geocode = int(os.getenv("MAX_GEOCODE", "30") or "30")
 
    with open(listings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
 
    c = HavenNestCrawler()
 
    changed_city = 0
    changed_beds = 0
    changed_coords = 0
    re_geocoded = 0
    center_fallback = 0
    geocode_used = 0
 
    for item in data:
        source = (item.get("source") or "").strip().lower()
        title = str(item.get("title") or "")
        addr = str(item.get("address") or "")
        desc = str(item.get("desc") or item.get("description") or "")
        text = " ".join([title, addr, desc])
 
        info = c.infer_city_info(text)
        inferred_city = (info.get("city") or "").strip()
        strength = int(info.get("strength") or 0)
        cur_city = (item.get("city") or "").strip()
 
        if inferred_city:
            if source == "owner":
                should_update_city = (not cur_city) or (cur_city.lower() == "vancouver") or (
                    strength >= 3 and cur_city.lower() != inferred_city.lower()
                )
            else:
                should_update_city = (not cur_city) or (cur_city.lower() == "vancouver") or (
                    strength >= 2 and cur_city.lower() != inferred_city.lower()
                )
 
            if should_update_city and cur_city != inferred_city:
                item["city"] = inferred_city
                changed_city += 1
                cur_city = inferred_city
 
        extracted_beds = c.extract_beds(text)
        cur_beds = item.get("beds")
        try:
            cur_beds_int = int(cur_beds) if cur_beds is not None else None
        except Exception:
            cur_beds_int = None
 
        if cur_beds_int is None:
            item["beds"] = extracted_beds
            changed_beds += 1
        else:
            if extracted_beds != cur_beds_int and (extracted_beds != 1 or cur_beds_int == 1):
                item["beds"] = extracted_beds
                changed_beds += 1
 
        lat = item.get("lat")
        lng = item.get("lng")
        coords_ok = _is_number(lat) and _is_number(lng)
        needs_coords = not coords_ok
 
        if coords_ok:
            if c.is_suspicious_coordinate(item):
                needs_coords = True
            elif cur_city in CITY_BBOX and not _in_bbox(cur_city, float(lat), float(lng)):
                needs_coords = True
 
        if not needs_coords:
            continue
 
        query = c.build_geocode_query(addr, cur_city)
        cache_key = _cache_key_from_query(query)
        if cache_key in c.coords_cache:
            try:
                del c.coords_cache[cache_key]
            except Exception:
                pass
 
        new_lat = None
        new_lng = None
        if geocode_used < max_geocode:
            geocode_used += 1
            coords = c.get_lat_lng(query)
            try:
                new_lat = float(coords[0]) if coords and coords[0] is not None else None
                new_lng = float(coords[1]) if coords and coords[1] is not None else None
            except Exception:
                new_lat = None
                new_lng = None
 
            if new_lat is not None and new_lng is not None:
                re_geocoded += 1
 
        if new_lat is None or new_lng is None or (cur_city in CITY_BBOX and not _in_bbox(cur_city, float(new_lat), float(new_lng))):
            new_lat, new_lng = _fallback_coords(cur_city)
            center_fallback += 1
 
        item["lat"] = float(new_lat)
        item["lng"] = float(new_lng)
        changed_coords += 1
 
    with open(listings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
 
    try:
        c._save_cache()
    except Exception:
        pass
 
    print(
        "Post-crawl fix done: "
        + f"city={changed_city}, beds={changed_beds}, coords_updated={changed_coords}, "
        + f"re_geocoded={re_geocoded}, center_fallback={center_fallback}, max_geocode={max_geocode}"
    )
 
 
if __name__ == "__main__":
    main()
