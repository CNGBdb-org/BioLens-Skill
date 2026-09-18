---
name: ckb-meta-machine-learning
description: >-
  Supervised machine learning for microbiome-based disease classification and
  biomarker discovery. Supports Random Forest, SVM, and Logistic Regression with
  cross-validation, ROC/PR curve, feature importance, and repeated RFE biomarker
  selection. Input: merged species abundance matrix + metadata with binary label
  column. Use for building classifiers and selecting discriminative taxa. Not for
  community diversity (use ckb-meta-community), group statistics (use
  ckb-meta-differential), or survival prediction (use ckb-meta-survival).
compatibility: "Python 3.10+; scikit-learn ≥1.3; pandas; numpy; matplotlib; PyYAML"
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

# ckb-meta-machine-learning：机器学习分类与 Biomarker 筛选

## Use When
- 需要基于微生物丰度建立疾病/表型二分类模型
- 需要 ROC 曲线、AUC、PR 曲线
- 需要筛选具有区分能力的 biomarker（重要特征）

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 群落多样性比较 | ckb-meta-community |
| 差异物种统计检验 | ckb-meta-differential |
| 生存分析 | ckb-meta-survival |
| 多分类（>2 类）| 当前版本不支持，停止并说明 |

## 软件依赖

```bash
python3 -c "import sklearn, pandas, numpy, matplotlib, yaml"
# 安装：pip install scikit-learn pandas numpy matplotlib pyyaml
# 要求：scikit-learn >= 1.3.0
```

无数据库依赖。

## Required Inputs

| 参数 | 说明 |
|---|---|
| abundance_path | merged 物种或功能矩阵 |
| metadata_path | metadata.tsv |
| sample_id_col | 样本 ID 列名 |
| label_col | 二分类标签列名（0/1 或 case/control）|
| model | `random_forest`（默认）/ `svm` / `logistic` |

## Necessary Questions

1. 未提供 label_col → 停止，询问标签列名
2. 标签 >2 类 → 停止，说明当前只支持二分类
3. 样本数 <20 → 警告，ML 结果可靠性低

## Workflow

**Gather**：确认矩阵、metadata、label_col（恰好 2 个类别）

**Act**：
```bash
python3 scripts/run_machine_learning.py --config config.yaml
```

config.yaml 示例：
```yaml
input:
  mode: separated
  abundance_path: merged_species_only.tsv
  metadata_path: metadata.tsv
  sample_id_col: sample_id
  label_col: label
  feature_col: clade_name
  abundance_orientation: wide_feature_by_sample
model:
  type: random_forest
  cv_folds: 5
  n_estimators: 100
rfe:
  enabled: true
  n_repeats: 20
output:
  dir: ml_output/
```

**Verify**：`cat ml_output/roc_results.tsv`

## Output Contract

| 文件 | 说明 |
|---|---|
| `roc_results.tsv` | CV AUC 均值 ± 标准差 |
| `feature_importance.tsv` | 特征重要性排序 |
| `rfe_selected_features.tsv` | RFE 筛选的 biomarker |
| `figures/roc_curve.png` | ROC 曲线 |
| `figures/pr_curve.png` | PR 曲线 |
| `figures/feature_importance.png` | 重要性条形图 |
| `ml_report.md` | Markdown 报告 |

## Guardrails

- 不在未分裂的训练集上报告测试集 AUC（防止数据泄漏）
- label_col 缺失时严格停止

## Citation

- scikit-learn: Pedregosa et al., JMLR 2011. https://scikit-learn.org
- RFE: Guyon et al., JMLR 2002
