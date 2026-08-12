# spatial-ingest


## 运行约定

```bash
cd skills/spatial/spatial-ingest
python ./scripts/query.py demo
python ./scripts/query.py run <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Ingest spatial transcriptomics into AnnData with obsm spatial coordinates (Visium-like h5ad or demo). Foundation for spatial QC/SVG/deconv/interaction skills.

```bash
python ./scripts/query.py run <spatial.h5ad>
python ./scripts/query.py demo
```
