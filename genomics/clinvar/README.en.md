# ClinVar Guide

NCBI **ClinVar** catalogs **clinical significance** (pathogenic / likely pathogenic / VUS / benign, etc.), review status, associated diseases, and OMIM IDs. Use for variant interpretation, disease-variant lookup, and VUS catalogs. Default build **GRCh38**.

Ask in natural language; include **rsID**, **gene**, **HGVS**, or **disease name** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Single variant | rsID / HGVS / ClinVar ID → significance, review status, diseases |
| Gene pathogenic spectrum | Pathogenic / likely pathogenic variants for a gene |
| Gene statistics | Counts by pathogenic, VUS, benign, conflicting |
| VUS / conflicts | Variants of uncertain significance or conflicting interpretations |
| Disease | Variants linked to a disease or phenotype keyword |
| Region | ClinVar variants in a genomic interval |

---

## Example queries

### Single variant

- Is rs80357906 pathogenic?
- ClinVar annotation for rs80357906
- Is BRCA1 c.5266dup pathogenic?
- What is ClinVar ID 17677?

### Gene

- BRCA1 pathogenic ClinVar variants
- How many pathogenic vs VUS variants in BRCA1?
- TP53 variants of uncertain significance
- BRCA1 conflicting interpretation variants
- BRCA1 ClinVar classification statistics

### Disease

- Pathogenic variants associated with Noonan syndrome
- ClinVar pathogenic variants related to breast cancer

### Region

- ClinVar variants in chr17:43057060-43057065

### Combined

- rs80357906 dbSNP, gnomAD frequency, and ClinVar pathogenicity together

---

## Three-database workflow

| Database | Focus |
| -------- | ----- |
| **dbSNP** | Coordinates, functional class, frequency summary |
| **gnomAD** | Precise population AF, gene constraint |
| **ClinVar** | **Clinical significance, VUS, disease association** |

**VUS** must not be reported as pathogenic; **conflicting** interpretations require additional evidence.

---

## Data

- Source: [NCBI ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/)
- Build: **GRCh38**
