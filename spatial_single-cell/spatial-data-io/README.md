# 多平台空间数据读入


## 运行约定

```bash
cd skills/spatial/spatial-data-io
python ./scripts/query.py run <path> [-o outdir] [--platform auto|h5ad|visium|10x]
```

内嵌：`scverse_common/`（本目录）

Load Visium directory / h5ad / 10x into AnnData with obsm['spatial']. Foundation before spatial-qc. Not for scRNA-only (use sc-ingest), GEO discovery (use geo-sra), or HESTA portal maps (use hesta).

## 示例问法

- 读入 Visium 目录
- 把空间 10x 转成带坐标的 h5ad
- spatial data io

## 命令

```bash
python ./scripts/query.py demo -o out/spatial_data_io
python ./scripts/query.py run /path/to/visium -o out/io --platform visium
```
