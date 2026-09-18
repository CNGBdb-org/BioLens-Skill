# Variant interpretation (orchestration)

Cross-database triage: **dbsnp → gnomad → clinvar**. Not a replacement for single-DB skills or clinical ACMG sign-out.

```bash
cd skills/genomics/variant-interpretation
python ./scripts/query.py --rsid rs80357906 --format json
```

Requires sibling skills `dbsnp`, `gnomad`, and `clinvar` under `skills/`.
