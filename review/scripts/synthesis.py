"""Quantitative synthesis for the distribution-shift review (protocol section 8).

Reads extraction/{ft_decisions,comparisons,appraisal}.csv and search/pool_v3.jsonl; writes
analysis/results.json (every number quoted in the manuscript), analysis/*.csv tables, the PRISMA
counts file and figures 2-5 for the manuscript.
Usage: python3 scripts/synthesis.py   (run from paper/review)"""
import csv, json, os, re
from collections import Counter, defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RNG = np.random.default_rng(20261002)
B = 10_000
OUT = "analysis"
FIG = "../manuscript/figures"
os.makedirs(OUT, exist_ok=True)

pool = {}
for line in [*open("search/pool_v3.jsonl"), *(open("search/pool_extra.jsonl") if __import__("os").path.exists("search/pool_extra.jsonl") else [])]:
    r = json.loads(line); pool[r["rid"]] = r
dec = {r["rid"]: r for r in csv.DictReader(open("extraction/ft_decisions.csv"))}
rows = list(csv.DictReader(open("extraction/comparisons.csv")))
app = {r["rid"]: r for r in csv.DictReader(open("extraction/appraisal.csv"))}
cand = list(csv.DictReader(open("screening/candidates.csv")))

INCLUDED = {k for k, d in dec.items() if d["decision"] in ("INCLUDE", "INCLUDE-O", "INCLUDE-A")}
FULLTEXT = {k for k, d in dec.items() if d["decision"] in ("INCLUDE", "INCLUDE-O")}
ABSTRACT = {k for k, d in dec.items() if d["decision"] == "INCLUDE-A"}
PREPRINT_VENUE = re.compile(r"arxiv|ssrn|research square|preprints\.org|zenodo|rxiv", re.I)


def year(rid):
    if rid == "X00001":
        return 2016
    return int(pool[rid].get("year") or 0)


def is_preprint(rid):
    if rid == "X00001":
        return False
    p = pool[rid]
    return bool(PREPRINT_VENUE.search(p.get("venue") or "")) or p.get("type") == "preprint"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def metric_group(r):
    m = r["metric"].lower()
    if r["hib"] == "0":
        return "error"
    if re.search(r"\br2\b|r²|r\^2", m):
        return "r2"
    if "pearson" in m or re.fullmatch(r"\s*r\s*", m):
        return "corr"
    return "bounded"


def scale(r, vals):
    """Bounded metrics on a 0-1 scale (percent-scale rows divided by 100)."""
    pct = "%" in r["metric"] or any(v is not None and abs(v) > 1.5 for v in vals)
    return [None if v is None else (v / 100 if pct else v) for v in vals]


SINGLE = ["acquisition", "location", "time", "sensor", "biological"]


def shift_cat(s):
    parts = [p for p in s.split("+") if p]
    return parts[0] if len(parts) == 1 else "compound"


def family(model):
    m = model.lower()
    if re.search(r"vit|swin|transformer|deit|segformer|dino|clip|siglip|qwen|vlm|detr|maxvit|tsvit|l-tae|ltae|pse|tae\b|attention|mamba|foundation|croma|alphaearth|prithvi|grounding|smolvlm|former|countr|tabpfn|ms-ttc|stma|edaps", m):
        return "transformer / attention"
    if re.search(r"lstm|gru|rnn|recurrent|convstar", m):
        return "recurrent"
    if re.search(r"cnn|resnet|vgg|efficientnet|mobilenet|densenet|inception|yolo|r-cnn|rcnn|u-?net|deeplab|convnext|alexnet|googlenet|centernet|squeeze|shuffle|ghost|pspnet|tempcnn|detector|segment|fcn|darknet|segnet|erfnet|espcn|ulite|dpcsn|tasselnet|visa|saf-cropnet|usta|xception|hrnet|pidnet|pmnet|psanet|edgenext|st-dres|ws-sis|\\bsan\\b", m):
        return "convolutional"
    if re.search(r"forest|svm|svr|xgboost|lightgbm|gradient boosting|catboost|logistic|decision tree|knn|elasticnet|pls|gpr|regression|kelm|gaussian|lasso|ridge|extra trees|best per trait|obia|elastic net|pixel classifier|stack", m):
        return "classical ML"
    return "other deep learning (MLP, DNN, unspecified)"


def modality(s):
    m = s.lower()
    if "uav" in m or "drone" in m:
        return "UAV"
    if re.search(r"sentinel|landsat|modis|satellite|planet|worldview|enmap|skysat|\bsar\b|gaofen|gf1|cdl|time series|aerial", m):
        return "satellite / airborne"
    if re.search(r"tabular|weather|records|statistics|soil|climate", m):
        return "tabular / weather"
    if re.search(r"hyperspectral|multispectral|thermal|spectr|nir", m):
        return "proximal spectral"
    return "proximal RGB"


def period(y):
    return "2016-2020" if y <= 2020 else ("2021-2023" if y <= 2023 else ("2024-2025" if y <= 2025 else "2026"))


def is_derived(r):
    return "derived" in (r["note"] + " " + r["loc"]).lower()


# ---------------------------------------------------------------- comparison-level effect sizes
comp = []
for r in rows:
    if r["rid"] not in INCLUDED and r["rid"] != "X00001":
        continue
    g = metric_group(r)
    idv, ood, ora, ada = (num(r[k]) for k in ("id", "ood", "oracle", "adapted"))
    if g == "bounded":
        idv, ood, ora, ada = scale(r, [idv, ood, ora, ada])
    mit = r["mit"] or "none"
    rec = dict(rid=r["rid"], study=r["study"], task=r["task"], shift=r["shift"], cat=shift_cat(r["shift"]),
               factors=[p for p in r["shift"].split("+") if p], group=g, mit=mit, fam=family(r["model"]),
               mod=modality(r["modality"]), year=year(r["rid"]), id=idv, ood=ood, oracle=ora, adapted=ada,
               labels=num(r["labels"]), derived=is_derived(r), model=r["model"], abstract=r["rid"] in ABSTRACT,
               preprint=is_preprint(r["rid"]), metric=r["metric"], desc=r["shift_desc"] + " " + r["note"])
    only = mit.endswith("-only")
    rec["primary"] = (idv is not None and ood is not None and not only)
    if rec["primary"]:
        if g == "bounded" and idv > 0:
            rec["ret"] = ood / idv; rec["gap_pp"] = 100 * (idv - ood)
        elif g == "r2":
            rec["dr2"] = idv - ood
        elif g == "error" and idv > 0:
            rec["err_ratio"] = ood / idv
        elif g == "corr":
            rec["dr"] = idv - ood
    # gap recovered (only defined when the source-only model loses performance OOD)
    if not only and mit != "none" and ada is not None and ood is not None:
        if idv is not None:
            gap = (idv - ood) if r["hib"] == "1" else (ood - idv)
            thr = 0.01
            if gap > thr:
                rec["g"] = (ada - ood) / (idv - ood)
        if ora is not None:
            gap_o = (ora - ood) if r["hib"] == "1" else (ood - ora)
            if gap_o > 0.01:
                rec["g_o"] = (ada - ood) / (ora - ood)
    if ora is not None and ood is not None and g == "bounded" and ora > 0 and not only:
        rec["ret_o"] = ood / ora
    if ora is not None and ood is not None and g == "error" and ora > 0 and not only:
        rec["err_ratio_o"] = ood / ora
    comp.append(rec)


def boot_median(vals_by_study):
    """Cluster bootstrap of the median of study-level values (one value per study)."""
    v = np.array(vals_by_study, dtype=float)
    if len(v) < 2:
        return [None, None]
    idx = RNG.integers(0, len(v), size=(B, len(v)))
    meds = np.median(v[idx], axis=1)
    return [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def summarise(vals):
    v = np.array(vals, dtype=float)
    if len(v) == 0:
        return dict(n=0)
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    lo, hi = boot_median(v)
    return dict(n=int(len(v)), median=float(med), q1=float(q1), q3=float(q3), ci_lo=lo, ci_hi=hi,
                min=float(v.min()), max=float(v.max()))


def study_values(recs, key, by=None):
    """One value per study (x level of `by`): the median of that study's comparisons."""
    d = defaultdict(list)
    for c in recs:
        if c.get(key) is None:
            continue
        levels = by(c) if by else [None]
        for lv in (levels if isinstance(levels, list) else [levels]):
            d[(c["rid"], lv)].append(c[key])
    out = defaultdict(list)
    for (rid, lv), vals in d.items():
        out[lv].append(float(np.median(vals)))
    return out


R = {}
prim = [c for c in comp if c["primary"]]
R["n_comparisons_total"] = len(comp)
R["n_comparisons_primary"] = len(prim)
R["n_studies_primary"] = len({c["rid"] for c in prim})
R["n_studies_bounded"] = len({c["rid"] for c in prim if "ret" in c})
R["n_comparisons_bounded"] = sum(1 for c in prim if "ret" in c)

# RQ1 overall
overall = study_values(prim, "ret")[None]
R["ret_overall"] = summarise(overall)
gap_overall = study_values(prim, "gap_pp")[None]
R["gap_pp_overall"] = summarise(gap_overall)
ov = np.array(overall)
R["share_studies_ret_below"] = {k: float(np.mean(ov < k)) for k in (0.9, 0.7, 0.5)}
R["share_studies_ret_above_1"] = float(np.mean(ov >= 1.0))

# by shift category (compound shifts as their own category) and by component factor
R["ret_by_shift"] = {k: summarise(v) for k, v in study_values(prim, "ret", lambda c: c["cat"]).items()}
R["ret_by_factor"] = {k: summarise(v) for k, v in study_values(prim, "ret", lambda c: c["factors"]).items()}
R["ret_by_task"] = {k: summarise(v) for k, v in study_values(prim, "ret", lambda c: c["task"]).items()}
R["ret_by_modality"] = {k: summarise(v) for k, v in study_values(prim, "ret", lambda c: c["mod"]).items()}
R["ret_by_family"] = {k: summarise(v) for k, v in study_values(prim, "ret", lambda c: c["fam"]).items()}
R["ret_by_period"] = {k: summarise(v) for k, v in study_values(prim, "ret", lambda c: period(c["year"])).items()}
lab2field = [c for c in prim if c["task"] == "D" and c["cat"] == "acquisition" and "ret" in c]
R["ret_disease_acquisition"] = summarise(study_values(lab2field, "ret")[None])
pv = [c for c in prim if "ret" in c and c["task"] == "D" and re.search(r"plantvillage", " ".join([c["study"]]), re.I)]
# regression outcomes
R["dr2_overall"] = summarise(study_values(prim, "dr2")[None])
R["dr2_by_shift"] = {k: summarise(v) for k, v in study_values(prim, "dr2", lambda c: c["cat"]).items()}
R["err_ratio_overall"] = summarise(study_values(prim, "err_ratio")[None])
R["corr_drop"] = summarise(study_values(prim, "dr")[None])
# oracle gap (target-trained reference on the same OOD test set)
R["ret_oracle"] = summarise(study_values(comp, "ret_o")[None])
R["err_ratio_oracle"] = summarise(study_values(comp, "err_ratio_o")[None])

# RQ2: gap recovered by mitigation type
mit_norm = lambda m: {"UDA": "UDA", "DG": "DG / augmentation", "FT": "target fine-tuning", "SSL": "pretraining / SSL",
                      "PT": "pretraining / SSL", "other": "other"}.get(m, m)
R["g_by_mit"] = {k: summarise(v) for k, v in study_values(comp, "g", lambda c: mit_norm(c["mit"])).items()}
R["g_overall"] = summarise(study_values(comp, "g")[None])
R["g_o_by_mit"] = {k: summarise(v) for k, v in study_values(comp, "g_o", lambda c: mit_norm(c["mit"])).items()}
R["g_o_overall"] = summarise(study_values(comp, "g_o")[None])
ft = [c for c in comp if c["mit"] == "FT" and c.get("g") is not None and c["labels"] is not None]
R["ft_labels"] = [dict(rid=c["rid"], labels=c["labels"], g=c["g"]) for c in ft]
R["n_studies_mitigation"] = len({c["rid"] for c in comp if c["mit"] != "none" and not c["mit"].endswith("-only")})
R["n_studies_mitigation_only"] = len({c["rid"] for c in comp if c["mit"].endswith("-only")})
R["n_studies_with_g"] = len({c["rid"] for c in comp if c.get("g") is not None})
R["n_studies_with_g_o"] = len({c["rid"] for c in comp if c.get("g_o") is not None})
R["share_g_below_0"] = float(np.mean(np.array(study_values(comp, "g")[None]) < 0)) if study_values(comp, "g")[None] else None

# sensitivity analyses on the overall study-level retention
def sens(filt):
    return summarise(study_values([c for c in prim if filt(c)], "ret")[None])


def appr(rid, q):
    return app.get(rid, {}).get(q, "unclear")


R["sensitivity"] = {
    "all studies (primary)": R["ret_overall"],
    "full text only (excluding abstract-only)": sens(lambda c: not c["abstract"]),
    "peer-reviewed only (excluding preprints)": sens(lambda c: not c["preprint"]),
    "excluding high concern on Q1 or Q2": sens(lambda c: appr(c["rid"], "Q1") != "high" and appr(c["rid"], "Q2") != "high"),
    "excluding derived values": sens(lambda c: not c["derived"]),
    "OOD test >= 100 samples (Q3 low)": sens(lambda c: appr(c["rid"], "Q3") == "low"),
    "accuracy-type metrics only": sens(lambda c: re.search(r"accuracy|\boa\b", c["metric"], re.I) is not None),
}

# RQ3: appraisal of full-text-assessed included studies
ft_inc = sorted(FULLTEXT | {"X00001"})
R["appraisal"] = {}
for q in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]:
    cnt = Counter(appr(rid, q) for rid in ft_inc)
    R["appraisal"][q] = {k: cnt.get(k, 0) for k in ("low", "unclear", "high")}
R["n_appraised"] = len(ft_inc)
cv_scheme = {c["rid"] for c in comp if re.search(r"random|cv\b|cross-validation|split ->|hold-out ->|grouped", c.get("shift", "") + " " + next((r["shift_desc"] for r in rows if r["rid"] == c["rid"]), ""), re.I)}

# study characteristics
inc_rows = defaultdict(list)
for c in comp:
    inc_rows[c["rid"]].append(c)
char = {"task": Counter(), "modality": Counter(), "shift": Counter(), "period": Counter(), "source": Counter()}
for rid in INCLUDED | {"X00001"}:
    cs = inc_rows.get(rid, [])
    for k, f in (("task", lambda c: c["task"]), ("modality", lambda c: c["mod"]), ("shift", lambda c: c["cat"])):
        for v in {f(c) for c in cs}:
            char[k][v] += 1
    char["period"][period(year(rid))] += 1
    char["source"]["abstract only" if rid in ABSTRACT else ("preprint" if is_preprint(rid) else "peer-reviewed (full text)")] += 1
R["characteristics"] = {k: dict(sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))) for k, v in char.items()}
R["n_included"] = len(INCLUDED | {"X00001"})
R["n_included_fulltext"] = len(FULLTEXT | {"X00001"})
R["n_included_abstract"] = len(ABSTRACT)
R["n_include_o"] = sum(1 for d in dec.values() if d["decision"] == "INCLUDE-O")
R["n_fig"] = sum(1 for d in dec.values() if d["decision"] == "FIG")
R["n_studies_cv_scheme"] = None  # filled in manuscript from extraction notes if needed

# PRISMA counts: database records (R...) and other methods (citation chasing C..., sentinels S..., X00001)
OTHER = lambda rid: rid[0] in "CSX"
nondup = [c for c in cand if not c["dup_of"]]
# Full texts are copyrighted and are not in the data archive: with fulltext/txt present, the list of retrieved reports
# (text longer than 2000 bytes) is written to fulltext/retrieved.json; without it, that manifest is read instead.
if os.path.isdir("fulltext/txt"):
    have = sorted(f[:-4] for f in os.listdir("fulltext/txt") if os.path.getsize(f"fulltext/txt/{f}") > 2000)
    json.dump(have, open("fulltext/retrieved.json", "w"), indent=0)
else:
    have = json.load(open("fulltext/retrieved.json"))
retrieved = {d for d in dec if d in set(have)}
retrieved.add("X00001")
ft_dec = [d for k, d in dec.items() if k in retrieved and not OTHER(k)]
ab_dec = [d for k, d in dec.items() if k not in retrieved and not OTHER(k)]
oft_dec = [d for k, d in dec.items() if k in retrieved and OTHER(k)]
oab_dec = [d for k, d in dec.items() if k not in retrieved and OTHER(k)]
reason = lambda d: d["reason"] if d["decision"] == "EXCLUDE" else d["decision"]
R["prisma"] = dict(sought=len(cand), studies=len(nondup), retrieved=len(ft_dec), not_retrieved=len(ab_dec),
                   ft_outcomes=dict(Counter(reason(d) for d in ft_dec)), abstract_outcomes=dict(Counter(reason(d) for d in ab_dec)),
                   other_retrieved=len(oft_dec), other_not_retrieved=len(oab_dec),
                   other_ft_outcomes=dict(Counter(reason(d) for d in oft_dec)), other_abstract_outcomes=dict(Counter(reason(d) for d in oab_dec)))
flow = json.load(open("screening/chase_flow.json"))
counts = json.load(open(f"{FIG}/counts.json"))
p = R["prisma"]
fo, ao, ofo, oao = p["ft_outcomes"], p["abstract_outcomes"], p["other_ft_outcomes"], p["other_abstract_outcomes"]
excl = lambda o: {k: v for k, v in sorted(o.items(), key=lambda kv: (-kv[1], kv[0])) if k not in ("INCLUDE", "INCLUDE-O", "INCLUDE-A", "FIG")}
inc = lambda o: o.get("INCLUDE", 0) + o.get("INCLUDE-O", 0)
counts = {k: counts[k] for k in ("openalex", "s2", "earlier", "duplicates", "screened", "excluded_ta", "sought", "studies", "dup_reports")}
counts.update({
    "retrieved": p["retrieved"], "not_retrieved": p["not_retrieved"],
    "ft_excluded": excl(fo), "ft_excluded_total": sum(excl(fo).values()),
    "ft_fig": fo.get("FIG", 0), "ft_included": inc(fo), "ft_include_o": fo.get("INCLUDE-O", 0),
    "abs_excluded": excl(ao), "abs_excluded_total": sum(excl(ao).values()), "abs_included": ao.get("INCLUDE-A", 0),
    "chase_identified": flow["new_after_dedup_against_pool"], "chase_seeds": flow["seeds_included_studies"],
    "chase_prefilter_removed": flow["removed_by_prefilter"], "chase_screened": flow["screened_ta"],
    "chase_excluded_ta": flow["screened_ta"] - flow["ta_included"], "chase_sought": flow["ta_included"],
    "sentinel_sought": len(flow["sentinel_reports_sought_directly"]), "other_dup_reports": len(flow["duplicate_reports"]),
    "other_retrieved": p["other_retrieved"], "other_not_retrieved": p["other_not_retrieved"],
    "other_ft_excluded": excl(ofo), "other_ft_excluded_total": sum(excl(ofo).values()), "other_ft_fig": ofo.get("FIG", 0),
    "other_ft_included": inc(ofo), "other_abs_excluded_total": sum(excl(oao).values()), "other_abs_included": oao.get("INCLUDE-A", 0),
    "other_included": inc(ofo) + oao.get("INCLUDE-A", 0),
    "included": R["n_included"],
})
json.dump(counts, open(f"{FIG}/counts.json", "w"), indent=2)

json.dump(R, open(f"{OUT}/results.json", "w"), indent=1, default=float)

# ---------------------------------------------------------------- tables (CSV; the manuscript tables are built from these)
def table(name, d, label):
    with open(f"{OUT}/{name}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([label, "studies", "median", "Q1", "Q3", "CI_lo", "CI_hi"])
        for k, s in sorted(d.items(), key=lambda kv: -kv[1]["n"]):
            if s["n"]:
                w.writerow([k, s["n"], f"{s['median']:.3f}", f"{s['q1']:.3f}", f"{s['q3']:.3f}",
                            "" if s["ci_lo"] is None else f"{s['ci_lo']:.3f}", "" if s["ci_hi"] is None else f"{s['ci_hi']:.3f}"])


table("ret_by_shift", R["ret_by_shift"], "shift"); table("ret_by_factor", R["ret_by_factor"], "factor")
table("ret_by_task", R["ret_by_task"], "task"); table("ret_by_modality", R["ret_by_modality"], "modality")
table("ret_by_family", R["ret_by_family"], "model family"); table("ret_by_period", R["ret_by_period"], "period")
table("g_by_mit", R["g_by_mit"], "mitigation"); table("sensitivity", R["sensitivity"], "analysis")

# comparison-level extraction table (supplement)
with open(f"{OUT}/comparisons_with_effects.csv", "w", newline="") as fh:
    keys = ["rid", "study", "model", "task", "shift", "cat", "mod", "fam", "metric", "group", "id", "ood", "oracle", "mit", "adapted",
            "labels", "ret", "gap_pp", "dr2", "err_ratio", "g", "g_o", "ret_o", "abstract", "preprint", "derived"]
    w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader()
    for c in comp:
        w.writerow({k: (round(c[k], 4) if isinstance(c.get(k), float) else c.get(k, "")) for k in keys})

# ---------------------------------------------------------------- figures
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})


def strip(ax, groups, labels, title):
    data = [(labels.get(k, k), v) for k, v in groups.items() if len(v) > 0]
    data.sort(key=lambda t: np.median(t[1]), reverse=True)
    for i, (lab, v) in enumerate(data):
        y = RNG.normal(i, 0.07, size=len(v))
        ax.scatter(v, y, s=9, alpha=0.55, color="#3B6E8F", edgecolors="none", zorder=2)
        s = summarise(v)
        ax.plot([s["median"]] * 2, [i - 0.3, i + 0.3], color="black", lw=1.6, zorder=3)
        if s["ci_lo"] is not None:
            ax.plot([s["ci_lo"], s["ci_hi"]], [i, i], color="#B03A2E", lw=1.4, zorder=4)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([f"{d[0]}  (n = {len(d[1])})" for d in data], fontsize=7.5)
    ax.invert_yaxis()
    ax.axvline(1.0, color="grey", lw=0.6, ls="--", zorder=1)
    ax.set_xlim(-0.02, 1.2)
    ax.set_title(title, fontsize=8.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)


SHIFT_LABEL = {"acquisition": "Acquisition (lab to field, imaging)", "location": "Location", "time": "Time (season, year)",
               "sensor": "Sensor or platform", "biological": "Biological (cultivar, species)", "compound": "Compound (two or more factors)"}
TASK_LABEL = {"D": "Disease, pest, abiotic stress", "W": "Weed and crop discrimination", "O": "Organ detection and counting",
              "P": "Phenotypic traits", "M": "Crop-type and cropland mapping", "Y": "Yield"}
fig, axes = plt.subplots(2, 1, figsize=(6.3, 5.4), gridspec_kw={"height_ratios": [6, 5]})
strip(axes[0], study_values(prim, "ret", lambda c: c["cat"]), SHIFT_LABEL, "(a) By shift type")
strip(axes[1], study_values(prim, "ret", lambda c: c["task"]), TASK_LABEL, "(b) By task")
axes[1].set_xlabel(r"Retention  $m_\mathrm{OOD}\,/\,m_\mathrm{ID}$  (one value per study; bounded metrics)")
fig.tight_layout(h_pad=1.2)
fig.savefig(f"{FIG}/fig2_retention.png", dpi=600, bbox_inches="tight"); fig.savefig(f"{FIG}/fig2_retention.svg", bbox_inches="tight")
plt.close(fig)

# ID vs OOD scatter (comparison level, bounded metrics)
fig, ax = plt.subplots(figsize=(4.9, 3.5))
colors = {"acquisition": "#B03A2E", "location": "#2E86C1", "time": "#229954", "sensor": "#7D3C98", "biological": "#CA6F1E", "compound": "#566573"}
for cat, col in colors.items():
    pts = [(c["id"], c["ood"]) for c in prim if "ret" in c and c["cat"] == cat]
    if pts:
        a = np.array(pts)
        ax.scatter(a[:, 0], a[:, 1], s=8, alpha=0.6, color=col, label=f"{cat} ({len(pts)})", edgecolors="none")
xs = np.linspace(0, 1, 50)
for k, ls in ((1.0, "-"), (0.9, "--"), (0.7, ":"), (0.5, "-.")):
    ax.plot(xs, k * xs, color="grey", lw=0.6, ls=ls)
    ax.text(1.0, k, f"{k:g}", fontsize=6.5, color="grey", ha="left", va="center")
ax.set_xlim(0, 1.04); ax.set_ylim(0, 1.04)
ax.set_xlabel("In-distribution value (0-1 scale)"); ax.set_ylabel("Out-of-distribution value (0-1 scale)")
ax.legend(fontsize=6.3, frameon=False, loc="upper left", bbox_to_anchor=(1.06, 1.0), title="Shift (comparisons)",
          title_fontsize=6.5)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{FIG}/fig3_id_ood.png", dpi=600, bbox_inches="tight"); fig.savefig(f"{FIG}/fig3_id_ood.svg", bbox_inches="tight")
plt.close(fig)

# gap recovered by mitigation type
fig, ax = plt.subplots(figsize=(5.6, 2.6))
gm = study_values(comp, "g", lambda c: mit_norm(c["mit"]))
data = sorted([(k, v) for k, v in gm.items() if v], key=lambda t: np.median(t[1]), reverse=True)
for i, (lab, v) in enumerate(data):
    vv = np.clip(v, -1.0, 2.0)
    ax.scatter(vv, RNG.normal(i, 0.06, len(vv)), s=12, alpha=0.6, color="#3B6E8F", edgecolors="none", zorder=2)
    s = summarise(v)
    ax.plot([s["median"]] * 2, [i - 0.3, i + 0.3], color="black", lw=1.6, zorder=3)
    if s["ci_lo"] is not None:
        ax.plot([s["ci_lo"], s["ci_hi"]], [i, i], color="#B03A2E", lw=1.4, zorder=4)
ax.axvline(0, color="grey", lw=0.6); ax.axvline(1, color="grey", lw=0.6, ls="--")
ax.set_yticks(range(len(data))); ax.set_yticklabels([f"{d[0]}  (n = {len(d[1])})" for d in data], fontsize=7.5)
ax.invert_yaxis()
ax.set_xlabel(r"Gap recovered  $g = (m_\mathrm{adapted} - m_\mathrm{source})\,/\,(m_\mathrm{ID} - m_\mathrm{source})$  (one value per study)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{FIG}/fig4_gap_recovered.png", dpi=600, bbox_inches="tight"); fig.savefig(f"{FIG}/fig4_gap_recovered.svg", bbox_inches="tight")
plt.close(fig)

# appraisal stacked bars
items = {"Q1": "Q1 Domain separation", "Q2": "Q2 Model selection", "Q3": "Q3 OOD test size >= 100", "Q4": "Q4 Label consistency",
         "Q5": "Q5 Run-to-run variability", "Q6": "Q6 Code or data available"}
fig, ax = plt.subplots(figsize=(5.4, 2.6))
n = R["n_appraised"]
for i, (q, lab) in enumerate(items.items()):
    left = 0
    for k, col in (("low", "#2E8B57"), ("unclear", "#D4AC0D"), ("high", "#B03A2E")):
        v = R["appraisal"][q][k] / n
        ax.barh(i, v, left=left, color=col, edgecolor="white", height=0.7, label=k if i == 0 else None)
        if v > 0.06:
            ax.text(left + v / 2, i, f"{R['appraisal'][q][k]}", ha="center", va="center", fontsize=6.5, color="white")
        left += v
ax.set_yticks(range(len(items))); ax.set_yticklabels(items.values(), fontsize=7); ax.invert_yaxis()
ax.set_xlabel(f"Share of full-text studies (n = {n})"); ax.set_xlim(0, 1)
ax.legend(ncol=3, fontsize=7, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), title="Concern", title_fontsize=7)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{FIG}/fig5_appraisal.png", dpi=600, bbox_inches="tight"); fig.savefig(f"{FIG}/fig5_appraisal.svg", bbox_inches="tight")
plt.close(fig)
# ---------------------------------------------------------------- confounding checks (computed after the figures so the
# bootstrap draws above are unchanged)
from math import comb


def sign_test(diffs):
    """Exact two-sided sign test; ties dropped."""
    k, n = sum(d < 0 for d in diffs), sum(d != 0 for d in diffs)
    if n == 0:
        return None
    tail = sum(comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


# task x shift cross-tabulation (one value per study x cell)
tx = study_values(prim, "ret", lambda c: f"{c['task']}|{c['cat']}")
R["ret_by_task_shift"] = {k: summarise(v) for k, v in tx.items()}
# within-study contrasts: studies reporting two shift categories; difference of the study's medians (first - second)
ws = defaultdict(lambda: defaultdict(list))
for c in prim:
    if "ret" in c:
        ws[c["rid"]][c["cat"]].append(c["ret"])
contr = {}
for a, b in (("compound", "single"), ("location", "time")):
    diffs = []
    for rid, v in ws.items():
        if a == "compound":
            singles = [np.median(x) for k, x in v.items() if k != "compound"]
            if "compound" in v and singles:
                diffs.append(float(np.median(v["compound"]) - np.median(singles)))
        elif a in v and b in v:
            diffs.append(float(np.median(v[a]) - np.median(v[b])))
    contr[f"{a} - {b}"] = dict(n=len(diffs), median_diff=float(np.median(diffs)) if diffs else None,
                               n_first_lower=sum(d < 0 for d in diffs), p_sign=sign_test(diffs))
wf = defaultdict(lambda: defaultdict(list))
for c in prim:
    if "ret" in c:
        wf[c["rid"]][c["fam"]].append(c["ret"])
for a, b in (("transformer / attention", "convolutional"), ("classical ML", "convolutional")):
    diffs = [float(np.median(v[a]) - np.median(v[b])) for v in wf.values() if a in v and b in v]
    contr[f"{a} - {b}"] = dict(n=len(diffs), median_diff=float(np.median(diffs)) if diffs else None,
                               n_first_lower=sum(d < 0 for d in diffs), p_sign=sign_test(diffs))
R["within_study_contrasts"] = contr
# abstract-only versus full-text studies within task
R["ret_abstract_vs_fulltext_by_task"] = {
    f"{t}|{'abstract' if flag else 'full text'}": summarise(study_values([c for c in prim if c["task"] == t and c["abstract"] == flag], "ret")[None])
    for t in ("D", "M", "W") for flag in (True, False)}
R["id_median_abstract"] = float(np.median(study_values([c for c in prim if c["abstract"]], "id")[None]))
R["id_median_fulltext"] = float(np.median(study_values([c for c in prim if not c["abstract"] and "ret" in c], "id")[None]))
# included studies without a primary (ID and OOD, source-only) comparison
R["n_included_without_primary"] = len((INCLUDED | {"X00001"}) - {c["rid"] for c in prim})
R["n_studies_regression_only"] = len({c["rid"] for c in prim} - {c["rid"] for c in prim if "ret" in c})
# post hoc: laboratory-to-field disease studies trained on PlantVillage versus other source data
pvflag = lambda c: re.search(r"plantvillage|\bPV\b", c["desc"], re.I) is not None
R["posthoc_disease_acq_plantvillage"] = summarise(study_values([c for c in lab2field if pvflag(c)], "ret")[None])
R["posthoc_disease_acq_other_source"] = summarise(study_values([c for c in lab2field if not pvflag(c)], "ret")[None])
R["posthoc_studies_plantvillage_source"] = len({c["rid"] for c in prim if "ret" in c and pvflag(c)})
# full-text retrieval by publisher (DOI prefix): retrieval relied on open-access copies
def publisher(rid):
    p = pool[rid]; doi = (p.get("doi") or "").lower(); v = (p.get("venue") or "").lower()
    if "arxiv" in v or doi.startswith("10.48550"):
        return "arXiv"
    return {"10.1016": "Elsevier", "10.1109": "IEEE", "10.3390": "MDPI", "10.3389": "Frontiers", "10.1007": "Springer"}.get(doi[:7], "other")


studies_all = [r["rid"] for r in nondup]
R["retrieval_by_publisher"] = {}
for pub_ in ("Elsevier", "IEEE", "Springer", "MDPI", "Frontiers", "arXiv", "other"):
    ids = [rid for rid in studies_all if publisher(rid) == pub_]
    R["retrieval_by_publisher"][pub_] = dict(n=len(ids), retrieved=sum(rid in retrieved for rid in ids))
cl = {c["rid"] for c in prim if "ret" in c and c["fam"] == "classical ML"}
R["classical_ml_studies"] = len(cl)
R["classical_ml_satellite_mapping"] = len({c["rid"] for c in prim if "ret" in c and c["fam"] == "classical ML"
                                          and c["task"] == "M" and c["mod"] == "satellite / airborne"})
R["publication"] = dict(sorted(Counter("preprint" if is_preprint(rid) else "peer-reviewed" for rid in INCLUDED | {"X00001"}).items(), key=lambda kv: (-kv[1], kv[0])))
R["n_comparisons_by_basis"] = dict(Counter("abstract" if c["abstract"] else "full text" for c in comp))
R["share_g_below_0_study_by_mitigation"] = float(np.mean(np.concatenate([np.array(v) for v in study_values(comp, "g", lambda c: mit_norm(c["mit"])).values()]) < 0))
json.dump(R, open(f"{OUT}/results.json", "w"), indent=1, default=float)
print(json.dumps({k: R[k] for k in ("n_included", "n_studies_primary", "n_studies_bounded", "n_comparisons_bounded", "ret_overall",
                                    "within_study_contrasts", "n_included_without_primary", "n_studies_regression_only")}, indent=1))
