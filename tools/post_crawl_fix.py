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
    "North Vancouver": (49.3207, -123.0724),
    "West Vancouver": (49.3280, -123.1623),
    "Port Coquitlam": (49.2622, -122.7811),
    "Port Moody": (49.2830, -122.8300),
    "New Westminster": (49.2062, -122.9111),
    "Delta": (49.0840, -123.0580),
    "Langley": (49.1044, -122.6607),
    "Maple Ridge": (49.2195, -122.6019),
    "White Rock": (49.0253, -122.8026),
}
 
CITY_BBOX = {
    "Vancouver": (49.20, 49.34, -123.27, -123.00),
    "Richmond": (49.08, 49.21, -123.25, -123.02),
    "Burnaby": (49.20, 49.32, -123.10, -122.88),
    "Coquitlam": (49.20, 49.35, -122.93, -122.74),
    "Surrey": (49.03, 49.23, -122.98, -122.65),
    "North Vancouver": (49.30, 49.37, -123.14, -122.94),
    "West Vancouver": (49.30, 49.39, -123.27, -123.07),
    "Port Coquitlam": (49.22, 49.30, -122.83, -122.72),
    "Port Moody": (49.25, 49.32, -122.88, -122.79),
    "New Westminster": (49.18, 49.24, -122.94, -122.86),
    "Delta": (49.00, 49.20, -123.20, -122.90),
    "Langley": (49.02, 49.18, -122.78, -122.47),
    "Maple Ridge": (49.16, 49.32, -122.75, -122.45),
    "White Rock": (49.00, 49.05, -122.83, -122.77),
}
 
COMMUNITY_BBOX = {
    ("Richmond", "Thompson"): (49.145, 49.185, -123.165, -123.105),
    ("Richmond", "Brighouse"): (49.155, 49.175, -123.145, -123.105),
    ("Richmond", "City Centre"): (49.160, 49.185, -123.150, -123.105),
    ("Richmond", "West Cambie"): (49.175, 49.205, -123.190, -123.120),
    ("Richmond", "East Cambie"): (49.175, 49.205, -123.110, -123.055),
    ("Richmond", "Steveston"): (49.115, 49.145, -123.205, -123.145),
    ("Richmond", "Terra Nova"): (49.105, 49.130, -123.225, -123.195),
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
    "south arm": "Southarm",
    "terra nova": "Terra Nova",
    "whalley (city centre)": "Whalley",
    "white rock (border area)": "White Rock",
}
 
COMMUNITY_BBOX_CACHE_PATH = os.path.join(ROOT, "community_bbox_cache.json")

COMMUNITY_VOCAB = {
    "Richmond": [
        "Bridgeport",
        "Brighouse",
        "Broadmoor",
        "Burkeville",
        "Finn Slough",
        "Golden Village",
        "Sea Island",
        "Seafair",
        "Southarm",
        "Steveston",
        "Terra Nova",
        "Thompson",
        "West Cambie",
    ],
    "Burnaby": [
        "Big Bend",
        "Brentwood",
        "Buckingham Heights",
        "Burnaby Heights",
        "Cascade Heights",
        "Eastburn",
        "Garden Village",
        "Lochdale",
        "Maywood",
        "Metrotown",
        "Middlegate",
        "Montecito",
        "South Slope",
        "Sullivan Heights",
    ],
    "Vancouver": [
        "Downtown",
        "West End",
        "Yaletown",
        "Coal Harbour",
        "Kitsilano",
        "Kerrisdale",
        "Marpole",
        "Mount Pleasant",
        "Strathcona",
        "Grandview-Woodland",
        "Shaughnessy",
        "Dunbar",
        "Point Grey",
        "Killarney",
        "Renfrew-Collingwood",
    ],
    "Surrey": [
        "Whalley (City Centre)",
        "Guildford",
        "Fleetwood",
        "Newton",
        "Cloverdale",
        "South Surrey",
        "Morgan Creek",
        "White Rock (Border Area)",
    ],
    "Coquitlam": [
        "Maillardville",
        "Coquitlam West",
        "Burke Mountain",
        "Westwood Plateau",
        "Austin Heights",
        "Central Coquitlam",
        "Ranch Park",
    ],
    "Port Coquitlam": [
        "Mary Hill",
        "Citadel Heights",
        "Oxford Heights",
        "Riverwood",
        "Glenwood",
        "Central Pt Coquitlam",
    ],
    "Port Moody": [
        "Heritage Mountain",
        "Newport Village",
        "Klahanie",
        "Glenayre",
        "Ioco",
        "Moody Centre",
        "College Park",
    ],
    "Delta": [
        "Ladner",
        "Tsawwassen",
        "North Delta",
        "Sunshine Hills",
        "Tilbury",
    ],
    "New Westminster": [
        "Queensborough",
        "Uptown",
        "Downtown",
        "West End",
        "Brow of the Hill",
        "Sapperton",
        "Victoria Hill",
    ],
    "Langley": [
        "Walnut Grove",
        "Willoughby Heights",
        "Brookswood",
        "Aldergrove",
        "Fort Langley",
        "Murrayville",
        "Langley City",
    ],
    "Maple Ridge": [
        "Haney",
        "Albion",
        "Silver Valley",
        "Cottonwood",
        "Whonnock",
        "Webster's Corners",
    ],
}

BUILDING_VOCAB = {
    "Richmond": [
        ("river green 2", "6688 Pearson Way, Richmond, BC"),
        ("rivergreen 2", "6688 Pearson Way, Richmond, BC"),
        ("river green", "River Green, Richmond, BC"),
        ("rivergreen", "River Green, Richmond, BC"),
        ("concord gardens", "Concord Gardens, Richmond, BC"),
        ("viewstar", "ViewStar, Richmond, BC"),
        ("郡苑", "ViewStar, Richmond, BC"),
        ("hollybridge", "Hollybridge at River Green, Richmond, BC"),
        ("cascade city", "Cascade City, Richmond, BC"),
        ("orchid", "Orchid, Richmond, BC"),
        ("lotus", "Lotus, Richmond, BC"),
        ("flo", "FLO, Richmond, BC"),
        ("quintet", "Quintet, Richmond, BC"),
        ("wall centre richmond", "Wall Centre Richmond, Richmond, BC"),
        ("paddocks townhouses", "Paddocks townhouses, Richmond, BC"),
    ],
    "Burnaby": [
        ("the amazing brentwood", "The Amazing Brentwood, Burnaby, BC"),
        ("amazing brentwood", "The Amazing Brentwood, Burnaby, BC"),
        ("concord brentwood", "Concord Brentwood, Burnaby, BC"),
        ("solo district", "Solo District, Burnaby, BC"),
        ("gilmore place", "Gilmore Place, Burnaby, BC"),
        ("station square", "Station Square, Burnaby, BC"),
        ("the sovereign", "The Sovereign, Burnaby, BC"),
        ("gold house", "Gold House, Burnaby, BC"),
        ("sun towers", "Sun Towers, Burnaby, BC"),
        ("silver towers", "Silver Towers, Burnaby, BC"),
        ("concord metrotown", "Concord Metrotown, Burnaby, BC"),
        ("city of lougheed", "The City of Lougheed, Burnaby, BC"),
    ],
    "Vancouver": [
        ("vancouver house", "Vancouver House, Vancouver, BC"),
        ("shangri-la", "Shangri-La, Vancouver, BC"),
        ("shangri la", "Shangri-La, Vancouver, BC"),
        ("paradox", "Paradox Hotel Vancouver, Vancouver, BC"),
        ("pacific rim", "Fairmont Pacific Rim, Vancouver, BC"),
        ("telus garden", "TELUS Garden, Vancouver, BC"),
        ("the butterfly", "The Butterfly, Vancouver, BC"),
        ("olympic village", "Olympic Village, Vancouver, BC"),
        ("marine gateway", "Marine Gateway, Vancouver, BC"),
        ("oakridge park", "Oakridge Park, Vancouver, BC"),
        ("oakridge", "Oakridge, Vancouver, BC"),
        ("w1", "W1, Vancouver, BC"),
        ("marine club", "Marine Club, Vancouver, BC"),
    ],
    "Surrey": [
        ("3 civic plaza", "3 Civic Plaza, Surrey, BC"),
        ("park boulevard", "Park Boulevard, Surrey, BC"),
        ("park place", "Park Place, Surrey, BC"),
        ("king george hub", "King George Hub, Surrey, BC"),
        ("evolve", "Evolve, Surrey, BC"),
        ("prime", "Prime, Surrey, BC"),
        ("georgetown", "Georgetown, Surrey, BC"),
    ],
    "Coquitlam": [
        ("567 clarke", "567 Clarke + Como, Coquitlam, BC"),
        ("clarke + como", "567 Clarke + Como, Coquitlam, BC"),
        ("clarke and como", "567 Clarke + Como, Coquitlam, BC"),
        ("the marquee", "The Marquee, Coquitlam, BC"),
        ("uptown", "Uptown, Coquitlam, BC"),
    ],
    "New Westminster": [
        ("pier west", "Pier West, New Westminster, BC"),
        ("riversky", "RiverSky, New Westminster, BC"),
        ("river sky", "RiverSky, New Westminster, BC"),
    ],
}

BUILDING_ANCHORS_PATH = os.path.join(ROOT, "building_anchors.json")

 
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
 
 
def _city_hint_from_craigslist_url(url: str) -> str:
    try:
        u = str(url or "")
        m0 = re.search(r"craigslist\.org/[a-z]{3}/apa/d/([a-z0-9-]+?)-", u, flags=re.IGNORECASE)
        if m0:
            slug = (m0.group(1) or "").lower()
            mslug = {
                "vancouver": "Vancouver",
                "richmond": "Richmond",
                "burnaby": "Burnaby",
                "coquitlam": "Coquitlam",
                "surrey": "Surrey",
                "delta": "Delta",
                "langley": "Langley",
                "maple-ridge": "Maple Ridge",
                "white-rock": "White Rock",
                "new-westminster": "New Westminster",
                "north-vancouver": "North Vancouver",
                "west-vancouver": "West Vancouver",
                "port-coquitlam": "Port Coquitlam",
                "port-moody": "Port Moody",
            }
            if slug in mslug:
                return mslug[slug]
        m = re.search(r"craigslist\.org/([a-z]{3})/", u, flags=re.IGNORECASE)
        if not m:
            return ""
        code = (m.group(1) or "").lower()
        m2 = {
            "van": "Vancouver",
            "rch": "Richmond",
            "nmo": "Port Moody",
            "nwb": "New Westminster",
            "nvy": "North Vancouver",
            "pml": "",
            "wht": "White Rock",
            "dlt": "Delta",
            "lan": "Langley",
        }
        return m2.get(code, "") or ""
    except Exception:
        return ""


def _city_from_coords(lat: float, lng: float, preferred_city: str = "") -> str:
    try:
        candidates = []
        for city, box in CITY_BBOX.items():
            if _in_box(box, float(lat), float(lng)):
                candidates.append(city)
        if not candidates:
            return ""
        if len(candidates) == 1:
            return candidates[0]
        if preferred_city:
            for c0 in candidates:
                if c0.lower() == preferred_city.lower():
                    return c0
        best = ""
        best_d = None
        for city in candidates:
            center = CITY_CENTERS.get(city)
            if not center:
                continue
            d = (float(lat) - float(center[0])) ** 2 + (float(lng) - float(center[1])) ** 2
            if best_d is None or d < best_d:
                best_d = d
                best = city
        return best or candidates[0]
    except Exception:
        return ""

 
def _cache_key_from_query(query: str) -> str:
    clean_addr = re.sub(r"[^\w\s,.-]", "", (query or "")).strip()
    return f"{clean_addr}, BC, Canada"
 
 
def _normalize_geocode_query(q: str) -> str:
    s = str(q or "").strip()
    if not s:
        return ""
    s = re.sub(r"(?i)\bno\.\s*(\d+)\b", r"No \1", s)
    s = re.sub(r"\bNo\s*(\d+)\b", r"No \1", s)
    s = re.sub(r"(?i)^\s*(?:#\s*)?[0-9a-z]{1,6}\s*-\s*", "", s)
    def _xx_to_mid2(m):
        try:
            p = int(m.group(1))
            return str(p * 100 + 50)
        except Exception:
            return m.group(0)
    s = re.sub(r"(?i)\b(\d{2,4})\s*x{2,4}\b", _xx_to_mid2, s)
    s = re.sub(r"(?i)\b(vancouver|richmond|burnaby|coquitlam|surrey|delta|langley|new westminster|north vancouver|west vancouver)(?:\s+\\1)+\b", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

 
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
 
def _community_aliases(name: str) -> list:
    s = (name or "").strip()
    if not s:
        return []
    out = [s]
    if "(" in s and ")" in s:
        head = s.split("(", 1)[0].strip()
        if head and head not in out:
            out.append(head)
        inside = s.split("(", 1)[1].rsplit(")", 1)[0].strip()
        if inside and inside not in out:
            out.append(inside)
    return out


def _build_alias_pattern(alias: str) -> str:
    a = (alias or "").strip().lower().replace("’", "'")
    a = a.replace("&", " and ")
    a = re.sub(r"\s+", " ", a).strip()
    if not a:
        return ""
    p = re.escape(a)
    p = p.replace(r"\ ", r"\s+")
    p = p.replace(r"\-", r"[\s\-]+")
    p = p.replace("'", r"['’]")
    return r"(?<![a-z])" + p + r"(?![a-z])"


def _infer_community_from_text(city: str, text: str) -> str:
    city0 = (city or "").strip()
    if not city0:
        return ""
    vocab = COMMUNITY_VOCAB.get(city0) or []
    if not vocab:
        return ""
    t = (text or "").lower().replace("’", "'")
    best = ""
    best_len = 0
    for name in vocab:
        for alias in _community_aliases(name):
            pat = _build_alias_pattern(alias)
            if not pat:
                continue
            if re.search(pat, t, flags=re.IGNORECASE):
                if len(alias) > best_len:
                    best = name
                    best_len = len(alias)
    return best

 
def _infer_building_query(city: str, text: str) -> str:
    city0 = (city or "").strip()
    if not city0:
        return ""
    vocab = BUILDING_VOCAB.get(city0) or []
    if not vocab:
        return ""
    t = (text or "").lower()
    for needle, building in vocab:
        if needle in t:
            b = str(building).strip()
            if not b:
                return ""
            if re.search(r"(?i)\b(canada|bc)\b", b):
                return b
            if re.search(r"(?i)\b(vancouver|richmond|burnaby|surrey|coquitlam|new westminster)\b", b):
                return b
            return f"{b}, {city0}, BC, Canada"
    return ""


def _load_building_vocab() -> Dict[str, list]:
    merged: Dict[str, list] = {}
    for city, items in (BUILDING_VOCAB or {}).items():
        merged[city] = list(items) if isinstance(items, list) else []
    try:
        if os.path.exists(BUILDING_ANCHORS_PATH):
            with open(BUILDING_ANCHORS_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for city, arr in raw.items():
                    if not isinstance(city, str) or not isinstance(arr, list):
                        continue
                    out = merged.get(city, [])
                    for rec in arr:
                        if not isinstance(rec, dict):
                            continue
                        anchor = str(rec.get("anchor_query") or "").strip()
                        aliases = rec.get("aliases") or []
                        if not anchor or not isinstance(aliases, list):
                            continue
                        for a in aliases:
                            s = str(a or "").strip().lower()
                            if s:
                                out.append((s, anchor))
                    merged[city] = out
    except Exception:
        pass
    return merged


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


def _looks_like_city_only_address(addr: str, cur_city: str) -> bool:
    a = (addr or "").strip()
    if not a:
        return True
    if re.search(r"\d", a):
        return False
    low = a.lower()
    city_names = [x.lower() for x in CITY_CENTERS.keys()]
    if low in city_names and low != (cur_city or "").strip().lower():
        return True
    if low in ["vancouver", "richmond", "burnaby", "surrey", "coquitlam"]:
        return low != (cur_city or "").strip().lower()
    return False


_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def _cn_to_int(s: str) -> int:
    t = (s or "").strip()
    if not t:
        return 0
    if t.isdigit():
        try:
            return int(t)
        except Exception:
            return 0
    if t in _CN_NUM:
        return _CN_NUM[t]
    return 0


def _normalize_street_name(s: str) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    t = t.replace("’", "'")
    t = re.sub(r"\bstn\b", "station", t, flags=re.IGNORECASE)
    m = re.search(r"([一二三四五六七八九十0-9]+)\s*号\s*路", t)
    if m:
        n = _cn_to_int(m.group(1))
        if n:
            return f"No. {n} Road"
    m = re.search(r"\bno\.?\s*(\d+)\b", t, flags=re.IGNORECASE)
    if m and "road" in t.lower():
        return f"No. {int(m.group(1))} Road"
    t = re.sub(r"(大道|大街)$", " Ave", t)
    t = re.sub(r"(街)$", " St", t)
    t = re.sub(r"(路)$", " Rd", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _extract_intersection(text: str) -> Tuple[str, str]:
    t = (text or "")
    if not t:
        return ("", "")
    m = re.search(r"([A-Za-z0-9.'\-\u4e00-\u9fff\s]+?)\s*(?:与|和|&|and)\s*([A-Za-z0-9.'\-\u4e00-\u9fff\s]+?)\s*(?:交汇处|交界处|路口|交叉口|intersection|cross)", t, flags=re.IGNORECASE)
    if m:
        a = _normalize_street_name(m.group(1))
        b = _normalize_street_name(m.group(2))
        return (a, b)
    return ("", "")


def _extract_street(text: str) -> str:
    t = (text or "")
    if not t:
        return ""
    m = re.search(r"([A-Za-z][A-Za-z0-9.'\-\s]{2,}?)\s*(?:Road|Rd|Street|St|Avenue|Ave)\b", t, flags=re.IGNORECASE)
    if m:
        return _normalize_street_name(m.group(0))
    m = re.search(r"([A-Za-z][A-Za-z0-9.'\-\s]{2,}?)\s*(?:路|街|大道)\b", t, flags=re.IGNORECASE)
    if m:
        return _normalize_street_name(m.group(0))
    m = re.search(r"([一二三四五六七八九十0-9]+)\s*号\s*路", t)
    if m:
        return _normalize_street_name(m.group(0))
    return ""


def _is_source_map(coord_source: str) -> bool:
    s = (coord_source or "").strip().lower()
    return s.startswith("source_map")


def _near_city_center(city: str, lat: float, lng: float) -> bool:
    base = CITY_CENTERS.get(city) or CITY_CENTERS["Vancouver"]
    try:
        return abs(float(lat) - float(base[0])) <= 0.0008 and abs(float(lng) - float(base[1])) <= 0.0008
    except Exception:
        return False


def _clean_extracted_addr(s: str) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    t = re.sub(r"\s*查看地图.*$", "", t).strip()
    t = re.sub(r"(?i)^\s*(?:#\s*)?[0-9a-z]{1,6}\s*-\s*", "", t)
    def _xx_to_mid(m):
        try:
            p = int(m.group(1))
            return str(p * 100 + 50)
        except Exception:
            return m.group(0)
    t = re.sub(r"(?i)\b(\d{2,4})\s*x{2,4}\b", _xx_to_mid, t)
    t = re.sub(r"\s+", " ", t)
    return t


def _extract_detailed_address(text: str) -> str:
    t = text or ""
    if not t:
        return ""
    candidates = []
    for pat in [
        r"(?im)^\s*address\s*:\s*(.+?)\s*$",
        r"(?im)^\s*addr\s*:\s*(.+?)\s*$",
        r"(?im)^\s*location\s*:\s*(.+?)\s*$",
        r"(?im)^\s*联系地址\s*(?:[:：])?\s*(.+?)\s*$",
        r"(?im)^\s*地址\s*(?:[:：])?\s*(.+?)\s*$",
    ]:
        for m in re.finditer(pat, t):
            v = _clean_extracted_addr(m.group(1))
            if v:
                candidates.append(v)
    lines = [x.strip() for x in (t.splitlines() if isinstance(t, str) else [])]
    for i, line in enumerate(lines):
        low = line.replace("：", ":").strip().lower()
        if low in ["联系地址", "联系地址:", "地址", "地址:"]:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                v = _clean_extracted_addr(lines[j])
                if v:
                    candidates.append(v)
    if not candidates:
        return ""
    candidates = [c for c in candidates if re.search(r"\d", c)]
    if not candidates:
        return ""
    candidates.sort(key=len, reverse=True)
    return candidates[0]


def _try_geocode_query(
    c: HavenNestCrawler,
    query: str,
    cur_city: str,
    cur_comm: str,
    box: Optional[Tuple[float, float, float, float]],
    max_geocode: int,
    geocode_used: int,
) -> Tuple[Optional[Tuple[float, float]], int]:
    if not query:
        return (None, geocode_used)
    if geocode_used >= max_geocode:
        return (None, geocode_used)
    cache_key = _cache_key_from_query(query)
    if cache_key in c.coords_cache:
        try:
            del c.coords_cache[cache_key]
        except Exception:
            pass
    geocode_used += 1
    coords = c.get_lat_lng(query)
    try:
        new_lat = float(coords[0]) if coords and coords[0] is not None else None
        new_lng = float(coords[1]) if coords and coords[1] is not None else None
    except Exception:
        new_lat, new_lng = None, None
    if new_lat is None or new_lng is None:
        return (None, geocode_used)
    if cur_city in CITY_BBOX and not _in_bbox(cur_city, float(new_lat), float(new_lng)):
        return (None, geocode_used)
    if box and cur_comm and not _in_box(box, float(new_lat), float(new_lng)):
        return (None, geocode_used)
    return ((new_lat, new_lng), geocode_used)


 
def _fallback_coords(city: str) -> Tuple[float, float]:
    base = CITY_CENTERS.get(city) or CITY_CENTERS["Vancouver"]
    return (float(base[0]), float(base[1]))
 
 
def main():
    listings_path = os.path.join(ROOT, "listings.json")
    if not os.path.exists(listings_path):
        raise SystemExit(f"listings.json not found: {listings_path}")
 
    max_geocode = int(os.getenv("MAX_GEOCODE", "30") or "30")
    max_priority_geocode = int(os.getenv("MAX_PRIORITY_GEOCODE", "60") or "60")
    max_building_geocode = int(os.getenv("MAX_BUILDING_GEOCODE", "10") or "10")
 
    with open(listings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
 
    c = HavenNestCrawler()
    global BUILDING_VOCAB
    BUILDING_VOCAB = _load_building_vocab()
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
    priority_geocode_used = 0
    building_geocode_used = 0
 
    for item in data:
        source = (item.get("source") or "").strip().lower()
        title = str(item.get("title") or "")
        addr = str(item.get("address") or "")
        desc = str(item.get("desc") or item.get("description") or "")
        text = " ".join([title, addr] if source == "vanpeople" else [title, addr, desc])
 
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
        coord_source = (item.get("coord_source") or "").strip().lower()
        is_source_map = _is_source_map(coord_source)
        if coords_ok and is_source_map:
            preferred_city = ""
            if source == "craigslist":
                preferred_city = _city_hint_from_craigslist_url(item.get("url") or "")
            new_city = _city_from_coords(float(lat), float(lng), preferred_city=preferred_city)
            if new_city and (not cur_city or cur_city.lower() != new_city.lower()):
                item["city"] = new_city
                changed_city += 1
                cur_city = new_city
                for k in ["community", "neighborhood", "area"]:
                    if item.get(k):
                        item[k] = ""
 
        raw_comm = item.get("community") or item.get("neighborhood") or item.get("area")
        if not raw_comm and cur_city:
            inferred_comm = _infer_community_from_text(cur_city, text)
            if inferred_comm:
                raw_comm = inferred_comm
                item["community"] = inferred_comm
        cur_comm = _normalize_community(raw_comm)
        if cur_comm and item.get("community") != cur_comm:
            item["community"] = cur_comm
        if cur_city and cur_comm:
            try:
                vocab = COMMUNITY_VOCAB.get(cur_city) or []
                if vocab and (cur_comm not in vocab) and ((cur_city, cur_comm) not in COMMUNITY_BBOX):
                    item["community"] = ""
                    cur_comm = ""
            except Exception:
                pass
        addr_for_check = str(item.get("address") or "")
        addr_clean = _clean_extracted_addr(addr_for_check)
        if addr_clean and addr_clean != addr_for_check:
            item["address"] = addr_clean
            addr_for_check = addr_clean
        has_detail_addr = bool(re.search(r"(?i)^\s*(?:(?:#\s*)?[0-9a-z]{1,6}\s*-\s*)?\s*\d{3,6}\b", addr_for_check))
        priority_needs_geocode = False
        
        if (not has_detail_addr) and re.search(r"(?i)\bburquitlam\b", text) and re.search(r"(?i)(station|skytrain|天车)", text):
            item["city"] = "Coquitlam"
            cur_city = "Coquitlam"
            item["community"] = "Burquitlam"
            cur_comm = "Burquitlam"
            item["address"] = "Burquitlam Station, Coquitlam"
            addr_for_check = str(item.get("address") or "")
            has_detail_addr = True
            needs_coords = True
            priority_needs_geocode = True

        if source == "owner" and (cur_city or "").strip().lower() == "richmond" and (cur_comm or "").strip().lower() == "thompson" and (not has_detail_addr):
            u = _stable_u(item, "thompson_lat")
            v = _stable_u(item, "thompson_lng")
            item["lat"] = 49.1633 + (u - 0.5) * 0.0018
            item["lng"] = -123.1653617 + (v - 0.5) * 0.0018
            item["coord_source"] = "community_anchor_fixed"
            changed_coords += 1
            continue

        if not has_detail_addr and _looks_like_city_only_address(addr_for_check, cur_city):
            item["address"] = f"{cur_comm}, {cur_city}".strip(", ").strip() if cur_comm else (cur_city or "Vancouver")
            addr_for_check = str(item.get("address") or "")
 
        extracted_addr = ""
        if not has_detail_addr:
            extracted_addr = _extract_detailed_address(text)
            if extracted_addr:
                item["address"] = extracted_addr
                addr_for_check = extracted_addr
                has_detail_addr = True
        if not has_detail_addr:
            try:
                mxx = re.search(r"(?i)\b(\d{2,4}\s*x{2,4})\b\s+([a-z][a-z0-9 .'-]{1,50}\b(?:road|rd|drive|dr|avenue|ave|street|st|place|pl|way|blvd|boulevard|crescent|cres|lane|ln|court|ct|terrace|terr)\b)", text)
                if mxx:
                    candidate = f\"{mxx.group(1)} {mxx.group(2)}\"
                    candidate = _clean_extracted_addr(candidate)
                    if candidate:
                        item[\"address\"] = f\"{candidate}, {cur_city}\".strip(\", \")
                        addr_for_check = str(item.get(\"address\") or \"\")
                        has_detail_addr = True
            except Exception:
                pass
        if not has_detail_addr:
            try:
                a, b = _extract_intersection(text)
                if a and b and cur_city:
                    item[\"address\"] = f\"{a} & {b}, {cur_city}\"
                    addr_for_check = str(item.get(\"address\") or \"\")
                    has_detail_addr = True
            except Exception:
                pass
        if (not coords_ok) and has_detail_addr and (not is_source_map):
            priority_needs_geocode = True

        if coords_ok:
            if c.is_suspicious_coordinate(item):
                needs_coords = not is_source_map
            elif cur_city in CITY_BBOX and not _in_bbox(cur_city, float(lat), float(lng)):
                needs_coords = not is_source_map
            elif cur_city and cur_comm and not has_detail_addr:
                box = COMMUNITY_BBOX.get((cur_city, cur_comm))
                if not box and comm_enabled:
                    box = _get_community_bbox(cur_city, cur_comm, community_cache, comm_budget, comm_sleep)
                if box and not _in_box(box, float(lat), float(lng)):
                    needs_coords = not is_source_map

            if has_detail_addr and (not is_source_map) and _near_city_center(cur_city, float(lat), float(lng)):
                needs_coords = True
                priority_needs_geocode = True
            if coord_source == "map_query" and has_detail_addr and (not is_source_map):
                needs_coords = True
                priority_needs_geocode = True
            if coord_source == "map_query" and (not has_detail_addr) and (not is_source_map):
                try:
                    base = CITY_CENTERS.get(cur_city) or CITY_CENTERS["Vancouver"]
                    if abs(float(lat) - float(base[0])) <= 0.015 and abs(float(lng) - float(base[1])) <= 0.015:
                        needs_coords = True
                        priority_needs_geocode = True
                except Exception:
                    pass
            if source == "owner" and has_detail_addr and (not is_source_map):
                needs_coords = True
                priority_needs_geocode = True

            if (not has_detail_addr) and (not is_source_map) and _near_city_center(cur_city, float(lat), float(lng)):
                a, b = _extract_intersection(text)
                s = _extract_street(text)
                if a and b:
                    needs_coords = True
                elif s and cur_comm:
                    needs_coords = True
 
        if source == "owner" and cur_city and cur_comm and (not has_detail_addr) and (not is_source_map):
            needs_coords = True

        if not needs_coords:
            continue

        box_for_comm = None
        if cur_city and cur_comm and comm_enabled:
            box_for_comm = COMMUNITY_BBOX.get((cur_city, cur_comm)) or _get_community_bbox(cur_city, cur_comm, community_cache, comm_budget, comm_sleep)

        if (not has_detail_addr) and (not cur_comm) and (not is_source_map) and cur_city and (building_geocode_used < max_building_geocode):
            bq = _infer_building_query(cur_city, text)
            if bq:
                coords2, building_geocode_used = _try_geocode_query(c, bq, cur_city, "", None, max_building_geocode, building_geocode_used)
                if coords2:
                    item["lat"] = float(coords2[0])
                    item["lng"] = float(coords2[1])
                    item["coord_source"] = "building_name"
                    changed_coords += 1
                    re_geocoded += 1
                    continue

        if (not has_detail_addr) and (not is_source_map):
            a, b = _extract_intersection(text)
            if a and b:
                for street in [a, b]:
                    q = f"{street}, {cur_comm}, {cur_city}, BC, Canada"
                    coords2, geocode_used = _try_geocode_query(c, q, cur_city, cur_comm, None, max_geocode, geocode_used)
                    if coords2:
                        item["lat"] = float(coords2[0])
                        item["lng"] = float(coords2[1])
                        item["coord_source"] = "text_intersection"
                        changed_coords += 1
                        re_geocoded += 1
                        continue
                if item.get("coord_source") == "text_intersection":
                    continue
            s = _extract_street(text)
            if s and cur_comm:
                q = f"{s}, {cur_comm}, {cur_city}, BC, Canada"
                coords2, geocode_used = _try_geocode_query(c, q, cur_city, cur_comm, None, max_geocode, geocode_used)
                if coords2:
                    item["lat"] = float(coords2[0])
                    item["lng"] = float(coords2[1])
                    item["coord_source"] = "text_street"
                    changed_coords += 1
                    re_geocoded += 1
                    continue

        if source == "owner" and cur_city and cur_comm and (not has_detail_addr) and (not is_source_map):
            q = f"{cur_comm}, {cur_city}, BC, Canada"
            if cur_city.lower() == "richmond" and cur_comm.lower() == "thompson":
                q = f"Thompson Community Centre, {cur_city}, BC, Canada"
            coords2, geocode_used = _try_geocode_query(c, q, cur_city, cur_comm, None, max_geocode, geocode_used)
            if coords2:
                item["lat"] = float(coords2[0])
                item["lng"] = float(coords2[1])
                item["coord_source"] = "community_anchor"
                changed_coords += 1
                re_geocoded += 1
                continue

        if cur_city and cur_comm and not has_detail_addr:
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
        if cur_city in CITY_BBOX and (not has_detail_addr):
            city_box = CITY_BBOX.get(cur_city)
            if city_box:
                new_lat, new_lng = _coords_from_bbox(item, city_box)
                item["lat"] = float(new_lat)
                item["lng"] = float(new_lng)
                changed_coords += 1
                center_fallback += 1
                continue
 
        query = c.build_geocode_query(str(item.get("address") or ""), cur_city)
        cache_key = _cache_key_from_query(query)
        if cache_key in c.coords_cache:
            try:
                del c.coords_cache[cache_key]
            except Exception:
                pass
 
        new_lat = None
        new_lng = None
        allow_geocode = geocode_used < max_geocode
        if (not allow_geocode) and bool(priority_needs_geocode) and (priority_geocode_used < max_priority_geocode):
            allow_geocode = True
            priority_geocode_used += 1
        elif allow_geocode:
            geocode_used += 1
        if allow_geocode:
            query = _normalize_geocode_query(query)
            coords = c.get_lat_lng(query)
            try:
                new_lat = float(coords[0]) if coords and coords[0] is not None else None
                new_lng = float(coords[1]) if coords and coords[1] is not None else None
            except Exception:
                new_lat = None
                new_lng = None
            if (new_lat is None or new_lng is None) and has_detail_addr:
                try:
                    q2 = re.sub(r"^\s*\d{1,6}\s+", "", query).strip()
                except Exception:
                    q2 = ""
                if q2 and q2 != query:
                    coords2 = c.get_lat_lng(q2)
                    try:
                        new_lat = float(coords2[0]) if coords2 and coords2[0] is not None else None
                        new_lng = float(coords2[1]) if coords2 and coords2[1] is not None else None
                    except Exception:
                        new_lat = None
                        new_lng = None
            if (new_lat is None or new_lng is None) and ("ubc" in query.lower()):
                try:
                    q3 = re.sub(r"(?i)\bubc\b", "", query)
                    q3 = re.sub(r"\s+", " ", q3).strip(" ,")
                except Exception:
                    q3 = ""
                if q3 and q3 != query:
                    coords3 = c.get_lat_lng(q3)
                    try:
                        new_lat = float(coords3[0]) if coords3 and coords3[0] is not None else None
                        new_lng = float(coords3[1]) if coords3 and coords3[1] is not None else None
                    except Exception:
                        new_lat = None
                        new_lng = None
            if (new_lat is None or new_lng is None) and (not has_detail_addr) and ("mcnai" in query.lower() or "mcnair" in query.lower()):
                q4 = query
                q4 = re.sub(r"(?i)\bsecondary\b", "Secondary School", q4)
                q4 = re.sub(r"(?i)\bschool school\b", "School", q4)
                q4 = re.sub(r"\s+", " ", q4).strip()
                if q4 and q4 != query:
                    coords4 = c.get_lat_lng(q4)
                    try:
                        new_lat = float(coords4[0]) if coords4 and coords4[0] is not None else None
                        new_lng = float(coords4[1]) if coords4 and coords4[1] is not None else None
                    except Exception:
                        new_lat = None
                        new_lng = None
 
            if new_lat is not None and new_lng is not None:
                re_geocoded += 1
                if not is_source_map:
                    cs0 = (item.get("coord_source") or "").strip().lower()
                    if cs0 == "map_query":
                        item["coord_source"] = "map_query_geocode"
                    elif source == "owner":
                        item["coord_source"] = "geocode_owner"
                    elif not cs0:
                        item["coord_source"] = "geocode"
 
        if (new_lat is None or new_lng is None) and (not allow_geocode) and coords_ok:
            continue
        if new_lat is None or new_lng is None or (cur_city in CITY_BBOX and not _in_bbox(cur_city, float(new_lat), float(new_lng))):
            base_lat, base_lng = _fallback_coords(cur_city)
            u = _stable_u(item, "city_fallback_lat")
            v = _stable_u(item, "city_fallback_lng")
            new_lat = float(base_lat) + (u - 0.5) * 0.01
            new_lng = float(base_lng) + (v - 0.5) * 0.01
            item["coord_source"] = "city_center_fallback"
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
