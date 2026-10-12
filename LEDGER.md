# Ledger — distribution shift in agricultural machine learning (systematic review)

venue: Technology in Society (Elsevier), review article (VENUE.md) | stage: S9 | updated: 2026-10-12 | manuscript: manuscript/review.md (template) → output/TiS_manuscript_anonymized_v1.1.{docx,pdf} + TiS_title_page_v1.1 + TiS_highlights_v1.1

## Story spine
1. TASK      — Crop-production models are evaluated on data from their training domain, then used on other fields, seasons and sensors.
2. GAP       — Primary studies report ID and OOD results in incompatible units and designs, **because** no synthesis converts them to a common effect size across tasks.
3. INSIGHT   — Retention (OOD/ID on the same model and metric) is computable for any study that reports both values, so evidence from six tasks becomes comparable.
4. METHOD    — PRISMA 2020 systematic review with citation chasing, 254 studies, 1,268 comparisons; study-level medians, cluster bootstrap, within-study contrasts; appraisal of six practice items.
5. EVIDENCE  — Median retention 0.85 (0.83 full text); acquisition, compound and sensor shifts cost most; target fine-tuning recovers 96% of the gap, UDA 39%.
6. SO WHAT   — An ID score must be read with the expected retention for the shift; OOD evaluations need a minimum reporting set (Table 6).

## Contribution claims (every number rendered from review/analysis/results.json)
| # | Claim | Type | Evidence | Location | Status |
|---|---|---|---|---|---|
| C1 | 254 studies contribute 1,268 ID–OOD comparisons | empirical | Fig. 1, Table 1, Appendix C | §3.1–3.2 | supported |
| C2 | Median retention 0.85 (95% CI 0.77–0.89; 187 studies); 0.83 in full-text studies | empirical | Table 2, Table 5 | §3.3, §3.6 | supported |
| C3 | Acquisition (0.61), compound (0.73) and sensor (0.77, n = 7) shifts retain less than location (0.88) and time (0.93) | empirical | Table 2, Fig. 2a | §3.3 | supported (sensor n = 7 stated; wording no longer ranks sensor second) |
| C4 | Within studies, compound shifts retain less than single-factor shifts (12 of 15) | comparative | within_study_contrasts | §3.3 | supported, post hoc, unadjusted p = 0.035; location < time in 12 of 14, p = 0.013; neither below the Bonferroni threshold 0.0125 (stated) |
| C5 | Weed recognition retains least (0.61); mapping (0.91) and organ detection (0.91) most | empirical | Table 2, Table 3 | §3.3 | supported |
| C6 | Fine-tuning recovers 96% of the gap, UDA 39% | empirical | Table 4, Fig. 4 | §3.4 | supported |
| C7 | 70% single run; 67% model selection not stated (204 full-text studies) | empirical | Fig. 5 | §3.5 | supported |
| C8 | Abstract-only studies report higher retention than full-text studies within task | empirical | ret_abstract_vs_fulltext_by_task | §3.6 | supported; two explanations given, neither tested |
| C9 | Transformers retain slightly more than CNNs within studies (median +0.03, 23 studies, p = 0.09) | comparative | within_study_contrasts | §3.3, §4.1 | supported, post hoc, caveat on proposed-model bias stated |

## Provenance
| Table/Figure | Source file | Script |
|---|---|---|
| Fig. 1 | manuscript/figures/counts.json | figures/make_prisma.py |
| Fig. 2–5, Tables 1–5, C1 | review/analysis/results.json, comparisons_with_effects.csv | review/scripts/synthesis.py, manuscript/make_tables.py |
| Every in-text number | review/analysis/results.json, figures/counts.json | manuscript/build.py (template rendering) |

## Gates (see readiness.json and manuscript/readiness_report.txt)
| Gate | Status | Blocking issues |
|---|---|---|
| G1 claim/evidence | PASS | — |
| G2 citations | PASS | 2026-10-02: 286 entries, 280 VERIFIED, 6 RESOLVED, 0 MISMATCH (manuscript/citation_report.md); claim support checked for all 30 citing sentences, two Introduction overstatements fixed |
| G3 venue compliance | NOT RUN | Technology in Society format met (tis_checks.json all PASS); technology-society framing added; passes only after the authors re-read the live guide (HTTP 403 to automated access) |
| G4 readiness | NOT READY (gated) | Technology in Society weighting: 68.9/100; G-TOKEN fails (9 author items, mostly title page); G-VENUE fails on scope |

## Terminology (fixed)
retention ρ · gap Δ · gap recovered g · oracle-referenced g_o · source-only · oracle · shift type (acquisition, location, time, sensor, biological, compound) · INCLUDE / INCLUDE-O / INCLUDE-A / FIG

## Open items (in order of what changes the outcome)
- [ ] Human verification: complete review/human_check/screening_check_*.xlsx and extraction_check_*.xlsx (both authors), run scripts/human_check_stats.py, report κ (protocol §5) — workbooks prepared 2026-10-02
- [ ] Double-extract the sampled comparisons (extraction_check workbooks) and correct errors; re-run `make all`
- [~] Retrieve paywalled full texts — fourth open-access pass done 2026-10-02 (all INCLUDE-A with full text and 86 E4 records re-assessed); the rest need library access (review/RETRIEVAL_LIST.csv)
- [~] FIG studies — 20 digitised or transcribed and 4 excluded on inspection (2026-10-02); 34 remain, mostly figures behind IEEE / Taylor & Francis access controls
- [x] Citation chasing of the included studies (2026-10-02; 30 studies added) — Scopus and Web of Science not searched (no licence; stated as a limitation)
- [~] Closest reviews: R02966 and R06651 read in full; R07003 from its abstract only (stated in §1)
- [x] Citation mismatches resolved — 2026-10-02 `make cites`: 286/286 verified or resolved
- [x] Re-run `make cites` with network access (Gate 2) — done 2026-10-01; result above, follow-up is the item just above
- [ ] Choose the journal; check its live guide for authors (VENUE.md)
- [ ] Fill the six [AUTHOR DECISION] items: affiliations/ORCID/corresponding author, AI-use attestation, data DOI, funding, competing interests, CRediT
- [~] Data-and-code archive for Zenodo/OSF — built 2026-10-12: `make archive` writes `../distribution_shift_review_data_and_code_v1.1.zip` (160 files, 55.8 MB; no full texts, build files or outputs) with `.zenodo.json`, `CITATION.cff` and `requirements.txt`; clean-room rebuild verified (section below). Target repository: https://github.com/2abi5/Distribution_Shift; the authors push the deposit themselves (an assistant push on 2026-10-12, commit 8a87c30, is to be replaced by the authors' own; GitHub would not let the default branch be deleted). Left for the authors: confirm the CC-BY-4.0 licence, keep the repository private until acceptance (double-anonymized review), make a GitHub release so Zenodo mints the DOI from `.zenodo.json`, then insert the DOI in the Data availability statement and `CITATION.cff`

## Layer 3 — framing citations added 2026-10-02 (opened in full text)
| Citation | Claim in manuscript | Location in source |
|---|---|---|
| galaz2021artificial | AI in agriculture can create systemic risks: algorithmic bias with allocative harms, unequal access, cascading failures | Abstract p. 1; §3 p. 4 |
| ryan2022social | Analyses of agricultural AI's social and ethical impacts place trust at the centre of adoption | p. 7 ("The value of trust is very important, and the adoption of AI within the sector...") |
| rose2018agriculture | Responsible innovation asks smart-farming developers to anticipate effects | Abstract p. 1 (anticipation, inclusion, reflexivity, responsiveness) |
| mitchell2019model | Model cards report performance across conditions and instruments, with intended use | §1 p. 1; §4.3.2 p. 4 |
| gebru2021datasheets | Datasheets document how training data were collected | §3.3 p. 6 |
| R02966 | High accuracy often reported without external, temporal or cross-site validation | Abstract and §1 (full text) |

## Data archive (2026-10-12)
Title: *Data and code for: How much performance do agricultural machine-learning models lose out of distribution? A systematic review and quantitative synthesis* (`.zenodo.json`, `CITATION.cff`; version v1.1; creators Pant, Mishra; licence CC-BY-4.0 pending the authors' confirmation).
- `make archive` zips `paper/` under the root name `distribution_shift_review/`, excluding `review/fulltext/{pdf,txt,html}` (copyright), `manuscript/build/`, `output/`, `*.out` run logs, caches and `.DS_Store`. Full texts stay local; `review/fulltext/` ships only the fetch logs, open-access metadata and `retrieved.json`.
- Fix found by the test: `review/scripts/synthesis.py` listed `fulltext/txt` to count the reports retrieved (PRISMA flow), so the archive could not rebuild without the texts. It now writes `review/fulltext/retrieved.json` (615 report ids with text longer than 2000 bytes, 506 of them with a full-text decision) when the texts are present and reads that manifest otherwise. The numbers are unchanged.
- Test: the archive was unzipped into an empty directory, `review/analysis/`, `manuscript/generated/` and the figure files were deleted, and `make all VERSION=v1.1` was run there. Byte-identical to the repository copies: `results.json`, `figures/counts.json`, the nine analysis CSVs, Tables 1–5, Appendix C, `included.bib`, `keys.json` and the five PNG figures. The SVG figures differ only in matplotlib's date stamp and element ids. All six journal format checks pass. Word files: identical document body (the files differ only in their embedded timestamps). PDFs: identical extracted text.
- Repository: https://github.com/2abi5/Distribution_Shift, pushed by the authors. To prepare a push: `make archive`, unzip, and commit the `distribution_shift_review/` contents at the repository root (a force-push replaces the 2026-10-12 placeholder commit 8a87c30). The monorepo `paper/` directory remains the working copy; the standalone repository never receives full texts, `manuscript/build/` or `output/`.
- Known content of the deposit worth a glance before upload: `manuscript/readiness_report.txt` quotes the local path of the research-pro scripts in its first line (generated by `make score`).
