"""Citation chasing (protocol section 2): one round of backward (reference lists) and forward (citing works) chasing
on every included study, through OpenAlex `referenced_works` and the `cites:` filter. Run 2 October 2026.

Writes search/chase_2026-10-02.jsonl (one record per chased work not already in the screened pool) and
search/chase_2026-10-02.meta.json (counts at each step). Records are then screened like the database records.
Usage (from paper/review):  python3 scripts/chase.py"""
import csv
import json
import re
import time
import urllib.parse
import urllib.request

UA = "location_doner-systematic-review/1.0 (https://github.com/2abi5/location_doner)"
OUT = "search/chase_2026-10-02.jsonl"
META = "search/chase_2026-10-02.meta.json"
SELECT = "id,doi,title,publication_year,type,language,primary_location,abstract_inverted_index,authorships,referenced_works_count"


def get(url):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return json.loads(r.read())
        except Exception as ex:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"failed: {url}")


def abstract(inv):
    if not inv:
        return ""
    pos = [(i, w) for w, idx in inv.items() for i in idx]
    return " ".join(w for _, w in sorted(pos))


pool = {}
for line in open("search/pool_v3.jsonl"):
    r = json.loads(line)
    pool[r["rid"]] = r
dec = {r["rid"]: r for r in csv.DictReader(open("extraction/ft_decisions.csv"))}
included = [k for k, d in dec.items() if d["decision"] in ("INCLUDE", "INCLUDE-O", "INCLUDE-A")]

# OpenAlex IDs of the included studies (search record, else look up by DOI)
seeds = {}
for rid in included:
    p = pool.get(rid, {})
    w = p.get("openalex")
    if w in (None, "None", ""):
        doi = "10.3389/fpls.2016.01419" if rid == "X00001" else (p.get("doi") or "")
        if doi:
            try:
                w = get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}?select=id")["id"].rsplit("/", 1)[1]
            except Exception:
                w = None
    if w:
        seeds[rid] = w
print("seeds with OpenAlex id:", len(seeds), "of", len(included), flush=True)

# identifiers already screened: the pool (OpenAlex ids, DOIs, normalised titles)
norm = lambda t: re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()
known_w = {p.get("openalex") for p in pool.values()}
known_doi = {(p.get("doi") or "").lower() for p in pool.values()} - {""}
known_t = {norm(p.get("title")) for p in pool.values()}

# backward: referenced works of every seed
back = {}
ids = list(seeds.values())
for i in range(0, len(ids), 50):
    d = get("https://api.openalex.org/works?per-page=50&select=id,referenced_works&filter=openalex:" + "|".join(ids[i:i + 50]))
    for w in d["results"]:
        for ref in w.get("referenced_works") or []:
            back.setdefault(ref.rsplit("/", 1)[1], set()).add(w["id"].rsplit("/", 1)[1])
    time.sleep(0.2)
print("backward: unique referenced works", len(back), flush=True)

# forward: works citing any seed (cursor paging)
fwd = {}
for i in range(0, len(ids), 40):
    cursor = "*"
    while cursor:
        d = get("https://api.openalex.org/works?per-page=200&select=id,referenced_works&cursor=" + cursor +
                "&filter=cites:" + "|".join(ids[i:i + 40]))
        for w in d["results"]:
            wid = w["id"].rsplit("/", 1)[1]
            cited = {r.rsplit("/", 1)[1] for r in w.get("referenced_works") or []} & set(ids[i:i + 40])
            fwd.setdefault(wid, set()).update(cited)
        cursor = d["meta"].get("next_cursor")
        time.sleep(0.2)
print("forward: unique citing works", len(fwd), flush=True)

chased = set(back) | set(fwd)
new = sorted(w for w in chased if w not in known_w and w not in set(seeds.values()))
print("chased works not already in the pool (by OpenAlex id):", len(new), flush=True)

# metadata for the new works
recs = []
for i in range(0, len(new), 50):
    d = get(f"https://api.openalex.org/works?per-page=50&select={SELECT}&filter=openalex:" + "|".join(new[i:i + 50]))
    for w in d["results"]:
        wid = w["id"].rsplit("/", 1)[1]
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        t = w.get("title") or ""
        if (doi and doi in known_doi) or norm(t) in known_t:
            continue                                   # same work, different OpenAlex id: already screened
        src = (w.get("primary_location") or {}).get("source") or {}
        recs.append({"wid": wid, "doi": doi, "title": t, "year": w.get("publication_year"), "type": w.get("type"),
                     "language": w.get("language"), "venue": src.get("display_name"),
                     "authors": [a["author"]["display_name"] for a in w.get("authorships") or []][:12],
                     "abstract": abstract(w.get("abstract_inverted_index")),
                     "backward_from": sorted(back.get(wid, [])), "forward_to": sorted(fwd.get(wid, []))})
    time.sleep(0.2)
    if i % 1000 == 0:
        print(" metadata", i, "/", len(new), flush=True)
with open(OUT, "w") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
json.dump({"date": time.strftime("%Y-%m-%d %H:%M"), "seeds": len(seeds), "included": len(included),
           "backward_unique": len(back), "forward_unique": len(fwd), "chased_unique": len(chased),
           "new_by_id": len(new), "new_after_doi_title_dedup": len(recs)}, open(META, "w"), indent=1)
print("written", len(recs), "records to", OUT, flush=True)
