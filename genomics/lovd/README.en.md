# LOVD Guide

**LOVD** (Leiden Open Variation Database) is a federated network of genetic variant databases. This skill provides:

1. **api.lovd.nl v2** — gene symbol and **HGVS syntax** validation (`checkGene` / `checkHGVS`)
2. **UCSC Beacon (dataset=lovd)** — whether a position exists in aggregated public LOVDs

For disease-specific records, search [lovd.nl](https://lovd.nl/3.0/search) or use **ClinVar**.

---

## What you can query

| Type | Description |
| ---- | ----------- |
| Gene validation | Symbol validity, HGNC ID, suggested corrections |
| HGVS validation | c./g./p. syntax, type, warnings |
| Position beacon | Coordinate presence in public LOVD |
| Region | Parse `chr:g.` or `chr:pos` then query beacon |

---

## Example queries

### Gene

- Is DMD a valid gene symbol in LOVD?
- Validate BRCA1 gene name via LOVD

### HGVS

- Is c.1234A>G valid HGVS?
- Check chr17:g.43057060G>A syntax
- Any warnings for c.5266dupC?

### Position / region

- Is chr17:43057060 in public LOVD?
- LOVD beacon for chr17:g.43057060G>A

### Combined

- After LOVD HGVS validation, ClinVar pathogenicity for this variant
- Do LOVD and HGMD beacons both hit this position?

---

## Related databases

| Database | Focus |
| -------- | ----- |
| **LOVD (this skill)** | **Symbol/HGVS validation, public beacon** |
| **ClinVar** | Clinical significance |
| **HGMD Beacon** | Public HGMD position |
| **Ensembl** | Coordinates, VEP annotation |

Sequence-level HGVS: [VariantValidator](https://variantvalidator.org)

---

## Data

- LOVD API: [api.lovd.nl/v2](https://api.lovd.nl/v2)
- Beacon: [UCSC hgBeacon lovd](https://genome.ucsc.edu/cgi-bin/hgBeacon?dataset=lovd)
- HGVS check is syntactic, not sequence-level
