"""Build the full-text candidate table from title/abstract decisions.
Usage: python3 scripts/candidates.py  ->  screening/candidates.csv"""
import csv, json

task = {l.split()[0]: l.split()[1] for l in open("screening/ta_include.txt") if l.strip()}
dup_of = {}
for l in open("screening/dup_candidates.txt"):
    if l.startswith("#") or not l.strip():
        continue
    keep, drop = l.split()[:2]
    if keep in task and drop in task:
        dup_of[drop] = keep
pool = {}
for line in open("search/pool_v3.jsonl"):
    r = json.loads(line)
    if r["rid"] in task:
        pool[r["rid"]] = r
cols = ["rid", "task", "dup_of", "year", "venue", "doi", "title", "arxiv", "pdf_url", "oa_url",
        "landing", "openalex", "s2id", "cited_by", "sources"]
with open("screening/candidates.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for rid in sorted(task):
        r = pool[rid]
        row = {c: r.get(c) for c in cols if c in r}
        row.update(rid=rid, task=task[rid], dup_of=dup_of.get(rid, ""), sources="+".join(r.get("sources", [])))
        w.writerow({c: ("" if row.get(c) in (None, "None") else row.get(c)) for c in cols})
rows = list(csv.DictReader(open("screening/candidates.csv")))
uniq = [r for r in rows if not r["dup_of"]]
print("candidates", len(rows), "duplicates collapsed", len(rows) - len(uniq), "unique", len(uniq))
print("with DOI", sum(bool(r["doi"]) for r in uniq), "| arXiv id", sum(bool(r["arxiv"]) for r in uniq),
      "| any OA link", sum(bool(r["pdf_url"] or r["oa_url"] or r["arxiv"]) for r in uniq),
      "| no DOI and no link", sum(not (r["doi"] or r["pdf_url"] or r["oa_url"] or r["arxiv"]) for r in uniq))
