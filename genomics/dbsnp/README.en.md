# dbSNP Guide

NCBI **dbSNP** is the human RefSNP catalog: look up SNPs by **rsID**, **coordinates**, or **gene** for basic info, alleles, functional class, and multi-study frequency summaries (ExAC, gnomAD, ALFA, etc.). Default build **GRCh38**.

Ask in natural language below; include **rsID**, **gene name**, or **chr:pos** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Single SNP | rsID → coordinates, alleles, gene, functional class, MAF summary |
| Coordinate lookup | chr:pos → rsIDs at that locus |
| Gene variants | All RefSNPs for a gene; filter missense / rare / common / clinical tags |
| Region | SNPs in a genomic interval |
| Batch | Multiple rsIDs in one question |
| Stats | SNV/indel breakdown for a gene |

---

## Example queries

### Single variant

- What is rs80357906?
- rs80357906 functional class and alleles
- Look up rs328 and rs80357906 together

### Coordinates

- What rsID is at chr17:43057062?
- dbSNP records at chromosome 17 position 43057062

### Gene

- dbSNP variants in BRCA1
- How many missense variants in TP53?
- Rare BRCA1 variants (MAF < 1%)
- TP53 dbSNP variant type statistics

### Region

- SNPs in chr17:43057060-43057065

### Combined with gnomAD / ClinVar

- rs80357906 dbSNP, gnomAD frequency, and ClinVar pathogenicity together

---

## Three-database workflow

| Database | Focus |
| -------- | ----- |
| **dbSNP** | Location, functional annotation, multi-study frequency summary |
| **gnomAD** | Precise population AF, per-population frequencies, gene constraint |
| **ClinVar** | Clinical significance |

For “what is this SNP, how common, is it pathogenic?” — ask for **all three together**.

---

## Data

- Source: [NCBI dbSNP](https://www.ncbi.nlm.nih.gov/snp/)
- Build: **GRCh38**
