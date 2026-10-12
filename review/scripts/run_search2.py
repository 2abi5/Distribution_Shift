"""Run the amended search (PROTOCOL.md deviation log, 2026-10-01) on OpenAlex and Semantic Scholar."""
import json, os, sys, time, datetime, urllib.parse, urllib.request, urllib.error
from oalib import *

outdir = sys.argv[1]
today = datetime.date.today().isoformat()

# ---- OpenAlex
flt = f"title_and_abstract.search:{QUERY2},{FILTER}"
total = works(flt, per=1)["meta"]["count"]
recs, cursor = [], "*"
while cursor:
    d = works(flt, per=200, cursor=cursor)
    if not d["results"]: break
    recs += [slim(w) for w in d["results"]]
    cursor = d["meta"].get("next_cursor")
    time.sleep(0.4)
with open(f"{outdir}/openalex_{today}.jsonl", "w") as fh:
    for r in recs: fh.write(json.dumps(r) + "\n")
json.dump({"database": "OpenAlex", "date_run": today, "field": "title_and_abstract.search",
           "query": QUERY2, "filter": FILTER, "hits_reported": total, "records_saved": len(recs)},
          open(f"{outdir}/openalex_{today}.meta.json", "w"), indent=2)
print("OpenAlex hits", total, "saved", len(recs))

# ---- Semantic Scholar
def s2(url, tries=8):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "review-pipeline"})
            return json.load(urllib.request.urlopen(req, timeout=90))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            raise
    raise RuntimeError(url)

q2 = to_s2(QUERY2)
fields = "paperId,externalIds,title,abstract,year,venue,publicationTypes,openAccessPdf,citationCount,authors"
params = {"query": q2, "fields": fields, "year": "2015-2026"}
srecs, token, stotal = [], None, None
while True:
    p = dict(params)
    if token: p["token"] = token
    d = s2("https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(p))
    stotal = d.get("total", stotal)
    for w in d.get("data", []):
        ext = w.get("externalIds") or {}
        srecs.append({
            "s2id": w["paperId"], "doi": (ext.get("DOI") or "").lower() or None, "arxiv": ext.get("ArXiv"),
            "title": w.get("title"), "year": w.get("year"), "venue": w.get("venue"),
            "types": w.get("publicationTypes"), "abstract": w.get("abstract") or "",
            "pdf_url": (w.get("openAccessPdf") or {}).get("url") or None,
            "cited_by": w.get("citationCount"),
            "authors": [a.get("name") for a in (w.get("authors") or [])][:12]})
    token = d.get("token")
    print("  S2 page, cumulative", len(srecs), "of", stotal)
    if not token: break
    time.sleep(1.5)
with open(f"{outdir}/semanticscholar_{today}.jsonl", "w") as fh:
    for r in srecs: fh.write(json.dumps(r) + "\n")
json.dump({"database": "Semantic Scholar Graph API (paper/search/bulk)", "date_run": today,
           "field": "title + abstract", "query": q2, "year": "2015-2026",
           "hits_reported": stotal, "records_saved": len(srecs)},
          open(f"{outdir}/semanticscholar_{today}.meta.json", "w"), indent=2)
print("S2 hits", stotal, "saved", len(srecs))
