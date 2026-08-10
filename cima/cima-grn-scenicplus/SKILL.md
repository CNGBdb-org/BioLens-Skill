---
name: cima-grn-scenicplus
description: >-
  CIMA eRegulon / GRN queries over pre-computed SCENIC+ tables (203 high-quality
  eRegulons, age/sex-related networks). Use for TF→target lookup or lineage
  regulon lists without recomputing SCENIC+. Not for local metacell prep (use
  cima-metacell), portal UMAP/donor explore (use cima), or heavy SCENIC+ retrain.
compatibility: Python 3.10+, pandas, certifi
metadata:
  author: cngbdb-skill-team
  version: "1.1.0"
  scope: database-unique
  depth: L4
  domain: single-cell
  capability_id: cngbdb.cima.grn-eregulation.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA Gene Regulatory Network (eRegulons)

独立查询预计算 SCENIC+ eRegulon（自带脚本，**不依赖**探索 Skill `cima`）。

## Use When

- 查 TF → 靶基因 / 按 lineage 列高质量 eRegulon
- 不想重跑 SCENIC+

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 门户 UMAP / donor / 临床 | `cima-atlas-explore`（或 `cima`） |
| 本地 metacell 生成 | `cima-metacell` |
| SCENIC+ 全量重算 | 超出本 Skill |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 本地表（优先） | `/public/.../CIMA_Resource/GRN/`（`CIMA_RESOURCE_ROOT` 可覆盖） |
| 外网回退 | FTP → `~/.cache/cima-spatial/tables/` |

## Required inputs

| 子命令 | 常用参数 |
|--------|----------|
| `grn_lookup` | `--tf` / `--gene`，可选 `--max` |
| `regulon_list` | `--lineage`（如 B / NK） |

## Workflow

1. **Gather**：确认 TF/gene/lineage  
2. **Act**：只跑 `./scripts/grn.sh …`  
3. **Verify**：核对表行；不编造靶基因  

## Commands

```bash
bash ./scripts/grn.sh grn_lookup --tf FOXP3 --max 20
bash ./scripts/grn.sh grn_lookup --gene CD8A --max 20
bash ./scripts/grn.sh regulon_list --lineage B
```

## Output contract

- 表格输出（TF / gene / Region / 关联字段）
- 无本地文件时缓存：`~/.cache/cima-spatial/tables/`

## Guardrails

- 必须跑包内脚本；禁止手写结果  
- 预计算查询 ≠ SCENIC+ 重训  

## Errors and fallback

- 本地与 FTP 都失败 → 检查 `CIMA_RESOURCE_ROOT` / 网络 / `CIMA_CACHE`  

## Examples

**用户**：查一下 CIMA 里 Treg 关键转录因子 FOXP3 调控哪些下游基因

```bash
cd skills/cima/cima-grn-scenicplus
bash ./scripts/grn.sh grn_lookup --tf FOXP3 --max 20
bash ./scripts/grn.sh regulon_list --lineage B
```

## Citation

Local: `/public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource/GRN/`  
FTP mirror: https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/GRN/  
Yin et al., Science 2026 — DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
