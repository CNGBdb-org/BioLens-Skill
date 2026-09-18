---
name: ckb-meta-survival
description: >-
  Microbiome-based survival analysis. Performs univariate Cox regression screening
  of taxa/functional features, constructs risk scores, plots Kaplan-Meier curves,
  timeROC analysis, and forest plots. Input: merged abundance matrix + metadata
  with survival time and event/status columns (0/1 coded). Use for linking
  microbiome features to patient survival or disease progression time. Not for
  group comparison (use ckb-meta-differential) or classification (use
  ckb-meta-machine-learning).
compatibility: "Python 3.10+; lifelines ≥0.27; pandas; numpy; matplotlib; PyYAML"
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

# ckb-meta-survival：生存分析

## Use When
- 分析微生物特征与患者生存时间（OS/PFS）的关联
- 需要 Cox 单因素筛选、KM 曲线、timeROC 分析
- 输入来自 ckb-meta-merge 的矩阵 + 含时间/终点的 metadata

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 组间差异比较 | ckb-meta-differential |
| 分类建模 AUC | ckb-meta-machine-learning |
| 无生存终点数据 | 停止，此 skill 专门用于生存分析 |

## 软件依赖

```bash
python3 -c "import lifelines, pandas, numpy, matplotlib, yaml"
# 安装：pip install lifelines pandas numpy matplotlib pyyaml
# 要求：lifelines >= 0.27.0
```

无数据库依赖。

## Required Inputs

| 参数 | 说明 |
|---|---|
| abundance_path | merged 物种或功能矩阵 |
| metadata_path | metadata.tsv（含 time_col 和 status_col）|
| sample_id_col | 样本 ID 列名 |
| time_col | 生存时间列名（数值，单位：月/天）|
| status_col | 终点事件列名（0=删失，1=事件发生）|

## Necessary Questions

1. 未提供 time_col 或 status_col → 停止，要求提供生存时间和终点事件列名
2. status_col 非 0/1 编码 → 提示用户转换编码方式
3. 事件数 <5 → 警告，Cox 回归结果不可靠

## Workflow

**Gather**：确认矩阵、metadata、time_col、status_col

**Act**：
```bash
python3 scripts/run_survival_analysis.py --config config.yaml
```

config.yaml 示例：
```yaml
input:
  mode: separated
  abundance_path: merged_species_only.tsv
  survival_metadata_path: metadata.tsv
  sample_id_col: sample_id
  time_col: survival_time
  status_col: survival_status
  abundance_format: wide_feature_by_sample
methods:
  cox_screening: univariate_cox
  correction: BH_FDR
  padj_threshold: 0.05
  km_split: median
output:
  dir: survival_output/
```

**Verify**：`cat survival_output/cox_results.tsv`

## Output Contract

| 文件 | 说明 |
|---|---|
| `cox_results.tsv` | 单因素 Cox HR、95%CI、p-value、padj |
| `risk_score.tsv` | 样本风险评分 |
| `figures/km_curve.png` | KM 生存曲线（高低风险组）|
| `figures/timeroc.png` | timeROC 曲线 |
| `figures/forest_plot.png` | 显著特征 forest plot |
| `survival_report.md` | Markdown 报告 |

## Guardrails

- time_col / status_col 缺失时严格停止，不默认猜测列名
- status_col 必须为 0/1 二值

## Citation

- lifelines: Davidson-Pilon et al., 2020. https://github.com/CamDavidsonPilon/lifelines
- timeROC: Blanche et al., Biometrics 2013
