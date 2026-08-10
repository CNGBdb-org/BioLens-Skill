---
name: cima-scratac-preprocessing
description: >-
  CIMA scATAC-seq preprocessing (CPU): peak-by-cell h5ad → TF-IDF → TruncatedSVD
  → UMAP/Leiden, and optional peak→gene activity for Step 5. Use when SnapATAC2/GPU
  unavailable. Not for scRNA (use cima-scrna-preprocessing), multi-omics merge
  (use cima-multiomics-integration), or portal explore (use cima).
compatibility: Python 3.10+, scanpy, scikit-learn, scipy; optional harmonypy
metadata:
  author: cngbdb-skill-team
  version: "1.1.0"
  scope: database-unique
  depth: L5
  domain: single-cell
  capability_id: cngbdb.cima.scratac-preprocessing.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA scATAC-seq Preprocessing (CPU)

CIMA 流水线 Step 4：peak 预处理 + **可选写出 gene activity**（供 Step 5）。**必须**调用包内脚本。

## Use When

- 有 peak-by-cell h5ad，需要聚类 / UMAP
- 需要给后续 multi-omics 准备基因水平 ATAC

## Do Not Use When

| 需求 | 交给 |
|------|------|
| scRNA QC/聚类 | `cima-scrna-preprocessing` |
| RNA+ATAC 整合（已有 gene/peak ATAC） | `cima-multiomics-integration`（Step5 也可自行 peak→gene） |
| 门户查询 | `cima` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入 | peaks × cells |
| peak→gene | `var['linked_gene']`，或 `--rna` / `--gene-list` |

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | peak matrix h5ad |
| `--output` | 是 | 输出目录 |
| `--rna` / `--gene-list` | 否 | 无 `linked_gene` 时用于 peak→gene |
| `--skip-gene-activity` | 否 | 只做 peak 聚类 |

## Workflow

1. TF-IDF → SVD → UMAP/Leiden（peak 空间）  
2. 聚合 peak→gene → `CIMA_scATAC_gene_activity.h5ad`  

## Commands

```bash
python ./scripts/cima_scratac_cpu.py \
  --input /path/to/peak_matrix.h5ad \
  --output ./step4_output/ \
  --rna /path/to/CIMA_Annotation_1st.h5ad
```

## Output contract

- `CIMA_scATAC_peaks.h5ad`（及兼容名 `pbmc_filtered_genescore.h5ad`）
- `CIMA_scATAC_gene_activity.h5ad`（默认写出；可供 Step 5）
- `figures/umap_atac_leiden.pdf`

## Guardrails

- 必须跑包内脚本；勿假装 SnapATAC2 结果
- 无 gene 链接时 gene activity 会跳过并提示

## Examples

**用户**：用配对 demo 跑 Step4（peaks → gene activity）

```bash
cd skills/cima/cima-scratac-preprocessing
python ./scripts/cima_scratac_cpu.py \
  --input ../demo/paired_demo_atac.h5ad \
  --output ./step4_output/ \
  --skip-harmony --n-components 30 \
  --rna ../demo/paired_demo_rna.h5ad
```

**产出**：`CIMA_scATAC_peaks.h5ad`、`CIMA_scATAC_gene_activity.h5ad`、`figures/umap_atac_leiden.pdf`

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
