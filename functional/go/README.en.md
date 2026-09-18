# Gene Ontology (GO) Guide

**Gene Ontology** provides standardized functional terms across **Biological Process (BP)**, **Molecular Function (MF)**, and **Cellular Component (CC)**. Queried via QuickGO API.

Ask in natural language; include **gene**, **GO ID**, or **function keyword** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| GO term | ID → name, definition, namespace |
| Search | Keyword → related GO terms |
| Gene annotations | GO terms and evidence for a gene |
| Ancestors | Parent terms in the GO hierarchy |

---

## Example queries

### Gene

- GO annotations for TP53
- Biological processes involving BRCA1

### Term

- What is GO:0006915?
- GO terms related to apoptosis
- Ancestor terms of GO:0006915

### Combined

- TP53 UniProt function and GO annotations together

---

## Data

- Source: [QuickGO REST API](https://www.ebi.ac.uk/QuickGO/)
- Taxon: human (9606)
