# eggNOG Guide

**eggNOG** provides cross-species functional annotation via ortholog groups (OGs). This skill resolves human genes through **UniProt cross-references**, then queries **eggNOG API v5** for GO terms and protein domains.

Ask in natural language; include **gene name** or **OG ID** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Gene | Human gene → UniProt → eggNOG OG + GO summary |
| Ortholog group | GO terms and domains by OG ID |
| Ortholog map | UniProt and OG IDs for a gene |
| Function | GO functional terms from the gene's OG |

---

## Example queries

### Gene

- What is TP53's eggNOG ortholog group?
- eggNOG and GO annotation for BRCA1
- Which OG does EGFR belong to in eggNOG?

### Ortholog group

- GO terms and domains for OG 4PQUD@1|root
- Functional annotation for this eggNOG OG

### Function / ortholog

- GO biological processes for TP53
- How many UniProt entries and eggNOG IDs for BRCA1?

---

## Related skills

| Skill | Focus |
| ----- | ----- |
| **kegg** | Metabolic and signaling pathways |
| **gencode** | Gene coordinates and transcripts |
| **ucsc** | Genome tracks and conservation |

---

## Data

- Default organism: **human (9606)**
- Sources: UniProt + eggNOG API v5 (EMBL)
