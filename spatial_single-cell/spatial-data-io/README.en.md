# spatial-data-io


## Runtime

```bash
cd skills/spatial/spatial-data-io
python ./scripts/query.py run <path> [-o outdir] [--platform auto|h5ad|visium|10x]
```

Bundled: `scverse_common/` (this directory)

Load Visium directory / h5ad / 10x into AnnData with obsm['spatial']. Foundation before spatial-qc. Not for scRNA-only (use sc-ingest), GEO discovery (use geo-sra), or HESTA portal maps (use hesta).

```bash
python ./scripts/query.py demo -o out/spatial_data_io
python ./scripts/query.py run /path/to/visium -o out/io --platform visium
```
