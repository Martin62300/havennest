import argparse
import csv
import json
import os
import re
from typing import Any, Dict


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
    obj = {"version": 1, "by_url": by_url}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review_csv", required=True)
    ap.add_argument("--overrides_json", default="location_overrides.json")
    args = ap.parse_args()

    by_url = _load_overrides(args.overrides_json)
    changed = 0

    with open(args.review_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
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
            fixed_addr = (row.get("review_fixed_address") or "").strip()
            ov: Dict[str, Any] = {}
            if fixed_city:
                ov["city"] = fixed_city
            if fixed_comm:
                ov["community"] = fixed_comm
            if fixed_addr:
                ov["address"] = fixed_addr
            ov["force_geocode"] = True
            if not ov:
                continue
            by_url[url] = ov
            changed += 1

    _save_overrides(args.overrides_json, by_url)
    print(f"Saved overrides: {args.overrides_json} (updated {changed})")


if __name__ == "__main__":
    main()
