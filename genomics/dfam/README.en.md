# Dfam Guide

**Dfam** catalogs transposable element and repetitive DNA **families** with consensus sequences and HMM models. This skill queries the Dfam REST API for family metadata. **Genomic coordinate repeat annotation** requires the **UCSC RepeatMasker** track.

Ask in natural language; include **family name**, **accession**, or **repeat type** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Family | Repeat family by name or accession |
| Search | Keyword search across Dfam families |
| HMM model | Model length, threshold, classification |
| Repeat type | Filter by LINE, SINE, LTR, etc. |
| Region | **No direct API**; UCSC linkage guidance |

---

## Example queries

### Family / search

- What is the Dfam family for Alu elements?
- Search Dfam for MER-related repeats
- HMM model parameters for DF0000001

### Repeat type

- LINE repeat families in Dfam
- SINE-type repetitive elements

### Region (use UCSC)

- Repeats in chr1:1000000-1010000
- RepeatMasker annotation for this genomic region

Workflow: `dfam region` (API note) → `ucsc track RepeatMasker` → `dfam family` for details.

---

## Related skills

| Skill | Focus |
| ----- | ----- |
| **ucsc** | RepeatMasker track for regional repeats |
| **gencode** | Gene transcript coordinates |

---

## Data

- Source: [Dfam](https://dfam.org/) REST API
- Regional annotation: UCSC Genome Browser RepeatMasker track
