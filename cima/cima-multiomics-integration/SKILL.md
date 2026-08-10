---
name: cima-multiomics-integration
description: >-
  CIMA scRNA+scATAC multi-omics integration (CPU): accepts gene-level ATAC or
  peak matrix (auto peak→gene), then HVG → PCA → joint Harmony → KNN label
  transfer. Use to transfer RNA cell types to ATAC without SCGLUE/GPU. Not for
  single-modality preprocess (use cima-scrna- / cima-scratac-preprocessing),
  metacell (use cima-metacell), or portal explore (use cima).
compatibility: Python 3.10+, scanpy, scikit-learn, scipy; optional harmonypy
metadata:
  author: cngbdb-skill-team
  version: "1.1.0"
  scope: database-unique
  depth: L5
  domain: single-cell
  capability_id: cngbdb.cima.multiomics-integration.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA Multi-omics Integration (CPU)

CIMA 流水线 Step 5：基因水平整合 scRNA + scATAC 并做标签迁移。**ATAC 可为 gene 或 peak（自动转换）**。

## Use When

- 已有 scRNA h5ad 与 scATAC（**gene activity 或 peak**）
- 需要跨模态标签迁移且 SCGLUE/GPU 不可用

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 仅 scRNA / 仅 scATAC 预处理 | `cima-scrna-preprocessing` / `cima-scratac-preprocessing` |
| Metacell | `cima-metacell` |
| 门户查询 | `cima` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| ATAC gene | 直接与 RNA 取共同基因 |
| ATAC peak | 自动 peak→gene（`linked_gene` 或按 RNA `var_names` 映射） |

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--rna` | 是 | scRNA h5ad |
| `--atac` | 是 | gene-level **或** peak h5ad（含 Step4 产出） |
| `--output` | 是 | 输出目录 |
| `--gene-col` | 否 | peak 时的链接列（默认 `linked_gene`） |

## Commands

```bash
# 推荐：吃 Step4 的 gene activity
python ./scripts/cima_multiomics_integration_cpu.py \
  --rna /path/to/rna.h5ad \
  --atac /path/to/CIMA_scATAC_gene_activity.h5ad \
  --output ./step5_output/

# 也可直接喂 peak（自动转换）
python ./scripts/cima_multiomics_integration_cpu.py \
  --rna /path/to/rna.h5ad \
  --atac /path/to/CIMA_scATAC_peaks.h5ad \
  --output ./step5_output/
```

## Output contract

- `CIMA_Combined.h5ad`
- `CIMA_scATAC_Annotation_Transfered.h5ad`
- 若输入为 peak：额外 `CIMA_scATAC_gene_activity_from_peaks.h5ad`
- `figures/umap_multiomics_*.pdf`

## Guardrails

- 必须跑包内脚本
- peak 无链接且无法映射时回报错误，勿编造整合结果

## Examples

**用户**：用配对 demo 做 RNA+ATAC 标签迁移

```bash
cd skills/cima/cima-multiomics-integration
python ./scripts/cima_multiomics_integration_cpu.py \
  --rna /path/to/CIMA_Annotation_1st_fullgenes.h5ad \
  --atac ../demo/paired_demo_atac_gene.h5ad \
  --output ./step5_output/ --n-hvg 800 --skip-harmony
```

**产出**：`CIMA_Combined.h5ad`、`CIMA_scATAC_Annotation_Transfered.h5ad`、`figures/umap_multiomics_*.pdf`

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
