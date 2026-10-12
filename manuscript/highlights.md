---
title: Highlights
---

- {{v('n_included')}} studies give {{n(v('n_comparisons_total'))}} paired in- and out-of-distribution results for crop models
- The median model keeps {{pc(v('ret_overall>median'))}}% of its in-distribution score; {{pc(v('sensitivity>full text only (excluding abstract-only)>median'))}}% in full-text studies
- Laboratory-to-field, sensor and compound shifts cost most; shifts in time cost little
- Target fine-tuning recovers {{pc(v('g_by_mit>target fine-tuning>median'))}}% of the gap; unsupervised adaptation {{pc(v('g_by_mit>UDA>median'))}}%
- {{ap('Q5','high')}}% of full-text studies report one run; {{ap('Q2','unclear')}}% do not say how models were selected
