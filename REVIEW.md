# Review — "How much performance do agricultural machine-learning models lose out of distribution?" → Elsevier agriculture journal (venue not fixed)

Pre-submission panel (paper-reviewer skill, full mode), run on v1.0 on 2026-10-02. The seats are a device for
covering different failure modes, not independent judgments. Findings marked **fixed** were corrected in v1.0
after the panel; everything else is open.

## Claim audit
| # | Claim (abstract / introduction) | Evidence offered | Holds? |
|---|---|---|---|
| 1 | 178 studies, 572 comparisons | Fig. 1, Table 1, App. C | yes |
| 2 | Median retention 0.82 (CI 0.74–0.89); 0.73 full text | Tables 2, 5 | yes |
| 3 | Acquisition 0.56, sensor 0.55, compound 0.67 vs location 0.87, time 0.91 | Table 2 | yes; sensor rests on 4 studies (stated) |
| 4 | "Crop mapping most" (draft) | Table 2 shows organ detection 0.95 > mapping 0.92 | **no → fixed**: abstract now gives both |
| 5 | "Highest for shifts in time" (draft) | pure biological shifts 0.93 (n = 5) | **no → fixed**: abstract no longer ranks time first |
| 6 | Ranking checked within studies | sign tests, 8/9 and 8/10 | partly: unadjusted p; **fixed** to state that neither survives Bonferroni |
| 7 | Fine-tuning 89%, UDA 28% of gap | Table 4 | yes |
| 8 | 71% single run, 77% selection unstated | Fig. 5 | yes |
| 9 | Minimum reporting set | Table 6 | yes (derived from findings, not validated) |

## Seat 1 — Venue fit
**Verdict:** accept-scope for an agricultural ML journal, conditional on the methodology blockers below.
- Systematic reviews with quantitative synthesis are in scope; the length (~7,000 words main text, 6 tables, 5 figures) is typical, but Appendix C (178 rows) will likely be moved to supplementary material.
- Declarations are incomplete (six author-only items), which is an editorial desk check at Elsevier journals.

## Seat 2 — Methodology
- §2.4: selection and extraction by one LLM-assisted reviewer, no human verification. PRISMA-based journals expect dual screening or a verified sample with κ. **Blocking.**
- §3.1: full text for 39% of studies, strongly skewed by publisher (Elsevier 11%, IEEE 18%, MDPI 68%, Frontiers 100%). The appraised set over-represents open-access venues. **Fixed** as a reported finding and limitation; the bias itself remains.
- §2.8/§3.3: four post hoc sign tests reported with unadjusted p; **fixed** (Bonferroni threshold stated).
- §3.3: bootstrap intervals for n ≤ 5 subgroups are not interpretable; **fixed** (stated in §2.8).
- §3.6: the abstract-versus-full-text gap was attributed to selective reporting only; an alternative (abstracts quote the proposed model, not a baseline) was omitted. **Fixed.**
- §2.7: retention is a ratio and saturates for accuracy-type metrics; acknowledged in §4.1 with the accuracy-only subset (0.90 vs 0.82).

## Seat 3 — Domain expert
- §1: the three closest reviews are characterised from their abstracts only. A reviewer who wrote one of them will check. **Score-raising; needs the full texts.**
- §2.3: no citation chasing; benchmark-based OOD evidence (GWHD and similar) is thin because dataset papers were missed by the search (sentinels). Stated in §4.5.
- 40 eligible studies with figure-only values are not synthesised (§3.1); a domain expert will ask whether they differ systematically.

## Seat 4 — Clarity
- Table 3 abbreviations were undefined in the caption; **fixed**.
- Figure axis labels used plain-text subscripts; **fixed** (math text).
- Decision codes (INCLUDE-A, INCLUDE-O, FIG) are defined once in §2.2/§2.4 and used consistently.

## Seat 5 — Devil's advocate
**Strongest case for rejection:** the evidence base was assembled and coded by a single automated reviewer with no
human check; 61% of candidate studies were never read in full, the unread ones are mostly from subscription
journals, 37% of included studies rest on abstract sentences that report systematically smaller gaps, and 40
eligible studies were dropped because their values are in figures. The headline 0.82 is therefore an estimate
from a non-random, partly unverified subset. The paper is honest about this, which is why the conclusion
survives at "approximate", but a methods referee can still ask for the human re-screen before review.
- Objection: the within-study contrasts are the only confound-controlled evidence and none survives multiplicity correction. Defeated only by more within-study data (digitising FIG studies may add some).
- Objection: transformer > CNN within studies may reflect proposed-method tuning. Stated in §4.1; cannot be defeated with this data.

## Editorial synthesis
**Decision:** major revision. **Confidence:** medium — a completed human verification with acceptable κ would move this to minor revision.

### Blocking
1. Human verification of selection (20% title/abstract, 100% full text, κ) and of extraction (20% double extraction) → author work, no new experiment.
2. Complete the six [AUTHOR DECISION] items and choose the journal.

### Score-raising
3. Retrieve paywalled full texts (review/RETRIEVAL_LIST.csv) and re-assess abstract-only and E4 studies.
4. Digitise the 40 FIG studies; re-run `make all`.
5. Citation chasing; Scopus and Web of Science; full-text read of the three closest reviews.
6. Re-run citation verification with network access.

### Optional
7. Move Appendix C to supplementary material if the journal limits length.

## Revision roadmap
| Priority | Fix | Type | Effort | Changes the outcome? |
|---|---|---|---|---|
| 1 | Human re-screen and double extraction with κ | verification | 2–4 days | yes — removes the main methods objection |
| 2 | Author information and declarations | writing | 1 hour | yes — desk check |
| 3 | Paywalled full texts + re-assessment | data | 3–5 days | likely — reduces retrieval bias |
| 4 | Digitise FIG studies | data | 2 days | possibly — adds within-study contrasts |
| 5 | Citation chasing, licensed databases | search | 2–3 days | possibly |

## What the authors should NOT change
- Keep both headline numbers (0.82 all studies, 0.73 full text). Dropping the abstract-only studies hides a finding; dropping the full-text figure hides the bias.
- Keep the study-level median and cluster bootstrap. An inverse-variance meta-analysis is not possible without sampling variances, and a reviewer who asks for one should be answered with §2.8.
- Keep Table 6. It is the practical contribution and each row is tied to a measured gap.


## Status after the 2 October 2026 updates (v1.0 rebuilt)
Numbers above refer to the panel's draft. Current values: 254 studies, 1,268 comparisons; median retention 0.85
(95% CI 0.77–0.89), 0.83 in full-text studies; acquisition 0.61, compound 0.73, sensor 0.77 (7 studies), location 0.88,
biological 0.91, time 0.93; fine-tuning recovers 96% of the gap, UDA 39%; 70% of appraised studies report one run.

| Roadmap item | Status |
|---|---|
| 1 Human re-screen and double extraction | **open** — workbooks prepared in review/human_check/, scoring script ready; needs both authors |
| 2 Author information and declarations | **open** — six [AUTHOR DECISION] items |
| 3 Paywalled full texts | partly done — fourth open-access pass; the rest need library access (RETRIEVAL_LIST.csv) |
| 4 Digitise FIG studies | partly done — 20 digitised or transcribed (values flagged derived, checked against text values where given), 4 excluded on inspection, 34 remain behind publisher access controls |
| 5 Citation chasing | done — 177 seeds, 11,459 new records, 30 studies added; Scopus/WoS not searched |
| 6 Citation verification | done — 286/286 verified or resolved |
| Closest reviews | two of three read in full |

Readiness (score_readiness.py, 2026-10-02): 70.4/100, gated NOT READY (G-TOKEN fails, G-VENUE not run). With the
author-only items done (declarations, journal guide, human verification with acceptable κ, third review read) the
same scorer projects about 77. Adding the remaining paywalled full texts and FIG studies, an archived data DOI and a
read-aloud pass projects about 84; 85 or more needs all of that plus a referee-proof human verification result.
