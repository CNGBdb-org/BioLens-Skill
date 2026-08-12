# 空间转录组摄取


## 运行约定

```bash
cd skills/spatial/spatial-ingest
python ./scripts/query.py demo
python ./scripts/query.py run <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Ingest spatial transcriptomics into AnnData with obsm spatial coordinates (Visium-like h5ad or demo). Foundation for spatial QC/SVG/deconv/interaction skills.

## 示例问法

- 帮我跑一下 空间转录组摄取
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py run <spatial.h5ad>
python ./scripts/query.py demo
```
