import json
import hashlib
import os
import random
import re
import time
import sys
from typing import Any, Dict, Optional, Tuple
 
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
 
from crawler import HavenNestCrawler
import requests
 
 
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
 
COMMUNITY_BBOX = {
    ("Richmond", "Thompson"): (49.145, 49.185, -123.165, -123.105),
    ("Richmond", "Brighouse"): (49.155, 49.175, -123.145, -123.105),
    ("Richmond", "City Centre"): (49.160, 49.185, -123.150, -123.105),
    ("Richmond", "West Cambie"): (49.175, 49.205, -123.190, -123.120),
    ("Richmond", "East Cambie"): (49.175, 49.205, -123.110, -123.055),
    ("Richmond", "Steveston"): (49.115, 49.145, -123.205, -123.145),
    ("Burnaby", "Metrotown"): (49.210, 49.245, -123.030, -122.980),
    ("Burnaby", "Brentwood"): (49.260, 49.285, -123.020, -122.980),
    ("Burnaby", "Edmonds"): (49.205, 49.235, -123.030, -122.950),
    ("Burnaby", "Highgate"): (49.205, 49.230, -123.015, -122.980),
    ("Coquitlam", "Coquitlam West"): (49.240, 49.280, -122.905, -122.840),
    ("Coquitlam", "Burquitlam"): (49.250, 49.290, -122.915, -122.850),
    ("Coquitlam", "Austin Heights"): (49.255, 49.290, -122.870, -122.820),
    ("Coquitlam", "Coquitlam Centre"): (49.265, 49.310, -122.850, -122.770),
}
 
COMMUNITY_SYNONYMS = {
    "thompson community": "Thompson",
    "thompson community centre": "Thompson",
    "rmd thompson": "Thompson",
    "列治文 thompson": "Thompson",
    "brighouse": "Brighouse",
    "richmond centre": "City Centre",
    "richmond center": "City Centre",
    "city centre": "City Centre",
    "west cambie": "West Cambie",
    "east cambie": "East Cambie",
    "steveston": "Steveston",
    "metrotown": "Metrotown",
    "brentwood": "Brentwood",
    "edmonds": "Edmonds",
    "highgate": "Highgate",
    "coquitlam west": "Coquitlam West",
    "west coquitlam": "Coquitlam West",
    "burquitlam": "Burquitlam",
    "austin heights": "Austin Heights",
    "coquitlam centre": "Coquitlam Centre",
    "coquitlam center": "Coquitlam Centre",
}
 
COMMUNITY_BBOX_CACHE_PATH = os.path.join(ROOT, "community_bbox_cache.json")

 
def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)
 
 
def _in_bbox(city: str, lat: float, lng: float) -> bool:
    box = CITY_BBOX.get(city)
    if not box:
        return True
    lat_min, lat_max, lng_min, lng_max = box
    return (lat_min <= lat <= lat_max) and (lng_min <= lng <= lng_max)
 
 
def _in_box(box: Tuple[float, float, float, float], lat: float, lng: float) -> bool:
    lat_min, lat_max, lng_min, lng_max = box
    return (lat_min <= lat <= lat_max) and (lng_min <= lng <= lng_max)
 
 
def _cache_key_from_query(query: str) -> str:
    clean_addr = re.sub(r"[^\w\s,.-]", "", (query or "")).strip()
    return f"{clean_addr}, BC, Canada"
 
 
def _stable_u(item: Dict[str, Any], salt: str) -> float:
    k = str(item.get("id") or item.get("url") or item.get("title") or "")
    d = hashlib.md5((salt + "|" + k).encode("utf-8", errors="ignore")).hexdigest()
    return int(d[:8], 16) / 0xFFFFFFFF
 
 
def _normalize_community(v: Any) -> str:
    if not v:
        return ""
    s = str(v).strip()
    if not s:
        return ""
    low = s.lower()
    return COMMUNITY_SYNONYMS.get(low, s)
 
 
def _coords_from_bbox(item: Dict[str, Any], box: Tuple[float, float, float, float]) -> Tuple[float, float]:
    lat_min, lat_max, lng_min, lng_max = box
    u = _stable_u(item, "lat")
    v = _stable_u(item, "lng")
    lat = lat_min + u * (lat_max - lat_min)
    lng = lng_min + v * (lng_max - lng_min)
    return (lat, lng)
 
 
def _load_community_bbox_cache() -> Dict[str, Tuple[float, float, float, float]]:
    try:
        if os.path.exists(COMMUNITY_BBOX_CACHE_PATH):
            with open(COMMUNITY_BBOX_CACHE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            out: Dict[str, Tuple[float, float, float, float]] = {}
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if not isinstance(k, str):
                        continue
                    if isinstance(v, (list, tuple)) and len(v) == 4:
                        try:
                            out[k] = (float(v[0]), float(v[1]), float(v[2]), float(v[3]))
                        except Exception:
                            continue
            return out
    except Exception:
        pass
    return {}


def _save_community_bbox_cache(cache: Dict[str, Tuple[float, float, float, float]]) -> None:
    try:
        with open(COMMUNITY_BBOX_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _community_key(city: str, community: str) -> str:
    c = (city or "").strip().lower()
    n = _normalize_community(community).strip().lower()
    return f"{c}||{n}"


def _fetch_community_bbox(city: str, community: str) -> Optional[Tuple[float, float, float, float]]:
    q = ", ".join([_normalize_community(community).strip(), (city or "").strip(), "BC", "Canada"]).strip(", ")
    if not q:
        return None
    url = "https://nominatim.openstreetmap.org/search"
    params = {"format": "json", "limit": 1, "q": q}
    headers = {"User-Agent": "HavenNest_Bot_v2.5.0"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    if r.status_code != 200:
        return None
    j = r.json()
    if not isinstance(j, list) or not j:
        return None
    bb = j[0].get("boundingbox")
    if not isinstance(bb, list) or len(bb) != 4:
        return None
    try:
        south = float(bb[0])
        north = float(bb[1])
        west = float(bb[2])
        east = float(bb[3])
        if not (south < north and west < east):
            return None
        return (south, north, west, east)
    except Exception:
        return None


def _get_community_bbox(
    city: str,
    community: str,
    cache: Dict[str, Tuple[float, float, float, float]],
    budget: Dict[str, int],
    sleep_seconds: float,
) -> Optional[Tuple[float, float, float, float]]:
    city0 = (city or "").strip()
    comm0 = _normalize_community(community).strip()
    if not city0 or not comm0:
        return None
    direct = COMMUNITY_BBOX.get((city0, comm0))
    if direct:
        return direct
    key = _community_key(city0, comm0)
    cached = cache.get(key)
    if cached:
        return cached
    remaining = int(budget.get("remaining") or 0)
    if remaining <= 0:
        return None
    budget["remaining"] = remaining - 1
    box = _fetch_community_bbox(city0, comm0)
    if box:
        cache[key] = box
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
    return box


 
def _fallback_coords(city: str) -> Tuple[float, float]:
    return (float(base[0]), float(base[1]))
 
 
def main():
    listings_path = os.path.join(ROOT, "listings.json")
    if not os.path.exists(listings_path):
        raise SystemExit(f"listings.json not found: {listings_path}")
 
    max_geocode = int(os.getenv("MAX_GEOCODE", "30") or "30")
 
    with open(listings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
 
    c = HavenNestCrawler()
    community_cache = _load_community_bbox_cache()
    comm_budget = {"remaining": int(os.getenv("MAX_COMMUNITY_GEOBOX", "10") or "10")}
    comm_sleep = float(os.getenv("COMMUNITY_GEOBOX_SLEEP", "1.2") or "1.2")
    comm_enabled = (os.getenv("DISABLE_COMMUNITY_GEOBOX", "0") or "0").strip() not in ["1", "true", "yes"]
 
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
 
        raw_comm = item.get("community") or item.get("neighborhood") or item.get("area")
        cur_comm = _normalize_community(raw_comm)
        if cur_comm and item.get("community") != cur_comm:
            item["community"] = cur_comm
        addr_for_check = str(item.get("address") or "")
        has_detail_addr = bool(re.search(r"\d", addr_for_check))
        coord_source = (item.get("coord_source") or "").strip().lower()
 
        if coords_ok:
            if c.is_suspicious_coordinate(item):
                needs_coords = True
            elif cur_city in CITY_BBOX and not _in_bbox(cur_city, float(lat), float(lng)):
                needs_coords = True
            elif cur_city in CITY_BBOX and cur_comm and not has_detail_addr:
                box = COMMUNITY_BBOX.get((cur_city, cur_comm))
                if not box and comm_enabled:
                    box = _get_community_bbox(cur_city, cur_comm, community_cache, comm_budget, comm_sleep)
                if box and not _in_box(box, float(lat), float(lng)):
                    needs_coords = coord_source != "source_map"
 
        if not needs_coords:
            continue
        if cur_city in CITY_BBOX and cur_comm and not has_detail_addr:
            box = COMMUNITY_BBOX.get((cur_city, cur_comm))
            if not box and comm_enabled:
                box = _get_community_bbox(cur_city, cur_comm, community_cache, comm_budget, comm_sleep)
            if box:
                new_lat, new_lng = _coords_from_bbox(item, box)
                item["lat"] = float(new_lat)
                item["lng"] = float(new_lng)
                changed_coords += 1
                center_fallback += 1
                continue
 
            city_box = CITY_BBOX.get(cur_city)
            if city_box:
                new_lat, new_lng = _coords_from_bbox(item, city_box)
                item["lat"] = float(new_lat)
                item["lng"] = float(new_lng)
                changed_coords += 1
                center_fallback += 1
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
    _save_community_bbox_cache(community_cache)
 
    print(
        "Post-crawl fix done: "
        + f"city={changed_city}, beds={changed_beds}, coords_updated={changed_coords}, "
        + f"re_geocoded={re_geocoded}, center_fallback={center_fallback}, max_geocode={max_geocode}"
    )
 
 
if __name__ == "__main__":
    main()
