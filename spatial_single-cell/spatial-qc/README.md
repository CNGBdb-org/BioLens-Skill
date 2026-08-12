# 空间质控


## 运行约定

```bash
cd skills/spatial/spatial-qc
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Spatial transcriptomics QC: counts/genes metrics and spatial QC maps. Use Squidpy/SpatialData-oriented workflow on AnnData with spatial coordinates.

## 示例问法

- 帮我跑一下 空间质控
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py <h5ad> -o out/spatial_qc
```
