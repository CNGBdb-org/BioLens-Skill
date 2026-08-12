# spatial-qc


## 运行约定

```bash
cd skills/spatial/spatial-qc
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Spatial transcriptomics QC: counts/genes metrics and spatial QC maps. Use Squidpy/SpatialData-oriented workflow on AnnData with spatial coordinates.

```bash
python ./scripts/query.py <h5ad> -o out/spatial_qc
```
