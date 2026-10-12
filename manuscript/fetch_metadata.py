"""Fetch authoritative bibliographic metadata for every included study and the three context reviews.

Crossref for registered DOIs, the arXiv API for arXiv preprints. For each preprint, Crossref is also searched for a
peer-reviewed version (protocol section 4: a preprint with a peer-reviewed version is replaced by that version).
Results are cached in bib_metadata.json so that make_tables.py builds the bibliography offline and reproducibly.
Usage (from paper/manuscript, network required):  python3 fetch_metadata.py [--refresh]"""
import csv
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))
REV = "../review"
CACHE = "bib_metadata.json"
UA = "location_doner-systematic-review/1.0 (https://github.com/2abi5/location_doner)"
CONTEXT = ["R02966", "R06651", "R07003"]

pool = {}
for line in [*open(f"{REV}/search/pool_v3.jsonl"), *(open(f"{REV}/search/pool_extra.jsonl") if __import__("os").path.exists(f"{REV}/search/pool_extra.jsonl") else [])]:
    r = json.loads(line)
    pool[r["rid"]] = r
dec = {r["rid"]: r for r in csv.DictReader(open(f"{REV}/extraction/ft_decisions.csv"))}
ids = sorted(k for k, d in dec.items() if d["decision"] in ("INCLUDE", "INCLUDE-O", "INCLUDE-A") and k != "X00001")
ids += CONTEXT

cache = {} if "--refresh" in sys.argv or not os.path.exists(CACHE) else json.load(open(CACHE))


def get(url, accept="application/json"):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(5 * (attempt + 1))
    return None


def norm(s):
    s = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def crossref(doi):
    raw = get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
    time.sleep(0.2)
    if not raw:
        return None
    m = json.loads(raw)["message"]
    keep = ["DOI", "type", "title", "author", "container-title", "short-container-title", "issued", "published-print",
            "published-online", "volume", "issue", "page", "article-number", "publisher", "event"]
    return {k: m[k] for k in keep if k in m}


def csl(doi):
    """DOI content negotiation (DataCite, mEDRA, JaLC ...) for DOIs that Crossref does not hold."""
    raw = get(f"https://doi.org/{urllib.parse.quote(doi)}", accept="application/vnd.citationstyles.csl+json")
    time.sleep(0.5)
    try:
        d = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return None
    return d if d and d.get("title") else None


def openalex(doi):
    raw = get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")
    time.sleep(0.2)
    if not raw:
        return None
    w = json.loads(raw)
    return {"title": w.get("title"), "publication_year": w.get("publication_year"), "biblio": w.get("biblio"),
            "authors": [a["author"]["display_name"] for a in w.get("authorships", [])],
            "raw_authors": [a.get("raw_author_name") for a in w.get("authorships", [])],
            "source": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            "issn": ((w.get("primary_location") or {}).get("source") or {}).get("issn_l")}


def arxiv(aid):
    raw = get(f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(aid)}", accept="application/atom+xml")
    time.sleep(3)
    if not raw or "<entry>" not in raw:
        return None
    e = raw.split("<entry>", 1)[1]
    tag = lambda t: " ".join((re.search(rf"<{t}[^>]*>(.*?)</{t}>", e, re.S) or [None, ""])[1].split())
    return {"id": aid, "title": tag("title"), "authors": [" ".join(n.split()) for n in re.findall(r"<name>(.*?)</name>", e, re.S)],
            "published": tag("published")[:10], "journal_ref": tag("arxiv:journal_ref"), "doi": tag("arxiv:doi")}


def published_version(title, first_surname):
    """Search Crossref for a peer-reviewed version of a preprint; return its DOI or None."""
    q = urllib.parse.quote(title[:200])
    raw = get(f"https://api.crossref.org/works?query.bibliographic={q}&rows=8&select=DOI,title,author,type")
    time.sleep(0.3)
    if not raw:
        return None
    for it in json.loads(raw)["message"]["items"]:
        if it.get("type") not in ("journal-article", "proceedings-article", "book-chapter"):
            continue
        t = (it.get("title") or [""])[0]
        if difflib.SequenceMatcher(None, norm(title), norm(t)).ratio() < 0.93:
            continue
        fams = [norm(a.get("family", "")) for a in it.get("author") or []]
        if first_surname and fams and norm(first_surname) not in " ".join(fams):
            continue
        return it["DOI"]
    return None


for i, rid in enumerate(ids):
    p = pool[rid]
    if rid in cache and cache[rid].get("ok"):
        continue
    doi = (p.get("doi") or "").strip()
    ax = None
    if doi.lower().startswith("10.48550/arxiv."):
        ax = doi.split("arxiv.", 1)[1] if "arxiv." in doi.lower() else None
        ax = re.sub(r"(?i)^10\.48550/arxiv\.", "", doi)
    elif not doi and p.get("arxiv") not in (None, "None", ""):
        ax = p["arxiv"]
    rec = {"rid": rid, "pool_doi": doi, "ok": False}
    if ax:
        a = arxiv(ax)
        rec.update(source="arxiv", arxiv=a, ok=bool(a))
        if a:
            fam = a["authors"][0].split()[-1] if a["authors"] else ""
            pv = a["doi"] or published_version(a["title"], fam)
            if pv:
                rec["published_doi"] = pv
                rec["published"] = crossref(pv)
    elif doi:
        c = crossref(doi)
        rec.update(source="crossref", crossref=c, ok=bool(c))
        if not c:
            d = csl(doi)
            if d:
                rec.update(source="csl", csl=d, ok=True)
            else:
                o = openalex(doi)
                rec.update(source="openalex", openalex=o, ok=bool(o))
    else:
        rec.update(source="pool", ok=True)
    cache[rid] = rec
    print(f"{i + 1:3d}/{len(ids)} {rid} {rec['source']:8s} ok={rec['ok']}"
          + (f"  published version: {rec['published_doi']}" if rec.get("published_doi") else ""), flush=True)
    if (i + 1) % 20 == 0:
        json.dump(cache, open(CACHE, "w"), indent=1, ensure_ascii=False, sort_keys=True)

json.dump(cache, open(CACHE, "w"), indent=1, ensure_ascii=False, sort_keys=True)
bad = [r for r in ids if not cache.get(r, {}).get("ok")]
print(f"done: {len(ids) - len(bad)}/{len(ids)} resolved; unresolved: {bad}")
