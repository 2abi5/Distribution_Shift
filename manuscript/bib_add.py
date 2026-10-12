"""Append BibTeX entries fetched from doi.org (content negotiation) to refs.bib, with readable keys.
Usage: python3 bib_add.py DOI [DOI ...]"""
import os, re, sys, time, unicodedata, urllib.request
os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")
STOP = {"a", "an", "the", "on", "of", "in", "for", "and", "to", "from", "with", "using", "towards", "toward"}
have = open("refs.bib").read() if os.path.exists("refs.bib") else ""
have_dois = {d.lower() for d in re.findall(r"doi\s*=\s*\{([^}]+)\}", have, re.I)}

def ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()

for doi in sys.argv[1:]:
    if doi.lower() in have_dois:
        print("have", doi); continue
    req = urllib.request.Request("https://doi.org/" + doi,
                                 headers={"Accept": "application/x-bibtex; charset=utf-8", "User-Agent": "review-pipeline"})
    try:
        bib = urllib.request.urlopen(req, timeout=60).read().decode("utf-8").strip()
    except Exception as e:
        print("FAIL", doi, e); continue
    m_auth = re.search(r"author\s*=\s*\{([^}]*)", bib)
    m_year = re.search(r"year\s*=\s*\{?(\d{4})", bib)
    m_tit = re.search(r"title\s*=\s*\{(.+?)\},?\s*\n", bib, re.S)
    first = ascii(m_auth.group(1).split(" and ")[0]) if m_auth else "anon"
    last = first.split(",")[0] if "," in first else first.split()[-1]
    last = re.sub(r"[^a-z]", "", last.lower()) or "anon"
    words = [w for w in re.findall(r"[a-z0-9]+", ascii(m_tit.group(1)).lower()) if w not in STOP] if m_tit else ["x"]
    key = f"{last}{m_year.group(1) if m_year else ''}{words[0] if words else ''}"
    base, n = key, 1
    while re.search(r"@\w+\{" + re.escape(key) + ",", have):
        n += 1; key = f"{base}{chr(96 + n)}"
    bib = re.sub(r"^@(\w+)\{[^,]*,", lambda m: f"@{m.group(1).lower()}{{{key},", bib, count=1)
    if "doi" not in bib.lower().split("{", 1)[1][:2000].lower():
        bib = bib.rstrip("}").rstrip() + f",\n doi = {{{doi}}}\n}}"
    have += "\n" + bib + "\n"
    have_dois.add(doi.lower())
    print(key, "<-", doi)
    time.sleep(0.5)
open("refs.bib", "w").write(have.strip() + "\n")
