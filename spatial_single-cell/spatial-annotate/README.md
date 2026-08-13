# 空间细胞类型注释


## 运行约定

```bash
cd skills/spatial/spatial-annotate
python ./scripts/query.py <h5ad> [-o outdir] [--markers markers.csv] [--key cell_type] [--n-clusters 4]
```

内嵌：`scverse_common/`（本目录）

Assign cell/spot type labels on spatial data via marker-gene scoring or Leiden/KMeans. Use after spatial-qc; for proportions use spatial-deconv; for scRNA CellTypist models use celltypist-annotate. Optional marker CSV with gene,cell_type columns.

## 示例问法

- 空间数据打细胞类型
- 用 marker 注释 Visium
- spatial annotate

## 命令

```bash
python ./scripts/query.py spatial.h5ad -o out/ann --markers markers.csv
python ./scripts/query.py --demo -o out/ann_demo
```
