---
name: ckb-meta-association
description: >-
  Microbiome-phenotype association analysis and co-abundance network construction.
  Supports two modes: (1) association mode — Spearman/Pearson correlation between
  taxa abundance and continuous phenotype variables; (2) network mode — SparCC or
  Pearson co-abundance network among taxa, with edge filtering and modularity
  analysis. Input: merged species abundance matrix + metadata with phenotype
  columns. Use for identifying microbiome-phenotype relationships or ecological
  co-occurrence patterns. Not for group comparison (use ckb-meta-differential)
  or supervised classification (use ckb-meta-machine-learning).
compatibility: "Python 3.10+; pandas; numpy; scipy; networkx; matplotlib; PyYAML"
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

# ckb-meta-association：表型关联与共丰度网络

## Use When
- 分析物种丰度与连续表型变量（BMI、年龄、血糖等）的相关性
- 构建物种间共丰度网络，识别菌群生态模块
- 输入来自 ckb-meta-merge 的合并矩阵 + metadata 表型列

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 组间差异（case vs control）| ckb-meta-differential |
| 监督学习/分类建模 | ckb-meta-machine-learning |
| 生存分析 | ckb-meta-survival |

## 软件依赖

```bash
python3 -c "import pandas, numpy, scipy, networkx, matplotlib, yaml"
# 安装：pip install pandas numpy scipy networkx matplotlib pyyaml
```

无数据库依赖。

## Required Inputs

| 参数 | 模式 | 说明 |
|---|---|---|
| abundance_path | 两种 | merged 物种矩阵 |
| metadata_path | association | metadata.tsv |
| phenotype_cols | association | 连续表型列名列表（如 [bmi, age]）|
| sample_id_col | 两种 | 样本 ID 列名 |
| mode | 两种 | `association` 或 `network` |
| correlation_method | network | `pearson`（默认）或 `sparcc` |

## Necessary Questions

1. `association` 模式未提供 phenotype_cols → 停止，询问表型列名
2. `network` 模式样本数 <10 → 提示网络结果可靠性低

## Workflow

**Gather**：确认模式（association/network）和必要参数

**Act**：
```bash
python3 scripts/run_association_network.py --config config.yaml
```

config.yaml（association 模式）示例：
```yaml
input:
  mode: association
  abundance_path: merged_species_only.tsv
  metadata_path: metadata.tsv
  sample_id_col: sample_id
  phenotype_cols: [bmi, age, blood_glucose]
  abundance_orientation: wide_feature_by_sample
output:
  dir: association_output/
```

**Verify**：检查 `association_output/association_results.tsv` 存在

## Output Contract

| 文件 | 说明 |
|---|---|
| `association_results.tsv` | 物种-表型相关系数与 FDR 矫正 p 值 |
| `network_edges.tsv` | 共丰度网络边列表（network 模式）|
| `figures/association_heatmap.png` | 关联热图 |
| `figures/network.png` | 网络可视化（network 模式）|

## Guardrails

- association 模式 phenotype_cols 必须为连续变量；分类变量请先用 ckb-meta-differential
- 不编造相关系数；脚本失败时报告错误信息

## Citation

- SparCC: Friedman & Alm, PLoS Comput Biol 2012
- networkx: Hagberg et al., 2008
