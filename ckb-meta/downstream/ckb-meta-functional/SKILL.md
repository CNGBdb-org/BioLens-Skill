---
name: ckb-meta-functional
description: >-
  Functional differential analysis and pathway enrichment for metagenomics.
  Input: merged HUMAnN3 functional matrix (pathabundance / genefamilies /
  KO-regrouped) from ckb-meta-merge + metadata with group column. Performs
  CLR-based differential analysis of functional features, KEGG pathway enrichment,
  and functional heatmap. Use after ckb-meta-humann functional annotation and
  ckb-meta-merge. Not for species-level differential (use ckb-meta-differential)
  or community diversity (use ckb-meta-community).
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

# ckb-meta-functional：功能差异与通路富集分析

## Use When
- 分析两组间功能通路（MetaCyc pathway）或基因家族（UniRef90/KO）的差异
- 需要功能热图、通路富集结果
- 输入来自 ckb-meta-merge 的 merged_pathabundance.tsv 或 merged_genefamilies.tsv

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 物种水平差异 | ckb-meta-differential |
| 群落多样性 | ckb-meta-community |
| 功能矩阵未合并 | 先做 ckb-meta-merge |

## 软件依赖

```bash
python3 -c "import pandas, numpy, scipy, matplotlib, seaborn, yaml"
# 安装：pip install pandas numpy scipy matplotlib seaborn pyyaml
```

无需额外数据库（KO/通路信息由 HUMAnN3 输出内含）。

## Required Inputs

| 参数 | 说明 |
|---|---|
| abundance_path | merged_pathabundance.tsv 或 merged_genefamilies.tsv（来自 ckb-meta-merge）|
| metadata_path | metadata.tsv |
| sample_id_col | 样本 ID 列名 |
| group_col | 分组列名（两组比较）|
| feature_type | `pathway`（默认）/ `genefamily` / `ko` |

## Necessary Questions

1. 未提供 group_col → 停止，询问分组列
2. feature_type 未指定 → 询问用户分析的是通路（pathabundance）还是基因家族（genefamilies）

## Workflow

**Gather**：确认功能矩阵路径、metadata、group_col

**Act**：
```bash
python3 scripts/run_functional_analysis.py --config config.yaml
```

config.yaml 示例：
```yaml
input:
  mode: separated
  abundance_path: merged_pathabundance.tsv
  metadata_path: metadata.tsv
  sample_id_col: sample_id
  group_col: group
  feature_type: pathway
  abundance_format: wide_feature_by_sample
methods:
  method: clr_welch
  correction: BH_FDR
  padj_threshold: 0.05
output:
  dir: functional_output/
```

**Verify**：`cat functional_output/functional_differential_results.tsv`

## Output Contract

| 文件 | 说明 |
|---|---|
| `functional_differential_results.tsv` | 全功能特征差异结果（log2FC, padj）|
| `significant_functions.tsv` | 显著差异功能特征 |
| `figures/functional_heatmap.png` | top 差异功能热图 |
| `figures/functional_volcano.png` | 火山图 |
| `functional_report.md` | Markdown 报告 |

## Guardrails

- 功能矩阵必须来自 HUMAnN3 输出（合并后），不接受随机丰度矩阵
- group_col 缺失时严格停止

## Citation

- HUMAnN3: Franzosa et al., Nat Methods 2018
- MetaCyc: Caspi et al., Nucleic Acids Res 2020. https://metacyc.org
