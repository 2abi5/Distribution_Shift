"""Second retrieval pass: render the article page in headless Chrome (one page at a time) for candidates the
first pass did not retrieve; convert the HTML to text with tables kept as ' | '-separated rows.
A record counts as retrieved only if the page holds a full article (length and section checks).
Resumable; log in fulltext/fetch_chrome_log.jsonl.   Usage: python3 scripts/fetch_chrome.py [--mdpi-first]"""
import csv, html, json, os, re, subprocess, sys, time
from html.parser import HTMLParser

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
PROFILE = os.path.abspath("fulltext/chrome-profile")
os.makedirs("fulltext/html", exist_ok=True)
LOG = "fulltext/fetch_chrome_log.jsonl"


class Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "header", "footer", "button", "form"}
    BLOCK = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "tr", "caption",
             "figcaption", "table", "ul", "ol", "dd", "dt", "blockquote"}

    def __init__(self):
        super().__init__(); self.out, self.skip, self.cell = [], 0, False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self.skip += 1
        elif tag in ("td", "th"): self.out.append(" | ")
        elif tag in self.BLOCK: self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip: self.skip -= 1
        elif tag in self.BLOCK: self.out.append("\n")

    def handle_data(self, data):
        if not self.skip: self.out.append(data)

    def text(self):
        t = "".join(self.out)
        t = re.sub(r"[ \t\r\f\v]+", " ", t)
        t = re.sub(r" *\n *", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()


def render(url):
    import threading
    p = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
                          f"--user-data-dir={PROFILE}", f"--user-agent={UA}", "--disable-blink-features=AutomationControlled",
                          "--window-size=1366,900", "--virtual-time-budget=12000", "--timeout=30000", "--dump-dom", url],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    buf = bytearray()

    def pump():
        for chunk in iter(lambda: p.stdout.read1(65536), b""):
            buf.extend(chunk)
    th = threading.Thread(target=pump, daemon=True); th.start()
    t0, last, stable = time.time(), -1, 0
    while time.time() - t0 < 90:
        time.sleep(0.5)
        if p.poll() is not None:
            break
        if b"</html>" in buf[-200:]:
            stable = stable + 1 if len(buf) == last else 0
            if stable >= 2:
                break
        last = len(buf)
    p.kill()
    th.join(timeout=2)
    subprocess.run(["pkill", "-f", PROFILE], capture_output=True)
    return bytes(buf).decode("utf-8", "ignore")


def full_article(t):
    low = t.lower()
    sections = sum(k in low for k in ("introduction", "method", "results", "discussion", "conclusion"))
    paywall = any(k in low for k in ("purchase pdf", "access through your institution", "buy article", "get access",
                                     "subscribe to", "rent this article", "purchase this article"))
    return len(t) > 25000 and sections >= 4 and not (paywall and len(t) < 60000)


rows = {r["rid"]: r for r in csv.DictReader(open("screening/candidates.csv")) if not r["dup_of"]}
first = {json.loads(l)["rid"]: json.loads(l)["status"] for l in open("fulltext/fetch_log.jsonl")}
done = {json.loads(l)["rid"] for l in open(LOG)} if os.path.exists(LOG) else set()
todo = [rid for rid, st in first.items() if st != "ok" and rid not in done and rows.get(rid, {}).get("doi")]
if "--mdpi-first" in sys.argv:
    todo.sort(key=lambda rid: (not rows[rid]["doi"].startswith("10.3390/"), rid))
print("to render:", len(todo), flush=True)
with open(LOG, "a") as log:
    for rid in todo:
        url = "https://doi.org/" + rows[rid]["doi"]
        t0 = time.time()
        dom = render(url)
        tp = Text(); tp.feed(dom); txt = tp.text()
        ok = full_article(txt)
        if dom:
            open(f"fulltext/html/{rid}.html", "w").write(dom)
        if ok:
            open(f"fulltext/txt/{rid}.txt", "w").write(txt)
        rec = {"rid": rid, "status": "ok_html" if ok else "not_retrieved", "url": url, "chars": len(txt),
               "seconds": round(time.time() - t0, 1)}
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(rid, rec["status"], rec["chars"], flush=True)
        time.sleep(4)
