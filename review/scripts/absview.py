"""Print title and full abstract for records judged at abstract level (full text not retrieved).
Usage: python3 scripts/absview.py R00001 ...   (run from paper/review)"""
import json, re, sys
pool = {}
for line in open("search/pool_v3.jsonl"):
    r = json.loads(line); pool[r["rid"]] = r
for rid in sys.argv[1:]:
    p = pool[rid]
    a = re.sub(r"\s+", " ", p.get("abstract") or "")
    print(f"## {rid} | {p.get('year')} | {(p.get('venue') or '')[:40]} | {p.get('title')}")
    print(a[:3000])
