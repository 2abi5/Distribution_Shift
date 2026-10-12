"""Download open-access full texts of candidates and convert them to text (pdftotext -layout).
Resumable; one JSON line per record in fulltext/fetch_log.jsonl.
Usage: python3 scripts/fetch_fulltext.py"""
import csv, html, json, os, re, subprocess, time, urllib.error, urllib.parse, urllib.request
os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
rows = [r for r in csv.DictReader(open("screening/candidates.csv")) if not r["dup_of"]]
s2 = json.load(open("fulltext/s2_enrich.json"))
oa = json.load(open("fulltext/oa_enrich.json"))
os.makedirs("fulltext/pdf", exist_ok=True); os.makedirs("fulltext/txt", exist_ok=True)
log_path = "fulltext/fetch_log.jsonl"
done = set()
if os.path.exists(log_path):
    done = {json.loads(l)["rid"] for l in open(log_path)}


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.headers.get("Content-Type", ""), r.read(40_000_000)


def pdf_link(base, body):
    for pat in (rb'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)',
                rb'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url'):
        m = re.search(pat, body, re.I)
        if m:
            return urllib.parse.urljoin(base, html.unescape(m.group(1).decode("utf-8", "ignore")))
    return None


def urls_for(r):
    e2, eo = s2.get(r["rid"]) or {}, oa.get(r["rid"]) or {}
    doi, out = r["doi"], []
    ax = r["arxiv"] or e2.get("arxiv")
    if doi.lower().startswith("10.48550/arxiv."):
        ax = ax or doi.split("arxiv.", 1)[1]
    if ax:
        out.append(f"https://arxiv.org/pdf/{ax}")
    out += [r["pdf_url"], e2.get("s2_pdf")] + eo.get("pdfs", [])
    if doi:
        p = doi.lower()
        if p.startswith("10.3389/"):
            out.append(f"https://www.frontiersin.org/articles/{doi}/pdf")
        if p.startswith("10.1371/"):
            out.append(f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable")
        if p.startswith(("10.1186/", "10.1007/", "10.1038/")):
            out.append(f"https://link.springer.com/content/pdf/{doi}.pdf")
        out.append(f"https://doi.org/{doi}")
    out += [r["oa_url"], eo.get("oa_url")] + eo.get("landings", [])
    seen, uniq = set(), []
    for u in out:
        if u and u not in seen and u != "None":
            seen.add(u); uniq.append(u)
    return uniq


with open(log_path, "a") as log:
    for r in rows:
        if r["rid"] in done:
            continue
        rec = {"rid": r["rid"], "status": "not_retrieved", "tried": []}
        for u in urls_for(r)[:8]:
            try:
                final, ctype, body = fetch(u)
                if not body.startswith(b"%PDF"):
                    link = pdf_link(final, body) if b"<" in body[:2000] else None
                    rec["tried"].append([u, "html" if link else "no_pdf"])
                    if not link:
                        continue
                    time.sleep(1)
                    final, ctype, body = fetch(link)
                    if not body.startswith(b"%PDF"):
                        rec["tried"].append([link, "no_pdf"])
                        continue
                pdf = f"fulltext/pdf/{r['rid']}.pdf"
                open(pdf, "wb").write(body)
                txt = f"fulltext/txt/{r['rid']}.txt"
                subprocess.run(["pdftotext", "-layout", pdf, txt], timeout=120, capture_output=True)
                n = os.path.getsize(txt) if os.path.exists(txt) else 0
                rec.update(status="ok" if n > 2000 else "pdf_no_text", source=final, bytes=len(body), text_bytes=n)
                break
            except Exception as ex:
                rec["tried"].append([u, type(ex).__name__ + ":" + str(ex)[:80]])
            finally:
                time.sleep(3 if "arxiv.org" in u else 1)
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(r["rid"], rec["status"], flush=True)
