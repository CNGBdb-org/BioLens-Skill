# Shared STOmics atlas toolkit

CNGB Cirrocumulus **parquet** skills shared by all atlases.

## Layout

```text
_shared/
├── lib/scripts/            # io_core, atlas_registry, atlas_runner, bootstrap
├── spatial/scripts/
├── markers/scripts/
└── …

datasets/
├── run.py                  # unified CLI (--atlas <name>)
├── custom/hesta|mosta|mccsta/   # atlas-only scripts only
└── datasets_list.tsv
```

## 运行

```bash
python .cursor/skills/datasets/run.py --atlas mosta spatial gene_expression E16.5_E1S1.MOSTA -g Sox2 --fast
python .cursor/skills/datasets/run.py --atlas hesta catalog list_datasets --stage CS23
```

**别名**（`atlas_runner`）：`plot_celltype_mask` / `plot_annotation_mask` → `plot_obs_mask`；`list_celltypes` / `list_annotations` → `list_obs_groups`。

## 共享脚本一览

| 模块 | 脚本 |
|------|------|
| spatial | plot_spatial_clusters, gene_expression, gene_summary, plot_spatial_gene, plot_spatial_qc, plot_spatial_batch, plot_obs_mask, list_markers |
| markers | compare_organs_gene, list_obs_groups, organ_overview, top_genes_by_group |
| cross-sample | gene_across_samples, gene_presence |
| catalog | list_datasets, recommend_sample, dataset_info |
| atlas-stats | organ_stage_landscape |
| susceptibility | virus_receptor_map |
| disease-genes | disease_gene_map |
| paper-markers | paper_panel |

## 新增 atlas

1. `datasets_list.tsv` 增加行 + `atlas_registry.py` 注册
2. `python datasets/run.py --atlas <name> catalog list_datasets` 验证
3. 更新 `stomics/SKILL.md`

**无需** per-atlas `run.py`、shim 或 SKILL.md（除非放入 `custom/` 的定制脚本）。
