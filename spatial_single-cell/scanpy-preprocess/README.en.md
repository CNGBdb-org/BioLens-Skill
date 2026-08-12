# scanpy-preprocess


## 运行约定

```bash
cd skills/single-cell/scanpy-preprocess
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Scanpy normalize, log1p, HVG selection, scale, and PCA. Use after QC and before clustering.

```bash
python ./scripts/query.py <h5ad> -o out/scanpy_preprocess
```
