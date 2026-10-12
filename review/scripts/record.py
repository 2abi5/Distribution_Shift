"""Append full-text decisions, extracted comparisons and appraisal ratings from JSON lines on stdin.
Each line: {"rid","decision":"INCLUDE|INCLUDE-O|EXCLUDE","reason","notes", "study", "rows":[{...}], "appraisal":{...}}
Row keys: task crop modality shift shift_desc model metric hib id ood oracle mit mit_name adapted labels id_n ood_n runs loc note
Usage: python3 scripts/record.py <<'X' ... X"""
import csv, json, os, sys
D = "extraction"
POOL = {}
for _l in [*open("search/pool_v3.jsonl"), *(open("search/pool_extra.jsonl") if __import__("os").path.exists("search/pool_extra.jsonl") else [])]:
    _r = json.loads(_l); POOL[_r["rid"]] = _r


def label(rid):
    r = POOL.get(rid, {})
    au = r.get("authors") or []
    if isinstance(au, str):
        try:
            import ast; au = ast.literal_eval(au)
        except Exception:
            au = [au]
    first = (au[0] if au else "Anon").split()[-1] if au else "Anon"
    n = len(au)
    lab = first if n == 1 else (f"{first} & {au[1].split()[-1]}" if n == 2 else f"{first} et al.")
    return f"{lab} {r.get('year', '')}"
F_DEC, F_ROW, F_APP = f"{D}/ft_decisions.csv", f"{D}/comparisons.csv", f"{D}/appraisal.csv"
DEC = ["rid", "study", "decision", "reason", "notes"]
ROW = ["rid", "study", "comp", "task", "crop", "modality", "shift", "shift_desc", "model", "metric", "hib", "id", "ood",
       "oracle", "mit", "mit_name", "adapted", "labels", "id_n", "ood_n", "runs", "loc", "note"]
APP = ["rid", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "code", "note"]


def append(path, cols, rec):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="raise")
        if new: w.writeheader()
        w.writerow({c: rec.get(c, "") for c in cols})


done = set()
if os.path.exists(F_DEC):
    done = {r["rid"] for r in csv.DictReader(open(F_DEC))}
text = "\n".join(l for l in sys.stdin.read().split("\n") if not l.lstrip().startswith("#"))
dec, pos, objs = json.JSONDecoder(), 0, []
while True:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos >= len(text):
        break
    obj, pos = dec.raw_decode(text, pos)
    objs.append(obj)
for d in objs:
    if d["rid"] in done:
        print("skip (already recorded)", d["rid"]); continue
    d["study"] = label(d["rid"])
    append(F_DEC, DEC, d)
    for i, r in enumerate(d.get("rows", []), 1):
        append(F_ROW, ROW, dict(r, rid=d["rid"], study=d.get("study", ""), comp=i))
    if d.get("appraisal"):
        append(F_APP, APP, dict(d["appraisal"], rid=d["rid"]))
    done.add(d["rid"])
    print(d["rid"], d["decision"], d.get("reason", ""), f"rows={len(d.get('rows', []))}")
