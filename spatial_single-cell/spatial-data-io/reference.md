# 多平台空间数据读入 — 解读路径

## 输入 → 输出

- 输入：本地空间 AnnData / Visium / 10x（或 demo）
- 输出：`report.md` + `figures/` + `tables/` +（如有）结果 h5ad

## 依赖

- 必需：scanpy, anndata, matplotlib, scikit-learn, scipy, pandas, numpy
- 可选：squidpy、harmonypy（整合增强）

## 注意

- 支持 platform=auto/h5ad/visium/10x；输出 `spatial.h5ad`。与 `spatial-ingest` 功能相近，本 skill 偏多平台读入入口。
- 本 skill 做分析编排，不负责从 GEO 下载（用 `geo-sra`）
- HESTA 门户图谱用 `hesta`，勿与本通用流水线混用
