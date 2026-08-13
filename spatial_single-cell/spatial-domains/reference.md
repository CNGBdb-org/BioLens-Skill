# 空间结构域 / 组织分区 — 解读路径

## 输入 → 输出

- 输入：本地空间 AnnData / Visium / 10x（或 demo）
- 输出：`report.md` + `figures/` + `tables/` +（如有）结果 h5ad

## 依赖

- 必需：scanpy, anndata, matplotlib, scikit-learn, scipy, pandas, numpy
- 可选：squidpy、harmonypy（整合增强）

## 注意

- 默认 Leiden；不可用时回退 PCA+空间 KMeans。写出 `domains.h5ad` 与 `figures/spatial_domains.png`。
- 本 skill 做分析编排，不负责从 GEO 下载（用 `geo-sra`）
- HESTA 门户图谱用 `hesta`，勿与本通用流水线混用
