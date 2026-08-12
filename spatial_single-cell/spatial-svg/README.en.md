# spatial-svg


## 运行约定

```bash
cd skills/spatial/spatial-svg
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Detect spatially variable genes via Moran I (Squidpy if available, else kNN Moran). Use for spatial pattern gene discovery.

```bash
python ./scripts/query.py <h5ad> -o out/spatial_svg
```
