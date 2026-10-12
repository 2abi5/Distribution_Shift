"""Screening view: title + keyword-in-context windows around shift terms in the abstract."""
import json, re, sys
TERMS = ["domain shift", "domain adaptation", "domain generali", "out-of-distribution", "distribution shift",
         "dataset shift", "cross-domain", "cross-dataset", "cross-region", "cross-site", "cross-season", "cross-year",
         "cross-location", "cross-sensor", "cross-crop", "cross-species", "unseen", "leave-one", "spatial cross-validation",
         "transferab", "generaliz", "generalis", "lab-to-field", "laboratory to field", "in the wild", "test-time",
         "new region", "new field", "new environment", "different region", "other region", "different year",
         "different site", "different location", "future year", "transferred", "spatial transfer", "temporal transfer",
         "real-world condition", "non-lab", "data partitioning", "independent", "external", "another", "trained on",
         "tested on", "source domain", "target domain", "dropped", "decreas", "degrad"]
pat = re.compile("|".join(re.escape(t) for t in TERMS), re.I)
pool = [json.loads(l) for l in open(sys.argv[1])]
start, end = int(sys.argv[2]), int(sys.argv[3])
W = int(sys.argv[4]) if len(sys.argv) > 4 else 14
for p in pool[start:end]:
    t = (p.get("title") or "").replace("\n", " ")[:150]
    a = re.sub(r"\s+", " ", p.get("abstract") or "")
    words = a.split(" ")
    # character offsets -> word windows
    spans, idx = [], []
    pos = 0; starts = []
    for w in words:
        starts.append(pos); pos += len(w) + 1
    import bisect
    for m in pat.finditer(a):
        wi = bisect.bisect_right(starts, m.start()) - 1
        idx.append(wi)
    wins = []
    for wi in idx:
        lo, hi = max(0, wi - W), min(len(words), wi + W + 1)
        if wins and lo <= wins[-1][1]:
            wins[-1] = (wins[-1][0], hi)
        else:
            wins.append((lo, hi))
    snip = " … ".join(" ".join(words[lo:hi]) for lo, hi in wins[:2])
    if not a:
        snip = "[no abstract]"
    elif not wins:
        snip = "[no term] " + " ".join(words[:30])
    print(f"{p['rid'][1:]}|{t}\n   > {snip[:400]}")
