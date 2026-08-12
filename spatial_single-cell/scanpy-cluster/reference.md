# Scanpy 聚类 — 解读路径

## 输入 → 输出

- 输入：本地单细胞 / 空间 AnnData（或 demo）
- 输出：`report.md` + `figures/` + `tables/` +（如有）结果 h5ad

## 依赖

- 必需：scanpy, anndata, matplotlib, scikit-learn, scipy, pandas, numpy
- 可选：scvi-tools（`scvi-integrate`）、squidpy（`spatial-svg` 增强）

## 注意

- 本 skill 做分析编排，不负责从 GEO 下载（用 `geo-sra`）
- 大样本需足够内存；scVI 训练建议 GPU
