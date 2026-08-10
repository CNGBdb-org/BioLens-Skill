---
name: cima-pseudobulk-variance
description: >-
  CIMA pseudobulk aggregation and OLS variance decomposition: sum counts per
  sample×celltype, partition variance by celltype/age/sex. Use after CIMA
  annotation for pseudobulk matrices. Not for portal cis-xQTL/SMR lookup (use
  cima), generic DE (out of scope), or Step-1 QC (use cima-scrna-preprocessing).
compatibility: Python 3.10+, scanpy, statsmodels
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: database-unique
  depth: L5
  domain: single-cell
  capability_id: cngbdb.cima.pseudobulk-variance.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA Pseudobulk Variance Decomposition

CIMA 流水线 Step 3（L5）：sample×celltype pseudobulk + OLS 方差分解。**必须**调用包内脚本。

## Use When

- 已有带 cell type 的 CIMA h5ad，需要 pseudobulk 表达矩阵
- 需要量化 celltype / age / sex 对表达方差的贡献

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 查预计算 eQTL / caQTL / SMR | `cima`（xqtl / immune-disease） |
| QC / 一级聚类 | `cima-scrna-preprocessing` |
| 通用单细胞 DE | 超出本 Skill |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 分组 | `sample` × `celltype_1st`（可用参数覆盖列名） |
| 模型 | `expression ~ celltype + age + sex`（log1p 后 OLS） |

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 带注释的 h5ad（如 Annotation_1st） |
| `--output` | 是 | 输出目录 |
| `--sample-col` / `--celltype-col` | 否 | 分组列 |
| `--covariates` | 否 | 如 `age sex` |

## Necessary questions

1. 缺样本或 celltype 列 → 补问列名  
2. 用户要查门户 QTL/SMR → 改用 `cima`  
3. 协变量缺失 → 说明方差分解将受限  

## Workflow

1. **Gather**：确认 h5ad、分组列、协变量  
2. **Act**：只跑 `./scripts/cima_pseudobulk_variance_cpu.py`  
3. **Verify**：检查 CSV；不编造方差占比  

## Commands

```bash
python ./scripts/cima_pseudobulk_variance_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step3_output/ \
  --sample-col sample \
  --celltype-col celltype_1st \
  --covariates age sex
```

## Output contract

- `pseudobulk_BySampleCelltype.csv`
- `pseudobulk_metadata.csv`
- `varPartResults.csv`（celltype / age / sex / residual）

## Guardrails

- 必须跑包内脚本；禁止手写 OLS 后假装为本流水线结果
- 结果为描述性方差分解，不作因果断言

## Errors and fallback

- 某 celltype 样本过少 → 脚本按 `--min-celltype-samples` 过滤并说明
- 缺 statsmodels → 提示安装

## Examples

**用户**：按 sample×celltype 做 pseudobulk，并看 age/sex 方差贡献  

```bash
cd skills/cima/cima-pseudobulk-variance
python ./scripts/cima_pseudobulk_variance_cpu.py \
  --input /path/to/CIMA_Annotation_1st.h5ad \
  --output ./step3_output/ \
  --sample-col sample \
  --celltype-col celltype_1st \
  --covariates age sex
```

**产出**：`pseudobulk_BySampleCelltype.csv`、`pseudobulk_metadata.csv`、`varPartResults.csv`

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
