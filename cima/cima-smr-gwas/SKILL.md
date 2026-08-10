---
name: cima-smr-gwas
description: >-
  CIMA SMR immune-disease lookup over the significant gene–trait table
  (CIMA_Significant_SMR_Pleiotropic_Associations.xlsx) and optional caQTL→eQTL
  SMR CSV. Use for gene/trait/celltype SMR hits and HEIDI context without local
  SMR/GCTA/PLINK. Not for raw cis-xQTL tables (use cima-xqtl), portal UMAP
  explore (use cima-atlas-explore), or ClinVar pathogenicity (use clinvar).
compatibility: Python 3.10+, pandas, openpyxl, certifi
metadata:
  author: cngbdb-skill-team
  version: "1.2.0"
  scope: database-unique
  depth: L4
  domain: single-cell
  capability_id: cngbdb.cima.smr-gwas.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA SMR / GWAS Immune Disease Lookup

独立查询预计算 SMR（自带脚本，**不依赖**探索 Skill `cima`）。

**默认表**：`CIMA_Significant_SMR_Pleiotropic_Associations.xlsx`（基因–性状显著 SMR，含 RA / As / GD 等）。  
**可选**：`--source caqtl` 查 `CIMA_caQTL_eQTL_SMR.csv`（caQTL→基因，**不是**疾病性状表；`exposure` 常为 peak/`nan`）。

## Use When

- 按 gene / trait / celltype 查免疫相关 SMR
- 无本地 SMR/GCTA/PLINK

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 仅 cis-eQTL / caQTL 表 | `cima-xqtl` |
| 门户表达 / 组成 | `cima-atlas-explore` |
| GRN | `cima-grn-scenicplus` |
| 临床致病性断言 | `clinvar` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 疾病显著表（默认） | `…/xQTL/CIMA_Significant_SMR_Pleiotropic_Associations.xlsx` |
| caQTL→eQTL SMR | `…/xQTL/CIMA_caQTL_eQTL_SMR.csv` |
| 外网回退 | FTP → `~/.cache/cima-spatial/tables/` |

## Required inputs

至少其一：`--gene` / `--snp` / `--celltype` / `--trait`，可选 `--max`、`--source`

## Workflow

1. **Gather**：确认 gene / trait / celltype  
2. **Act**：只跑 `./scripts/smr.sh …`（默认 disease 表）  
3. **Verify**：核对 p_SMR / trait；不编造显著性  

## Commands

```bash
# 疾病显著表（推荐演示）
bash ./scripts/smr.sh --gene CTLA4 --max 10
bash ./scripts/smr.sh --gene BLK --trait RA --max 10
bash ./scripts/smr.sh --gene ORMDL3 --trait As --max 10

# caQTL→eQTL 表（非疾病）
bash ./scripts/smr.sh --source caqtl --gene ARL14EP --max 10
```

## Output contract

- disease：`gene / trait / celltype / topSNP / p_SMR / p_HEIDI`
- caqtl：`exposure / outcome / celltype / topSNP / p_SMR`
- 无本地文件时缓存：`~/.cache/cima-spatial/tables/`

## Guardrails

- 必须跑包内脚本  
- SMR 为统计关联证据，不作临床诊断结论  
- 问「免疫病」时用默认 disease 表，勿只用 caqtl CSV  

## Errors and fallback

- 本地与 FTP 都失败 → 检查 `CIMA_RESOURCE_ROOT` / 网络 / `CIMA_CACHE`  
- 无命中 → 换 gene（如 BLK/ORMDL3/IL18R1）或放宽 `--trait`  

## Examples

**用户**：CTLA4 在显著 SMR 里和哪些免疫相关疾病有关联？

```bash
cd skills/cima/cima-smr-gwas
bash ./scripts/smr.sh --gene CTLA4 --max 10
# → GD (Graves disease) 等
```

**用户**：BLK 和类风湿关节炎（RA）有没有 SMR 关联？

```bash
bash ./scripts/smr.sh --gene BLK --trait RA --max 10
```

## Citation

Local disease table: `/public/.../CIMA_Resource/xQTL/CIMA_Significant_SMR_Pleiotropic_Associations.xlsx`  
FTP: https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/xQTL/CIMA_Significant_SMR_Pleiotropic_Associations.xlsx  
Yin et al., Science 2026 — DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
