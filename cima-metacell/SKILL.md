---
name: cima-metacell
description: >-
  CIMA metacell generation (CPU): per sample×celltype Leiden micro-clusters then
  sum aggregation for RNA/ATAC metacell matrices. Use when SEACells unavailable.
  Not for SEACells GPU pipeline, portal GRN/xQTL queries (use cima), or multi-omics
  label transfer (use cima-multiomics-integration).
compatibility: Python 3.10+, scanpy, scipy, scikit-learn
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: database-unique
  depth: L5
  domain: single-cell
  capability_id: cngbdb.cima.metacell.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA Metacell Generation (CPU)

CIMA 流水线 Step 6（L5）：无 SEACells 的 metacell 聚合。**必须**调用包内脚本。

## Use When

- 已有带 `celltype_1st` + sample 的 scRNA（及可选 scATAC）h5ad
- 需要 metacell 矩阵供下游 GRN/xQTL 本地分析
- SEACells 编译/GPU 不可用

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 可用 SEACells+GPU 原流水线 | 原 SEACells 流程（非本 Skill） |
| 仅查预计算 eRegulon / xQTL | `cima` |
| RNA↔ATAC 标签迁移 | `cima-multiomics-integration` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 分组 | sample × celltype |
| 方法 | 组内 PCA → KNN → Leiden(res≈0.3) → sum |

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--rna` | 是 | scRNA h5ad |
| `--atac` | 否 | scATAC h5ad |
| `--output` | 是 | 输出目录 |

## Necessary questions

1. 确认 obs 含 sample 与 celltype 列  
2. 用户只要查门户 GRN → 改用 `cima`  

## Workflow

1. **Gather**：确认 RNA/ATAC 与输出目录  
2. **Act**：只跑 `./scripts/cima_metacell_cpu.py`  
3. **Verify**：检查 metacell h5ad / 映射 CSV  

## Commands

```bash
python ./scripts/cima_metacell_cpu.py \
  --rna /path/to/rna.h5ad \
  --atac /path/to/atac.h5ad \
  --output ./step6_output/
```

## Output contract

- `CIMA_scRNA_Metacell.h5ad` / `CIMA_scATAC_Metacell.h5ad`
- `CIMA_scRNA_Metacell.csv` / `CIMA_scATAC_Metacell.csv`
- `Pseudo_multiomics_barcode_info.csv`（若双模态）

## Guardrails

- 必须跑包内脚本；注明为 SEACells 逻辑近似
- 不把 metacell 结果冒充门户预计算表

## Errors and fallback

- 某分组细胞过少 → 跳过或合并并在日志说明
- 缺 ATAC → 仅输出 RNA metacell

## Examples

**用户**：没有 SEACells，做 CIMA metacell  

```bash
cd skills/cima/cima-metacell
python ./scripts/cima_metacell_cpu.py \
  --rna /path/to/rna_annotated.h5ad \
  --atac /path/to/atac.h5ad \
  --output ./step6_output/
```

**产出**：`CIMA_scRNA_Metacell.h5ad`、`CIMA_scATAC_Metacell.h5ad`、映射 CSV

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
