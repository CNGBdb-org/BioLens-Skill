# 多数据集整合与批次检查


## 运行约定

```bash
cd skills/single-cell/sc-multi-integrate
python ./scripts/query.py demo
python ./scripts/query.py run <h5ad...> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Light self-built multi-dataset ingest, concat, Combat batch correction, UMAP before/after, and kNN batch-mixing score. CellAtria-style orchestration skill for multi-cohort scRNA integration QC.

## 示例问法

- 帮我跑一下 多数据集整合与批次检查
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py run a.h5ad b.h5ad
python ./scripts/query.py demo
```
