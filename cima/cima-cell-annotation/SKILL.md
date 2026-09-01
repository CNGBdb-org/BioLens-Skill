---
name: cima-cell-annotation
description: >-
  CIMA L1–L4 hierarchical cell annotation using TrueBlood marker signatures
  (73 leaves), optional user --marker-table, multi-round refine, --profile
  small/large, --sweep-resolutions, and --method transfer from a reference
  h5ad (CPU kNN / scanpy ingest; scVI-style mapping without GPU).
  Use after cima-scrna-preprocessing. Not for Step-1 QC or portal explore.
compatibility: Python 3.10+, scanpy, scikit-learn; optional cosg, harmonypy
metadata:
  author: cngbdb-skill-team
  version: "1.5.0"
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

CIMA 流水线 Step 2：按系群子聚类，并用 [TrueBlood CellType marker](https://db.cngb.org/trueblood/cima/cellType) 层级签名自动写 **L1–L4**（73 leaf ≈ 门户 `cell_type_l4`）。支持用户上传 **自定义 Marker 表**。**必须**调用包内脚本。

## Use When

- 已有 `CIMA_Annotation_1st.h5ad`（Step 1）
- 需要对 B / myeloid / TNK（含 CD4/CD8/NK）做 **L2–L4 细注释**
- 用户自带 marker 表做注释（`--marker-table`）
- 用已注释参考数据集做标签迁移（`--method transfer --reference`）
- 已有可靠标签，仅映射到本体（`--use-existing-annotation`）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| raw QC / 一级聚类 / 系群拆分 | `cima-scrna-preprocessing` |
| 门户细胞组成 / UMAP 基因图 | `cima-atlas-explore` |

## Multi-round refinement（人工迭代）

每轮结束后写出 `{lineage}_ambiguous_clusters.csv`（按 cluster 汇总 `annotation_margin`）。

| 参数 | 作用 |
|------|------|
| `--ambiguous-margin` | 中位 margin 低于此值标为 ambiguous（默认 0.05） |
| `--input-is-lineage` | 输入已是上一轮 `CIMA_*_subclustered.h5ad` |
| `--exclude-clusters 2,5` | 剔除这些簇，剩余重聚类；剔除细胞标为 `Ambiguous`（或 `--relabel-map`） |
| `--refine-clusters 2,5` | 只对模糊簇提高 `--resolution` 再细分重注，结果写回全表 |
| `--relabel-map 2:Doublet,5:Unknown` | 强制改标（也可指向 CSV：`cluster,label`） |
| `--cluster-key` | 指定上一轮 leiden 列（默认自动找） |

推荐对话流程：

1. 跑第一轮 → 打开 `*_ambiguous_clusters.csv`，把低 margin 簇给用户  
2. 用户决定：丢掉 / 强制改名 / 细分  
3. 用上一轮 h5ad + `--exclude-clusters` 或 `--refine-clusters` 再跑一轮  

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入 | Step 1 的 `CIMA_Annotation_1st.h5ad`（需 `celltype_1st`） |
| 默认本体 | `scripts/cima_celltype_ontology.json`（8 L1 → 73 leaves） |
| 自定义表 | CSV/TSV：`label` + `markers`（或 `positive`/`negative`） |
| 系群 | `all` / `B_cells` / `myeloid` / `TNK` / `CD4T` / `CD8T` / `NK` |

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | Annotation_1st h5ad |
| `--output` | 是 | 输出目录 |
| `--lineage` | 否 | 默认 all（跑 B_cells + myeloid + TNK） |
| `--resolution` | 否 | Leiden 分辨率（默认 1.0） |
| `--marker-table` | 否 | 用户 marker CSV/TSV |
| `--marker-mode` | 否 | `builtin`（默认）/ `custom` / `merge` |
| `--exclude-clusters` | 否 | 多轮：剔除先验簇 |
| `--refine-clusters` | 否 | 多轮：只细分先验簇 |
| `--relabel-map` | 否 | 多轮：强制改标 |
| `--ambiguous-margin` | 否 | 导出模糊簇阈值（默认 0.05） |
| `--profile` | 否 | `auto` / `small` / `large`（小样本少 PC、可跳过 Harmony） |
| `--sweep-resolutions` | 否 | 如 `0.4,0.8,1.0,1.2`；写出 sweep 摘要并自动选 margin 最优 |
| `--method` | 否 | `signature`（默认）/ `transfer` |
| `--reference` | transfer 时必填 | 已注释参考 h5ad |
| `--reference-label` | 否 | 参考标签列（默认 `cell_type_l4` 等） |
| `--transfer-backend` | 否 | `knn`（默认）/ `ingest` |
| `--use-existing-annotation` | 否 | 跳过重聚类，按名称映射本体 |
| `--min-margin` | 否 | leaf 分数边际阈值（默认 0） |
| `--merge-output` | 否 | 额外写出合并的 `CIMA_scRNA_Annotation.h5ad` |

## Marker table format

示例见 `examples/custom_markers_example.csv`：

```csv
label,markers,cell_type_l1
Naive_B_like,"MS4A1+,CD79A+,CD27-,IGHD+",B cells
NK_CD16_like,"NKG7+,FCGR3A+,CD3D-",NK
```

或拆列：

```csv
label,positive,negative,cell_type_l1
MyB,MS4A1;CD79A,CD3D,B cells
```

| `--marker-mode` | 行为 |
|-----------------|------|
| `builtin` | 仅 TrueBlood 73 leaf（默认；不要带 `--marker-table`） |
| `custom` | **只用**用户表；无 `cell_type_l1` 时全部挂到 `Custom`，写出 `custom_label` |
| `merge` | 同名 leaf **覆盖** marker；新 label 必须带 `cell_type_l1` |

## Necessary questions

1. 未完成 Step 1 → 先 `cima-scrna-preprocessing`
2. 未指定 lineage → 默认 all
3. 用户是否自带 marker 表 → `custom` 或 `merge`
4. 是否有已注释参考 h5ad → `--method transfer --reference`
5. 是否已有可靠细注释 → 才加 `--use-existing-annotation`

## Workflow

1. **Gather**：确认 Annotation_1st、lineage、marker 表/模式  
2. **Act**：只跑 `./scripts/cima_cell_annotation_cpu.py`  
3. **Verify**：检查 `cell_type_l1..l4` / `custom_label`、`*_l1_l4_assignments.csv`、UMAP；看脚本打印的 marker coverage  

## Commands

```bash
# 推荐：TrueBlood 签名 → L1–L4
python ./scripts/cima_cell_annotation_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step2_output/ \
  --lineage all \
  --resolution 1.0

# 用户自定义 marker（不映射 73 leaf）
python ./scripts/cima_cell_annotation_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step2_custom/ \
  --lineage all \
  --marker-table ./examples/custom_markers_example.csv \
  --marker-mode custom

# 在 TrueBlood 上覆盖/追加 marker
python ./scripts/cima_cell_annotation_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step2_merge/ \
  --marker-table ./examples/custom_markers_example.csv \
  --marker-mode merge

# 多轮：剔除模糊簇后重跑
python ./scripts/cima_cell_annotation_cpu.py \
  --input ./step2_output/CIMA_TNK_subclustered.h5ad \
  --output ./step2_r2/ \
  --lineage TNK \
  --input-is-lineage \
  --exclude-clusters 2,5 \
  --resolution 1.2

# 多轮：只对模糊簇细分重注
python ./scripts/cima_cell_annotation_cpu.py \
  --input ./step2_output/CIMA_TNK_subclustered.h5ad \
  --output ./step2_r2_refine/ \
  --lineage TNK \
  --input-is-lineage \
  --refine-clusters 2,5 \
  --resolution 1.5

# 参数梯度实验（自动选 median annotation_margin 最优）
python ./scripts/cima_cell_annotation_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step2_sweep/ \
  --lineage TNK \
  --profile small \
  --sweep-resolutions 0.4,0.8,1.0,1.2

# 参考迁移注释（CPU kNN，对齐 scVI mapping 的用法、不需要 GPU）
python ./scripts/cima_cell_annotation_cpu.py \
  --input CIMA_Annotation_1st.h5ad \
  --output ./step2_transfer/ \
  --lineage TNK \
  --method transfer \
  --reference /path/to/annotated_reference.h5ad \
  --reference-label cell_type_l4

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
3. 在**全基因**矩阵上对 ontology / 用户 leaf 的 `+/-` marker 签名打分  
4. 以 **cluster 均值**选最佳 leaf，回填路径：`cell_type_l1`…`cell_type_l4`（custom 另写 `custom_label`）  
5. DEG/COSG 仍输出，供人工复核  

> 这是 atlas / 用户 marker 规则 + 聚类的可复现近似，**不能**保证与论文人工注释逐细胞一致。低 `annotation_margin` 的 cluster 应人工检查。

## Reference transfer (`--method transfer`)

把已注释参考（用户自己的 atlas、上一批数据、或 CIMA 子集 h5ad）的标签迁到 query：

1. 取共享基因 → 参考 HVG → **联合 PCA**  
2. 在 PCA 空间对每个 query 细胞做 kNN，**多数投票**  
3. `annotation_score` = 投票占比；`annotation_margin` = 第一名−第二名占比  
4. 能对上 TrueBlood 本体的写入 `cell_type_l1..l4`，原始迁移名写入 `custom_label`

`--transfer-backend ingest` 走 `scanpy.tl.ingest`（基因必须对齐；失败则回退 knn）。  
**不内置 scVI 训练**：Skill 默认 CPU/无 GPU；有 scVI 环境时可自训后把带标签的 h5ad 当 `--reference`。

参考过大时按标签分层抽到 `--reference-max-cells`（默认 2 万）。

## Output contract

- `CIMA_{lineage}_subclustered.h5ad`（含 `cell_type_l1`…`l4`、可选 `custom_label`、`annotation_score`、`annotation_margin`）
- `{lineage}_l1_l4_assignments.csv`
- `{lineage}_ambiguous_clusters.csv`（多轮人工决策入口）
- `{lineage}_sweep_summary.csv`（若启用 `--sweep-resolutions`）
- `figures/umap_{lineage}_*.pdf`
- 无脚本结果不得编造标签

## Guardrails

- 必须跑包内脚本；禁止临时重写注释逻辑  
- 默认本体以包内 `cima_celltype_ontology.json` 为准；`custom` 模式以用户表为准  
- 与门户预计算注释区分：本地重算用本 Skill，查询用 `cima-atlas-explore`

## Errors and fallback

- 缺 cosg → 仍可注释；仅少 COSG 表  
- 输入缺 `celltype_1st` → 回报并建议回退 Step 1  
- marker 基因大量缺失 → 脚本打印 coverage；结果不可靠  
- `merge` 新增 label 缺 `cell_type_l1` → 报错，改用 `custom` 或补列  

## Examples

**用户**：对 Step1 的 Annotation_1st 做全系群 L4 注释  

```bash
cd skills/cima/cima-cell-annotation
python ./scripts/cima_cell_annotation_cpu.py \
  --input /path/to/CIMA_Annotation_1st.h5ad \
  --output ./step2_output/ \
  --lineage all
```

**用户**：用已注释的参考集做标签迁移  

```bash
python ./scripts/cima_cell_annotation_cpu.py \
  --input /path/to/CIMA_Annotation_1st.h5ad \
  --output ./step2_transfer/ \
  --lineage TNK \
  --method transfer \
  --reference /path/to/ref_annotated.h5ad \
  --reference-label cell_type_l4
```

**用户**：我有自己的 marker 表，不要只用 TrueBlood  

```bash
python ./scripts/cima_cell_annotation_cpu.py \
  --input /path/to/CIMA_Annotation_1st.h5ad \
  --output ./step2_custom/ \
  --marker-table /path/to/my_markers.csv \
  --marker-mode custom
```

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)  
Marker ontology: [TrueBlood CellType](https://db.cngb.org/trueblood/cima/cellType)
