"""One-call reading view for full-text re-assessment: ftread.py output, HTML tables (fttables.py), and the sentences
needed for appraisal (data/code availability, model selection, runs/seeds, test-set sizes).
Usage (from paper/review):  python3 scripts/ftfull.py RID [--tables-max-rows 25] [--no-tables]"""
import os
import re
import subprocess
import sys

rid = sys.argv[1]
mr = sys.argv[sys.argv.index("--tables-max-rows") + 1] if "--tables-max-rows" in sys.argv else "25"
print(subprocess.run([sys.executable, "scripts/ftread.py", rid, "--max-chars", "4000"], capture_output=True, text=True).stdout)
if "--no-tables" not in sys.argv and os.path.exists(f"fulltext/html/{rid}.html"):
    print("-- HTML TABLES:")
    print(subprocess.run([sys.executable, "scripts/fttables.py", rid, "--max-rows", mr], capture_output=True, text=True).stdout[:20000])
t = " ".join(open(f"fulltext/txt/{rid}.txt", errors="ignore").read().split())
PATS = {"availability": r"(data|code) (availability|are available|is available|will be made available|can be obtained|on (reasonable )?request)|github\.com|zenodo|publicly available|open-source|open source",
        "selection": r"early stopping|validation (set|split|data)|hyper-?parameters? (were|was) (tuned|selected|optimi[sz]ed|chosen)|grid search|cross-validation|best (model|checkpoint|epoch)",
        "runs": r"random seeds?|\b\d+ (independent )?runs\b|repeated \d+ times|mean ?± ?|standard deviation|five times|ten times|\d+-fold"}
for k, p in PATS.items():
    hits = [m for m in re.finditer(r"[^.]{0,220}(" + p + r")[^.]{0,220}", t, re.I)]
    print(f"-- {k.upper()} ({len(hits)}):")
    for m in hits[:6]:
        print("  ~", m.group(0).strip()[:440])
