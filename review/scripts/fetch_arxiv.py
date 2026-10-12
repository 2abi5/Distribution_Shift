"""Third retrieval pass: find arXiv preprints of candidates still without full text (title match >= 0.92),
download the PDF and convert it with pdftotext. arXiv API etiquette: one request every 3 s.
Resumable; log in fulltext/fetch_arxiv_log.jsonl.   Usage: python3 scripts/fetch_arxiv.py"""
import csv, difflib, json, os, re, subprocess, time, unicodedata, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")
LOG = "fulltext/fetch_arxiv_log.jsonl"
NS = {"a": "http://www.w3.org/2005/Atom"}


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def have_text(rid):
    return os.path.exists(f"fulltext/txt/{rid}.txt") and os.path.getsize(f"fulltext/txt/{rid}.txt") > 2000


rows = [r for r in csv.DictReader(open("screening/candidates.csv")) if not r["dup_of"]]
done = {json.loads(l)["rid"] for l in open(LOG)} if os.path.exists(LOG) else set()
todo = [r for r in rows if not have_text(r["rid"]) and r["rid"] not in done and r["title"]]
print("to search:", len(todo), flush=True)
with open(LOG, "a") as log:
    for r in todo:
        words = [w for w in norm(r["title"]) if len(w) > 2][:12]
        q = " AND ".join(f"ti:{w}" for w in words[:8])
        url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": q, "max_results": 5})
        rec = {"rid": r["rid"], "status": "no_match"}
        try:
            feed = ET.fromstring(urllib.request.urlopen(url, timeout=60).read())
            best = (0, None, None)
            for e in feed.findall("a:entry", NS):
                title = " ".join(norm(e.findtext("a:title", "", NS)))
                sim = difflib.SequenceMatcher(None, title, " ".join(norm(r["title"]))).ratio()
                if sim > best[0]:
                    best = (sim, e.findtext("a:id", "", NS), title)
            rec.update(best_sim=round(best[0], 3), arxiv=best[1])
            if best[0] >= 0.92 and best[1]:
                aid = best[1].rsplit("/abs/", 1)[-1]
                time.sleep(3)
                pdf = urllib.request.urlopen(urllib.request.Request(f"https://arxiv.org/pdf/{aid}",
                                             headers={"User-Agent": "review-pipeline"}), timeout=120).read()
                if pdf.startswith(b"%PDF"):
                    open(f"fulltext/pdf/{r['rid']}.pdf", "wb").write(pdf)
                    subprocess.run(["pdftotext", "-layout", f"fulltext/pdf/{r['rid']}.pdf", f"fulltext/txt/{r['rid']}.txt"],
                                   timeout=120, capture_output=True)
                    rec["status"] = "ok_arxiv" if have_text(r["rid"]) else "pdf_no_text"
        except Exception as ex:
            rec["status"] = "error:" + type(ex).__name__
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(r["rid"], rec["status"], rec.get("best_sim"), flush=True)
        time.sleep(3)
