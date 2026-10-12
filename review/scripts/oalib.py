"""Minimal OpenAlex client used by the review pipeline (stdlib only)."""
import json, os, time, urllib.parse, urllib.request, urllib.error

os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")
MAIL = ""  # no contact address is sent to any API
BASE = "https://api.openalex.org/works"

LEARN = ('("deep learning" OR "machine learning" OR "neural network" OR "neural networks" '
         'OR "convolutional" OR "vision transformer" OR "random forest")')
AGRI = ('(crop OR crops OR plant OR plants OR weed OR weeds OR fruit OR fruits OR orchard '
        'OR vineyard OR wheat OR maize OR corn OR rice OR soybean OR potato OR tomato '
        'OR cassava OR agriculture OR agricultural OR cropland OR farmland OR phenotyping)')
SHIFT = ('("domain shift" OR "domain adaptation" OR "domain generalization" '
         'OR "domain generalisation" OR "out-of-distribution" OR "distribution shift" '
         'OR "dataset shift" OR "cross-domain" OR "cross-dataset" OR "cross-region" '
         'OR "cross-site" OR "cross-season" OR "cross-year" OR "cross-location" '
         'OR "cross-sensor" OR "cross-crop" OR "cross-species" OR "unseen field" '
         'OR "unseen fields" OR "unseen region" OR "unseen regions" OR "unseen location" '
         'OR "unseen locations" OR "unseen year" OR "unseen years" OR "unseen season" '
         'OR "unseen environments" OR "leave-one-year-out" OR "leave-one-site-out" '
         'OR "leave-one-location-out" OR "leave-one-field-out" OR "spatial cross-validation" '
         'OR "spatial transferability" OR "temporal transferability" '
         'OR "spatiotemporal transferability" OR "spatial generalization" '
         'OR "temporal generalization" OR "spatiotemporal generalization" '
         'OR "lab-to-field" OR "laboratory to field" OR "in the wild" '
         'OR "test-time adaptation")')
QUERY = f"{LEARN} AND {AGRI} AND {SHIFT}"
FILTER = "publication_year:2015-2026,type:article|preprint|review"


def get(url, tries=10):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(60, 3 * (i + 1))); continue
            raise
        except Exception as e:
            last = repr(e)
            time.sleep(min(60, 3 * (i + 1)))
    raise RuntimeError(f"failed after {tries} tries ({last}): " + url[:200])


def works(filter_str, per=200, cursor="*", select=None, search=None):
    q = {"filter": filter_str, "per_page": per, "cursor": cursor}
    if select: q["select"] = select
    if search: q["search"] = search
    return get(BASE + "?" + urllib.parse.urlencode(q))


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    pos = {p: t for t, ps in inv.items() for p in ps}
    return " ".join(pos[i] for i in sorted(pos))


def slim(w):
    pl = w.get("primary_location") or {}
    src = pl.get("source") or {}
    boa = w.get("best_oa_location") or {}
    return {
        "id": w["id"].rsplit("/", 1)[-1],
        "doi": (w.get("doi") or "").replace("https://doi.org/", "") or None,
        "title": w.get("title") or w.get("display_name"),
        "year": w.get("publication_year"),
        "date": w.get("publication_date"),
        "type": w.get("type"),
        "venue": src.get("display_name"),
        "authors": [a["author"]["display_name"] for a in (w.get("authorships") or [])][:12],
        "cited_by": w.get("cited_by_count"),
        "is_oa": (w.get("open_access") or {}).get("is_oa"),
        "oa_url": (w.get("open_access") or {}).get("oa_url"),
        "pdf_url": boa.get("pdf_url"),
        "landing": boa.get("landing_page_url") or pl.get("landing_page_url"),
        "language": w.get("language"),
        "abstract": abstract(w),
        "refs": [r.rsplit("/", 1)[-1] for r in (w.get("referenced_works") or [])],
    }

EXTRA = ('("new regions" OR "new region" OR "new field conditions" OR "new environments" '
         'OR "different regions" OR "other regions" OR "different years" OR "different sites" '
         'OR "different locations" OR "future years" OR "transferred across" OR "spatial transfer" '
         'OR "temporal transfer" OR "real-world conditions" OR "non-lab" OR "data partitioning")')
QUERY2 = f"{LEARN} AND {AGRI} AND ({SHIFT[1:-1]} OR {EXTRA[1:-1]})"


def to_s2(q):
    """Translate the OpenAlex Boolean string into Semantic Scholar bulk-search syntax."""
    return q.replace(" AND ", " + ").replace(" OR ", " | ")

SHIFT_ML = ('("domain shift" OR "domain adaptation" OR "domain generalization" OR "domain generalisation" '
            'OR "out-of-distribution" OR "distribution shift" OR "dataset shift" OR "test-time adaptation" '
            'OR "unsupervised domain")')
LEARN2 = ('("deep learning" OR "deep-learning" OR "machine learning" OR "neural network" OR "neural networks" '
          'OR "convolutional" OR "vision transformer" OR "random forest" OR "computer vision" '
          'OR "semantic segmentation" OR "object detection" OR "image classification" OR "classifier" OR "classifiers")')
# Final search string (PROTOCOL.md deviation log, entry 4)
QUERY3 = f"{AGRI} AND ({SHIFT_ML[1:-1]} OR ({LEARN2} AND ({SHIFT[1:-1]} OR {EXTRA[1:-1]})))"
