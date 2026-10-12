"""Final search, OpenAlex part (PROTOCOL.md deviation log): QUERY3, resumable cursor harvest.
Usage: python3 run_search3_oa.py ../search 2026-10-02"""
import json, os, sys, time
from oalib import *

outdir, run_date = sys.argv[1], sys.argv[2]
oa_path = f"{outdir}/openalex_final_{run_date}.jsonl"
state_path = oa_path + ".cursor"
flt = f"title_and_abstract.search:{QUERY3},{FILTER}"
total = works(flt, per=1)["meta"]["count"]
cursor = open(state_path).read().strip() if os.path.exists(state_path) else "*"
seen = sum(1 for _ in open(oa_path)) if os.path.exists(oa_path) and cursor != "*" else 0
with open(oa_path, "a" if cursor != "*" else "w") as fh:
    while cursor and cursor != "DONE":
        d = works(flt, per=200, cursor=cursor)
        if not d["results"]:
            cursor = "DONE"; break
        for w in d["results"]:
            fh.write(json.dumps(slim(w)) + "\n")
        fh.flush()
        seen += len(d["results"])
        cursor = d["meta"].get("next_cursor") or "DONE"
        open(state_path, "w").write(cursor)
        print(f"{seen}/{total}", flush=True)
        time.sleep(0.5)
json.dump({"database": "OpenAlex", "date_run": run_date + " (UTC; 2026-10-01 local time, UTC-6)", "field": "title_and_abstract.search",
           "query": QUERY3, "filter": FILTER, "hits_reported": total, "records_saved": seen},
          open(f"{outdir}/openalex_final_{run_date}.meta.json", "w"), indent=2)
print("OpenAlex hits", total, "saved", seen)
