# spatial-domains


## Runtime

```bash
cd skills/spatial/spatial-domains
python ./scripts/query.py <h5ad> [-o outdir] [--n-domains 4] [--key domain]
```

Bundled: `scverse_common/` (this directory)

Detect tissue domains on spatial AnnData after QC via Leiden or PCA+spatial KMeans. Use after spatial-qc. Not for SVG (use spatial-svg), spot deconvolution (use spatial-deconv), or cell-type labels (use spatial-annotate / celltypist-annotate).

```bash
python ./scripts/query.py spatial.h5ad -o out/domains --n-domains 4
python ./scripts/query.py --demo -o out/domains_demo
```
