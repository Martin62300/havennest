import argparse
import csv
import importlib.util
import json
import math
import os
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple


def _load_post_crawl_fix_module(root_dir: str):
    p = os.path.join(root_dir, "tools", "post_crawl_fix.py")
    spec = importlib.util.spec_from_file_location("post_crawl_fix", p)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load tools/post_crawl_fix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d1 = math.radians(lat2 - lat1)
    d2 = math.radians(lng2 - lng1)
    a = math.sin(d1 / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d2 / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _in_bbox(box: Tuple[float, float, float, float], lat: float, lng: float) -> bool:
    lat_min, lat_max, lng_min, lng_max = box
    return (lat_min <= lat <= lat_max) and (lng_min <= lng <= lng_max)


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _has_detail_addr(addr: str) -> bool:
    a = (addr or "").strip()
    if not a:
        return False
    if not re.search(r"(?i)^\s*(?:(?:#\s*)?[0-9a-z]{1,6}\s*-\s*)?\s*\d{3,6}\b", a):
        return False
    street_typ = r"(?:Ave|Avenue|St|Street|Rd|Road|Dr|Drive|Blvd|Boulevard|Ln|Lane|Way|Pl|Place|Ct|Court|Cres|Crescent|Terr|Terrace|Hwy|Highway)"
    return bool(re.search(rf"(?i)\b{street_typ}\b", a))


def _has_street_level_addr(addr: str) -> bool:
    a = (addr or "").strip()
    if not a:
        return False
    street_typ = r"(?:Ave|Avenue|St|Street|Rd|Road|Dr|Drive|Blvd|Boulevard|Ln|Lane|Way|Pl|Place|Ct|Court|Cres|Crescent|Terr|Terrace|Hwy|Highway)"
    return bool(re.search(rf"(?i)\b{street_typ}\b", a))


def _is_city_only(addr: str) -> bool:
    a = (addr or "").strip().lower()
    if not a:
        return False
    a = re.sub(r"[^a-z\s]", " ", a)
    a = re.sub(r"\s+", " ", a).strip()
    if a in {
        "vancouver",
        "richmond",
        "burnaby",
        "surrey",
        "coquitlam",
        "delta",
        "langley",
        "new westminster",
        "north vancouver",
        "west vancouver",
        "port coquitlam",
        "port moody",
        "abbotsford",
        "maple ridge",
        "white rock",
    }:
        return True
    if re.fullmatch(r"vancouver\s+(east|west|north|south)", a):
        return True
    if a in {"east vancouver", "west vancouver", "north vancouver", "south vancouver"}:
        return True
    return False


def audit_listings(items: List[Dict[str, Any]], pcf) -> Dict[str, Any]:
    city_bbox = getattr(pcf, "CITY_BBOX", {}) or {}
    city_centers = getattr(pcf, "CITY_CENTERS", {}) or {}
    community_bbox = getattr(pcf, "COMMUNITY_BBOX", {}) or {}
    city_hint_fn = getattr(pcf, "_city_hint_from_craigslist_url", None)

    issues: List[Dict[str, Any]] = []
    reason_counts = Counter()

    for it in items:
        if not isinstance(it, dict):
            continue

        src = (it.get("source") or "").strip()
        city = (it.get("city") or "").strip()
        comm = (it.get("community") or "").strip()
        addr = (it.get("address") or "").strip()
        url = (it.get("url") or "").strip()
        coord_source = (it.get("coord_source") or "").strip()
        lat = _safe_float(it.get("lat"))
        lng = _safe_float(it.get("lng"))

        if lat is None or lng is None:
            continue

        reasons: List[str] = []

        if city and city in city_bbox and (not _in_bbox(city_bbox[city], lat, lng)):
            reasons.append("out_of_city_bbox")

        if src.lower() == "craigslist" and city_hint_fn and url:
            try:
                hint = city_hint_fn(url) or ""
            except Exception:
                hint = ""
            if hint and city and hint.lower() != city.lower():
                reasons.append("craigslist_city_mismatch_url_hint")

        if src.lower() == "vanpeople":
            if _is_city_only(addr) and (not re.search(r"\d", addr)) and (" & " not in addr):
                reasons.append("vanpeople_city_only_address")

        if comm and city and (city, comm) in community_bbox and coord_source not in ("community_bbox", "city_bbox"):
            box = community_bbox[(city, comm)]
            if not _in_bbox(box, lat, lng):
                reasons.append("out_of_community_bbox")

        if coord_source in ("city_bbox", "community_bbox") and _has_detail_addr(addr):
            reasons.append("bbox_but_has_house_number")

        if coord_source == "city_center_fallback" and _has_street_level_addr(addr):
            reasons.append("center_fallback_with_street")

        if city and city in city_centers and _has_detail_addr(addr):
            c0 = city_centers[city]
            try:
                d_km = _haversine_km(lat, lng, float(c0[0]), float(c0[1]))
            except Exception:
                d_km = None
            if d_km is not None and d_km <= 0.8 and coord_source in ("city_center_fallback", "city_bbox", "community_bbox"):
                reasons.append("near_city_center_with_detail_addr")

        if reasons:
            for r in reasons:
                reason_counts[r] += 1
            issues.append(
                {
                    "source": src,
                    "city": city,
                    "community": comm,
                    "address": addr,
                    "coord_source": coord_source,
                    "lat": lat,
                    "lng": lng,
                    "url": url,
                    "reasons": reasons,
                }
            )

    issues.sort(key=lambda x: (len(x.get("reasons") or []), x.get("source") or "", x.get("city") or ""), reverse=True)
    return {"issues": issues, "reason_counts": dict(reason_counts), "total": len(items)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="listings.json")
    ap.add_argument("--output", default="location_audit.json")
    ap.add_argument("--csv", default="location_audit.csv")
    ap.add_argument("--max_print", type=int, default=80)
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pcf = _load_post_crawl_fix_module(root)

    with open(args.input, "r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise RuntimeError("Input must be a JSON array")

    rep = audit_listings(items, pcf)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    with open(args.csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "city", "community", "coord_source", "lat", "lng", "address", "url", "reasons"])
        for it in rep["issues"]:
            w.writerow(
                [
                    it.get("source", ""),
                    it.get("city", ""),
                    it.get("community", ""),
                    it.get("coord_source", ""),
                    it.get("lat", ""),
                    it.get("lng", ""),
                    it.get("address", ""),
                    it.get("url", ""),
                    "|".join(it.get("reasons") or []),
                ]
            )

    print(f"Location audit: total={rep['total']}, issues={len(rep['issues'])}")
    top = sorted(rep["reason_counts"].items(), key=lambda kv: kv[1], reverse=True)
    for k, v in top[:20]:
        print(f"  {k}: {v}")
    if rep["issues"]:
        print("")
        print("Top suspicious listings:")
        for it in rep["issues"][: max(1, int(args.max_print))]:
            print(f"- [{it.get('source')}] {it.get('city')} {it.get('coord_source')} {it.get('address')}")
            if it.get("url"):
                print(f"  {it['url']}")
            rs = it.get("reasons") or []
            if rs:
                print(f"  reasons={','.join(rs)}")


if __name__ == "__main__":
    main()

