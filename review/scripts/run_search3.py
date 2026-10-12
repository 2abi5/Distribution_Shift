"""Final search (PROTOCOL.md deviation log, entry 4): OpenAlex + Semantic Scholar, resumable."""
import json, os, sys, time, datetime, urllib.parse, urllib.request, urllib.error
from oalib import *

outdir, today = sys.argv[1], "2026-10-01"
oa_path = f"{outdir}/openalex_final_{today}.jsonl"
state_path = oa_path + ".cursor"
flt = f"title_and_abstract.search:{QUERY3},{FILTER}"
total = works(flt, per=1)["meta"]["count"]
cursor = open(state_path).read().strip() if os.path.exists(state_path) else "*"
seen = sum(1 for _ in open(oa_path)) if os.path.exists(oa_path) and cursor != "*" else 0
mode = "a" if cursor != "*" else "w"
with open(oa_path, mode) as fh:
    while cursor and cursor != "DONE":
        d = works(flt, per=200, cursor=cursor)
        if not d["results"]:
            cursor = "DONE"; break
        for w in d["results"]:
            fh.write(json.dumps(slim(w)) + "\n")
        fh.flush()
        seen += len(d["results"])
        cursor = d["meta"].get("next_cursor") or "DONE"
        open(state_path, "w").write(cursor)
        time.sleep(0.5)
print("OpenAlex hits", total, "saved", seen)
json.dump({"database": "OpenAlex", "date_run": today, "field": "title_and_abstract.search",
           "query": QUERY3, "filter": FILTER, "hits_reported": total, "records_saved": seen},
          open(f"{outdir}/openalex_final_{today}.meta.json", "w"), indent=2)

def s2(url, tries=10):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "review-pipeline"})
            return json.load(urllib.request.urlopen(req, timeout=120))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(60, 4 * (i + 1))); continue
            raise
        except Exception:
            time.sleep(min(60, 4 * (i + 1)))
    raise RuntimeError(url[:200])

s2_path = f"{outdir}/semanticscholar_final_{today}.jsonl"
q = to_s2(QUERY3)
fields = "paperId,externalIds,title,abstract,year,venue,publicationTypes,openAccessPdf,citationCount,authors"
srecs, token, stotal = [], None, None
while True:
    p = {"query": q, "fields": fields, "year": "2015-2026"}
    if token: p["token"] = token
    d = s2("https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(p))
    stotal = d.get("total", stotal)
    for w in d.get("data", []):
        ext = w.get("externalIds") or {}
        srecs.append({"s2id": w["paperId"], "doi": (ext.get("DOI") or "").lower() or None, "arxiv": ext.get("ArXiv"),
                      "title": w.get("title"), "year": w.get("year"), "venue": w.get("venue"),
                      "types": w.get("publicationTypes"), "abstract": w.get("abstract") or "",
                      "pdf_url": (w.get("openAccessPdf") or {}).get("url") or None, "cited_by": w.get("citationCount"),
                      "authors": [a.get("name") for a in (w.get("authors") or [])][:12]})
    token = d.get("token")
    if not token: break
    time.sleep(1.5)
with open(s2_path, "w") as fh:
    for r in srecs: fh.write(json.dumps(r) + "\n")
json.dump({"database": "Semantic Scholar Graph API (paper/search/bulk)", "date_run": today, "field": "title + abstract",
           "query": q, "year": "2015-2026", "hits_reported": stotal, "records_saved": len(srecs)},
          open(f"{outdir}/semanticscholar_final_{today}.meta.json", "w"), indent=2)
print("S2 hits", stotal, "saved", len(srecs))
