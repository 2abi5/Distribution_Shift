: Table 4. Share of the out-of-distribution gap recovered by mitigation, one value per study and mitigation type. *g* uses the in-distribution value as the reference; *g*~o~ uses a target-trained (oracle) model on the same test set. *g* = 0: no recovery; *g* = 1: in-distribution (or oracle) performance restored.

| Mitigation | Studies | Median | IQR | 95% CI of median |
|:--------------------------------------------|--------:|----------:|----------:|------------:|
| *Gap recovered relative to ID, g* | | | | |
| All mitigations | 49 | 0.48 | 0.26–0.84 | 0.39–0.70 |
| Fine-tuning on labelled target data | 14 | 0.96 | 0.78–1.13 | 0.76–1.13 |
| Domain generalisation or augmentation | 14 | 0.53 | 0.26–0.71 | 0.26–0.71 |
| Large-scale or self-supervised pretraining | 4 | 0.35 | 0.28–0.43 | 0.26–0.46 |
| Unsupervised domain adaptation | 15 | 0.39 | 0.06–0.50 | 0.09–0.53 |
| Other | 4 | 0.22 | 0.17–0.29 | 0.14–0.36 |
| *Gap recovered relative to oracle, g~o~* | | | | |
| All mitigations | 27 | 0.91 | 0.59–1.02 | 0.63–0.99 |
| Fine-tuning on labelled target data | 9 | 1.14 | 1.04–1.33 | 1.00–1.40 |
| Domain generalisation or augmentation | 5 | 0.64 | 0.63–0.68 | 0.62–0.73 |
| Unsupervised domain adaptation | 12 | 0.48 | 0.39–0.94 | 0.39–0.95 |
