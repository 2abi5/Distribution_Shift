"""Third retrieval pass (2 October 2026): free-to-read copies that the first two passes missed.

The first pass (fetch_fulltext.py) was blocked by bot protection at several open-access publishers and failed
TLS checks on some repositories; the headless-browser pass (fetch_chrome.py) stopped after 146 of the records.
This pass tries, in order:
  1. Europe PMC full-text XML (open-access subset), converted to text with tables as ' | ' rows;
  2. PDFs listed in the record's current OpenAlex locations (open-access copies only), converted with pdftotext;
     a PDF is accepted only if its first pages contain the record's title;
  3. the article page rendered in headless Chrome, accepted only if it holds a complete article.
Only open-access or free-to-read copies are used; nothing behind a login is attempted.
Targets: RETRIEVAL_LIST.csv (abstract-only inclusions, E4 exclusions, figure-only studies, missed sentinels) and
the three closest reviews. PDFs go to fulltext/pdf/ (not committed); text to fulltext/txt/ as before.
Resumable; one JSON line per record in fulltext/retry/fetch_retry_log.jsonl.
Usage (from paper/review):  python3 scripts/fetch_retry.py [--workers 3] [--only RID,RID]"""
import csv
import html
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/129.0.0.0 Safari/537.36")
API_UA = "location_doner-systematic-review/1.0 (https://github.com/2abi5/location_doner)"
CHASE = "--chase" in sys.argv
LOG = "fulltext/retry/fetch_chase_log.jsonl" if CHASE else "fulltext/retry/fetch_retry_log.jsonl"
for d in ("fulltext/pdf", "fulltext/txt", "fulltext/html", "fulltext/retry"):
    os.makedirs(d, exist_ok=True)

SENTINELS = {"S00001": ("10.1016/j.compag.2018.01.009", "Deep learning models for plant disease detection and diagnosis"),
             "S00002": ("10.34133/2020/3521852", "Global Wheat Head Detection (GWHD) Dataset"),
             "S00003": ("10.34133/2021/9846158", "Global Wheat Head Detection 2021"),
             "S00004": ("10.1002/rob.21869", "Transfer learning between crop types for semantic segmentation of crops versus weeds")}
CONTEXT = ["R02966", "R06651", "R07003"]

pool = {}
for line in open("search/pool_v3.jsonl"):
    r = json.loads(line)
    pool[r["rid"]] = r
rl = list(csv.DictReader(open("RETRIEVAL_LIST.csv")))
prio = {r["rid"]: (int(r["priority"]), r["current_decision"]) for r in rl if r["rid"] in pool}
targets = sorted(prio, key=lambda k: (prio[k][0], {"INCLUDE-A": 0, "FIG": 1}.get(prio[k][1], 2), k))
targets = CONTEXT + list(SENTINELS) + targets
CHASED = {}
if CHASE:   # citation-chasing records forwarded at title/abstract (screening/chase_ta_include.txt)
    fwd = [l.split()[0] for l in open("screening/chase_ta_include.txt") if l.strip()]
    for l in open("search/chase_2026-10-02.jsonl"):
        r = json.loads(l)
        if r["wid"] in fwd:
            CHASED[r["wid"]] = r
    targets = [w for w in dict.fromkeys(fwd) if w in CHASED]
if "--only" in sys.argv:
    targets = sys.argv[sys.argv.index("--only") + 1].split(",")
oa = json.load(open("fulltext/retry/openalex_oa_2026-10-02.json")) if os.path.exists(
    "fulltext/retry/openalex_oa_2026-10-02.json") else {}


def meta(rid):
    if rid in CHASED:
        return CHASED[rid].get("doi") or "", CHASED[rid].get("title") or ""
    if rid in SENTINELS:
        return SENTINELS[rid][0], SENTINELS[rid][1]
    p = pool[rid]
    return (p.get("doi") or "").strip(), p.get("title") or ""


def norm(s):
    s = unicodedata.normalize("NFKD", html.unescape(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def title_in(title, text):
    """True if most of the title's content words occur in the first part of the text."""
    words = [w for w in norm(title).split() if len(w) > 3]
    head = norm(text[:6000])
    return bool(words) and sum(w in head for w in words) / len(words) >= 0.8


def get(url, accept="*/*", ua=UA, timeout=60, limit=60_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.headers.get("Content-Type", ""), r.read(limit)


# ------------------------------------------------------------------ text from HTML / XML
class Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "header", "footer", "button", "form"}
    BLOCK = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "tr", "caption",
             "figcaption", "table", "ul", "ol", "dd", "dt", "blockquote", "title", "label", "sec", "fig",
             "table-wrap", "abstract", "ref", "list-item"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in ("td", "th"):
            self.out.append(" | ")
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)

    def text(self):
        t = "".join(self.out)
        t = re.sub(r"[ \t\r\f\v]+", " ", t)
        t = re.sub(r" *\n *", "\n", t)
        return re.sub(r"\n{3,}", "\n\n", t).strip()


def to_text(markup):
    p = Text()
    p.feed(markup)
    return p.text()


def full_article(t):
    low = t.lower()
    sections = sum(k in low for k in ("introduction", "method", "result", "discussion", "conclusion"))
    paywall = any(k in low for k in ("purchase pdf", "access through your institution", "buy article", "get access",
                                     "subscribe to", "rent this article", "purchase this article", "log in to view"))
    return len(t) > 20000 and sections >= 4 and not (paywall and len(t) < 60000)


# ------------------------------------------------------------------ sources
def europepmc(doi, title):
    q = urllib.parse.quote(f'DOI:"{doi}"')
    _, _, raw = get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&resultType=lite",
                    ua=API_UA, timeout=30)
    res = json.loads(raw)["resultList"]["result"]
    hit = next((r for r in res if r.get("pmcid") and r.get("isOpenAccess") == "Y"), None)
    if not hit:
        return None
    _, _, xml = get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{hit['pmcid']}/fullTextXML", ua=API_UA, timeout=60)
    txt = to_text(xml.decode("utf-8", "ignore"))
    if len(txt) > 15000 and title_in(title, txt):
        return {"source": f"europepmc:{hit['pmcid']}", "text": txt}
    return None


def pdf_urls(rid, doi):
    w = oa.get(rid)
    if w is None and rid in CHASED:
        try:
            _, _, raw = get(f"https://api.openalex.org/works/{rid}", ua=API_UA, timeout=30)
            w = json.loads(raw)
        except Exception:
            w = None
    if w is None and doi:
        try:
            _, _, raw = get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}", ua=API_UA, timeout=30)
            w = json.loads(raw)
        except Exception:
            w = None
    urls = []
    if w:
        for loc in [w.get("best_oa_location") or {}] + (w.get("locations") or []):
            if loc and loc.get("pdf_url") and (loc.get("is_oa") or loc.get("license")):
                urls.append(loc["pdf_url"])
    d = doi.lower()
    if d.startswith("10.3389/"):
        urls.append(f"https://www.frontiersin.org/articles/{doi}/pdf")
    if d.startswith(("10.1186/", "10.1007/s13007")):
        urls.append(f"https://link.springer.com/content/pdf/{doi}.pdf")
    if d.startswith("10.1371/"):
        urls.append(f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable")
    if d.startswith("10.34133/"):
        urls.append(f"https://spj.science.org/doi/pdf/{doi}")
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:5]


def pdf(rid, doi, title):
    for u in pdf_urls(rid, doi):
        try:
            final, ctype, body = get(u, accept="application/pdf,*/*;q=0.8", timeout=45)
        except Exception as ex:
            continue
        if not body.startswith(b"%PDF"):
            continue
        path = f"fulltext/pdf/{rid}.pdf"
        open(path, "wb").write(body)
        out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, timeout=120).stdout.decode("utf-8", "ignore")
        if len(out) > 15000 and title_in(title, out):
            return {"source": final, "text": out, "pdf": path}
        os.remove(path)
    return None


_slot = threading.local()


def chrome(rid, doi, title):
    """Render the DOI landing page in headless Chrome and dump the DOM to a file (not a pipe: Chrome's helper
    processes inherit pipes and keep them open). The whole process group is stopped afterwards."""
    if not doi:
        return None
    if not hasattr(_slot, "profile"):
        _slot.profile = os.path.abspath(f"fulltext/chrome-profile-{os.getpid()}-{threading.get_ident()}")
    url = "https://doi.org/" + doi
    out_path = os.path.abspath(f"fulltext/retry/dom-{os.getpid()}-{threading.get_ident()}.html")
    with open(out_path, "wb") as out:
        p = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
                              "--disable-crash-reporter", "--disable-breakpad", "--no-default-browser-check",
                              f"--user-data-dir={_slot.profile}", f"--user-agent={UA}",
                              "--disable-blink-features=AutomationControlled", "--window-size=1366,900",
                              "--virtual-time-budget=15000", "--timeout=40000", "--dump-dom", url],
                             stdout=out, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            t0, last, stable = time.time(), -1, 0
            while time.time() - t0 < 90 and p.poll() is None:
                time.sleep(0.5)
                size = os.path.getsize(out_path)
                if size > 0:
                    with open(out_path, "rb") as fh:
                        fh.seek(max(0, size - 300))
                        tail = fh.read()
                    stable = stable + 1 if (size == last and b"</html>" in tail) else 0
                    if stable >= 3:
                        break
                last = size
        finally:
            try:
                os.killpg(p.pid, 9)
            except (ProcessLookupError, PermissionError):
                pass
            subprocess.run(["pkill", "-9", "-f", _slot.profile], capture_output=True)
    dom = open(out_path, "rb").read().decode("utf-8", "ignore")
    os.remove(out_path)
    txt = to_text(dom)
    if full_article(txt) and title_in(title, txt):
        open(f"fulltext/html/{rid}.html", "w").write(dom)
        return {"source": url, "text": txt, "html": f"fulltext/html/{rid}.html"}
    return None


lock = threading.Lock()
done = set()
if os.path.exists(LOG):
    done = {json.loads(l)["rid"] for l in open(LOG)}


def work(rid):
    doi, title = meta(rid)
    rec = {"rid": rid, "doi": doi, "status": "not_retrieved", "tried": []}
    t0 = time.time()
    order = (("europepmc", europepmc), ("pdf", pdf), ("chrome", chrome))
    if prio.get(rid, (0, ""))[1] == "FIG":           # figure-only studies: the PDF is needed for digitisation
        order = (("pdf", pdf), ("chrome", chrome), ("europepmc", europepmc))
    for name, fn in order:
        if name != "pdf" and not doi:
            continue
        try:
            res = fn(rid, doi, title) if name != "europepmc" else fn(doi, title)
        except Exception as ex:
            rec["tried"].append([name, type(ex).__name__ + ":" + str(ex)[:80]])
            continue
        if res:
            # keep an existing full text (first two passes) unless this one is longer
            path = f"fulltext/txt/{rid}.txt"
            old = os.path.getsize(path) if os.path.exists(path) else 0
            if len(res["text"].encode()) > old:
                open(path, "w").write(res["text"])
            rec.update(status="ok", via=name, source=res["source"], text_bytes=len(res["text"].encode()),
                       pdf=res.get("pdf", ""), html=res.get("html", ""))
            break
        rec["tried"].append([name, "no"])
    rec["seconds"] = round(time.time() - t0, 1)
    with lock:
        with open(LOG, "a") as log:
            log.write(json.dumps(rec) + "\n")
        print(rid, rec["status"], rec.get("via", ""), rec.get("text_bytes", ""), flush=True)
    time.sleep(2 + random.random() * 2)


todo = [r for r in targets if r not in done]
workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
print(f"to retrieve: {len(todo)} (workers {workers})", flush=True)
with ThreadPoolExecutor(max_workers=workers) as ex:
    list(ex.map(work, todo))
print("done", flush=True)
