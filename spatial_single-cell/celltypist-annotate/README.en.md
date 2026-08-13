# celltypist-annotate


## Runtime

```bash
cd skills/single-cell/celltypist-annotate
python ./scripts/query.py annotate <h5ad> [-o outdir]
```

Bundled: `scverse_common/` (this directory)

Automated scRNA-seq cell type annotation with CellTypist (built-in or custom models).

```bash
python ./scripts/query.py models
python ./scripts/query.py annotate preprocessed.h5ad -o out/celltypist --over-clustering leiden
python ./scripts/query.py demo -o out/celltypist_demo
```
