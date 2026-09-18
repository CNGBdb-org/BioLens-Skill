# DGV Guide

**DGV** (Database of Genomic Variants) and **DGVa** catalog **copy-number variants (CNVs)** and structural variants in human populations. This skill queries **Ensembl REST API** `structural_variation` (DGVa first, DGV fallback).

Results are **population research** CNV catalogs, not individual clinical CNV reports. Use **ClinVar** for clinical interpretation.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Region CNV | DGV/DGVa structural variants overlapping an interval |
| Gene CNV | Known CNVs at a gene locus |
| Variant ID | Lookup by nsv accession |

---

## Example queries

### Region

- DGV CNVs in chr16:29500000-29600000
- Any known deletions or duplications in this interval?

### Gene

- CNVs overlapping TBX1
- Common copy-number variants at APP

### Variant ID

- What is nsv516481?
- DGV variant ID nsv123456 coordinates and type

### Combined

- DGV CNVs vs ClinVar clinical CNVs in this region
- TBX1 deletion in DGV and ClinVar

---

## Related databases

| Database | Focus |
| -------- | ----- |
| **DGV/DGVa (this skill)** | **Population CNV / structural variants** |
| **ClinVar** | **Clinical CNV pathogenicity** |
| **Ensembl / GENCODE** | Gene coordinates |
| **UCSC** | Conservation, track data |

---

## Data

- Source: Ensembl overlap API, `source=DGVa` / `DGV`
- Build: **GRCh38**
- DGV integrated into DGVa/dbVar
