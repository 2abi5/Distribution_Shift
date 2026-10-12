"""Merge database exports, remove duplicates (DOI, then normalised title + year), write the screening pool."""
import json, re, sys, unicodedata

def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()

oa = [json.loads(l) for l in open(sys.argv[1])]
s2 = [json.loads(l) for l in open(sys.argv[2])]
pool, by_doi, by_title = [], {}, {}
def add(rec, src):
    doi = (rec.get("doi") or "").lower() or None
    key_t = (norm(rec.get("title"))[:120], rec.get("year"))
    hit = None
    if doi and doi in by_doi: hit = by_doi[doi]
    elif key_t in by_title: hit = by_title[key_t]
    else:
        # tolerate +-1 year (preprint vs journal year)
        for dy in (-1, 1):
            k = (key_t[0], (rec.get("year") or 0) + dy)
            if k in by_title: hit = by_title[k]; break
    if hit is not None:
        p = pool[hit]
        p["sources"] = sorted(set(p["sources"] + [src]))
        if len(rec.get("abstract") or "") > len(p.get("abstract") or ""):
            p["abstract"] = rec["abstract"]
        p["pdf_url"] = p.get("pdf_url") or rec.get("pdf_url")
        p["doi"] = p.get("doi") or doi
        if src == "S2": p["s2id"] = rec.get("s2id"); p["arxiv"] = rec.get("arxiv")
        p["dupes"] = p.get("dupes", 0) + 1
        return False
    r = {"rid": f"R{len(pool)+1:05d}", "sources": [src], "doi": doi, "title": rec.get("title"),
         "year": rec.get("year"), "venue": rec.get("venue"), "abstract": rec.get("abstract") or "",
         "pdf_url": rec.get("pdf_url"), "oa_url": rec.get("oa_url"), "landing": rec.get("landing"),
         "type": rec.get("type") or ",".join(rec.get("types") or []), "authors": rec.get("authors"),
         "openalex": rec.get("id"), "s2id": rec.get("s2id"), "arxiv": rec.get("arxiv"),
         "cited_by": rec.get("cited_by"), "language": rec.get("language")}
    pool.append(r)
    if doi: by_doi[doi] = len(pool) - 1
    by_title[key_t] = len(pool) - 1
    return True
n_oa = sum(add(r, "OpenAlex") for r in oa)
n_s2 = sum(add(r, "S2") for r in s2)
with open(sys.argv[3], "w") as fh:
    for p in pool: fh.write(json.dumps(p) + "\n")
both = sum(1 for p in pool if len(p["sources"]) == 2)
noabs = sum(1 for p in pool if len(p["abstract"]) < 100)
print(f"OpenAlex records {len(oa)}, S2 records {len(s2)}, combined {len(oa)+len(s2)}")
print(f"unique after dedupe {len(pool)} (duplicates removed {len(oa)+len(s2)-len(pool)}); in both DBs {both}; no/short abstract {noabs}")
