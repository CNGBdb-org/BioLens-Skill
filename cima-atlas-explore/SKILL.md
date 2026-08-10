---
name: cima-atlas-explore
description: >-
  Explore CIMA / TrueBlood atlas portal views (PBMCs/CD4T/CD8T/B/Myeloid/NK):
  list views, donor/clinical metadata, cell-type composition, gene UMAP
  expression, and cross-lineage gene compare. Use for CIMA atlas browsing and
  expression maps. Not for downloadable file catalogs (use cima-resource),
  GRN/eRegulon (use cima-grn-scenicplus), cis-xQTL (use cima-xqtl), SMR/GWAS
  (use cima-smr-gwas), or local preprocess pipelines (use cima-scrna-* / …).
compatibility: Python 3.10+, HTTPS; requests + pandas + plotting stack
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: database-unique
  depth: L4
  domain: single-cell
  capability_id: cngbdb.cima.atlas-explore.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA Atlas Explore（图谱浏览）

在 `skills/cima/` 分类下的 **门户图谱探索** Skill：列视图、donor 临床、亚型组成、基因 **UMAP**、跨 lineage 比较。

**Portal:** https://db.cngb.org/trueblood/cima/  

与下列 Skill **分工，勿重叠**：

| 需求 | 用 |
|------|-----|
| 有哪些可下载数据 / 本地路径 | `cima-resource` |
| TF→靶基因 / eRegulon | `cima-grn-scenicplus` |
| cis-eQTL / cis-caQTL | `cima-xqtl` |
| SMR 基因–疾病关联 | `cima-smr-gwas` |
| 本地 h5ad 预处理流水线 | `cima-scrna-*` 等 |

> 同源探索代码也保留在 `skills/single-cell/cima`（短名 `cima`）；`--category cima` 安装时用本 Skill。

## Use When

- CIMA / TrueBlood 有哪些 **视图**、donor、临床协变量
- 某视图 **cell_type_l4 组成**
- 某基因在某视图的 **UMAP 表达图**
- 同一基因跨 B/NK/T 等视图比较

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 数据清单 / FTP / 本地 `CIMA_Resource` 路径 | `cima-resource` |
| FOXP3 eRegulon / GRN | `cima-grn-scenicplus` |
| CDC42 cis-eQTL 等 | `cima-xqtl` |
| ARL14EP SMR / 免疫病 | `cima-smr-gwas` |
| 本地 QC/注释/多组学 | `cima-scrna-preprocessing` 等 |
| HESTA / MOSTA 空间切片 | `hesta` / `mosta` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 视图 | `PBMCs` / `CD4T` / `CD8T` / `B` / `Myeloid` / `NK` |
| obs | 默认 `cell_type_l4` |
| 基因 | **大写**：`CD8A`、`IKZF4` |
| 出图 | **UMAP**（非空间切片） |

## Workflow

1. **Gather**：确认视图（优先 B/NK）、基因或主题  
2. **Act**：只跑本目录 `./scripts/query.py`  
3. **Verify**：核对 ExploreId、基因大小写、图/表路径  
4. 若用户问 GRN / xQTL / SMR / 下载清单 → **改用上表对应 Skill**，不要用本目录查这些表  

## Commands

```bash
python ./scripts/query.py <module> <script> [args…]
```

| 任务 | 命令 |
|------|------|
| 列视图 | `python ./scripts/query.py catalog list_datasets` |
| donor 表 | `python ./scripts/query.py catalog donor_metadata` |
| 临床摘要 | `python ./scripts/query.py clinical clinical_summary B` |
| 亚型组成 | `python ./scripts/query.py composition celltype_composition B --top 15 --plot` |
| 年龄分层组成 | `python ./scripts/query.py composition covariate_composition B --covariate age --plot`（优先 B/NK 等小谱系；PBMCs 全量较慢） |
| 基因 UMAP | `python ./scripts/query.py spatial gene_expression B -g CD8A --fast` |
| 跨视图基因 | `python ./scripts/query.py cross-view cross_view_gene -g CD8A --plot` |

`grn` / `xqtl` / `immune-disease` 模块在本 Skill **已禁用**，会提示改用专用 Skill。

## Output contract

- 表格 / 图文件路径；含 ExploreId、基因、视图  
- 无脚本结果不得虚构表达量  

## Guardrails

- 必须跑包内 `./scripts/query.py`  
- UMAP ≠ 空间切片；勿与 HESTA/MOSTA 混淆  
- 禁止用本 Skill 回答下载目录、GRN、xQTL、SMR  

## Errors and fallback

- 基因未找到 → 检查大小写 / 换小视图（B/NK）  
- 网络失败 → `CIMA_CACHE` / `CIMA_USE_LOCAL`  
- 用户要 GRN/xQTL/SMR/清单 → 转对应 Skill  

## Examples

**用户**：CIMA 有哪些视图 / donor？  

```bash
cd skills/cima/cima-atlas-explore
python ./scripts/query.py catalog list_datasets
python ./scripts/query.py catalog donor_metadata
```

**用户**：CIMA B 细胞视图画 CD8A 的 UMAP  

```bash
python ./scripts/query.py spatial gene_expression B -g CD8A --fast
```

**用户**：FOXP3 调控哪些基因？ → **不要用本 Skill**，用 `cima-grn-scenicplus`。

## Env

| 变量 | 含义 |
|------|------|
| `CIMA_CACHE` | 缓存目录（默认 `~/.cache/cima-spatial`） |
| `CIMA_USE_LOCAL` | `1` 优先本地缓存 |

## Citation

Portal: https://db.cngb.org/trueblood/cima/  
Yin et al., Science 2026 — DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
