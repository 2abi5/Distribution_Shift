# Extraction rules (fixed at start of full-text review, 2026-10-01)

- One row per ID-OOD comparison. `id` and `ood` are the ID and OOD values of the SAME source-only (unadapted) model.
- If a mitigation is evaluated on the same OOD test set: `mit` in {UDA, DG, FT, PT, SSL, other}, `adapted` = mitigated model's OOD value, `labels` = number of labelled target samples used (0 for UDA/DG). The mitigated model's own ID value goes in `note`.
- If only a mitigated model is reported (no source-only result): `mit` = "<type>-only"; `id`/`ood` then refer to the mitigated model. Excluded from the primary RQ1 analysis and from the gap-recovered ratio.
- `oracle` = model trained on labelled target-domain data and tested on the same OOD test set.
- Conditional ID: when every test is held out in time (e.g. out-of-year yield tests), the same-region out-of-year test serves as ID for a location shift; recorded in `shift_desc`.
- CV-scheme comparisons: the same model specification evaluated under a random split (ID) and a domain-defined split (OOD) of the same data satisfies I2 (screening rule f).
- Regression metrics: `hib` = 1 for R2, 0 for RMSE/MAE. Values as printed (percent or fraction); units in `metric`.
- Exclusion codes at full text: I1 scope (not a crop-production supervised ML task, incl. model plants such as Arabidopsis); I2 no ID and OOD values for the same model and metric; I3 no source-only OOD value; E1-E5 as in the protocol; NR full text not retrieved and abstract lacks ID and OOD values.
