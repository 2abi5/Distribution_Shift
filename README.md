# Data and code for: How much performance do agricultural machine-learning models lose out of distribution? A systematic review and quantitative synthesis

Abinash Pant and Binayak Prakash Mishra. Protocol fixed 1 October 2026; searches run 1–2 October 2026; manuscript v1.1
prepared for *Technology in Society* (Elsevier, review article; `VENUE.md`). Every number in the manuscript is rendered
from `review/analysis/results.json`, which `review/scripts/synthesis.py` computes from the extraction tables.
Repository: https://github.com/2abi5/Distribution_Shift (data and code; the full texts of the included studies are not
redistributed). Releases are archived on Zenodo with the metadata in `.zenodo.json`.

## Deliverables (`output/`, v1.1; built by `make paper`, not part of the data archive)
| File | Contents |
|---|---|
| `TiS_manuscript_anonymized_v1.1.docx` / `.pdf` | Anonymized manuscript (APA 7 references, line and page numbers, Tables 1–6, Figs 1–5, Appendices A–D) |
| `TiS_title_page_v1.1.docx` / `.pdf` | Title page with authors and declarations (`[AUTHOR DECISION]` items still open) |
| `TiS_highlights_v1.1.docx` | Five highlights, at most 85 characters each |

## Layout
| Path | Contents |
|---|---|
| `review/PROTOCOL.md` | Protocol fixed on 2026-10-01 before searching, with the dated deviation log |
| `review/search/` | OpenAlex and Semantic Scholar exports with their query metadata, citation-chasing records (`chase_2026-10-02.jsonl`), deduplicated pools (`pool_v3.jsonl` is the one used; `pool_extra.jsonl` adds the chased records) |
| `review/screening/` | Title/abstract decisions and candidates (`candidates.csv`, `ta_include.txt`, `chase_ta_include.txt`), duplicate links, PRISMA flow counts for the chase (`chase_flow.json`), keyword-in-context extracts |
| `review/extraction/` | Full-text and abstract-level decisions (`ft_decisions.csv`), one row per ID–OOD comparison with its source location (`comparisons.csv`), appraisal (`appraisal.csv`), reassessment log, extraction rules (`RULES.md`) |
| `review/analysis/` | `results.json` (every number in the paper), `comparisons_with_effects.csv`, summary tables by shift, task, modality, family, factor and period, sensitivity analyses |
| `review/RETRIEVAL_LIST.csv` | Studies whose full text could not be retrieved, in priority order |
| `review/human_check/` | Blind second-reviewer workbooks for screening and extraction (both authors), sampling key, `human_check_stats.py` output |
| `review/fulltext/` | Fetch logs and open-access metadata only. The full texts themselves (`pdf/`, `txt/`, `html/`) are copyrighted and are not redistributed |
| `review/scripts/` | Search (`run_search*.py`), deduplication, citation chasing, retrieval, recording, reassessment, human-check workbooks, and `synthesis.py` |
| `manuscript/review.md` | Manuscript template: `{{ ... }}` expressions are filled from `results.json` at build time, so no number is typed by hand; `title_page.md`, `highlights.md` |
| `manuscript/make_tables.py`, `figures/make_prisma.py` | Tables 1–5, Appendix C, the included-study bibliography (`generated/`) and Fig. 1 |
| `manuscript/build.py` | Renders the template and produces the Word and PDF files; checks the journal's format rules (`build/tis_checks.json`) |
| `manuscript/refs.bib`, `bib_metadata.json`, `bib_corrections.json`, `citation_report.md` | Reference list, Crossref metadata for the included studies, manual corrections, citation verification report |
| `LEDGER.md`, `REVIEW.md`, `readiness.json`, `venue_registry.json` | Claim–evidence ledger, adversarial pre-submission review, readiness scorecard, venue profile |
| `.zenodo.json`, `CITATION.cff`, `requirements.txt`, `Makefile` | Archive metadata, pinned environment, build targets |

## Rebuild
Run from this directory (`paper/` in the authors' working tree; the root of the `Distribution_Shift` repository).
```bash
make all                   # synthesis -> results.json, figures 1-5 -> tables -> Word and PDF (VERSION=v1.1)
make check S=<research-pro scripts>   # prose metrics, citation verification (needs network), gate tokens
make score S=<research-pro scripts>   # gated readiness verdict
make archive               # data-and-code zip for Zenodo/OSF, written to the parent directory (no full texts, build files or outputs)
```
Needs Python 3.10 with the packages in `requirements.txt` (pandoc 3.9 comes with pypandoc) and Google Chrome or
Chromium for the PDFs. `synthesis.py` uses a fixed bootstrap seed: a clean-room rebuild from the archive reproduces
`results.json` byte for byte.

## Status (2026-10-12)
Readiness: **NOT READY (gated)**, 73.0/100 (`manuscript/readiness_report.txt`). What remains is listed in `LEDGER.md`
under Open items; the items that change the outcome are:

1. Human verification of study selection and data extraction (protocol §5): the review was screened and extracted by one
   LLM-assisted reviewer; the blind workbooks in `review/human_check/` are prepared but not yet filled.
2. The `[AUTHOR DECISION]` items: affiliations/ORCID/corresponding author, AI-use attestation, funding, competing
   interests, CRediT, author biographies, and the archive DOI for the data availability statement (upload the
   `make archive` zip, then insert the DOI).
3. Full texts of paywalled studies (`review/RETRIEVAL_LIST.csv`), the 34 figure-only studies still to digitise, and
   Scopus/Web of Science searches (no licence; stated as a limitation).
4. Re-reading the live Guide for Authors (automated access was refused) and the journal's scope fit (`VENUE.md`).
