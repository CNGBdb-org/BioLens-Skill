---
name: cima-resource
description: >-
  List and locate CIMA / TrueBlood datasets (metadata, Cell Atlas scRNA/scATAC
  h5ad, GRN, xQTL/SMR, CIMA-CLM, ASLM). This skill package has no local CIMA
  data: answer “where is the data” with public FTP URLs under
  https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/. Use when the
  user asks what CIMA data exists or where it is (e.g. NK h5ad, TrueBlood
  resource). Not for portal UMAP explore (use cima-atlas-explore), local
  preprocessing (use cima-scrna- / cima-scratac-*), or querying precomputed
  GRN/xQTL tables (use cima-grn-scenicplus / cima-xqtl / cima-smr-gwas).
compatibility: Python 3.10+
metadata:
  author: cngbdb-skill-team
  version: "1.2.0"
  scope: database-unique
  depth: L3
  domain: single-cell
  capability_id: cngbdb.cima.resource-catalog.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA Resource Catalog

回答「CIMA 有哪些数据、在哪」。**本 Skill 包不附带本地 CIMA 数据**；问「在哪」时 **只回答公开 FTP（及门户）**，不要编造 `/public/...` 或其它本地盘路径。

**FTP 根目录：**

`https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/`

门户目录：https://db.cngb.org/trueblood/cima/resource  
大文件可用 RaySync：https://ftp.cngb.org/pub/course/tool/raysync/

**必须**先跑包内脚本，再据结果回答；勿编造文件名、URL 或体积。

## Use When

- CIMA / TrueBlood 有哪些数据、文件清单、大小、下载位置
- NK / B / ATAC 等 h5ad 或 metadata / GRN / xQTL 文件在哪（→ FTP URL）
- 按需求推荐：全量 RNA、系群子集、ATAC、GRN、xQTL、CLM demo 等

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 门户 UMAP / 组成 / 基因表达图 | `cima-atlas-explore` |
| 用户自备 h5ad 的 scRNA/scATAC 预处理 | `cima-scrna-preprocessing` / `cima-scratac-preprocessing` |
| 查已下载的 eRegulon / xQTL / SMR 表 | `cima-grn-scenicplus` / `cima-xqtl` / `cima-smr-gwas` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| **数据位置（默认）** | 公开 FTP：`https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/` |
| 门户 | https://db.cngb.org/trueblood/cima/resource |
| 本仓库 | **无** CIMA Resource 本地镜像；勿回答本地绝对路径 |
| 分类 | Metadata / Cell Atlas / GRN / xQTL / CIMA-CLM / Full Length |

## Workflow

1. **Gather**：用户要总览、某类（RNA/ATAC/GRN…）、还是具体文件名  
2. **Act**：只跑 `./scripts/cima_resource_lookup.py`  
3. **Verify**：回答里**先给 FTP URL**（及门户）；明确说明本环境没有本地 Resource 数据  

## Commands

```bash
# 分类总览（含 FTP URL）
python ./scripts/cima_resource_lookup.py overview

# 位置 / 下载说明（FTP 优先）
python ./scripts/cima_resource_lookup.py howto

# 按类 / 关键词（默认打印 url）
python ./scripts/cima_resource_lookup.py list --category "Cell Atlas"
python ./scripts/cima_resource_lookup.py list -q NK
python ./scripts/cima_resource_lookup.py list -q xQTL --small

# 只要 FTP URL
python ./scripts/cima_resource_lookup.py get-url NK_
python ./scripts/cima_resource_lookup.py get-url Lead_cis-xQTL
```

## Output contract

- **优先**：公开 FTP `url` + 文件名、分类、大小、说明  
- 可附带门户 Resource 页与 RaySync（大文件）  
- Full Length / ASLM 若无直链：给出 FTP 根 + 门户，说明用 RaySync  
- 可附带 `related_skill` 建议下一步用哪个分析 Skill  
- **不要**输出 `/public/database/...` 或声称本机已有文件，除非用户自己提供了本地路径  

## Guardrails

- 必须跑包内脚本；目录以 `cima_resource_catalog.json` 为准  
- 回答「在哪」时默认用 **FTP URL**，不要只回或优先回本地路径  
- 门户若更新而脚本未同步：说明「以官网 Resource 页为准」，并给出门户链接  
- 勿声称已替用户下载或验证盘上存在  

## Errors and fallback

- 无匹配 → 扩大关键词或改 `overview`，并给 FTP 根目录与门户  
- 无直链 → 指向 `ftp_root` + 门户 / RaySync  

## Examples

**用户**：CIMA 有哪些数据、在哪？  

```bash
cd cima-resource   # or BioLens-Skill/cima/cima-resource
python ./scripts/cima_resource_lookup.py overview
python ./scripts/cima_resource_lookup.py howto
```

→ 按分类列出文件，位置一律给 FTP（如 `https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/...`）。

**用户**：NK 的 scRNA h5ad 在哪？ / TrueBlood resource 路径  

```bash
python ./scripts/cima_resource_lookup.py get-url NK_
# → https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/Cell_Atlas/CIMA_RNA_NK_....h5ad
```

**用户**：xQTL / SMR 表在哪？  

```bash
python ./scripts/cima_resource_lookup.py list --category xQTL
```

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)  
Resource: [db.cngb.org/trueblood/cima/resource](https://db.cngb.org/trueblood/cima/resource)  
FTP: [ftp.cngb.org/.../CIMA_Resource/](https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/)
