import argparse
import csv
import json
import os
import re
from typing import Any, Dict, Optional, TextIO, Tuple


def _normalize_url(s: str) -> str:
    t = str(s or "")
    t = t.replace("\u200b", "").replace("\ufeff", "")
    t = t.strip().strip('"').strip("'")
    t = t.replace("`", "").strip()
    m = re.search(r"https?://[^\s)>\"]+", t)
    if m:
        t = m.group(0)
    t = t.strip().strip('"').strip("'")
    t = t.rstrip(").,;]")
    return t.strip()


def _open_csv_dictreader(path: str) -> Tuple[TextIO, csv.DictReader]:
    encodings = ["utf-8-sig", "utf-16", "gb18030", "cp936", "cp1252", "latin-1"]
    last_err: Optional[Exception] = None
    for enc in encodings:
        try:
            f: TextIO = open(path, "r", encoding=enc, newline="")
            r: csv.DictReader = csv.DictReader(f)
            _ = r.fieldnames
            if not r.fieldnames:
                f.close()
                raise RuntimeError("empty csv header")
            print(f"CSV encoding: {enc}")
            return (f, r)
        except Exception as e:
            last_err = e
            try:
                f.close()
            except Exception:
                pass
    raise RuntimeError(f"Failed to read CSV with common encodings: {path}: {last_err}")


def _is_truthy(x: Any) -> bool:
    s = str(x or "").strip().lower()
    return s in {"1", "true", "yes", "y", "lock", "locked"}


def _to_float(x: Any) -> Optional[float]:
    try:
        s = str(x or "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def _load_overrides(path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        by_url: Dict[str, Any] = {}
        if isinstance(obj, dict) and isinstance(obj.get("by_url"), dict):
            by_url = obj.get("by_url") or {}
        elif isinstance(obj, dict):
            by_url = obj
        out: Dict[str, Any] = {}
        if isinstance(by_url, dict):
            for k, v in by_url.items():
                nk = _normalize_url(k)
                if nk:
                    out[nk] = v
        return out
        return {}
    except Exception:
        return {}


def _save_overrides(path: str, by_url: Dict[str, Any]) -> None:
    out: Dict[str, Any] = {}
    if isinstance(by_url, dict):
        for k, v in by_url.items():
            nk = _normalize_url(k)
            if nk:
                out[nk] = v
    obj = {"version": 1, "by_url": out}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _normalize_address(addr: str, fixed_city: str = "") -> str:
    a = str(addr or "").strip()
    if not a:
        return ""
    a = a.replace("\u200b", "").replace("\ufeff", "")
    a = a.replace("?", ", ")
    a = re.sub(r"\s+", " ", a).strip()
    a = re.sub(r"(?i)\bseymore\b", "Seymour", a)
    a = re.sub(r"(?i)\bvancouve\b", "Vancouver", a)
    a = re.sub(r"(?i)\bdunblune\b", "Dunblane", a)
    if fixed_city:
        fc = fixed_city.strip()
        if fc and (fc.lower() not in a.lower()):
            a = f"{a}, {fc}"
    return a


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review_csv", required=True)
    ap.add_argument("--overrides_json", default="location_overrides.json")
    ap.add_argument(
        "--replace",
        action="store_true",
        help="Replace overrides_json using ONLY rows in review_csv (do not merge with existing file).",
    )
    args = ap.parse_args()

    existing_by_url = _load_overrides(args.overrides_json)
    by_url = {} if args.replace else dict(existing_by_url)
    changed = 0

    f, r = _open_csv_dictreader(args.review_csv)
    try:
        for row in r:
            url = _normalize_url(row.get("url") or "")
            if not url:
                continue
            status = (row.get("review_status") or "").strip().lower()
            if not status or status in {"ok", "keep", "pass"}:
                continue
            if status in {"drop", "delete", "remove"}:
                by_url[url] = {"drop": True}
                changed += 1
                continue
            if status not in {"fix", "update"}:
                continue
            fixed_city = (row.get("review_fixed_city") or "").strip()
            fixed_comm = (row.get("review_fixed_community") or "").strip()
            fixed_addr = _normalize_address(row.get("review_fixed_address") or "", fixed_city=fixed_city)
            fixed_lat = _to_float(row.get("review_fixed_lat"))
            fixed_lng = _to_float(row.get("review_fixed_lng"))
            lock_coords = _is_truthy(row.get("review_lock_coords") or "")
            ov: Dict[str, Any] = {}
            if fixed_city:
                ov["city"] = fixed_city
            if fixed_comm:
                ov["community"] = fixed_comm
            if fixed_addr:
                ov["address"] = fixed_addr
            if fixed_lat is not None and fixed_lng is not None:
                ov["lat"] = fixed_lat
                ov["lng"] = fixed_lng
            if not ov:
                continue
            if fixed_addr:
                ov["force_geocode"] = True
            if lock_coords:
                ov["lock_coords"] = True
            by_url[url] = ov
            changed += 1
    finally:
        try:
            f.close()
        except Exception:
            pass

    _save_overrides(args.overrides_json, by_url)
    try:
        mode = "replace" if args.replace else "merge"
        print(f"Mode: {mode}")
        print(f"Existing overrides: {len(existing_by_url)}")
        print(f"Updated from CSV: {changed}")
        print(f"Total overrides saved: {len(by_url)}")
    except Exception:
        pass
    print(f"Saved overrides: {args.overrides_json} (updated {changed})")


if __name__ == "__main__":
    main()
