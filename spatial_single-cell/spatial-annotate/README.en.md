# spatial-annotate


## Runtime

```bash
cd skills/spatial/spatial-annotate
python ./scripts/query.py <h5ad> [-o outdir] [--markers markers.csv] [--key cell_type] [--n-clusters 4]
```

Bundled: `scverse_common/` (this directory)

Assign cell/spot type labels on spatial data via marker-gene scoring or Leiden/KMeans. Use after spatial-qc; for proportions use spatial-deconv; for scRNA CellTypist models use celltypist-annotate. Optional marker CSV with gene,cell_type columns.

```bash
python ./scripts/query.py spatial.h5ad -o out/ann --markers markers.csv
python ./scripts/query.py --demo -o out/ann_demo
```
