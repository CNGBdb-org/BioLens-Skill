# PharmGKB Guide

**PharmGKB** (Pharmacogenomics Knowledge Base) catalogs **pharmacogenomics** genes, variants, **CPIC guidelines**, clinical annotations, and metabolic pathways. This skill calls the **ClinPGx** REST API (`api.clinpgx.org`).

Include **gene**, **rsID**, or **drug name** for best results.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Gene | PharmGKB ID, CPIC/PharmVar flags, GRCh38 coordinates |
| Variant | rsID PGx significance and variant class |
| Guideline | CPIC and other guideline annotations |
| Clinical | Allele–phenotype evidence and level of evidence |
| Drug | Chemical/drug name search |
| Pathway | PK/PD pathways |

---

## Example queries

### Gene

- Is CYP2D6 a CPIC gene?
- PharmGKB info for SLCO1B1
- CYP2C19 pharmacogenomics overview

### Variant

- PharmGKB annotation for rs4244285
- Is this rsID related to clopidogrel response?

### Guideline / clinical

- CPIC dosing guidelines for CYP2C19
- TPMT PharmGKB clinical annotations and evidence level
- Testing recommendations for warfarin PGx

### Drug / pathway

- PharmGKB ID for warfarin
- CYP450 metabolic pathway in PharmGKB

### Combined

- gnomAD frequency and PharmGKB annotation for rs4244285

---

## Related databases

| Database | Focus |
| -------- | ----- |
| **PharmGKB (this skill)** | **PGx, CPIC guidelines, drug–gene evidence** |
| **dbSNP / gnomAD** | rsID coordinates and population AF |
| **Ensembl / GENCODE** | Gene structure and transcripts |

---

## Data

- Source: [ClinPGx API](https://api.clinpgx.org/) (PharmGKB / CPIC)
- Build: **GRCh38**
- Report evidence levels accurately; low-level evidence must not be overstated
