# sc-ingest


## 运行约定

```bash
cd skills/single-cell/sc-ingest
python ./scripts/query.py demo
python ./scripts/query.py run <matrix|h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Ingest scRNA-seq matrices (h5ad / 10x h5 / 10x mtx) into a normalized AnnData h5ad. Supports demo data generation for smoke tests. Use for reading single-cell counts before QC or integration.

```bash
python ./scripts/query.py run <matrix|h5ad>
python ./scripts/query.py demo
```
