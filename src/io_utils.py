import csv
import json
from pathlib import Path


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def write_jsonl(path, rows):
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    ensure_dir(path.parent)

    rows = list(rows)
    if not rows:
        if fieldnames is None:
            fieldnames = ["message"]
            rows = [{"message": "no data"}]

    if fieldnames is None:
        seen = []
        seen_set = set()
        for row in rows:
            for key in row.keys():
                if key in seen_set:
                    continue
                seen_set.add(key)
                seen.append(key)
        fieldnames = seen

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
