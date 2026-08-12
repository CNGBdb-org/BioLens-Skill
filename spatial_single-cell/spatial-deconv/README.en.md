# spatial-deconv


## 运行约定

```bash
cd skills/spatial/spatial-deconv
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Baseline spatial deconvolution with NMF factor proportions per spot. Self-built Squidpy/SpatialData-stack skill for cell-type mixture approximation.

```bash
python ./scripts/query.py <h5ad> -o out/spatial_deconv
```
