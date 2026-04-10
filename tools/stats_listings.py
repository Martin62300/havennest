import json
import os
from collections import Counter


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "listings.json")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ctr = Counter((str(i.get("source") or "UNKNOWN")).strip() for i in data)

    print(f"Total: {len(data)}")
    for k, v in ctr.most_common():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()

