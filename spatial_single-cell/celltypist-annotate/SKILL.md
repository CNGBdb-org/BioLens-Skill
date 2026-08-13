---
name: celltypist-annotate
description: >-
  Automated scRNA-seq cell type annotation with CellTypist logistic models
  (built-in tissue/immune models or local .pkl). Use after scanpy-preprocess
  (log1p normalize to 1e4) to assign predicted_labels / majority_voting.
  Not for CIMA TrueBlood L1–L4 (use cima-cell-annotation), cluster markers
  (use scanpy-markers), or spatial spot deconvolution (use spatial-deconv).
compatibility: Python 3.10+, scanpy/anndata, celltypist; HTTPS for model download
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: single-cell
  capability_id: cngbdb.scrna.celltypist-annotate.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# CellTypist 细胞注释

本地 AnnData/h5ad 分析步骤（L5）。**必须**调用内置脚本；本 Skill 内嵌 `scverse_common/`

## Use When

- 用 CellTypist 预训模型给 scRNA 细胞打类型标签
- 按组织/免疫场景选模型（默认 `Immune_All_Low.pkl`）
- 需要 `majority_voting` 细化标签，或导出置信度 / 概率矩阵

## Do Not Use When

| 需求 | 交给 |
|------|------|
| CIMA TrueBlood L1–L4 | `cima-cell-annotation` |
| 按 cluster 找 marker | `scanpy-markers` |
| 先 QC / normalize / 聚类 | `scanpy-qc` / `scanpy-preprocess` / `scanpy-cluster` |
| 空间 spot 细胞组成 | `spatial-deconv` |
| HESTA 门户图谱 | `hesta` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据对象 | 本地 `h5ad`（log1p normalize 到 1e4；基因名多为 symbol） |
| 模型 | 官方内置 `.pkl` 或本地路径；首次需下载 |
| 与 CIMA | 通用注释用本 skill；CIMA 本体用 `cima-cell-annotation` |

## Required inputs

| 任务 | 必填 |
|------|------|
| `annotate` | 已 preprocess 的 h5ad（或加 `--auto-normalize`） |
| `models` / `download` | 无；可选 `--model` |
| `demo` | 无（用 CellTypist 内置 sample） |

## Necessary questions

1. 用户未提供本地文件路径 → 补问路径，或建议先 `geo-sra` / `sc-ingest` → `scanpy-preprocess`
2. 组织/物种未说明 → 根据场景推荐模型（免疫默认 Low/High；肝/肺/脑等用对应组织模型）
3. 是否已有 `leiden` → 可作为 `--over-clustering leiden` 供 majority voting
4. 提到 CIMA / TrueBlood → 确认是否应改用 `cima-cell-annotation`

## Workflow

1. **Gather**：确认 h5ad、模型名、是否 majority voting、输出目录  
2. **Act**：只运行 `./scripts/query.py`  
3. **Verify**：检查 `report.md`、`tables/`、`celltypist_annotated.h5ad`；不编造标签比例  

## Commands

```bash
python ./scripts/query.py models
python ./scripts/query.py download --model Immune_All_Low.pkl
python ./scripts/query.py annotate <h5ad> [-o outdir] [--model Immune_All_Low.pkl] [--majority-voting|--no-majority-voting] [--over-clustering leiden] [--auto-normalize]
python ./scripts/query.py demo [-o outdir]
```

依赖：`pip install celltypist`，以及 `pip install -r ../../requirements.txt`。

## Output contract

- `figures/`、`tables/`、`report.md`、`celltypist_annotated.h5ad`
- report 写明模型、majority voting、标签计数；无脚本结果不得虚构注释

## Guardrails

- 禁止重写分析逻辑；必须跑包内脚本
- 禁止把 CIMA TrueBlood 注释需求路由到本 skill
- 不做自定义模型训练（`celltypist.train` 超出本 skill v1）
- 模型需与查询组织匹配；默认免疫模型不适配脑/肝等专用场景时先 `models` 再选

## Errors and fallback

- 缺 `celltypist` → 提示 `pip install celltypist`
- 输入像 raw counts → 提示先 `scanpy-preprocess`，或加 `--auto-normalize`
- 模型未缓存 → 脚本自动 `download`；网络失败则说明需可达 `celltypist.cog.sanger.ac.uk`
- `--over-clustering` 列不存在 → 列出 `obs` 列或先 `scanpy-cluster`

## Examples

```bash
cd skills/single-cell/celltypist-annotate
python ./scripts/query.py models
python ./scripts/query.py annotate preprocessed.h5ad -o out/celltypist --model Immune_All_Low.pkl --over-clustering leiden
python ./scripts/query.py demo -o out/celltypist_demo
```

## Citation

- Domínguez Conde et al., *Science* 2022；Xu et al., *Cell* 2023（CellTypist / 模型）
- Scanpy / AnnData；内嵌：`scverse_common/`

## 联动

- 找公开数据：`geo-sra`
- 单细胞：`sc-ingest` → `scanpy-qc` → `scanpy-preprocess` → `scanpy-cluster` → **`celltypist-annotate`** → `scanpy-markers`
- 多批次：`sc-multi-integrate` / `scvi-integrate`（注释前或后均可；整合后注释需注意批次）
- CIMA TrueBlood：`cima-cell-annotation`
- 空间：`spatial-ingest` → …（本 skill 面向单细胞级标签，非 spot 解卷积）
- 内嵌：`scverse_common/`

## 详细说明

见 [reference.md](reference.md)
