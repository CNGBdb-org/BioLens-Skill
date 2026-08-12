# scanpy-qc


## 运行约定

```bash
cd skills/single-cell/scanpy-qc
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Run Scanpy QC on an AnnData/h5ad: QC metrics, violin plots, filter by min genes and mito percent. Use for single-cell quality control before preprocessing.

```bash
python ./scripts/query.py <h5ad> -o out/scanpy_qc
```
