# Citation integrity report

- Source: `manuscript/refs_crossref.tmp.bib`  ·  30 entries
- Network: available
- **MISMATCH** 1  ·  **VERIFIED** 29

## Verdict: FAIL — see findings below. Gate 2 does not pass.

## Findings

### `singh2020plantdoc` — MISMATCH  (line 11)
*PlantDoc: A Dataset for Visual Plant Disease Detection*
- metadata: title mismatch (similarity 0.26) — record says: "PlantDoc"
- matched via crossref, DOI `10.1145/3371158.3371196`

### `page2021prisma` — VERIFIED  (line 1)
*The PRISMA 2020 statement: an updated guideline for reporting systematic reviews*
- structure: journal article without `volume`
- matched via crossref, DOI `10.1136/bmj.n71`

### `mohanty2016deep` — VERIFIED  (line 7)
*Using Deep Learning for Image-Based Plant Disease Detection*
- structure: journal article without `pages`
- matched via crossref, DOI `10.3389/fpls.2016.01419`

### `quinonerocandela2008dataset` — VERIFIED  (line 13)
*Dataset Shift in Machine Learning*
- structure: missing required field `author` for @book
- matched via crossref, DOI `10.7551/mitpress/9780262170055.001.0001`

### `ploton2020spatial` — VERIFIED  (line 23)
*Spatial validation reveals poor predictive performance of large-scale ecological mapping models*
- structure: journal article without `pages`
- matched via crossref, DOI `10.1038/s41467-020-18321-y`

### `khraisha2024can` — VERIFIED  (line 43)
*Can large language models replace humans in systematic reviews? Evaluating
                    <scp>GPT</scp>
                    ‐4’s effic*
- structure: capitalisation of `GPT` in title is not brace-protected
- matched via crossref, DOI `10.1002/jrsm.1715`

### `morales2023machine` — VERIFIED  (line 55)
*Using machine learning for crop yield prediction in the past or the future*
- structure: journal article without `pages`
- matched via crossref, DOI `10.3389/fpls.2023.1128388`

## Layer 3 — claim support (manual, and required)

Layers 1 and 2 cannot tell you whether a source says what you claim it says.
For every citation attached to a claim in the Abstract, Introduction, or a
comparison: open the source, find the supporting sentence/table/figure, and
record it in the ledger as `[key] -> section, table`. A citation you have not
opened is not a citation.
