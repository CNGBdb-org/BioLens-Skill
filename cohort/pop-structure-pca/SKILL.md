---
name: pop-structure-pca
description: >-
  Population structure analysis: LD pruning, PCA, eigenvalue/eigenvector
  computation, population clustering, and ancestry inference. Use for
  detecting population stratification, batch effects, ancestry components,
  and sample outliers before GWAS. Accepts PLINK bed/bim/fam input.
  Not for genotype QC (use pop-genotype-qc), imputation (use pop-imputation),
  GWAS association (use pop-gwas-association), or rare variant analysis.
compatibility: Python 3.10+, PLINK 1.9+/2.0, pandas, numpy, sklearn, matplotlib
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-structure.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Structure PCA（群体结构分析）

通过 LD 剪枝 + PCA 分析群体分层、批次效应和祖源构成。

## Use When

- GWAS 前检测群体分层（需要做 PCA 校正）
- 检查样本是否有批次效应
- 推断样本的祖源构成
- 识别离群样本（非目标祖源）
- 可视化群体结构

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 样本/变异质控 | `pop-genotype-qc` |
| 基因型填充 | `pop-imputation` |
| GWAS 关联分析 | `pop-gwas-association` |
| 变异功能注释 | `pop-variant-annotation` |
| 多基因风险评分 | `pop-prs` |

## Workflow

1. **Gather**：确认输入（QC 后的 PLINK 前缀）、PC 数量、LD 剪枝参数
2. **LD Pruning**：PLINK --indep-pairwise（默认 50 5 0.2）
3. **PCA**：PLINK --pca（默认 10 个 PC）
4. **Clustering**：sklearn KMeans 或层次聚类
5. **Outlier Detection**：PC 离群检测（默认 6 SD）
6. **Visualization**：PC1 vs PC2 散点图 + 解释方差
7. **Output**：eigenvalues, eigenvectors, cluster labels, plot

## Commands

```bash
python ./scripts/query.py <module> [args…]
```

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --input <prefix> --output <outdir>` |
| LD 剪枝 | `python ./scripts/query.py ld prune --input <prefix> --output <outdir> --window 50 --step 5 --r2 0.2` |
| PCA | `python ./scripts/query.py pca compute --input <prefix> --output <outdir> --n-pcs 10` |
| 聚类 | `python ./scripts/query.py cluster kmeans --eigenvec <file> --n-clusters 3 --output <outdir>` |
| 离群检测 | `python ./scripts/query.py outlier detect --eigenvec <file> --output <outdir> --sd 6` |
| 可视化 | `python ./scripts/query.py plot scatter --eigenvec <file> --eigenval <file> --output <plot.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --n-pcs | 10 | 计算的 PC 数量 |
| --window | 50 | LD 剪枝窗口大小（kb） |
| --step | 5 | LD 剪枝步长 |
| --r2 | 0.2 | LD r2 阈值 |
| --sd | 6 | 离群检测 SD 倍数 |
| --n-clusters | 3 | KMeans 聚类数 |

## Guardrails

- 输入应为 QC 后的 PLINK 格式（建议先跑 pop-genotype-qc）
- PLINK 路径自动检测
- 可视化需 matplotlib + seaborn

## Citation

- Price et al., Nature Reviews Genetics 2006 (PCA correction)
- Purcell et al., 2007 (PLINK --indep)
- Pritchard et al., 2000 (ADMIXTURE 原理)
