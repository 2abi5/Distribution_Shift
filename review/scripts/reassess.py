"""Re-assess records after the third full-text retrieval pass (2 October 2026): replace a record's decision, rows and
appraisal, and log the change in extraction/reassessment_log.csv (previous decision, new decision, full-text source).
Input on stdin: JSON objects in the format of record.py, each with an extra "why" (what the full text changed).
Usage (from paper/review):  python3 scripts/reassess.py <<'X' {...} X"""
import csv
import json
import os
import subprocess
import sys

text = "\n".join(l for l in sys.stdin.read().split("\n") if not l.lstrip().startswith("#"))
dec, pos, objs = json.JSONDecoder(), 0, []
while True:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos >= len(text):
        break
    obj, pos = dec.raw_decode(text, pos)
    objs.append(obj)

prev = {r["rid"]: r["decision"] + (f"/{r['reason']}" if r["reason"] else "") for r in csv.DictReader(open("extraction/ft_decisions.csv"))}
src = {}
for log in ("fulltext/retry/fetch_retry_log.jsonl", "fulltext/retry/fetch_chase_log.jsonl"):
    if os.path.exists(log):
        for l in open(log):
            x = json.loads(l)
            if x.get("status") == "ok":
                src[x["rid"]] = x.get("source", "")
rids = [o["rid"] for o in objs]
existing = [r for r in rids if r in prev]
if existing:
    subprocess.run([sys.executable, "scripts/unrecord.py", *existing], check=True, capture_output=True)
p = subprocess.run([sys.executable, "scripts/record.py"], input="\n".join(json.dumps({k: v for k, v in o.items() if k != "why"}) for o in objs),
                   text=True, capture_output=True, check=True)
print(p.stdout.strip())
LOG = "extraction/reassessment_log.csv"
new = not os.path.exists(LOG)
with open(LOG, "a", newline="") as fh:
    w = csv.writer(fh)
    if new:
        w.writerow(["rid", "date", "previous_decision", "new_decision", "full_text_source", "what_changed"])
    for o in objs:
        w.writerow([o["rid"], "2026-10-02", prev.get(o["rid"], "(new record)"), o["decision"] + (f"/{o.get('reason')}" if o.get("reason") else ""),
                    src.get(o["rid"], ""), o.get("why", "")])
