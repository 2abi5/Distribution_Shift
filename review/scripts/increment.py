"""Merge the final OpenAlex harvest (QUERY3) into the screening pool; new records get new ids.
Usage: python3 scripts/increment.py search/pool_v2.jsonl search/openalex_final_2026-10-02.jsonl search/pool_v3.jsonl"""
import json, re, sys, unicodedata

def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()

pool = [json.loads(l) for l in open(sys.argv[1])]
new = [json.loads(l) for l in open(sys.argv[2])]
by_oa = {p["openalex"]: i for i, p in enumerate(pool) if p.get("openalex") not in (None, "None")}
by_doi = {p["doi"].lower(): i for i, p in enumerate(pool) if p.get("doi") not in (None, "None")}
by_t = {(norm(p["title"])[:120], int(p["year"]) if str(p.get("year")).isdigit() else 0): i for i, p in enumerate(pool)}
matched, added, seen_ids = 0, 0, set()
q3_hit = set()
for r in new:
    if r["id"] in seen_ids:
        continue
    seen_ids.add(r["id"])
    doi = (r.get("doi") or "").lower() or None
    kt = (norm(r.get("title"))[:120], r.get("year") or 0)
    hit = by_oa.get(r["id"])
    if hit is None and doi: hit = by_doi.get(doi)
    if hit is None:
        for dy in (0, -1, 1):
            hit = by_t.get((kt[0], kt[1] + dy))
            if hit is not None: break
    if hit is not None:
        matched += 1; q3_hit.add(hit)
        p = pool[hit]
        if "OpenAlex" not in p["sources"]:
            p["sources"] = sorted(set(p["sources"] + ["OpenAlex"]))
        if len(r.get("abstract") or "") > len(p.get("abstract") or ""):
            p["abstract"] = r["abstract"]
        p["openalex"] = p.get("openalex") if p.get("openalex") not in (None, "None") else r["id"]
        continue
    rec = {"rid": f"R{len(pool)+1:05d}", "sources": ["OpenAlex"], "doi": doi, "title": r.get("title"),
           "year": r.get("year"), "venue": r.get("venue"), "abstract": r.get("abstract") or "",
           "pdf_url": r.get("pdf_url"), "oa_url": r.get("oa_url"), "landing": r.get("landing"),
           "type": r.get("type"), "authors": r.get("authors"), "openalex": r["id"], "s2id": None,
           "arxiv": None, "cited_by": r.get("cited_by"), "language": r.get("language"), "increment": True}
    pool.append(rec); added += 1
    if doi: by_doi[doi] = len(pool) - 1
    by_t[kt] = len(pool) - 1
    q3_hit.add(len(pool) - 1)
with open(sys.argv[3], "w") as fh:
    for p in pool: fh.write(json.dumps(p) + "\n")
oa_q2_only = sum(1 for i, p in enumerate(pool[:7036]) if "OpenAlex" in p["sources"] and i not in q3_hit and p.get("openalex") not in (None, "None"))
print(f"final OpenAlex records {len(seen_ids)} (unique ids); matched to existing pool {matched}; new {added}")
print(f"pool now {len(pool)}; new ids R07037..R{len(pool):05d}")
print(f"pool records retrieved by OpenAlex QUERY2 but not by OpenAlex QUERY3: {oa_q2_only}")
