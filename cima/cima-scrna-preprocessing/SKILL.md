---
name: cima-scrna-preprocessing
description: >-
  CIMA scRNA-seq preprocessing: QC filtering, stratified subsampling, HVG, PCA,
  Harmony batch correction, UMAP, Leiden, and lineage split (B/myeloid/TNK/erythrocyte).
  Use for CIMA-compatible raw h5ad → Annotation_1st. Not for generic Scanpy-only QC
  (use scanpy-qc / scanpy-preprocess / scanpy-cluster), already-annotated subtype
  work (use cima-cell-annotation), portal explore/GRN/xQTL/SMR (use cima), or spatial
  (use spatial-qc / hesta).
compatibility: Python 3.10+, scanpy, igraph; optional harmony-pytorch
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: database-unique
  depth: L5
  domain: single-cell
  capability_id: cngbdb.cima.scrna-preprocessing.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA scRNA-seq Preprocessing

CIMA 流水线 Step 1（L5）：raw h5ad → QC → HVG → PCA → Harmony → UMAP → Leiden → 系群拆分。**必须**调用包内脚本。

## Use When

- 需要对齐 CIMA 的 scRNA raw h5ad 做 QC + 聚类 + 系群拆分
- 需要分层抽样控制细胞规模后的 Annotation_1st

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 通用 scRNA QC / 预处理 / 聚类 | `scanpy-qc` / `scanpy-preprocess` / `scanpy-cluster` |
| 系群 L1–L4 marker 签名注释 | `cima-cell-annotation` |
| CIMA 门户表达 / GRN / xQTL / SMR | `cima` |
| 空间转录组 | `spatial-qc` / `hesta` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | 本地 h5ad（CIMA 风格 cell type 映射可选） |
| 物种 | 人（PBMC / 免疫） |
| 输出对象 | `CIMA_Annotation_1st.h5ad` 及系群拆分 |

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | raw h5ad |
| `--output` | 是 | 输出目录 |
| `--n-target` | 否 | 抽样目标细胞数（默认 50000） |
| `--hvg-n` | 否 | HVG 数（默认 2500） |
| `--celltype-col` | 否 | 已有注释列 |
| `--sample-col` | 否 | 样本列 |
| `--batch-key` | 否 | Harmony 批次键 |

## Necessary questions

1. 未给本地 h5ad 路径 → 补问路径（或先 `geo-sra` / `sc-ingest`）
2. 用户只要门户查询而非本地预处理 → 改用 `cima`
3. 非 CIMA 通用流水线 → 确认是否改用 `scanpy-*`

## Workflow

1. **Gather**：确认输入 h5ad、输出目录、是否抽样 / Harmony  
2. **Act**：只跑 `./scripts/cima_scrna_preprocessing_cpu.py`  
3. **Verify**：检查 `CIMA_Annotation_1st.h5ad` 与 figures；不编造聚类结果  

## Commands

```bash
python ./scripts/cima_scrna_preprocessing_cpu.py \
  --input /path/to/raw.h5ad \
  --output ./step1_output/ \
  --n-target 5000 \
  --hvg-n 2000
```

## Output contract

- `CIMA_Annotation_1st.h5ad` — 主结果（UMAP + Leiden）
- `CIMA_B_cells.h5ad` / `CIMA_myeloid.h5ad` / `CIMA_TNK.h5ad` — 系群拆分
- `CIMA_hvg_keep.csv`、`figures/umap_*.pdf`
- 无脚本产物不得虚构细胞数 / 聚类标签

## Guardrails

- 禁止重写分析逻辑；必须跑包内脚本
- PCA 使用 `zero_center=False`（NumPy 2.x 兼容），勿擅自改回
- 无 cell type 列时回退 Leiden ID，需在结果中说明

## Errors and fallback

- 缺依赖（scanpy / igraph）→ 提示安装后再跑
- Harmony 不可用 → `--skip-harmony` 或跳过批次校正并注明
- 内存不足 → 降低 `--n-target`

## Examples

**用户**：按 CIMA 流程预处理配对 demo RNA

```bash
cd skills/cima/cima-scrna-preprocessing
python ./scripts/cima_scrna_preprocessing_cpu.py \
  --input ../demo/paired_demo_rna.h5ad \
  --output ./step1_output/ \
  --hvg-n 1500 --sample-col sample --skip-subsampling
```

**产出**：`step1_output/CIMA_Annotation_1st.h5ad`、系群 h5ad、`figures/umap_*.pdf`（及 PNG）

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
