"""Add Semantic Scholar open-access PDF links and arXiv ids for full-text candidates.
Usage: python3 scripts/enrich_s2.py  ->  fulltext/s2_enrich.json"""
import csv, json, os, time, urllib.request, urllib.error
os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")

rows = [r for r in csv.DictReader(open("screening/candidates.csv")) if not r["dup_of"]]
ids, back = [], {}
for r in rows:
    key = r["s2id"] or (f"DOI:{r['doi']}" if r["doi"] else None)
    if key:
        ids.append(key); back[key] = r["rid"]
out = {}
for i in range(0, len(ids), 400):
    chunk = ids[i:i + 400]
    body = json.dumps({"ids": chunk}).encode()
    url = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=paperId,externalIds,openAccessPdf,isOpenAccess"
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "review-pipeline"})
            res = json.load(urllib.request.urlopen(req, timeout=120))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(5 * (attempt + 1)); continue
            raise
    for key, p in zip(chunk, res):
        if p:
            ext = p.get("externalIds") or {}
            out[back[key]] = {"s2id": p.get("paperId"), "arxiv": ext.get("ArXiv"),
                              "s2_pdf": (p.get("openAccessPdf") or {}).get("url"), "s2_oa": p.get("isOpenAccess")}
    time.sleep(2)
json.dump(out, open("fulltext/s2_enrich.json", "w"), indent=1)
print("queried", len(ids), "returned", len(out), "| s2 pdf", sum(bool(v["s2_pdf"]) for v in out.values()),
      "| arXiv", sum(bool(v["arxiv"]) for v in out.values()))
