"""Print a screening batch: rid|year|title|venue (titles only) or with abstracts."""
import json, sys
pool = [json.loads(l) for l in open(sys.argv[1])]
start, end = int(sys.argv[2]), int(sys.argv[3])
mode = sys.argv[4] if len(sys.argv) > 4 else "title"
ids = None
if len(sys.argv) > 5:
    ids = set(open(sys.argv[5]).read().split())
for p in pool[start:end]:
    if ids is not None and p["rid"] not in ids: continue
    v = (p.get("venue") or "")[:28]
    t = (p.get("title") or "").replace("\n", " ")[:160]
    if mode == "title":
        print(f"{p['rid'][1:]}|{t}|{v}")
    else:
        a = (p.get("abstract") or "").replace("\n", " ")
        print(f"### {p['rid']} | {p['year']} | {t} | {v}\n{a[:int(mode)]}\n")
