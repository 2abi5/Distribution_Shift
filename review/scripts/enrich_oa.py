"""Fetch OpenAlex locations (all OA copies) and reference lists for full-text candidates, by DOI.
Usage: python3 scripts/enrich_oa.py  ->  fulltext/oa_enrich.json"""
import csv, json, sys, time, urllib.parse
sys.path.insert(0, "scripts")
from oalib import get, BASE

rows = [r for r in csv.DictReader(open("screening/candidates.csv")) if not r["dup_of"]]
dois = {r["doi"].lower(): r["rid"] for r in rows if r["doi"]}
out, keys = {}, sorted(dois)
for i in range(0, len(keys), 50):
    chunk = keys[i:i + 50]
    q = {"filter": "doi:" + "|".join(chunk), "per_page": 50,
         "select": "id,doi,locations,best_oa_location,open_access,referenced_works,cited_by_count,publication_year"}
    d = get(BASE + "?" + urllib.parse.urlencode(q))
    for w in d["results"]:
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        if doi in dois:
            out[dois[doi]] = {"openalex": w["id"].rsplit("/", 1)[-1],
                              "pdfs": [l.get("pdf_url") for l in (w.get("locations") or []) if l.get("pdf_url")],
                              "landings": [l.get("landing_page_url") for l in (w.get("locations") or []) if l.get("landing_page_url")],
                              "oa_url": (w.get("open_access") or {}).get("oa_url"),
                              "refs": [x.rsplit("/", 1)[-1] for x in (w.get("referenced_works") or [])],
                              "cited_by": w.get("cited_by_count")}
    time.sleep(0.3)
json.dump(out, open("fulltext/oa_enrich.json", "w"))
print("DOIs", len(keys), "matched", len(out), "| with pdf location", sum(bool(v["pdfs"]) for v in out.values()),
      "| with refs", sum(bool(v["refs"]) for v in out.values()))
