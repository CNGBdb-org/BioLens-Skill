---
name: ckb-meta-differential
description: >-
  Differential abundance analysis of microbiome taxa or functional features
  between two groups. Uses CLR (centered log-ratio) transformation + Welch t-test
  or Wilcoxon rank-sum test, with BH FDR correction. Outputs differential results
  table, volcano plot, and heatmap of top features. Input: merged species or
  functional abundance matrix + metadata with group column. Use for identifying
  which taxa/functions differ significantly between groups. Not for community
  diversity (use ckb-meta-community) or survival analysis.
compatibility: "Python 3.10+; pandas; numpy; scipy; matplotlib; seaborn; PyYAML"
metadata:
  author: ckb-meta-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: metagenomics
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# ckb-meta-differential：差异丰度分析

## Use When
- 比较两组样本中哪些物种/功能特征显著差异
- 需要火山图、热图、显著特征列表
- 输入来自 ckb-meta-merge 的物种或功能矩阵

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 群落整体多样性 | ckb-meta-community |
| 多变量建模/biomarker 筛选 | ckb-meta-machine-learning |
| 功能通路富集 | ckb-meta-functional |

## 软件依赖

```bash
python3 -c "import pandas, numpy, scipy, matplotlib, seaborn, yaml"
# 安装：pip install pandas numpy scipy matplotlib seaborn pyyaml
```

无数据库依赖。

## Required Inputs

| 参数 | 说明 |
|---|---|
| abundance_path | merged 矩阵（物种或功能）|
| metadata_path | metadata.tsv |
| sample_id_col | 样本 ID 列名 |
| group_col | 分组列名（仅支持两组比较）|
| method | `clr_welch`（默认）或 `clr_wilcoxon` |

## Necessary Questions

1. 未提供 group_col → 停止
2. group_col 超过 2 个组 → 说明当前版本只支持两组，询问如何拆分

## Workflow

**Gather**：确认矩阵、metadata、group_col（恰好 2 个水平）

**Act**：
```bash
python3 scripts/run_differential_analysis.py --config config.yaml
```

config.yaml 示例：
```yaml
input:
  mode: separated
  abundance_path: merged_species_only.tsv
  metadata_path: metadata.tsv
  sample_id_col: sample_id
  group_col: group
  abundance_format: wide_feature_by_sample
methods:
  method: clr_welch
  correction: BH_FDR
  padj_threshold: 0.05
  log2fc_threshold: 1.0
output:
  dir: differential_output/
```

**Verify**：检查 `differential_output/differential_results.tsv` 存在

## Output Contract

| 文件 | 说明 |
|---|---|
| `differential_results.tsv` | 全特征差异结果（log2FC, pvalue, padj）|
| `significant_features.tsv` | 显著差异特征（padj<0.05 & |log2FC|>1）|
| `figures/volcano_plot.png` | 火山图 |
| `figures/differential_heatmap.png` | top 差异特征热图 |
| `differential_analysis_report.md` | Markdown 报告 |

## Guardrails

- 仅支持两组比较；多组需用户拆分后分别运行
- 不编造统计结果；脚本无输出时报错

## Citation

- CLR transformation: Aitchison 1986
- BH FDR: Benjamini & Hochberg, 1995
