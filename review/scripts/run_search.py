"""Run the protocol search (PROTOCOL.md §3.1) against OpenAlex and save every record."""
import json, sys, time, datetime, urllib.parse
from oalib import *

out = sys.argv[1]
flt = f"title_and_abstract.search:{QUERY},{FILTER}"
first = works(flt, per=1)
total = first["meta"]["count"]
print("total hits:", total)
recs, cursor = [], "*"
while cursor:
    d = works(flt, per=200, cursor=cursor)
    recs += [slim(w) for w in d["results"]]
    cursor = d["meta"].get("next_cursor")
    if not d["results"]:
        break
    time.sleep(0.4)
with open(out, "w") as fh:
    for r in recs:
        fh.write(json.dumps(r) + "\n")
meta = {"database": "OpenAlex", "date_run": datetime.date.today().isoformat(),
        "field": "title_and_abstract.search", "query": QUERY, "filter": FILTER,
        "hits_reported": total, "records_saved": len(recs),
        "url_first_page": BASE + "?" + urllib.parse.urlencode({"filter": flt, "per_page": 1})}
json.dump(meta, open(out.replace(".jsonl", ".meta.json"), "w"), indent=2)
print("saved", len(recs))
