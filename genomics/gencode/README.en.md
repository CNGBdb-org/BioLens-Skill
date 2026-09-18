# GENCODE Guide

**GENCODE** is a high-quality human gene annotation set. This skill queries GENCODE annotations via the **Ensembl REST API** (synchronized with the GENCODE website). Default build **GRCh38**.

Ask in natural language; include **gene name**, **transcript ID**, or **genomic coordinates** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Gene | GENCODE/Ensembl ID, description, transcript list |
| Transcript | Exon count, coordinates, biotype |
| Version | Current Ensembl/GENCODE release |
| Region | Protein-coding transcripts overlapping an interval |

---

## Example queries

### Gene

- GENCODE transcripts for BRCA1
- GENCODE annotation and coordinates for TP53
- Ensembl ID for EGFR

### Transcript

- How many exons in ENST00000357654?
- Details for this Ensembl transcript

### Version / region

- What is the current GENCODE release?
- Protein-coding genes in chr17:43044295-43170245

---

## Related skills

| Skill | Focus |
| ----- | ----- |
| **ensembl** | Variant VEP, homology (same API) |
| **ucsc** | Genome browser tracks |
| **kegg** | Pathway-level function |

---

## Data

- Source: [GENCODE](https://www.gencodegenes.org/) via [Ensembl REST](https://rest.ensembl.org/)
- Build: **GRCh38**
