---
name: cima-xqtl
description: >-
  CIMA cis-xQTL (eQTL + caQTL) lookup over 223,405 lead associations × 69 cell
  types from pre-computed tables. Use for gene/variant/celltype/analysis filters
  without tensorQTL recomputation. Not for SMR/GWAS pleiotropy (use cima-smr-gwas),
  portal UMAP explore (use cima), or local pseudobulk generation
  (use cima-pseudobulk-variance).
compatibility: Python 3.10+, pandas, certifi
metadata:
  author: cngbdb-skill-team
  version: "1.1.0"
  scope: database-unique
  depth: L4
  domain: single-cell
  capability_id: cngbdb.cima.xqtl-lookup.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA cis-xQTL Lookup

独立查询预计算 cis-eQTL / cis-caQTL（自带脚本，**不依赖**探索 Skill `cima`）。

## Use When

- 按 gene / variant / celltype / analysis 查 xQTL
- 无需 tensorQTL / PLINK 重算

## Do Not Use When

| 需求 | 交给 |
|------|------|
| SMR / 免疫疾病因果关联 | `cima-smr-gwas` |
| 门户表达 UMAP / donor | `cima-atlas-explore`（或 `cima`） |
| 本地 pseudobulk 矩阵 | `cima-pseudobulk-variance` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据位置 | 公开 FTP：`https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/xQTL/`（本包无本地表） |
| 脚本取数 | FTP 下载 → 缓存 `~/.cache/cima-spatial/tables/` |

## Required inputs

至少其一：`--gene` / `--variant` / `--celltype` / `--analysis`（或 `--type`：cis-eQTL / cis-caQTL）

## Workflow

1. **Gather**：确认 gene/variant/celltype/analysis  
2. **Act**：只跑 `./scripts/xqtl.sh …`  
3. **Verify**：检查关联行；不编造 p 值  

## Commands

```bash
bash ./scripts/xqtl.sh --gene CDC42 --max 20
bash ./scripts/xqtl.sh --gene CDC42 --analysis cis-eQTL --max 20
bash ./scripts/xqtl.sh --analysis cis-caQTL --celltype Bn_TCL1A --max 20
```

## Output contract

- 关联表行（gene / SNP / celltype / analysis / 统计量）
- 无本地文件时缓存：`~/.cache/cima-spatial/tables/`

## Guardrails

- 必须跑包内脚本；禁止虚构 QTL  
- 描述关联，不作临床因果断言  

## Errors and fallback

- FTP / 缓存失败 → 检查网络 / `CIMA_CACHE`；表位置见 FTP xQTL 目录  
- 无命中 → 放宽 celltype 或换 gene  

## Examples

**用户**：基因 CDC42 在 CIMA 里有没有 cis-eQTL（表达量相关的遗传位点）？

```bash
cd skills/cima/cima-xqtl
bash ./scripts/xqtl.sh --gene CDC42 --analysis cis-eQTL --max 20
```

## Citation

FTP: https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/xQTL/  
Yin et al., Science 2026 — DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
