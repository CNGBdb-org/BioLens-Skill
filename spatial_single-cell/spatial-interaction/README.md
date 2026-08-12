# 空间细胞互作


## 运行约定

```bash
cd skills/spatial/spatial-interaction
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Spatial neighborhood co-occurrence / interaction enrichment between labels (domains or clusters). Use for who-interacts-with-whom in tissue.

## 示例问法

- 帮我跑一下 空间细胞互作
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py <h5ad> -o out/spatial_interaction
```
