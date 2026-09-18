# KEGG Guide

**KEGG** (Kyoto Encyclopedia of Genes and Genomes) provides metabolic pathways, diseases, compounds, and human gene associations. This skill queries the KEGG REST API for **academic use only**.

Ask in natural language; include **gene name**, **pathway ID**, or **disease/compound keyword** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Gene | Human KEGG gene entry and linked pathways |
| Pathway | Pathway description and member genes by ID |
| Disease | Disease keyword → KEGG disease entries |
| Compound | Metabolite or drug compound information |
| Pathway search | Keyword search for human (hsa) pathways |

---

## Example queries

### Gene

- Which KEGG pathways is TP53 linked to?
- KEGG entry for BRCA1
- What signaling pathways involve EGFR?

### Pathway

- What is pathway hsa04110?
- Genes in the KEGG cell cycle pathway (04110)

### Disease / compound

- KEGG disease entries related to diabetes
- KEGG compound ID for glucose

### Pathway search

- Human KEGG pathways related to apoptosis
- Search MAPK signaling pathways

---

## Related skills

| Skill | Focus |
| ----- | ----- |
| **gencode** | Gene coordinates, GENCODE transcripts |
| **eggnog** | Ortholog groups, GO annotation |
| **ucsc** | Genome browser tracks and conservation |

---

## Data

- Source: [KEGG](https://www.kegg.jp/) REST API (`rest.kegg.jp`)
- Default organism: **human (hsa)**
- Academic use terms apply
