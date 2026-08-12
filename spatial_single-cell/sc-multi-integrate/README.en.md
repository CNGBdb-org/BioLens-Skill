# sc-multi-integrate


## 运行约定

```bash
cd skills/single-cell/sc-multi-integrate
python ./scripts/query.py demo
python ./scripts/query.py run <h5ad...> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Light self-built multi-dataset ingest, concat, Combat batch correction, UMAP before/after, and kNN batch-mixing score. CellAtria-style orchestration skill for multi-cohort scRNA integration QC.

```bash
python ./scripts/query.py run a.h5ad b.h5ad
python ./scripts/query.py demo
```
