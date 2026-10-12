"""Resolve the protocol's sentinel studies (PROTOCOL.md §3.3) and test search recall."""
import json, sys, time, urllib.parse
from oalib import *

SENT = [
 ("Mohanty 2016", "Using deep learning for image-based plant disease detection"),
 ("Ferentinos 2018", "Deep learning models for plant disease detection and diagnosis"),
 ("Singh 2020 PlantDoc", "PlantDoc: A Dataset for Visual Plant Disease Detection"),
 ("David 2020 GWHD", "Global Wheat Head Detection (GWHD) dataset"),
 ("David 2021 GWHD", "Global Wheat Head Detection 2021: an improved dataset for benchmarking wheat head detection methods"),
 ("Xu 2020 DeepCropMapping", "DeepCropMapping: A multi-temporal deep learning approach with improved spatial generalizability for dynamic corn and soybean mapping"),
 ("Wang 2019 RF transfer", "Crop type mapping without field-level labels: Random forest transfer and unsupervised clustering techniques"),
 ("Kluger 2021 two shifts", "Two shifts for crop mapping: Leveraging aggregate crop statistics to improve satellite-based maps in new regions"),
 ("Nyborg 2022 TimeMatch", "TimeMatch: Unsupervised cross-region adaptation by temporal shift estimation"),
 ("Gogoll 2020", "Unsupervised Domain Adaptation for Transferring Plant Classification Systems to New Field Environments, Crops, and Robots"),
 ("Bosilj 2020", "Transfer learning between crop types for semantic segmentation of crops versus weeds in precision agriculture"),
 ("Morales 2023", "Using machine learning for crop yield prediction in the past or the future"),
 ("Wu 2023 MSUN", "From Laboratory to Field: Unsupervised Domain Adaptation for Plant Disease Recognition in the Wild"),
]
ids = {json.loads(l)["id"] for l in open(sys.argv[1])}
hit = 0
rows = []
for name, title in SENT:
    d = get(BASE + "?" + urllib.parse.urlencode({"filter": f"title.search:{title}", "per_page": 3}))
    best = d["results"][0] if d["results"] else None
    if not best:
        print(f"{name:26s} NOT FOUND IN OPENALEX"); continue
    w = slim(best)
    inset = w["id"] in ids
    hit += inset
    rows.append({"sentinel": name, **{k: w[k] for k in ("id", "doi", "title", "year", "venue")}, "retrieved": inset})
    print(f"{name:26s} {'RETRIEVED' if inset else 'missed   '} | {w['year']} | {w['title'][:80]} | {w['venue']} | {w['doi']}")
    time.sleep(0.3)
print(f"\nrecall: {hit}/{len(rows)}")
json.dump(rows, open(sys.argv[2], "w"), indent=1)
