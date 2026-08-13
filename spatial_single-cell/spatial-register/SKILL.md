---
name: spatial-register
description: >-
  Align multiple spatial slices into a common coordinate frame (Procrustes on expression landmarks; PASTE if available). Use before spatial-integrate for multi-slice. Not for expression batch correction alone (use spatial-integrate).
compatibility: Python 3.10+, scanpy/anndata; optional squidpy/harmonypy
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: cell-spatial
  capability_id: cngbdb.spatial.spatial-register.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# 多切片空间配准

本地 AnnData/h5ad 分析步骤（L5）。**必须**调用内置脚本；本 Skill 内嵌 `scverse_common/`

## Use When

- 将多张切片坐标对齐到同一坐标系

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 表达批次校正 | `spatial-integrate` |
| 单切片 QC / 域分析 | `spatial-qc` / `spatial-domains` |
| scRNA 多样本整合 | `sc-multi-integrate` / `scvi-integrate` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据对象 | 本地 `h5ad` / Visium / 10x（非远程登录号） |
| 空间要求 | 需 `obsm['spatial']`（`spatial-data-io` / `spatial-ingest` 之后） |
| 与 HESTA | HESTA 门户图谱用 `hesta`，勿走本通用流水线 |

## Required inputs

| 任务 | 必填 |
|------|------|
| `run` | ≥2 个含 spatial 的 h5ad |
| `demo` | 无 |

## Necessary questions

1. 用户未提供本地文件路径 → 补问路径，或建议先 `geo-sra` / `spatial-data-io` / `spatial-ingest`
2. 要「分析公开库表达」但未下载 → 先发现与摄取，再分析
3. 提到 HESTA/人胚胎 Stereo-seq 图谱 → 确认是否应改用 `hesta`

## Workflow

1. **Gather**：确认输入 h5ad/矩阵与输出目录  
2. **Act**：只运行 `./scripts/query.py`  
3. **Verify**：检查 `report.md`、figures/tables；不编造统计量  

## Commands

```bash
python ./scripts/query.py run <h5ad1> <h5ad2> [more...] [-o outdir]
python ./scripts/query.py demo [-o outdir]
```

依赖：`pip install -r ../../requirements.txt`（可选 `squidpy` / `harmonypy`）。

## Output contract

- `figures/`、`tables/`、`report.md`；部分步骤写出结果 `h5ad`
- 方法与参数写在 report；无脚本结果不得虚构统计量

## Guardrails

- 禁止重写分析逻辑；必须跑包内脚本
- 禁止把 HESTA 门户查询当成通用 spatial skill
- 缺 `obsm['spatial']` 时先 `spatial-data-io` / `spatial-ingest`

## Errors and fallback

- 缺依赖 → 提示安装 `../../requirements.txt`
- 缺 `obsm['spatial']` → 改用 `spatial-data-io` / `spatial-ingest` 或检查文件
- 可选包不可用（Harmony/PASTE 等）→ 脚本内置回退，并在 report 注明 method

## Examples

```bash
cd skills/spatial/spatial-register
python ./scripts/query.py demo -o out/register
python ./scripts/query.py run s1.h5ad s2.h5ad -o out/register
```

## Citation

- Scanpy / AnnData / Squidpy（按实际安装与 report 注明版本）
- 内嵌：`scverse_common/`

## 联动

- 找公开数据：`geo-sra`
- 空间主线：`spatial-data-io` / `spatial-ingest` → `spatial-qc` → `spatial-domains` / `spatial-annotate` / `spatial-svg` / `spatial-deconv` / `spatial-interaction` / `spatial-trajectory`
- 多切片：`spatial-register` → `spatial-integrate`
- scRNA 参考：`sc-ingest` → `scanpy-*` → `celltypist-annotate`
- HESTA 人胚胎图谱：`hesta`（不要与通用空间流水线混用）
- 内嵌：`scverse_common/`

## 详细说明

见 [reference.md](reference.md)
