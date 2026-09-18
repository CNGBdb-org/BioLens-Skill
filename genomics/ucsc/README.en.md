# UCSC Guide

The **UCSC Genome Browser** provides rich genomic tracks and annotations. This skill queries the UCSC **Genome Browser API** for genes, track data, and conservation. Default genome **hg38**.

Ask in natural language; include **gene name**, **track name**, or **genomic region** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Gene | Gene search and coordinates in UCSC |
| Region | knownGene genes in an interval |
| Track | Records from any UCSC track in a region |
| Conservation | phastCons conservation data availability |

---

## Example queries

### Gene

- UCSC hg38 coordinates for BRCA1
- Search for TP53 in UCSC

### Region / track

- Genes in chr17:43044295-43170245
- RepeatMasker elements in chr1:1000000-1010000
- refGene annotations in this region

### Conservation

- Conservation in chr17:7577000-7579000
- phastCons scores for this site

### Other assemblies

- TP53 coordinates on hg19 (use `--genome hg19`)

---

## Related skills

| Skill | Focus |
| ----- | ----- |
| **gencode** | GENCODE transcripts and release |
| **dfam** | Repeat families; use UCSC RepeatMasker for regions |
| **clinvar** | Variant clinical significance |

---

## Data

- Source: [UCSC Genome Browser API](https://api.genome.ucsc.edu/)
- Default assembly: **hg38** (override with `--genome`)
