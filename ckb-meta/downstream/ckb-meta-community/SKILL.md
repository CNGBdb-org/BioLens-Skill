---
name: ckb-meta-community
description: >-
  Community-level microbiome diversity analysis. Computes alpha diversity
  (Shannon, observed species, Simpson, Pielou evenness), beta diversity
  (Bray-Curtis, Jaccard, Aitchison distances), PCoA/PCA/NMDS ordination, and
  PERMANOVA group comparison. Input: merged species abundance matrix from
  ckb-meta-merge + sample metadata with group column. Use for microbiome
  diversity comparison between groups. Not for differential abundance of
  individual taxa (use ckb-meta-differential), or functional analysis (use
  ckb-meta-functional).
compatibility: "Python 3.10+; scipy; scikit-bio; pandas; matplotlib; PyYAML"
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

# ckb-meta-community：群落多样性分析

## Use When
- 比较不同组别（病例/对照、治疗前后）的微生物群落多样性
- 需要 alpha 多样性箱线图、beta 多样性 PCoA 图、PERMANOVA 检验
- 输入来自 ckb-meta-merge 的 merged_species_only.tsv

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 差异物种（具体哪个菌显著差异）| ckb-meta-differential |
| 功能通路分析 | ckb-meta-functional |
| 机器学习分类建模 | ckb-meta-machine-learning |

## 软件依赖

```bash
python3 -c "import scipy, pandas, matplotlib, yaml"
# 安装：pip install scipy pandas matplotlib scikit-bio pyyaml
#       conda install -c conda-forge scipy pandas matplotlib pyyaml
```

无数据库依赖。

## Required Inputs

| 参数 | 说明 |
|---|---|
| abundance_path | merged_species_only.tsv（来自 ckb-meta-merge）|
| metadata_path | metadata.tsv |
| sample_id_col | metadata 中样本 ID 列名 |
| group_col | 分组列名（如 group / disease / treatment）|
| abundance_orientation | `wide_feature_by_sample` 或 `wide_sample_by_feature` |

## Necessary Questions

1. 未提供 group_col → 停止，询问分组列名
2. 未提供 metadata → 停止，要求提供 metadata 文件

## Workflow

**Gather**：确认矩阵路径、metadata 路径、group_col 存在

**Act**：
```bash
python3 scripts/run_community_analysis.py --config config.yaml
```

config.yaml 示例：
```yaml
input:
  mode: separated
  abundance_path: merged_species_only.tsv
  metadata_path: metadata.tsv
  metadata_sample_id_col: sample_id
  metadata_group_col: group
  abundance_orientation: wide_feature_by_sample
output:
  dir: community_output/
```

**Verify**：检查 `community_output/figures/` 下 alpha_shannon_boxplot.png 和 pcoa_bray.png 存在

## Output Contract

| 文件 | 说明 |
|---|---|
| `alpha_diversity.tsv` | 每个样本的 alpha 多样性指标 |
| `alpha_group_statistics.tsv` | 各组 alpha 指标统计检验结果（Wilcoxon/Kruskal）|
| `beta_distance_bray.tsv` | Bray-Curtis 距离矩阵 |
| `permanova_results.tsv` | PERMANOVA 检验结果（R²、p-value）|
| `figures/alpha_shannon_boxplot.png` | Shannon 多样性箱线图 |
| `figures/pcoa_bray.png` | Bray-Curtis PCoA 图 |
| `community_analysis_report.md` | Markdown 分析报告 |

## Guardrails

- group_col 缺失时严格停止，不默认任意分组
- 不在 per-sample profile（未合并）上运行

## Citation

- Bray-Curtis: Bray & Curtis, 1957; scipy.spatial.distance
- PERMANOVA: Anderson, 2001; implemented in scikit-bio
