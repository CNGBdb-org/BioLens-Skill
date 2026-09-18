# gnomAD Guide

**gnomAD** (Genome Aggregation Database) provides population allele frequencies and gene constraint (**pLI**, **LOEUF**) — commonly used for ACMG evidence such as PM2/BA1. Default **gnomAD v4**, build **GRCh38**.

Ask in natural language; include **rsID** or **gene name** for best results.

> **Note:** gnomAD API rate limits apply; a single rsID query may take **1–2 minutes**.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Variant frequency | rsID or coord+allele → Exome/Genome AF, major population AFs, rare/common interpretation |
| Gene constraint | Gene → pLI, LOEUF, oe_lof — LoF intolerance |
| Gene variant filters | Rare / common / LoF / missense lists within a gene |
| Region | Variants and frequencies in an interval |
| Batch | Multiple rsIDs (≤5 recommended) |

---

## Example queries

### Frequency

- gnomAD frequency of rs80357906
- How common is this variant in the population?
- rs80357906 AF in each gnomAD population

### Gene constraint

- BRCA1 gene constraint
- TP53 pLI and LOEUF
- Is this gene tolerant to LoF variants?

### Gene / region

- Rare variants in BRCA1
- LoF variants in TP53
- gnomAD variants in chr17:43057060-43057065

### Combined

- rs80357906 dbSNP, gnomAD frequency, and ClinVar pathogenicity together

---

## Three-database workflow

| Database | Focus |
| -------- | ----- |
| **dbSNP** | SNP location, functional class, frequency summary |
| **gnomAD** | **Precise population AF, per-population AF, gene constraint** |
| **ClinVar** | Clinical significance |

---

## Data

- Source: [gnomAD](https://gnomad.broadinstitute.org/)
- Version: **gnomAD v4** (GRCh38)
