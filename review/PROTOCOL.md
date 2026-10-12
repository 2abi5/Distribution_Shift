# Review protocol — distribution shift in agricultural machine learning

Fixed: 2026-10-01, before any search was run. Deviations are logged at the end of
this file with date and reason; nothing above the deviation log is edited after
searching starts.

Registration: `[AUTHOR DECISION]` register this protocol on OSF Registries before
submission and cite the DOI in §2.

## 1. Review questions

Population/domain (D): supervised machine-learning models built for crop-production
tasks — (a) disease, pest and abiotic-stress recognition; (b) weed/crop
discrimination; (c) detection, counting or segmentation of plants, organs or
fruits; (d) plant phenotypic trait estimation; (e) crop-type and cropland mapping;
(f) crop yield estimation or forecasting.

Comparison (T vs C): the same trained model evaluated on data from a domain not
seen in training (out-of-distribution, OOD) versus held-out data from the training
domain (in-distribution, ID).

Outcome (O): change in the task metric between ID and OOD evaluation.

- **RQ1 (magnitude).** How much performance is lost under OOD evaluation, and how
  does the loss vary with shift type (acquisition setting, location, time,
  sensor/platform, biological material) and task?
- **RQ2 (mitigation).** Where studies apply a mitigation (domain adaptation, domain
  generalisation/augmentation, target-domain fine-tuning, large-scale pretraining),
  what fraction of the gap is recovered, and with how many target-domain labels?
- **RQ3 (practice).** How are OOD evaluations designed and reported: domain
  separation, model selection, test-set size, run-to-run variability, and
  code/data availability?

## 2. Information sources

- **OpenAlex** (api.openalex.org), queried 2026-10-01. Chosen because it indexes
  Crossref, PubMed, arXiv and institutional repositories, is free, and its queries
  are exactly reproducible. Searched field: title and abstract
  (`title_and_abstract.search`).
- **Citation chasing**: one round of backward (reference lists) and forward
  (citing works) chasing on every included study, through OpenAlex
  `referenced_works` and `cites:` filters.
- **Search validation**: a sentinel set of known eligible studies (§3.3), listed
  before searching; recall of the search string on this set is reported.
- Licensed indexes (Scopus, Web of Science) were not accessible to the drafting
  pipeline. `[AUTHOR DECISION]` re-run the strings in Scopus and Web of Science and
  screen the non-overlapping records before submission.

## 3. Search

### 3.1 Strings (verbatim)

```
LEARN = ("deep learning" OR "machine learning" OR "neural network" OR "neural networks"
         OR "convolutional" OR "vision transformer" OR "random forest")
AGRI  = (crop OR crops OR plant OR plants OR weed OR weeds OR fruit OR fruits OR orchard
         OR vineyard OR wheat OR maize OR corn OR rice OR soybean OR potato OR tomato
         OR cassava OR agriculture OR agricultural OR cropland OR farmland OR phenotyping)
SHIFT = ("domain shift" OR "domain adaptation" OR "domain generalization"
         OR "domain generalisation" OR "out-of-distribution" OR "distribution shift"
         OR "dataset shift" OR "cross-domain" OR "cross-dataset" OR "cross-region"
         OR "cross-site" OR "cross-season" OR "cross-year" OR "cross-location"
         OR "cross-sensor" OR "cross-crop" OR "cross-species" OR "unseen field"
         OR "unseen fields" OR "unseen region" OR "unseen regions" OR "unseen location"
         OR "unseen locations" OR "unseen year" OR "unseen years" OR "unseen season"
         OR "unseen environments" OR "leave-one-year-out" OR "leave-one-site-out"
         OR "leave-one-location-out" OR "leave-one-field-out" OR "spatial cross-validation"
         OR "spatial transferability" OR "temporal transferability"
         OR "spatiotemporal transferability" OR "spatial generalization"
         OR "temporal generalization" OR "spatiotemporal generalization"
         OR "lab-to-field" OR "laboratory to field" OR "in the wild"
         OR "test-time adaptation")
QUERY = LEARN AND AGRI AND SHIFT
```

Filters: `publication_year:2015-2026`; types article, preprint, review (reviews are
retrieved only to mine their reference lists, then excluded).

### 3.2 Date range and language

1 January 2015 to the search date. 2015 is the year convolutional networks entered
plant phenotyping and disease recognition; models before it rarely report
cross-domain tests. English-language records only — a stated source of bias.

### 3.3 Sentinel studies (fixed before searching)

Studies the search must retrieve if it is adequate. Each is checked against its
Crossref/OpenAlex record before use:

1. Mohanty, Hughes & Salathé 2016 — PlantVillage CNN; tested on images from other sources
2. Ferentinos 2018 — plant disease CNNs; laboratory-to-field tests
3. Singh et al. 2020 — PlantDoc field dataset
4. David et al. 2020 / 2021 — Global Wheat Head Detection
5. Xu et al. 2020 — DeepCropMapping, spatial generalisability
6. Wang, Azzari & Lobell 2019 — crop-type mapping transfer without field labels
7. Kluger et al. 2021 — two shifts for crop mapping in new regions
8. Nyborg et al. 2022 — TimeMatch cross-region adaptation
9. Gogoll et al. 2020 — unsupervised adaptation of plant classifiers to new fields, crops and robots
10. Bosilj et al. 2020 — crop-to-crop transfer for crop/weed segmentation
11. Morales & Villalobos 2023 — yield prediction "in the past or the future"
12. Wu et al. 2023 (Plant Phenomics) — laboratory-to-field unsupervised adaptation (MSUN)

## 4. Eligibility

### Include (all must hold)
- **I1** Primary empirical study that trains a supervised ML model (classical or
  deep) for a task in §1(a)–(f).
- **I2** Reports performance on an ID test set **and** on at least one OOD test
  set, with the same metric and the same label space (or a reported common
  subset). The OOD domain differs from training by an identifiable factor:
  acquisition setting (controlled/laboratory → field), location (field, site,
  region, country), time (season, year), sensor/platform (camera, device, UAV,
  satellite), or biological material (cultivar, species, growth stage).
- **I3** The source-only (unadapted) model's OOD result is reported, so the gap is
  computable.

### Exclude
- **E1** Livestock, aquaculture, forestry, post-harvest/food processing, soil-only
  mapping, generic land cover without crop classes.
- **E2** Shift created only by synthetic perturbation (noise, blur, simulated
  weather) or by training on synthetic images and testing on real ones.
- **E3** Random or k-fold splits only; no domain-defined hold-out.
- **E4** Reviews, editorials, theses with a published version, non-English records,
  records whose full text cannot be retrieved **and** whose abstract lacks both the
  ID and the OOD value.
- **E5** OOD label space disjoint from training with no overlapping-class result.

Preprints are eligible; a preprint with a peer-reviewed version is replaced by
that version. A sensitivity analysis excludes preprints.

## 5. Screening

Two stages: title/abstract, then full text. Records were screened against §4 by an
LLM-assisted screener (Claude, Anthropic; prompts = the criteria above),
which records a decision and a criterion code for every record.

`[TBD]` Human verification before submission: the author independently re-screens a
random 20% of title/abstract decisions and 100% of full-text decisions; report
Cohen's κ and resolve disagreements by discussion. Until this is done the screening
is single-screener and must be reported as such.

## 6. Data extraction (one row per ID–OOD comparison)

study id · DOI · year · venue · peer-reviewed (y/n) · task (a–f) · crop(s) ·
modality (RGB proximal, multispectral/hyperspectral proximal, UAV, satellite,
tabular/weather) · shift type (acquisition / location / time / sensor / biological;
multiple allowed) · shift description · model family · training-set size · metric ·
ID value · OOD value (source-only) · mitigation type (none / unsupervised domain
adaptation / domain generalisation or augmentation / target fine-tuning with k
labels / large-scale pretraining) · adapted OOD value · target labels used ·
target-trained ("oracle") value if reported · ID test size · OOD test size ·
number of runs · code available · data available · source location (table/figure
in the study).

Every extracted number carries its source location so it can be re-checked.

## 7. Appraisal (per study, low / high / unclear concern)

Adapted from the analysis and applicability domains of PROBAST+AI and from the
leakage taxonomy of Kapoor & Narayanan (2023); no agriculture-specific instrument
exists.

- **Q1 Domain separation** — OOD data come from fields/sites/years/devices absent
  from training and validation.
- **Q2 Model selection** — hyperparameters, early stopping and checkpoints chosen
  without OOD labels.
- **Q3 Test size** — OOD test-set size reported and ≥ 100 samples (images, fields
  or site-years, as appropriate).
- **Q4 Label consistency** — same classes and annotation protocol across domains.
- **Q5 Variability** — multiple runs, or confidence intervals, reported.
- **Q6 Availability** — code or data publicly available.

## 8. Effect measures and synthesis

- Bounded metrics in [0, 1] (accuracy, F1, mAP/AP50, mIoU/Dice, overall
  accuracy): **retention** ρ = m_OOD / m_ID and **gap** Δ = m_ID − m_OOD
  (percentage points).
- Regression (R², RMSE, MAE): ΔR² and RMSE ratio, synthesised separately.
- Mitigation: **gap recovered** g = (m_adapted − m_source-only) / (m_ID − m_source-only).
- One value per study × shift type for the primary analysis (median of that
  study's comparisons), so studies with many comparisons do not dominate.
- Summary: medians with IQR, and 95% intervals from a cluster bootstrap (resampling
  studies, 10 000 draws). Heterogeneity is described, not pooled away: no inverse-
  variance meta-analysis is attempted, because most studies do not report the
  sampling variance of their metric and metrics differ across tasks.
- Planned moderators: shift type, task, modality, model family (CNN / transformer /
  classical), training-set size, publication year.
- Sensitivity: exclude preprints; exclude studies with high concern on Q1 or Q2;
  accuracy-only subset with chance correction (acc − 1/K)/(1 − 1/K).

## 9. Reporting

PRISMA 2020 statement and checklist (Page et al., 2021). Search strings, the
screening log, the extraction table and the analysis code are released as
supplementary material.

## Deviation log

| Date | Deviation | Reason |
|---|---|---|
| 2026-10-01 | Search string extended: `QUERY = LEARN AND AGRI AND (SHIFT OR EXTRA)`, with `EXTRA = ("new regions" OR "new region" OR "new field conditions" OR "new environments" OR "different regions" OR "other regions" OR "different years" OR "different sites" OR "different locations" OR "future years" OR "transferred across" OR "spatial transfer" OR "temporal transfer" OR "real-world conditions" OR "non-lab" OR "data partitioning")` | The sentinel test (§3.3) retrieved 2 of the first 9 sentinels resolved. Abstracts of the missed sentinels describe their out-of-domain tests in this plain vocabulary rather than with shift terminology. EXTRA adds 1,556 OpenAlex records. |
| 2026-10-01 | Semantic Scholar (Graph API bulk search, title + abstract) added as a second database, same Boolean query in its syntax | OpenAlex holds no abstract for many Elsevier records (e.g. Ferentinos 2018, Wang et al. 2019, Kluger et al. 2021), so those records were searchable by title only. Semantic Scholar holds abstracts for some of them (Wang et al. 2019, Kluger et al. 2021). |
| 2026-10-01 | Sentinel 4 (GWHD 2020/2021 dataset papers) is a recall check only | Dataset papers may not report paired ID/OOD results; eligibility is decided at full text like any other record. |
| 2026-10-01 | Final search string: `QUERY3 = AGRI AND (SHIFT_ML OR (LEARN2 AND (SHIFT OR EXTRA)))`, where `SHIFT_ML = ("domain shift" OR "domain adaptation" OR "domain generalization" OR "domain generalisation" OR "out-of-distribution" OR "distribution shift" OR "dataset shift" OR "test-time adaptation" OR "unsupervised domain")` and `LEARN2` = LEARN plus ("deep-learning" OR "computer vision" OR "semantic segmentation" OR "object detection" OR "image classification" OR "classifier" OR "classifiers"). Run in both databases. | With QUERY2, sentinel recall was 6/13. Missed sentinels state the shift in machine-learning vocabulary without any LEARN term, or name the model by its vision task (segmentation, detection) rather than "deep learning". QUERY3 recall: 8/13. The five sentinels still missed (Mohanty 2016, Ferentinos 2018, GWHD 2020 and 2021, Bosilj 2020) do not describe their out-of-domain test in title or abstract; no title/abstract string retrieves them without a large loss of precision, so they are left to citation chasing. |
| 2026-10-02 | The OpenAlex half of QUERY3 was run on 2026-10-02 00:36 UTC (2026-10-01 local time, UTC-6). The Semantic Scholar half ran on 2026-10-01. The 593 OpenAlex records not already in the pool were screened with the same rules. | The free OpenAlex daily request quota was exhausted on 2026-10-01 and reset at 00:00 UTC. |
| 2026-10-01 | Operational screening rules, applied to every record: (a) robot navigation perception (crop-row following, under-canopy navigation, path extraction) is outside tasks (a)-(f); (b) crop variety or cultivar identification and plant species identification (incl. herbarium/PlantCLEF) are outside tasks (a)-(f); (c) cropland change detection and irrigated-cropland mapping count as task (e); (d) open-set and zero-shot studies whose OOD classes are all unseen in training are E5; cross-domain few-shot studies with disjoint label spaces are E5; (e) out-of-distribution detection without an ID-vs-OOD task metric is excluded; (f) single-scheme leave-one-year-out or spatial cross-validation without an ID comparator does not meet I2; (g) grassland, pasture, turf and forage are outside "crop production"; (h) synthetic-to-real training (incl. radiative-transfer simulations) is E2; (i) yield forecasting from genotype or weather only and crop recommendation are outside scope. | Section 4 did not anticipate these study types; the rules were fixed when first met and applied to all records. |
| 2026-10-01 | Title/abstract screening used the title plus keyword-in-context excerpts of the abstract (at most two windows of +/-14 words around shift terms, at most 400 characters). The full abstract was read for borderline records. Records without an abstract were screened on title alone. Inclusion decisions were recorded with a task code; exclusion reasons were not coded per record at this stage. | Throughput over 7,629 records. PRISMA 2020 requires exclusion reasons only at full text. The 20% human re-screen (section 5) will estimate the sensitivity of this procedure. |
| 2026-10-01 | Duplicate reports of one study (conference and journal versions, preprint and article) are linked at screening (15 pairs); the most complete report is used for extraction. | Avoids double counting in the synthesis. |
| 2026-10-01 | Studies that report a source-only result and a target-trained (oracle) result on the same OOD test set, but no ID result, are included (decision code INCLUDE-O). They contribute to RQ2 (gap recovered relative to the oracle, $g_o = (m_{adapted} - m_{source}) / (m_{oracle} - m_{source})$) and to a secondary RQ1 analysis of the oracle gap; they do not enter the primary ID-OOD analysis. | Domain-adaptation studies routinely report source-only and oracle results on the target test set but rarely the source-domain (ID) result; excluding them would leave RQ2 with few studies. The oracle gap holds the test set fixed and is reported as a separate measure. |
| 2026-10-02 | Studies without retrievable full text included on abstract values when the abstract gives the ID and OOD values of the same model (decision code INCLUDE-A); all appraisal items rated unclear for these studies. | Makes rule E4 explicit: 468 of 770 studies could not be retrieved. |
| 2026-10-02 | Eligible full-text studies whose ID and OOD values appear only in figures recorded as FIG and not digitised (40 studies). | Digitisation was not feasible within the review; the studies are listed in `extraction/ft_decisions.csv` and in `RETRIEVAL_LIST.csv`. |
| 2026-10-02 | The four sentinel studies missed by the search were sought directly ("other methods"); one (Mohanty et al. 2016) was retrieved and included. | Citation chasing could not be run (next row). |
| 2026-10-02 | Citation chasing (§2), Scopus and Web of Science searches (§2), and the human re-screen of a 20% sample (§5) not performed. | Bibliographic services were not reachable from the analysis environment; no second screener was available. Reported as limitations; listed as next steps. |
| 2026-10-02 | §8 changes: training-set size not analysed as a moderator; chance correction replaced by an accuracy-only subset; g computed only when the source-only gap exceeds 0.01 (0-1 scale or R²); compound shifts analysed as their own category plus a factor-level analysis; data modality and model family coded by regular-expression rules (`scripts/synthesis.py`). | Training-set size and the number of classes K were not reported consistently enough to extract; g is unstable for near-zero gaps; many comparisons changed more than one factor. |
| 2026-10-02 | Post hoc analyses added: task-by-shift cross-tabulation; within-study contrasts (compound vs single factor, location vs time, transformer vs convolutional, classical vs convolutional) with exact sign tests, unadjusted; PlantVillage-source comparison; abstract-versus-full-text comparison within task; full-text retrieval by publisher. | Shift type and task are confounded; abstract-only studies differed from full-text studies; retrieval relied on open-access copies. |
