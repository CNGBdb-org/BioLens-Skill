# 空间解卷积


## 运行约定

```bash
cd skills/spatial/spatial-deconv
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Baseline spatial deconvolution with NMF factor proportions per spot. Self-built Squidpy/SpatialData-stack skill for cell-type mixture approximation.

## 示例问法

- 帮我跑一下 空间解卷积
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py <h5ad> -o out/spatial_deconv
```
