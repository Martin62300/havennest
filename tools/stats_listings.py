import json
import os
import sys
import urllib.request
from collections import Counter


def _fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HavenNestStats/1.0"
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args = [a for a in sys.argv[1:] if a.strip()]
    with_owner = "--with-owner" in args
    args = [a for a in args if a != "--with-owner"]

    target = args[0].strip() if len(args) > 0 else "listings.json"
    if not (target.startswith("http://") or target.startswith("https://")):
        target = os.path.join(root, target)

    if target.startswith("http://") or target.startswith("https://"):
        data = _fetch_json(target)
    else:
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)

    owner_api = []
    if with_owner:
        try:
            base = target
            if not (base.startswith("http://") or base.startswith("https://")):
                base = "https://havennestapp.com/"
            if not base.endswith("/"):
                base += "/"
            owner_api = _fetch_json(base + "api/public/listings").get("listings") or []
        except Exception as e:
            print(f"WARNING: failed to fetch owner API: {e}")
            owner_api = []

    if owner_api:
        seen = set()
        merged = []
        for it in data:
            k = (it.get("id") or it.get("url") or "")
            if k:
                seen.add(k)
            merged.append(it)
        for it in owner_api:
            k = (it.get("id") or it.get("url") or "")
            if k and k in seen:
                continue
            merged.append(it)
        data = merged

    ctr = Counter((str(i.get("source") or "UNKNOWN")).strip() for i in data)
    max_date = max((str(i.get("date") or "") for i in data), default="")
    owner_count = sum(1 for i in data if str(i.get("source") or "").strip().lower() == "owner")

    print(f"Target: {target}")
    print(f"Total: {len(data)}")
    print(f"owner: {owner_count}")
    print(f"max_date: {max_date}")
    for k, v in ctr.most_common():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
