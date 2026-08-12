# scanpy-markers


## 运行约定

```bash
cd skills/single-cell/scanpy-markers
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Rank marker genes per cluster with Scanpy wilcoxon. Use after clustering to find cluster markers.

```bash
python ./scripts/query.py <h5ad> -o out/scanpy_markers
```
