---
name: cima-cell-annotation
description: >-
  CIMA L1–L4 hierarchical cell annotation using TrueBlood marker signatures
  (73 leaves). Leiden subclustering per lineage + signature scoring →
  cell_type_l1..l4. Use after cima-scrna-preprocessing (CIMA_Annotation_1st.h5ad).
  Not for Step-1 QC (use cima-scrna-preprocessing), generic markers
  (use scanpy-markers), or portal explore (use cima).
compatibility: Python 3.10+, scanpy; optional cosg, harmonypy
metadata:
  author: cngbdb-skill-team
  version: "1.1.0"
  scope: database-unique
  depth: L5
  domain: single-cell
  capability_id: cngbdb.cima.cell-annotation.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA Cell Annotation

CIMA 流水线 Step 2：按系群子聚类，并用 [TrueBlood CellType marker](https://db.cngb.org/trueblood/cima/cellType) 层级签名自动写 **L1–L4**（73 leaf ≈ 门户 `cell_type_l4`）。**必须**调用包内脚本。

## Use When

- 已有 `CIMA_Annotation_1st.h5ad`（Step 1）
- 需要对 B / myeloid / TNK（含 CD4/CD8/NK）做 **L2–L4 细注释**
- 已有可靠标签，仅映射到本体（`--use-existing-annotation`）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| raw QC / 一级聚类 / 系群拆分 | `cima-scrna-preprocessing` |
| 通用 cluster marker | `scanpy-markers` |
| 门户细胞组成 / UMAP 基因图 | `cima` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入 | Step 1 的 `CIMA_Annotation_1st.h5ad`（需 `celltype_1st`） |
| 本体 | `scripts/cima_celltype_ontology.json`（8 L1 → 73 leaves） |
| 系群 | `all` / `B_cells` / `myeloid` / `TNK` / `CD4T` / `CD8T` / `NK` |

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | Annotation_1st h5ad |
| `--output` | 是 | 输出目录 |
| `--lineage` | 否 | 默认 all（跑 B_cells + myeloid + TNK） |
| `--resolution` | 否 | Leiden 分辨率（默认 1.0） |
| `--use-existing-annotation` | 否 | 跳过重聚类，按名称映射本体 |
| `--min-margin` | 否 | leaf 分数边际阈值（默认 0） |
| `--merge-output` | 否 | 额外写出合并的 `CIMA_scRNA_Annotation.h5ad` |

## Necessary questions

1. 未完成 Step 1 → 先 `cima-scrna-preprocessing`
2. 未指定 lineage → 默认 all
3. 是否已有可靠细注释 → 才加 `--use-existing-annotation`

## Workflow

1. **Gather**：确认 Annotation_1st、lineage、是否沿用注释  
2. **Act**：只跑 `./scripts/cima_cell_annotation_cpu.py`  
3. **Verify**：检查 `cell_type_l1..l4`、`*_l1_l4_assignments.csv`、UMAP 图  

## Commands

```bash
# 推荐：子聚类 + TrueBlood marker 签名 → L1–L4
python ./scripts/cima_cell_annotation_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step2_output/ \
  --lineage all \
  --resolution 1.0

# 已有细标签：仅映射到本体层级
python ./scripts/cima_cell_annotation_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step2_output/ \
  --lineage B_cells \
  --use-existing-annotation \
  --celltype-col final_annotation
```

## How annotation works

1. 按 L1 / `celltype_1st` 取系群子集  
2. HVG → PCA →（可选 Harmony）→ neighbors → UMAP → Leiden  
3. 在**全基因**矩阵上对 ontology leaf 的 `+/-` marker 签名打分  
4. 以 **cluster 均值**选最佳 leaf，回填路径：`cell_type_l1`…`cell_type_l4`  
5. DEG/COSG 仍输出，供人工复核  

> 这是 atlas marker 规则 + 聚类的可复现近似，**不能**保证与论文 1000 万细胞人工注释逐细胞一致。低 `annotation_margin` 的 cluster 应人工检查。

## Output contract

- `CIMA_{lineage}_subclustered.h5ad`（含 `cell_type_l1`…`l4`、`annotation_score`、`annotation_margin`）
- `{lineage}_l1_l4_assignments.csv`
- `figures/umap_{lineage}_cell_type_l{1,2,4}.pdf`
- 无脚本结果不得编造 L4 标签

## Guardrails

- 必须跑包内脚本；禁止临时重写注释逻辑  
- 本体以包内 `cima_celltype_ontology.json` 为准（源自 TrueBlood）  
- 与门户预计算注释区分：本地重算用本 Skill，查询用 `cima`

## Errors and fallback

- 缺 cosg → 仍可 L1–L4 注释；仅少 COSG 表  
- 输入缺 `celltype_1st` → 回报并建议回退 Step 1  
- demo/合成数据 marker 弱 → L4 可能不稳定，以 `annotation_margin` 判断  

## Examples

**用户**：对 Step1 的 Annotation_1st 做全系群 L4 注释  

```bash
cd skills/cima/cima-cell-annotation
python ./scripts/cima_cell_annotation_cpu.py \
  --input /path/to/CIMA_Annotation_1st.h5ad \
  --output ./step2_output/ \
  --lineage all
```

**产出**：`CIMA_B_cells_subclustered.h5ad` 等、`*_l1_l4_assignments.csv`、`figures/umap_*_cell_type_l4.pdf`

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)  
Marker ontology: [TrueBlood CellType](https://db.cngb.org/trueblood/cima/cellType)
