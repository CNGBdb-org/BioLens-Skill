# Scanpy 聚类


## 运行约定

```bash
cd skills/single-cell/scanpy-cluster
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Scanpy neighbors, UMAP, and Leiden clustering on preprocessed AnnData. Use for single-cell cluster discovery.

## 示例问法

- 帮我跑一下 Scanpy 聚类
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py <h5ad> -o out/scanpy_cluster
```
