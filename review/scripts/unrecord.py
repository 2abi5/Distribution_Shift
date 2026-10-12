"""Remove all records of the given rids from the three extraction CSVs (to re-record a corrected decision).
Usage: python3 scripts/unrecord.py R00001 [R00002 ...]   (run from paper/review)"""
import csv, sys
rids = set(sys.argv[1:])
for path in ("extraction/ft_decisions.csv", "extraction/comparisons.csv", "extraction/appraisal.csv"):
    rows = list(csv.DictReader(open(path)))
    cols = list(rows[0].keys())
    keep = [r for r in rows if r["rid"] not in rids]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(keep)
    print(path, "removed", len(rows) - len(keep))
