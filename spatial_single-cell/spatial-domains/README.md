# 空间结构域 / 组织分区


## 运行约定

```bash
cd skills/spatial/spatial-domains
python ./scripts/query.py <h5ad> [-o outdir] [--n-domains 4] [--key domain]
```

内嵌：`scverse_common/`（本目录）

Detect tissue domains on spatial AnnData after QC via Leiden or PCA+spatial KMeans. Use after spatial-qc. Not for SVG (use spatial-svg), spot deconvolution (use spatial-deconv), or cell-type labels (use spatial-annotate / celltypist-annotate).

## 示例问法

- 划分组织域
- spatial domains
- 组织分区 Leiden

## 命令

```bash
python ./scripts/query.py spatial.h5ad -o out/domains --n-domains 4
python ./scripts/query.py --demo -o out/domains_demo
```
