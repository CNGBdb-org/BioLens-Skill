---
name: stomics-datasets
description: >-
  Discover and explore CNGB STOmics/CDCP atlas catalog (~900 atlases, STDS*/SCDS*/
  named portals) via scripts/query.py. Use for cross-atlas search (tissue/species/
  DOI), listing samples for STDS0000xxx/SCDS0000xxx/portal atlases, recommend
  sections, and generic spatial gene UMAP/plots when no dedicated atlas skill
  exists. NOT for HESTA (use hesta), MOSTA (use mosta), or CIMA/TrueBlood (use
  cima-atlas-explore). Not for NCBI GEO/SRA archival search (use geo-sra) or scanpy pipeline
  analysis (use sc-ingest/scanpy-*).
compatibility: Python 3.10+, HTTPS; requests + plotting stack for spatial figures
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2-L4
  domain: discovery
  capability_id: cngbdb.discovery.stomics-datasets.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
  databases: [stomics, cdcp, stds, scds]
---

# CNGB STOmics / CDCP 全库数据集探索

跨图谱 **发现 + 通用 Explore 画图**。自包含：拷贝本目录即可用。

**Catalog：** `scripts/datasets_list.tsv`（约 1.1 万样本行 / 900+ atlas）

## 路由（与专用 Skill 并存时）

| 用户说法 | 用哪个 Skill |
|----------|----------------|
| **HESTA** / 人胚胎 CS12–CS23 / Carnegie | **`hesta`**（不要用本 skill） |
| **MOSTA** / 小鼠器官发生 E9.5–E16.5 | **`mosta`** |
| **CIMA** / TrueBlood / 中国人免疫 / PBMC 亚型 | **`cima-atlas-explore`** |
| **STDS0000xxx** / **SCDS0000xxx** / 其它门户 atlas | **本 skill** |
| 「有哪些图谱有 Brain/皮肤？」跨库检索 | **本 skill** `search` |
| GEO/SRA 公开归档 | `geo-sra` |

> Agent 规则：只要用户点名 HESTA / MOSTA / CIMA，**优先专用 skill**。本 skill 即使也能 `--atlas hesta` 画图，也只作 fallback。

## Use When

- 跨 atlas 找样本（组织、物种、DOI、关键词）
- 探索 **没有** 独立 skill 的 STDS/SCDS/门户图谱
- 对上述图谱做 catalog 列表 / 推荐切片 / 单基因空间或 UMAP 图

## Do Not Use When

| 需求 | 交给 |
|------|------|
| HESTA 基因表达 / 样本推荐 | `hesta` |
| MOSTA 基因表达 | `mosta` |
| CIMA 组成 / GRN / xQTL | `cima-atlas-explore` / `cima-grn-scenicplus` / `cima-xqtl` |
| GEO Series / SRA Run | `geo-sra` |
| 本地 scanpy QC/聚类 | `scanpy-*` |

## Commands

```bash
# 跨图谱搜索（可不加 --atlas）
python ./scripts/query.py search --tissue Brain --limit 20
python ./scripts/query.py search --species human --kind spatial --limit 20
python ./scripts/query.py search -s Visium --api-mode parquet

# 指定 atlas 列样本 / 筛选
python ./scripts/query.py --atlas STDS0000001 catalog list_datasets
python ./scripts/query.py --atlas STDS0000001 catalog filter_datasets --tissue Skin --format json
python ./scripts/query.py --atlas SCDS0000040 catalog recommend_sample --tissue Brain --top 3

# 论文 → 样本
python ./scripts/query.py --atlas hesta catalog paper_to_samples "10.1038/s41586-026-10545-0"

# 通用空间/UMAP 表达（非专用 atlas）
python ./scripts/query.py --atlas STDS0000001 spatial gene_expression <section> -g GENE --fast
```

## Examples

**用户**：CNGB 上有没有 Brain 相关的空间数据集？  
**Agent**：`search --tissue Brain --has-spatial --limit 20`

**用户**：STDS0000001 有哪些样本？皮肤相关的画个基因表达  
**Agent**：`--atlas STDS0000001 catalog list_datasets` → `spatial gene_expression …`

**用户**：HESTA CS23 上看 SOX2  
**Agent**：**改用 `hesta` skill**，不要用本 skill

## Env

| 变量 | 含义 |
|------|------|
| `STOMICS_CATALOG` | 覆盖 catalog TSV |
| `{ATLAS}_CACHE` | 各 atlas parquet 缓存（如 `STDS0000001_CACHE`） |
| `STOMICS_USE_LOCAL` | 优先本地数据根 |

## Layout

```text
stomics-datasets/
├── SKILL.md
└── scripts/
    ├── query.py
    ├── datasets_list.tsv
    ├── stds_registry.json / cdcp_registry.json / portal_atlas_registry.json
    └── _shared/   # catalog + spatial + markers + lib
```
