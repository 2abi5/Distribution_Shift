"""Reading view for one full text during the third retrieval pass: the current decision and extracted rows, then the
abstract, every table (caption + ' | ' rows as rendered from HTML, or layout lines from PDF text), and sentences that
mention a cross-domain test. Usage (from paper/review):  python3 scripts/ftread.py RID [--max-chars 30000] [--grep REGEX]"""
import csv
import json
import re
import sys

rid = sys.argv[1]
maxc = int(sys.argv[sys.argv.index("--max-chars") + 1]) if "--max-chars" in sys.argv else 30000
extra = re.compile(sys.argv[sys.argv.index("--grep") + 1], re.I) if "--grep" in sys.argv else None
dec = {r["rid"]: r for r in csv.DictReader(open("extraction/ft_decisions.csv"))}
comp = [r for r in csv.DictReader(open("extraction/comparisons.csv")) if r["rid"] == rid]
pool = {}
for line in [*open("search/pool_v3.jsonl"), *(open("search/pool_extra.jsonl") if __import__("os").path.exists("search/pool_extra.jsonl") else [])]:
    r = json.loads(line)
    pool[r["rid"]] = r
t = open(f"fulltext/txt/{rid}.txt", errors="ignore").read()
t = re.sub(r"[ \t]+", " ", t)

p = pool.get(rid, {})
print(f"== {rid} | {p.get('title', '')[:150]} | {p.get('year', '')} | {p.get('venue', '')}")
d = dec.get(rid)
if d:
    print(f"-- decision: {d['decision']} {d['reason']} | {d['notes'][:400]}")
for c in comp:
    print("-- row:", " | ".join(f"{k}={c[k]}" for k in ("comp", "task", "shift", "shift_desc", "model", "metric", "id", "ood", "oracle",
                                                     "mit", "adapted", "labels", "id_n", "ood_n", "runs", "loc", "note") if c[k]))
i = t.lower().find("abstract")
print("-- ABSTRACT:", " ".join(t[i:i + 1600].split()) if i >= 0 else "(none)")

# tables: a caption line, then consecutive lines containing ' | ' (HTML) or several numbers (PDF layout)
lines = t.split("\n")
out, n = [], 0
for j, ln in enumerate(lines):
    if re.match(r"^\s*(\| )?(Table|TABLE)\s*[0-9IVXA-C]+[.:| ]", ln):
        block = [ln.strip()[:300]]
        k = j + 1
        while k < len(lines) and k < j + 60:
            l2 = lines[k].strip()
            if "|" in l2 or len(re.findall(r"\d+\.\d+|\d+%", l2)) >= 2:
                block.append(l2[:260])
            elif block and len(block) > 3 and not l2:
                break
            k += 1
        out.append("\n   ".join(block))
        n += 1
print(f"-- TABLES ({n}):")
body = "\n".join(out)
print("   " + body[:maxc])

KEY = re.compile(r"cross[- ]?(domain|dataset|site|region|season|year|field|location|sensor|crop|species|farm)|unseen|"
                 r"out[- ]of[- ](domain|distribution)|in[- ]domain|source[- ]only|target domain|source domain|oracle|"
                 r"generali[sz]ation (test|performance|abilit)|transfer(red|ability)|independent (test|year|site|region|dataset)|"
                 r"(another|different|new) (year|site|field|region|dataset|location|season)|laboratory|lab[- ]to[- ]field|"
                 r"field (images|conditions|data)|leave[- ]one", re.I)
sents = re.split(r"(?<=[.!?])\s+", " ".join(t.split()))
hits = [s for s in sents if (KEY.search(s) or (extra and extra.search(s))) and re.search(r"\d", s)]
print(f"-- SENTENCES ({len(hits)}):")
for s in hits[:40]:
    print("  *", s[:400])
