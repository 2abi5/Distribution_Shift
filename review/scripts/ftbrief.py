"""Compact full-text triage view (used once the PDFs are no longer on disk): title, abstract excerpt,
cross-domain result sentences (two-column layout text de-columnised first), and numeric table rows.
Usage: python3 scripts/ftbrief.py [--rows N] R00150 R00157 ...   (run from paper/review)"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
STRONG = re.compile(r"source[- ]domain|target[- ]domain|source[- ]only|without (domain )?adaptation|no adaptation|baseline|"
                    r"cross[- ]?(domain|dataset|site|region|season|year|field|location|sensor|crop|species|farm|orchard|"
                    r"variet|cultivar|platform|camera|device|scene|country)|unseen|in[- ]domain|out[- ]of[- ]domain|"
                    r"out[- ]of[- ]distribution|intra[- ]?(domain|dataset|site|field|region|year)|inter[- ]?(domain|dataset|site|region|year)|"
                    r"trained (on|in|with)|tested (on|in)|test(ed|ing)? (on|in) (a |the )?(different|new|another|other|independent)|"
                    r"oracle|upper bound|leave[- ]one|generali[sz]|transfer|domain (shift|gap|adaptation|generali)|"
                    r"laboratory|lab[- ]to[- ]field|field (images|conditions|data)|another (year|site|field|region)|"
                    r"different (years?|sites?|fields?|regions?|locations?|sensors?|cameras?|seasons?|datasets?)|"
                    r"spatial(ly)? (cross|independent|hold|transfer)|temporal(ly)? (cross|independent|hold|transfer)|independent test", re.I)
NUM = re.compile(r"\d+(\.\d+)?\s*%|\b0\.\d{2,}\b|\b\d{2}\.\d{1,2}\b", re.I)
CAP = re.compile(r"^\s*(\| )?(Table|TABLE)\s+[0-9IVX]+[.:|]?", re.M)
LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "‐": "-", "­": ""}

from html.parser import HTMLParser


class Tables(HTMLParser):
    """Collect <table> elements as lists of rows (cells joined by ' | '), with captions."""
    def __init__(self):
        super().__init__(); self.tables = []; self.depth = 0; self.row = None; self.cell = None; self.cap = None; self.skip = 0

    def handle_starttag(self, tag, a):
        if tag in ("script", "style"): self.skip += 1
        if tag == "table":
            self.depth += 1; self.tables.append({"cap": "", "rows": []})
        elif self.depth and tag == "tr": self.row = []
        elif self.depth and tag in ("td", "th"): self.cell = []
        elif self.depth and tag == "caption": self.cap = []

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip: self.skip -= 1
        if tag == "table" and self.depth: self.depth -= 1
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip()); self.cell = None
        elif tag == "tr" and self.row is not None:
            if any(self.row): self.tables[-1]["rows"].append(" | ".join(self.row))
            self.row = None
        elif tag == "caption" and self.cap is not None:
            self.tables[-1]["cap"] = re.sub(r"\s+", " ", "".join(self.cap)).strip(); self.cap = None

    def handle_data(self, d):
        if self.skip: return
        if self.cell is not None: self.cell.append(d)
        elif self.cap is not None: self.cap.append(d)


pool = {}
for line in open("search/pool_v3.jsonl"):
    r = json.loads(line)
    pool[r["rid"]] = r


def decolumn(text):
    """Rebuild reading order for two-column pdftotext -layout output, page by page."""
    out = []
    for page in text.split("\f"):
        lines = page.split("\n")
        width = max((len(l) for l in lines), default=0)
        if width < 100:
            out.append(page); continue
        starts = {}
        for l in lines:
            for m in re.finditer(r"\S\s{3,}(?=\S)", l):
                pos = m.end()
                if 0.33 * width < pos < 0.67 * width:
                    starts[pos] = starts.get(pos, 0) + 1
        if not starts or max(starts.values()) < 8:
            out.append(page); continue
        split = max(starts, key=starts.get)
        left, right = [], []
        for l in lines:
            if len(l) > split and l[split - 1:split].strip() == "" or len(l) <= split:
                left.append(l[:split].strip()); right.append(l[split:].strip())
            else:
                left.append(l.strip())
        out.append("\n".join(left) + "\n" + "\n".join(right))
    return "\n".join(out)


def sentences(text):
    t = re.sub(r"-\n(?=[a-z])", "", text)
    t = re.sub(r"\s*\n\s*", " ", t)
    t = re.sub(r"\s{2,}", " ", t)
    return re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", t)


args = sys.argv[1:]
nrows = 30
if "--rows" in args:
    i = args.index("--rows"); nrows = int(args[i + 1]); del args[i:i + 2]
for rid in args:
    p = pool[rid]
    print("=" * 100)
    print(f"{rid} | {p.get('title')} | {p.get('year')} | {p.get('venue')}")
    print("ABS:", re.sub(r"\s+", " ", p.get("abstract") or "")[:550])
    lay = open(f"fulltext/txt/{rid}.txt", encoding="utf-8", errors="ignore").read()
    for a, b in LIG.items():
        lay = lay.replace(a, b)
    html = lay.count("\n| ") > 20
    body = lay if html else decolumn(lay)
    cuts = list(re.finditer(r"\n\s*(References|REFERENCES|Bibliography|Literature Cited)\s*\n", body))
    if cuts and cuts[-1].start() > len(body) * 0.4:
        body = body[:cuts[-1].start()]
    hits, seen = [], set()
    for s in sentences(body):
        if 40 < len(s) < 600 and STRONG.search(s) and NUM.search(s) and s[:70] not in seen:
            seen.add(s[:70]); hits.append(s.strip())
    print(f"-- sentences ({len(hits)}; first 10)")
    for x in hits[:10]:
        print("  *", x[:280])
    lines = lay.split("\n")
    hp = f"fulltext/html/{rid}.html"
    if os.path.exists(hp):
        tp = Tables(); tp.feed(open(hp, encoding="utf-8", errors="ignore").read())
        tabs = [t for t in tp.tables if any(re.search(r"\d\.\d|\d%", r) for r in t["rows"])]
        print(f"-- HTML tables with numbers ({len(tabs)})")
        for t in tabs[:8]:
            print("  [" + t["cap"][:140] + "]")
            for r in [r for r in t["rows"] if re.search(r"\d", r) or len(r) < 120][:nrows // 2]:
                print("    " + r[:170])
        continue
    if html:
        rows = [l for l in lines if l.startswith("| ") and re.search(r"\d\.\d|\d%", l)]
        print(f"-- HTML numeric rows ({len(rows)}; first {nrows})")
        for l in rows[:nrows]:
            print("  " + l[:160])
    else:
        caps = [i for i, l in enumerate(lines) if CAP.match(l)]
        print(f"-- tables ({len(caps)})")
        shown = 0
        for i in caps:
            cap = re.sub(r"\s{3,}", "   ", lines[i].strip())[:150]
            if re.search(r"hyper|parameter|architecture|abbreviat|notation|configur|setting", cap, re.I):
                continue
            num = [re.sub(r"\s{3,}", "  ", l.strip())[:150] for l in lines[i + 1:i + 22] if re.search(r"\d\.\d", l)]
            print("  [" + cap + "]")
            for l in num[:9]:
                print("    " + l)
            shown += 1
            if shown >= 6:
                break
