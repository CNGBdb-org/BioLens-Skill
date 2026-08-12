---
name: spatial-svg
description: >-
  Detect spatially variable genes via Moran I (Squidpy if available, else kNN Moran). Use for spatial pattern gene discovery. Not for cluster markers (use scanpy-markers) or HESTA organ markers (use hesta).
compatibility: Python 3.10+, scanpy/anndata; optional scvi-tools/squidpy
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: cell-spatial
  capability_id: cngbdb.spatial.spatial-svg.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# 空间可变基因

本地 AnnData/h5ad 分析步骤（L5）。**必须**调用内置脚本；本 Skill 内嵌 `scverse_common/`

## Use When

- Moran I / Squidpy SVG 检测

## Do Not Use When

| 需求 | 交给 |
|------|------|
| cluster marker | `scanpy-markers` |
| HESTA marker | `hesta` |
| 空间解卷积 | `spatial-deconv` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据对象 | 本地 `h5ad` / 10x 矩阵（非远程登录号） |
| 空间要求 | 空间 skill 需要 `obsm['spatial']` |
| 与 HESTA | HESTA 门户图谱用 `hesta`，勿走本通用流水线 |

## Required inputs

| 任务 | 必填 |
|------|------|
| `run` | 含 spatial 的 h5ad |

## Necessary questions

1. 用户未提供本地文件路径 → 补问路径，或建议先 `geo-sra` / `sc-ingest` / `spatial-ingest`
2. 要「分析公开库表达」但未下载 → 先发现与摄取，再分析
3. 提到 HESTA/人胚胎 Stereo-seq 图谱 → 确认是否应改用 `hesta`

## Workflow

1. **Gather**：确认输入 h5ad/矩阵与输出目录  
2. **Act**：只运行 `./scripts/query.py`  
3. **Verify**：检查 `report.md`、figures/tables；不编造 p 值/marker  

## Commands

```bash
python ./scripts/query.py <h5ad> [-o outdir]
```

依赖：`pip install -r ../../requirements.txt`（可选 `scvi-tools` / `squidpy`）。

## Output contract

- `figures/`、`tables/`、`report.md`；部分步骤写出结果 `h5ad`
- 方法与参数写在 report；无脚本结果不得虚构统计量

## Guardrails

- 禁止重写分析逻辑；必须跑包内脚本
- 禁止把 HESTA 门户查询当成通用 spatial skill
- 大批量/GPU 训练超出本 skill 时说明限制

## Errors and fallback

- 缺依赖 → 提示安装 `../../requirements.txt`
- 缺 `obsm['spatial']` → 改用 `spatial-ingest` 或检查文件
- scVI 不可用 → `scvi-integrate` 自动降级 Combat（见该 skill report）

## Examples

```bash
cd skills/spatial/spatial-svg
python ./scripts/query.py <h5ad> [-o outdir]
```

## Citation

- Scanpy / AnnData / scvi-tools / Squidpy（按实际安装与 report 注明版本）
- 内嵌：`scverse_common/`

## 联动

- 找公开数据：`geo-sra`
- 单细胞：`sc-ingest` → `scanpy-qc` → `scanpy-preprocess` → `scanpy-cluster` → `scanpy-markers`
- 多批次：`sc-multi-integrate` / `scvi-integrate`
- 空间：`spatial-ingest` → `spatial-qc` → `spatial-svg` / `spatial-deconv` / `spatial-interaction`
- HESTA 人胚胎图谱：`hesta`（不要与通用空间流水线混用）
- 内嵌：`scverse_common/`

## 详细说明

见 [reference.md](reference.md)
