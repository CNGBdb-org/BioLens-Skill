# Ensembl Guide

**Ensembl** provides human gene, transcript, and variant annotation plus **VEP** consequence prediction. Default species: human, build **GRCh38**.

Ask in natural language; include **gene**, **rsID**, **genomic region**, or **HGVS** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Gene | Ensembl ID, description, coordinates, transcripts |
| Variant | rsID/COSMIC → coordinates, alleles |
| Region | Genes overlapping an interval |
| Homology | Cross-species orthologues |
| VEP | HGVS → consequence, SIFT/PolyPhen |

---

## Example queries

### Gene

- What is the Ensembl ID for BRCA1?
- Main transcripts for TP53
- Genomic coordinates of BRCA1

### Variant / VEP

- Ensembl annotation for rs80357906
- Functional consequence of p.V600E
- VEP prediction for c.5266dup

### Region / homology

- Genes in chr17:43044295-43170245
- Mouse orthologue of TP53

### Combined

- rs80357906 Ensembl coordinates, gnomAD AF, and ClinVar pathogenicity together

---

## Data

- Source: [Ensembl REST API](https://rest.ensembl.org/)
- Species: human, **GRCh38**
