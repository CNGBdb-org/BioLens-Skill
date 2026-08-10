---
name: cima-resource
description: >-
  List and locate CIMA / TrueBlood datasets (metadata, Cell Atlas scRNA/scATAC
  h5ad, GRN, xQTL/SMR, CIMA-CLM, ASLM). On CNGBdb deploy, answer with local paths
  under /public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource. Use when the
  user asks what CIMA data exists or where it is. Not for portal UMAP explore
  (use cima), local preprocessing (use cima-scrna- / cima-scratac-*), or querying
  precomputed GRN/xQTL tables (use cima-grn-scenicplus / cima-xqtl / cima-smr-gwas).
compatibility: Python 3.10+
metadata:
  author: cngbdb-skill-team
  version: "1.1.0"
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

回答「CIMA 有哪些数据、在哪」。部署环境里数据与公开 Resource 一致，**优先给出本地绝对路径**：

`/public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource/`

（可用环境变量 `CIMA_RESOURCE_ROOT` 覆盖根目录。）门户 / FTP 仅作外部镜像说明。

**必须**先跑包内脚本，再据结果回答；勿编造文件名、路径或体积。

## Use When

- CIMA / TrueBlood 有哪些数据、文件清单、大小、本地位置
- 需要本地 path（部署）或公开 FTP / RaySync（外部）
- 按需求推荐：全量 RNA、系群子集、ATAC、GRN、xQTL、CLM demo 等

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 门户 UMAP / 组成 / 基因表达图 | `cima-atlas-explore`（或 `cima`） |
| 本地 scRNA/scATAC 预处理 | `cima-scrna-preprocessing` / `cima-scratac-preprocessing` |
| 查已下载的 eRegulon / xQTL / SMR 表 | `cima-grn-scenicplus` / `cima-xqtl` / `cima-smr-gwas` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| **本地根（优先）** | `/public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource/` |
| 覆盖根目录 | env `CIMA_RESOURCE_ROOT` |
| 门户 | https://db.cngb.org/trueblood/cima/resource |
| FTP 镜像 | https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/ |
| 分类 | Metadata / Cell Atlas / GRN / xQTL / CIMA-CLM / Full Length |

## Workflow

1. **Gather**：用户要总览、某类（RNA/ATAC/GRN…）、还是具体文件名  
2. **Act**：只跑 `./scripts/cima_resource_lookup.py`  
3. **Verify**：回答里**先给 local path**；仅在用户明确要外网下载时再附 FTP/RaySync  

## Commands

```bash
# 分类总览（含本地 path）
python ./scripts/cima_resource_lookup.py overview

# 位置说明（本地优先）
python ./scripts/cima_resource_lookup.py howto

# 按类 / 关键词（默认打印 path）
python ./scripts/cima_resource_lookup.py list --category "Cell Atlas"
python ./scripts/cima_resource_lookup.py list -q NK
python ./scripts/cima_resource_lookup.py list -q xQTL --small

# 只要本地路径
python ./scripts/cima_resource_lookup.py get-path Lead_cis-xQTL

# 需要公开 FTP 时再加
python ./scripts/cima_resource_lookup.py list -q NK --url
python ./scripts/cima_resource_lookup.py get-url Lead_cis-xQTL
```

## Output contract

- 优先：`local_path`（绝对路径）+ 文件名、分类、大小、说明  
- 次要：公开 FTP URL（用户要外网下载时）  
- Full Length / ASLM 若子目录不确定：给出 `local_root` 并说明需确认 `Full_Length/` 是否存在  
- 可附带 `related_skill` 建议下一步用哪个分析 Skill  

## Guardrails

- 必须跑包内脚本；目录以 `cima_resource_catalog.json` 为准  
- 回答「在哪」时默认用本地路径，不要只回 FTP  
- 门户若更新而脚本未同步：说明「以官网 Resource 页为准」，并给出门户链接  
- 勿声称已替用户验证文件在盘上存在，除非本机 `ls`/`test -f` 确认  

## Errors and fallback

- 无匹配 → 扩大关键词或改 `overview`，并给本地根目录  
- 本地路径不存在 → 检查 `CIMA_RESOURCE_ROOT`；外部场景再给门户 / FTP  

## Examples

**用户**：CIMA 有哪些数据、在哪？  

```bash
cd skills/cima/cima-resource
python ./scripts/cima_resource_lookup.py overview
python ./scripts/cima_resource_lookup.py howto
```

**用户**：NK 的 scRNA h5ad 路径  

```bash
python ./scripts/cima_resource_lookup.py get-path NK_
# → /public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource/Cell_Atlas/...
```

**用户**：xQTL / SMR 表在哪？  

```bash
python ./scripts/cima_resource_lookup.py list --category xQTL
```

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)  
Resource: [db.cngb.org/trueblood/cima/resource](https://db.cngb.org/trueblood/cima/resource)
