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


def _pad_bbox(box: Tuple[float, float, float, float], pad_lat: float, pad_lng: float) -> Tuple[float, float, float, float]:
    lat_min, lat_max, lng_min, lng_max = box
    return (lat_min - pad_lat, lat_max + pad_lat, lng_min - pad_lng, lng_max + pad_lng)


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _has_detail_addr(addr: str) -> bool:
    a = (addr or "").replace("\xa0", " ").replace("’", "'").strip()
    if not a:
        return False
    if not re.search(r"(?i)^\s*(?:address\s*:\s*)?(?:(?:#\s*)?[0-9a-z]{1,6}\s*(?:--+|-)\s*)?\s*\d{3,6}\b", a):
        return False
    street_typ = r"(?:Ave|Avenue|St|Street|Rd|Road|Dr|Drive|Blvd|Boulevard|Ln|Lane|Way|Pl|Place|Ct|Court|Cres|Crescent|Terr|Terrace|Hwy|Highway)"
    return bool(re.search(rf"(?i)\b{street_typ}\b", a))

def _has_intersection_addr(addr: str) -> bool:
    a = (addr or "").replace("\xa0", " ").replace("’", "'").strip()
    if not a:
        return False
    a0 = re.sub(r"(?i)\s+\band\b\s+", " & ", a)
    if not any(x in a0 for x in ["&", "＆", "/", "／"]):
        return False
    a0 = a0.replace("＆", "&").replace("／", "/")
    return _has_street_level_addr(a0)


def _has_street_level_addr(addr: str) -> bool:
    a = (addr or "").replace("\xa0", " ").replace("’", "'").strip()
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


def _city_from_address_tail(addr: str) -> str:
    a = (addr or "").replace("\xa0", " ").strip()
    if not a:
        return ""
    try:
        m = re.search(
            r"(?i)(?:^|,)\s*(vancouver|surrey|richmond|burnaby|coquitlam|delta|langley|new westminster|north vancouver|west vancouver|port coquitlam|port moody|tsawwassen|squamish|white rock)\s*(?:,|$)",
            a,
        )
    except Exception:
        m = None
    if not m:
        return ""
    return str(m.group(1) or "").strip().title()


def audit_listings(items: List[Dict[str, Any]], pcf) -> Dict[str, Any]:
    city_bbox = getattr(pcf, "CITY_BBOX", {}) or {}
    city_centers = getattr(pcf, "CITY_CENTERS", {}) or {}
    community_bbox = getattr(pcf, "COMMUNITY_BBOX", {}) or {}
    city_hint_fn = getattr(pcf, "_city_hint_from_craigslist_url", None)
    c = None
    try:
        c = getattr(pcf, "HavenNestCrawler", None)()
    except Exception:
        c = None

    issues: List[Dict[str, Any]] = []
    reason_counts = Counter()

    for it in items:
        if not isinstance(it, dict):
            continue

        src = (it.get("source") or "").strip()
        city = (it.get("city") or "").strip()
        comm = (it.get("community") or "").strip()
        addr = (it.get("address") or "").strip()
        title = (it.get("title") or "").strip()
        desc = (it.get("desc") or it.get("description") or "").strip()
        url = (it.get("url") or "").strip()
        coord_source = (it.get("coord_source") or "").strip()
        lat = _safe_float(it.get("lat"))
        lng = _safe_float(it.get("lng"))

        if lat is None or lng is None:
            continue

        reasons: List[str] = []

        if c is not None:
            try:
                info = c.infer_city_info(" ".join([title, addr, desc]))
                text_city = (info.get("city") or "").strip()
                strength = int(info.get("strength") or 0)
            except Exception:
                text_city = ""
                strength = 0
            if (not _has_detail_addr(addr)) and (not _has_intersection_addr(addr)) and text_city and city and text_city.lower() != city.lower() and strength >= 2:
                reasons.append("text_city_mismatch")

        if city and city in city_bbox and (not _in_bbox(city_bbox[city], lat, lng)):
            reasons.append("out_of_city_bbox")

        if src.lower() == "craigslist" and city_hint_fn and url:
            try:
                hint = city_hint_fn(url) or ""
            except Exception:
                hint = ""
            if hint and city and hint.lower() != city.lower():
                addr_city = _city_from_address_tail(addr)
                if addr_city and addr_city.lower() == city.lower() and city in city_bbox and _in_bbox(city_bbox[city], lat, lng):
                    pass
                else:
                    reasons.append("craigslist_city_mismatch_url_hint")

        if src.lower() == "vanpeople":
            if _is_city_only(addr) and (not re.search(r"\d", addr)) and (" & " not in addr):
                reasons.append("vanpeople_city_only_address")
            low_addr = addr.lower()
            if any(k in low_addr for k in ["metrotower", "shellbridge way", "west covina", "head office", "branch"]):
                reasons.append("vanpeople_company_address_pollution")

        if comm and city and (city, comm) in community_bbox and coord_source not in ("community_bbox", "city_bbox"):
            box = community_bbox[(city, comm)]
            box2 = _pad_bbox(box, 0.008, 0.010)
            if not _in_bbox(box2, lat, lng):
                if (not _has_detail_addr(addr)) and (not _has_intersection_addr(addr)):
                    reasons.append("out_of_community_bbox")

        if coord_source in ("city_bbox", "community_bbox") and _has_detail_addr(addr):
            reasons.append("bbox_but_has_house_number")

        if coord_source == "city_center_fallback" and _has_street_level_addr(addr):
            reasons.append("center_fallback_with_street")
        if coord_source in ("source_map", "source_map_pb", "source_map_open") and _has_detail_addr(addr):
            reasons.append("detail_addr_but_source_map")

        if city and city in city_centers and _has_detail_addr(addr):
            c0 = city_centers[city]
            try:
                d_km = _haversine_km(lat, lng, float(c0[0]), float(c0[1]))
            except Exception:
                d_km = None
            if d_km is not None and d_km <= 0.8 and coord_source in ("city_center_fallback", "city_bbox", "community_bbox"):
                reasons.append("near_city_center_with_detail_addr")

        if reasons:
            severity = "low"
            if any(r in reasons for r in ("out_of_city_bbox", "center_fallback_with_street", "bbox_but_has_house_number", "vanpeople_city_only_address")):
                severity = "high"
            elif "craigslist_city_mismatch_url_hint" in reasons:
                severity = "medium"
            next_step = ""
            if "vanpeople_city_only_address" in reasons:
                next_step = "drop_low_quality"
            elif "vanpeople_company_address_pollution" in reasons:
                next_step = "fix_vanpeople_addr_extract_or_override"
            elif "detail_addr_but_source_map" in reasons:
                next_step = "force_geocode_house_addr"
            elif "text_city_mismatch" in reasons:
                next_step = "check_city_label_or_lock_coords"
            elif "bbox_but_has_house_number" in reasons:
                next_step = "force_geocode_house_addr"
            elif "center_fallback_with_street" in reasons:
                next_step = "fix_addr_normalize_or_geocode"
            elif "out_of_city_bbox" in reasons:
                next_step = "check_city_or_override_source_map"
            elif "craigslist_city_mismatch_url_hint" in reasons:
                next_step = "check_url_hint_and_address_line"
            elif "out_of_community_bbox" in reasons:
                next_step = "verify_community_bbox_or_ignore"
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
                    "severity": severity,
                    "next_step": next_step,
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
        w.writerow(["severity", "next_step", "source", "city", "community", "coord_source", "lat", "lng", "address", "url", "reasons", "review_status", "review_note", "review_fixed_city", "review_fixed_community", "review_fixed_address", "review_fixed_lat", "review_fixed_lng", "review_lock_coords"])
        for it in rep["issues"]:
            w.writerow(
                [
                    it.get("severity", ""),
                    it.get("next_step", ""),
                    it.get("source", ""),
                    it.get("city", ""),
                    it.get("community", ""),
                    it.get("coord_source", ""),
                    it.get("lat", ""),
                    it.get("lng", ""),
                    it.get("address", ""),
                    it.get("url", ""),
                    "|".join(it.get("reasons") or []),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
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
