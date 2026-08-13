# CellTypist 细胞注释


## 运行约定

```bash
cd skills/single-cell/celltypist-annotate
python ./scripts/query.py annotate <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Automated scRNA-seq cell type annotation with CellTypist (built-in or custom models).

## 示例问法

- 用 CellTypist 给这份 PBMC 数据做细胞注释
- 列出可用模型并下载 Immune_All_Low
- 对 preprocess 后的 h5ad 跑 majority voting 注释

## 命令

```bash
python ./scripts/query.py models
python ./scripts/query.py download --model Immune_All_Low.pkl
python ./scripts/query.py annotate preprocessed.h5ad -o out/celltypist --over-clustering leiden
python ./scripts/query.py demo -o out/celltypist_demo
```
