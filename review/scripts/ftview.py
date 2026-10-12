"""Full-text eligibility/extraction view: abstract, result sentences about cross-domain testing, and the
tables whose captions mention domains, sites, years, sensors or datasets.
Usage: python3 scripts/ftview.py R00004 R00009 ...   (reads fulltext/pdf, fulltext/txt, search/pool_v3.jsonl)"""
import json, re, subprocess, sys

STRONG = re.compile(r"source[- ]domain|target[- ]domain|source[- ]only|without (domain )?adaptation|no adaptation|"
                    r"cross[- ]?(domain|dataset|site|region|season|year|field|location|sensor|crop|species|farm|orchard|"
                    r"variet|cultivar|platform|camera|device|scene|continent|country)|unseen|in[- ]domain|out[- ]of[- ]domain|"
                    r"out[- ]of[- ]distribution|intra[- ]?(domain|dataset|site|field|region|year)|"
                    r"inter[- ]?(domain|dataset|site|field|region|year)|"
                    r"trained on|tested on|test(ed|ing)? (on|in) (a |the )?(different|new|another|other|independent)|"
                    r"oracle|upper bound|lower bound|leave[- ]one|generali[sz]|transferab|domain (shift|gap|adaptation|"
                    r"generali)|laboratory|lab[- ]to[- ]field|field (images|conditions|data)|another (year|site|field|region)|"
                    r"different (years?|sites?|fields?|regions?|locations?|sensors?|cameras?|seasons?)|"
                    r"spatial(ly)? (cross|independent|hold)|temporal(ly)? (cross|independent|hold)|random split|"
                    r"k-fold|validation set|early stopping|github|code (is )?available|data (is |are )?available", re.I)
NUM = re.compile(r"\d+(\.\d+)?\s*%|\b0\.\d{2,}\b|\b\d{2}\.\d{1,2}\b|R2|R²|RMSE|mAP|mIoU|F1|accuracy|kappa", re.I)
SIZE = re.compile(r"\b\d[\d,]{1,7}\s+(images|samples|photos|fields|plots|patches|tiles|sites|site-years|county-years|parcels|plants|frames)\b", re.I)
CAP = re.compile(r"^\s*(\| )?(Table|TABLE)\s+[0-9IVX]+[.:]?", re.M)
TABLE_TOPIC = re.compile(r"domain|source|target|cross|unseen|site|year|season|region|field|sensor|dataset|test|"
                         r"generali|transfer|adapt|location|camera|platform|comparison|performance|result|accuracy|F1|score|IoU|mAP|R2|RMSE|error|kappa|precision|metric", re.I)

pool = {}
for line in open("search/pool_v3.jsonl"):
    r = json.loads(line)
    pool[r["rid"]] = r


def sentences(text):
    t = re.sub(r"-\n(?=[a-z])", "", text)
    t = re.sub(r"\s*\n\s*", " ", t)
    t = re.sub(r"\s{2,}", " ", t)
    return re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", t)


for rid in sys.argv[1:]:
    p = pool[rid]
    print("=" * 110)
    print(f"{rid} | {p.get('title')} | {p.get('year')} | {p.get('venue')} | doi:{p.get('doi')}")
    print("ABSTRACT:", re.sub(r"\s+", " ", p.get("abstract") or "")[:700])
    import os
    try:
        lay = open(f"fulltext/txt/{rid}.txt", encoding="utf-8", errors="ignore").read()
        if os.path.exists(f"fulltext/pdf/{rid}.pdf"):
            raw = subprocess.run(["pdftotext", f"fulltext/pdf/{rid}.pdf", "-"], capture_output=True, timeout=120).stdout.decode("utf-8", "ignore")
        else:
            raw = lay  # HTML-derived text (tables as ' | ' rows)
            print("  [source: rendered HTML]")
    except Exception as e:
        print("  [no full text]", e); continue
    LIG = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl", "\u2010": "-", "\u00ad": ""}
    for a, b in LIG.items():
        raw = raw.replace(a, b); lay = lay.replace(a, b)
    cuts = list(re.finditer(r"\n\s*(References|REFERENCES|Bibliography)\s*\n", raw))
    body = raw[:cuts[-1].start()] if cuts and cuts[-1].start() > len(raw) * 0.4 else raw
    hits, seen = [], set()
    for s in sentences(body):
        if len(s) < 40 or len(s) > 700:
            continue
        if STRONG.search(s) and (NUM.search(s) or re.search(r"github|available|validation set|early stopping|k-fold|random split", s, re.I)):
            key = s[:80]
            if key not in seen:
                seen.add(key); hits.append(s.strip())
    sizes = [x.strip() for x in sentences(body) if SIZE.search(x) and 30 < len(x) < 400][:3]
    print(f"--- result sentences ({len(hits)} found; first 12) ---")
    for x in hits[:12]:
        print("  •", x[:300])
    if sizes:
        print("--- dataset sizes ---")
        for x in sizes:
            print("  ·", x[:300])
    lines = lay.split("\n")
    if not os.path.exists(f"fulltext/pdf/{rid}.pdf"):
        rows_ = [l for l in lines if l.startswith("| ") and re.search(r"\d", l) and not re.search(r"\b(19|20)\d\d\b.*\b(19|20)\d\d\b.*\b(19|20)\d\d\b", l[:40])]
        print(f"--- HTML table rows with numbers ({len(rows_)}; first 40) ---")
        for l in rows_[:40]:
            print("  " + l[:170])
        continue
    caps = [i for i, l in enumerate(lines) if CAP.match(l)]
    shown, covered = 0, set()
    print(f"--- tables ({len(caps)} captions) ---")
    for i in caps:
        if i in covered:
            continue
        cap = " ".join(x.strip() for x in lines[i:i + 2])
        if not TABLE_TOPIC.search(cap) or shown >= 3 or re.search(r"hyper|parameter|architecture|structure|setting|notation|abbreviation|dataset (description|statistics)|statistics of", cap, re.I):
            continue
        shown += 1
        covered.update(range(i, i + 22))
        block = [l.rstrip() for l in lines[i:i + 22] if l.strip()]
        print("\n".join("  | " + re.sub(r"\s{3,}", "   ", l)[:160] for l in block[:17]))
        print("  |")
