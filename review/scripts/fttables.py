"""Print every HTML table of a saved article page (fulltext/html/RID.html) with its caption, one row per line.
Usage (from paper/review):  python3 scripts/fttables.py RID [--max-rows 40] [--only "Table 5"]"""
import re
import sys
from html.parser import HTMLParser

rid = sys.argv[1]
maxr = int(sys.argv[sys.argv.index("--max-rows") + 1]) if "--max-rows" in sys.argv else 40
only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None


class T(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.stack, self.row, self.cell, self.skip = [], [], None, None, 0
        self.cap_buf, self.last_text = None, []

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "table":
            self.stack.append({"cap": " ".join(self.last_text[-40:])[-300:], "rows": []})
        elif self.stack and tag == "tr":
            self.row = []
        elif self.stack and tag in ("td", "th"):
            self.cell = []
        elif self.stack and tag == "caption":
            self.cap_buf = []

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag == "table" and self.stack:
            self.tables.append(self.stack.pop())
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None and self.stack:
            if any(c for c in self.row):
                self.stack[-1]["rows"].append(self.row)
            self.row = None
        elif tag == "caption" and self.cap_buf is not None and self.stack:
            self.stack[-1]["cap"] = re.sub(r"\s+", " ", "".join(self.cap_buf)).strip()
            self.cap_buf = None

    def handle_data(self, d):
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(d)
        if self.cap_buf is not None:
            self.cap_buf.append(d)
        s = d.strip()
        if s:
            self.last_text.append(s)
            self.last_text = self.last_text[-60:]


html = open(f"fulltext/html/{rid}.html", errors="ignore").read()
# Taylor & Francis keeps its tables as escaped HTML in a script variable (tandf.tfviewerdata); unpack them
import json
for m in re.finditer(r"tfviewerdata=(\{.*?\});?\s*</script>", html, re.S):
    try:
        data = json.loads(m.group(1))
        html += "".join(t.get("content", "") for t in data.get("tables", []))
    except json.JSONDecodeError:
        pass
p = T()
p.feed(html)
seen = set()
for t in p.tables:
    sig = str(t["rows"][:3])
    if sig in seen or not t["rows"]:
        continue
    seen.add(sig)
    cap = t["cap"]
    m = re.search(r"(Table|TABLE)\s*[0-9IVXA-Z]+.*", cap)
    cap = m.group(0)[:250] if m else cap[-200:]
    if only and only.lower() not in cap.lower():
        continue
    print(f"### {cap}")
    for r in t["rows"][:maxr]:
        print("   | " + " | ".join(c[:40] for c in r))
    if len(t["rows"]) > maxr:
        print(f"   ... {len(t['rows']) - maxr} more rows")
