# Open Targets Guide

The **Open Targets Platform** integrates **target–disease associations**, genetics evidence, known drugs, and clinical trial phases for drug target prioritization.

Ask in natural language; include **gene**, **disease**, **rsID**, or **drug name** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Target/gene | Basic info, known drugs, tractability |
| Disease | EFO disease search |
| Variant | rsID annotation and colocalisation |
| Drug | Drug name search |
| Target–disease | Association score for gene and disease |

---

## Example queries

### Target / drug

- Known drugs for EGFR
- Open Targets ID for imatinib

### Disease / association

- EFO ID for breast cancer
- Association score between BRCA1 and breast cancer
- Is TCF7L2 associated with type 2 diabetes?

### Variant

- Open Targets annotation for rs7903146

### Combined

- TCF7L2 GWAS hits and Open Targets target score together

---

## Data

- Source: [Open Targets Platform](https://platform.opentargets.org/)
- Scores are integrated evidence; validate with primary GWAS/ClinVar data
