"""Generate the manuscript tables, the included-studies appendix and its bibliography from the review data.
Every number comes from ../review/analysis/results.json or the extraction CSVs; nothing is typed by hand.
Writes generated/{table1..table5,appendix_c}.md and generated/included.bib.
Usage: python3 make_tables.py   (run from paper/manuscript)"""
import csv
import html
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict

import numpy as np

REV = "../review"
OUT = "generated"
os.makedirs(OUT, exist_ok=True)
R = json.load(open(f"{REV}/analysis/results.json"))
pool = {}
for line in [*open(f"{REV}/search/pool_v3.jsonl"), *(open(f"{REV}/search/pool_extra.jsonl") if __import__("os").path.exists(f"{REV}/search/pool_extra.jsonl") else [])]:
    r = json.loads(line)
    pool[r["rid"]] = r
dec = {r["rid"]: r for r in csv.DictReader(open(f"{REV}/extraction/ft_decisions.csv"))}
comps = list(csv.DictReader(open(f"{REV}/analysis/comparisons_with_effects.csv")))
raw = list(csv.DictReader(open(f"{REV}/extraction/comparisons.csv")))
INCLUDED = sorted(k for k, d in dec.items() if d["decision"] in ("INCLUDE", "INCLUDE-O", "INCLUDE-A"))

TASK = {"D": "Disease, pest and abiotic stress", "W": "Weed–crop discrimination", "O": "Plant and organ detection, counting",
        "P": "Phenotypic traits", "M": "Crop-type and cropland mapping", "Y": "Yield"}
TASK_SHORT = {"D": "Disease", "W": "Weed", "O": "Organ", "P": "Trait", "M": "Mapping", "Y": "Yield"}
SHIFT = {"acquisition": "Acquisition (laboratory to field, imaging setup)", "location": "Location", "time": "Time (season, year)",
         "sensor": "Sensor or platform", "biological": "Biological material", "compound": "Compound (two or more factors)"}
SHIFT_SHORT = {"acquisition": "Acq.", "location": "Loc.", "time": "Time", "sensor": "Sens.", "biological": "Biol.", "compound": "Comp."}


def f2(x):
    return "–" if x is None else f"{x:.2f}"


def row(name, s):
    if not s or not s.get("n"):
        return f"| {name} | 0 | – | – | – |"
    ci = "–" if s.get("ci_lo") is None else f"{f2(s['ci_lo'])}–{f2(s['ci_hi'])}"
    return f"| {name} | {s['n']} | {f2(s['median'])} | {f2(s['q1'])}–{f2(s['q3'])} | {ci} |"


def ordered(d, order=None):
    keys = order or sorted(d, key=lambda k: -d[k]["n"])
    return [k for k in keys if k in d]


# ------------------------------------------------------------------ Table 1: characteristics of included studies
n = R["n_included"]
ch = R["characteristics"]
pct = lambda k: f"{k} ({100 * k / n:.0f})"
t1 = [": Table 1. Characteristics of the {} included studies. A study can count under more than one task, modality "
      "or shift type, so those panels can sum to more than {}.".format(n, n), "",
      "| Characteristic | Studies, n (%) |", "|:------------------------------------------------------------|--------------:|"]
t1.append("| **Basis of data extraction** | |")
t1.append(f"| Full text | {pct(R['n_included_fulltext'])} |")
t1.append(f"| Abstract only (full text not retrieved) | {pct(R['n_included_abstract'])} |")
t1.append("| **Publication status** | |")
for k in ("peer-reviewed", "preprint"):
    t1.append(f"| {k.capitalize()} | {pct(R['publication'].get(k, 0))} |")
t1.append("| **Publication year** | |")
for k in ("2016-2020", "2021-2023", "2024-2025", "2026"):
    t1.append(f"| {k.replace('-', '–')}{' (to 2 October)' if k == '2026' else ''} | {pct(ch['period'].get(k, 0))} |")
t1.append("| **Task** | |")
for k in sorted(ch["task"], key=lambda k: -ch["task"][k]):
    t1.append(f"| {TASK[k]} | {pct(ch['task'][k])} |")
t1.append("| **Data modality** | |")
MOD = {"proximal RGB": "Proximal RGB", "satellite / airborne": "Satellite or airborne", "UAV": "UAV",
       "proximal spectral": "Proximal multispectral, hyperspectral or thermal", "tabular / weather": "Tabular or weather"}
for k in sorted(ch["modality"], key=lambda k: -ch["modality"][k]):
    t1.append(f"| {MOD[k]} | {pct(ch['modality'][k])} |")
t1.append("| **Shift type** | |")
for k in sorted(ch["shift"], key=lambda k: -ch["shift"][k]):
    t1.append(f"| {SHIFT[k]} | {pct(ch['shift'][k])} |")
t1.append("| **Outcome available for synthesis** | |")
t1.append(f"| Bounded metric, ID and OOD (retention) | {pct(R['n_studies_bounded'])} |")
t1.append(f"| Regression metric only (ΔR², error ratio) | {pct(R['n_studies_regression_only'])} |")
t1.append(f"| No ID value or mitigated model only | {pct(R['n_included_without_primary'])} |")
t1.append(f"| Mitigation with source-only comparator | {pct(R['n_studies_mitigation'])} |")
open(f"{OUT}/table1.md", "w").write("\n".join(t1) + "\n")

# ------------------------------------------------------------------ Table 2: retention by moderator
SEP5 = "|:" + "-" * 44 + "|" + "-" * 8 + ":|" + "-" * 10 + ":|" + "-" * 10 + ":|" + "-" * 12 + ":|"
hdr = ["| Subgroup | Studies | Median retention | IQR | 95% CI of median |", SEP5]
t2 = [": Table 2. Retention of in-distribution performance under distribution shift (ρ = m~OOD~/m~ID~, bounded "
      "metrics), one value per study and subgroup. IQR, interquartile range of study values; CI, cluster-bootstrap "
      "interval (10,000 resamples of studies).", ""] + hdr
t2.append(row("**All studies**", R["ret_overall"]))
t2.append("| *Shift type (primary classification)* | | | | |")
for k in ordered(R["ret_by_shift"], ["acquisition", "sensor", "compound", "location", "time", "biological"]):
    t2.append(row(SHIFT[k], R["ret_by_shift"][k]))
t2.append("| *Shift factor (compound shifts counted under each factor)* | | | | |")
for k in ordered(R["ret_by_factor"], ["acquisition", "sensor", "biological", "location", "time"]):
    t2.append(row(SHIFT[k].split(" (")[0], R["ret_by_factor"][k]))
t2.append("| *Task* | | | | |")
for k in ordered(R["ret_by_task"], ["W", "D", "M", "O", "P"]):
    t2.append(row(TASK[k], R["ret_by_task"][k]))
t2.append("| *Data modality* | | | | |")
for k in ordered(R["ret_by_modality"], ["proximal RGB", "UAV", "proximal spectral", "satellite / airborne"]):
    t2.append(row(MOD[k], R["ret_by_modality"][k]))
t2.append("| *Model family* | | | | |")
FAM = {"convolutional": "Convolutional network", "transformer / attention": "Transformer or attention-based",
       "recurrent": "Recurrent network", "classical ML": "Classical machine learning",
       "other deep learning (MLP, DNN, unspecified)": "Other deep network (MLP, unspecified)"}
for k in ordered(R["ret_by_family"], ["convolutional", "transformer / attention", "recurrent",
                                      "other deep learning (MLP, DNN, unspecified)", "classical ML"]):
    t2.append(row(FAM[k], R["ret_by_family"][k]))
t2.append("| *Publication year* | | | | |")
for k in ordered(R["ret_by_period"], ["2016-2020", "2021-2023", "2024-2025", "2026"]):
    t2.append(row(k.replace("-", "–"), R["ret_by_period"][k]))
open(f"{OUT}/table2.md", "w").write("\n".join(t2) + "\n")

# ------------------------------------------------------------------ Table 3: task x shift cross-tabulation
cats = ["acquisition", "sensor", "compound", "location", "time", "biological"]
tasks = ["D", "W", "O", "M", "P"]
cell = R["ret_by_task_shift"]
t3 = [": Table 3. Median retention by task and shift type: median of study values (number of studies). "
      "Cells with fewer than three studies are shown in parentheses as descriptive only. Acq., acquisition; Sens., sensor "
      "or platform; Comp., compound; Loc., location; Biol., biological material. Yield studies used regression metrics "
      "and do not appear.", "",
      "| Task | " + " | ".join(SHIFT_SHORT[c] for c in cats) + " |", "|:------------|" + ("-" * 10 + ":|") * len(cats)]
for t in tasks:
    cells = []
    for c in cats:
        s = cell.get(f"{t}|{c}")
        if not s:
            cells.append("")
        elif s["n"] < 3:
            cells.append(f"({f2(s['median'])}; {s['n']})")
        else:
            cells.append(f"{f2(s['median'])} ({s['n']})")
    t3.append(f"| {TASK_SHORT[t]} | " + " | ".join(cells) + " |")
open(f"{OUT}/table3.md", "w").write("\n".join(t3) + "\n")

# ------------------------------------------------------------------ Table 4: gap recovered by mitigation
MIT_ORDER = ["target fine-tuning", "DG / augmentation", "pretraining / SSL", "UDA", "other"]
MIT = {"target fine-tuning": "Fine-tuning on labelled target data", "DG / augmentation": "Domain generalisation or augmentation",
       "pretraining / SSL": "Large-scale or self-supervised pretraining", "UDA": "Unsupervised domain adaptation",
       "other": "Other"}
t4 = [": Table 4. Share of the out-of-distribution gap recovered by mitigation, one value per study and mitigation "
      "type. *g* uses the in-distribution value as the reference; *g*~o~ uses a target-trained (oracle) model on the "
      "same test set. *g* = 0: no recovery; *g* = 1: in-distribution (or oracle) performance restored.", "",
      "| Mitigation | Studies | Median | IQR | 95% CI of median |", SEP5]
t4.append("| *Gap recovered relative to ID, g* | | | | |")
t4.append(row("All mitigations", R["g_overall"]))
for k in ordered(R["g_by_mit"], MIT_ORDER):
    t4.append(row(MIT[k], R["g_by_mit"][k]))
t4.append("| *Gap recovered relative to oracle, g~o~* | | | | |")
t4.append(row("All mitigations", R["g_o_overall"]))
for k in ordered(R["g_o_by_mit"], MIT_ORDER):
    t4.append(row(MIT[k], R["g_o_by_mit"][k]))
open(f"{OUT}/table4.md", "w").write("\n".join(t4) + "\n")

# ------------------------------------------------------------------ Table 5: sensitivity analyses
SENS = {"all studies (primary)": "All studies (primary analysis)",
        "full text only (excluding abstract-only)": "Full-text extraction only (abstract-only studies removed)",
        "peer-reviewed only (excluding preprints)": "Peer-reviewed only (preprints removed)",
        "excluding high concern on Q1 or Q2": "High concern on domain separation or model selection removed",
        "excluding derived values": "Values read directly from the report (derived values removed)",
        "OOD test >= 100 samples (Q3 low)": "OOD test set reported and ≥ 100 units",
        "accuracy-type metrics only": "Accuracy-type metrics only"}
t5 = [": Table 5. Sensitivity of the overall median retention to study selection.", "",
      "| Analysis | Studies | Median retention | IQR | 95% CI of median |", SEP5]
for k, lab in SENS.items():
    t5.append(row(lab, R["sensitivity"][k]))
open(f"{OUT}/table5.md", "w").write("\n".join(t5) + "\n")


# ------------------------------------------------------------------ included-study bibliography
# Built from authoritative records cached by fetch_metadata.py (Crossref; arXiv; DataCite; OpenAlex), with the manual
# corrections in bib_corrections.json, each of which states its reason. Falls back to the search record if uncached.
def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    s = re.sub(r"[\x80-\x9f]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def bibesc(s):
    return s.replace("\\", "").replace("{", "").replace("}", "").replace("&", "\\&").replace("%", "\\%").replace("#", "\\#")


PARTICLES = {"de", "da", "das", "do", "dos", "du", "del", "della", "der", "den", "di", "la", "le", "van", "von", "ten", "ter"}


def caps(x):
    """'ZHANG' -> 'Zhang'; leaves initials ('M.K.S.') and mixed case alone."""
    return "-".join(p.capitalize() if p.isupper() and len(p) > 1 and "." not in p else p for p in x.split("-"))


def split_name(full):
    """'Given Middle Family' -> (family, given), keeping particles such as 'de Solan' with the family name."""
    full = clean(full)
    if "," in full:
        fam, giv = full.split(",", 1)
        return caps(fam.strip()), giv.strip()
    t = full.split()
    if len(t) == 1:
        return caps(t[0]), ""
    i = len(t) - 1
    while i > 1 and t[i - 1].lower() in PARTICLES:
        i -= 1
    return caps(" ".join(t[i:])), " ".join(t[:i])


def fold(x):
    return unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()


META = json.load(open("bib_metadata.json")) if os.path.exists("bib_metadata.json") else {}
CORR = json.load(open("bib_corrections.json")) if os.path.exists("bib_corrections.json") else {}


def record(rid):
    """Return dict(type, authors[(family, given)], title, year, venue, volume, number, pages, doi, eprint, url)."""
    p, m, k = pool[rid], META.get(rid, {}), CORR.get(rid, {})
    e = dict(type="article", authors=[split_name(a) for a in p["authors"]], title=clean(p["title"]), year=str(p["year"]),
             venue=clean(p.get("venue") or ""), volume="", number="", pages="", doi=p.get("doi") or "", eprint="", url="")
    if p.get("arxiv") not in (None, "None", ""):
        e["eprint"] = p["arxiv"]
    cr = m.get("published") or m.get("crossref")
    if m.get("arxiv") and not m.get("published"):
        a = m["arxiv"]
        e.update(authors=[split_name(x) for x in a["authors"]], title=clean(a["title"]), year=a["published"][:4],
                 venue=f"arXiv preprint arXiv:{a['id']}", eprint=a["id"], doi=f"10.48550/arXiv.{a['id']}")
    if cr:
        auth = []
        for x in cr.get("author") or []:
            if x.get("family"):
                auth.append((caps(clean(x["family"])), clean(x.get("given") or "")))
            elif x.get("name") and len(x["name"]) < 60 and not re.search(r"\d|,", x["name"]):
                auth.append((clean(x["name"]), ""))
        typ = cr.get("type")
        e.update(authors=auth or e["authors"], title=clean((cr.get("title") or [e["title"]])[0]),
                 year=str(cr["issued"]["date-parts"][0][0]), doi=cr["DOI"],
                 venue=clean((cr.get("container-title") or [""])[0]), volume=cr.get("volume") or "",
                 number=cr.get("issue") or "", pages=(cr.get("page") or cr.get("article-number") or "").replace("-", "–"),
                 type="inproceedings" if typ == "proceedings-article" else "article")
        if typ == "posted-content":
            e["venue"] = ("SSRN preprint" if cr["DOI"].lower().startswith("10.2139/ssrn") else
                          "Research Square preprint" if cr["DOI"].lower().startswith("10.21203/rs") else "Preprint")
        # the database drops accents that the search record keeps: restore them where the names otherwise agree
        pa = [split_name(a) for a in p["authors"]]
        if len(pa) == len(e["authors"]):
            e["authors"] = [(pf, g) if fold(pf) == fold(f) else (f, g) for (f, g), (pf, _) in zip(e["authors"], pa)]
    if m.get("csl"):
        d = m["csl"]
        e.update(authors=[(caps(x.get("family", "")), x.get("given", "")) for x in d.get("author", [])], title=clean(d["title"]),
                 year=str(d["issued"]["date-parts"][0][0]), doi=d.get("DOI", e["doi"]).lower().replace("zenodo", "zenodo"),
                 venue=clean(d.get("container-title") or "") or "Zenodo")
    if m.get("openalex"):
        e.update(title=clean(m["openalex"]["title"]), year=str(m["openalex"]["publication_year"]))
    # manual corrections, each with a stated reason in bib_corrections.json
    if k.get("use_arxiv"):
        a_id = k["use_arxiv"]
        a = (META.get(rid, {}).get("arxiv") or {}) if META.get(rid, {}).get("arxiv", {}).get("id") == a_id else None
        e.update(venue=f"arXiv preprint arXiv:{a_id}", eprint=a_id, doi=f"10.48550/arXiv.{a_id}")
        if a:
            e.update(authors=[split_name(x) for x in a["authors"]], title=clean(a["title"]), year=a["published"][:4])
    if k.get("authors"):
        e["authors"] = [tuple(x) for x in k["authors"]]
    if k.get("first_author"):
        e["authors"] = [tuple(k["first_author"])] + e["authors"][1:]
    if k.get("swap_given_family"):
        e["authors"] = [(g, f) for f, g in e["authors"]]
    if k.get("use_pool_authors"):
        e["authors"] = [split_name(a) for a in p["authors"]]
    if k.get("authors_raw_family_first") and m.get("openalex"):
        e["authors"] = [(caps(x.split()[0]), " ".join(x.split()[1:])) for x in m["openalex"]["raw_authors"]]
    for f in ("title", "year", "volume", "number", "pages", "url", "type"):
        if k.get(f):
            e[f] = k[f]
    if k.get("url") and e["doi"].lower().startswith("10.48550/"):
        e["doi"] = ""                          # the peer-reviewed version's own link replaces the arXiv DOI
    if k.get("journal"):
        e["venue"] = k["journal"]
    if k.get("venue"):
        e["venue"] = k["venue"]
    return e


existing = open("refs.bib").read()
doi_key = {m.group(2).lower(): m.group(1) for m in re.finditer(r"@\w+\{([^,]+),(?:(?!@\w+\{).)*?doi\s*=\s*[{\"]([^}\"]+)", existing, re.S | re.I)}
KEY = {"X00001": "mohanty2016deep"}
CONTEXT = ["R02966", "R06651", "R07003"]       # recent reviews cited in the Introduction
entries = []
for rid in [r for r in INCLUDED if r != "X00001"] + CONTEXT:
    p = pool[rid]
    doi = (p.get("doi") or "").lower()
    if doi and doi in doi_key:
        KEY[rid] = doi_key[doi]
        continue
    KEY[rid] = rid
    e = record(rid)
    names = " and ".join(bibesc(f"{f}, {g}" if g else (f if " " not in f else "{" + f + "}")) for f, g in e["authors"])
    fields = [f"  author = {{{names or 'Anonymous'}}}", f"  title = {{{{{bibesc(e['title'])}}}}}", f"  year = {{{e['year']}}}"]
    if e["venue"]:
        fields.append(f"  {'booktitle' if e['type'] == 'inproceedings' else 'journal'} = {{{bibesc(e['venue'])}}}")
    for f in ("volume", "number", "pages"):
        if e[f]:
            fields.append(f"  {f} = {{{bibesc(str(e[f]))}}}")
    if e["doi"]:
        fields.append(f"  doi = {{{e['doi']}}}")
    if e["eprint"]:
        fields += [f"  eprint = {{{e['eprint']}}}", "  archivePrefix = {arXiv}"]
    if e["url"]:
        fields.append(f"  url = {{{e['url']}}}")
    entries.append(f"@{e['type']}{{{rid},\n" + ",\n".join(fields) + "\n}")
open(f"{OUT}/included.bib", "w").write("\n\n".join(entries) + "\n")
json.dump(KEY, open(f"{OUT}/keys.json", "w"), indent=0)

# ------------------------------------------------------------------ Appendix C: included studies
by = defaultdict(list)
for c in comps:
    by[c["rid"]].append(c)
crop = defaultdict(set)
for r in raw:
    if r["crop"]:
        crop[r["rid"]].add(r["crop"])
BASIS = {"INCLUDE": "FT", "INCLUDE-O": "FT-O", "INCLUDE-A": "Abs"}


def effect(cs):
    prim = [c for c in cs if not c["mit"].endswith("-only")]
    ret = [float(c["ret"]) for c in prim if c["ret"]]
    if ret:
        return f"ρ {np.median(ret):.2f}"
    dr2 = [float(c["dr2"]) for c in prim if c["dr2"]]
    if dr2:
        return f"ΔR² {np.median(dr2):.2f}"
    er = [float(c["err_ratio"]) for c in prim if c["err_ratio"]]
    if er:
        return f"error ×{np.median(er):.2f}"
    ro = [float(c["ret_o"]) for c in cs if c["ret_o"]]
    if ro:
        return f"ρ~o~ {np.median(ro):.2f}"
    return "–"


def short(s, n=34):
    s = s.replace("|", "/")
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


rows_c = []
for rid in INCLUDED:
    cs = by.get(rid, [])
    year = 2016 if rid == "X00001" else pool[rid]["year"]
    tasks = "/".join(sorted({TASK_SHORT[c["task"]] for c in cs}))
    shifts = "/".join(sorted({SHIFT_SHORT[c["cat"]] for c in cs}))
    crops = short("; ".join(sorted(crop.get(rid, []))))
    fa = "Mohanty" if rid == "X00001" else clean(pool[rid]["authors"][0])
    first = fa.split(",")[0] if "," in fa else (fa.split() or ["~"])[-1]
    first = unicodedata.normalize("NFKD", first).encode("ascii", "ignore").decode() or first
    rows_c.append(((first.lower(), year), rid, f"| @{KEY[rid]} | {tasks} | {short(crops)} | {shifts} | {len(cs)} | {effect(cs)} | "
                              f"{BASIS[dec[rid]['decision']]} |"))
rows_c.sort()
ac = [": Table C1. Studies included in the synthesis. Task: Disease (disease, pest, stress), Weed, Organ (plant and "
      "organ detection or counting), Trait, Mapping, Yield. Shift: Acq. acquisition, Loc. location, Sens. sensor or "
      "platform, Biol. biological material, Comp. compound. *k*, number of extracted comparisons. Effect: study median "
      "retention ρ (bounded metrics), ΔR², ratio of OOD to ID error, or retention relative to an oracle ρ~o~. Basis: FT "
      "full text; FT-O full text, oracle reference only; Abs abstract only.", "",
      "| Study | Task | Crop | Shift | *k* | Effect | Basis |",
      "|:" + "-" * 30 + "|:" + "-" * 13 + "|:" + "-" * 24 + "|:" + "-" * 13 + "|" + "-" * 4 + ":|:" + "-" * 11 + "|:" + "-" * 6 + "|"]
ac += [r[2] for r in rows_c]
open(f"{OUT}/appendix_c.md", "w").write("\n".join(ac) + "\n")
print(f"tables 1-5, appendix C ({len(rows_c)} studies), included.bib ({len(entries)} new entries)")
