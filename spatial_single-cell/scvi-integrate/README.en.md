# scvi-integrate


## 运行约定

```bash
cd skills/single-cell/scvi-integrate
python ./scripts/query.py <args>  # 见 README
```

内嵌：`scverse_common/`（本目录）

Integrate scRNA batches with scvi-tools SCVI when installed; otherwise fall back to Scanpy Combat/PCA. Use for deep generative batch correction.

```bash
python ./scripts/query.py <h5ad> -o out/scvi_integrate
```
