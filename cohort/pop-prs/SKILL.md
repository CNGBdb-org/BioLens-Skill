---
name: pop-prs
description: >-
  Polygenic risk score (PRS) calculation and evaluation: supports PRSice2,
  PRS-CS, LDpred2, and PLINK --score methods. Calculates PRS from GWAS
  summary statistics, evaluates predictive performance (AUC, R2), and
  generates score distributions. Use for genetic risk prediction from
  GWAS results. Not for GWAS association testing (use pop-gwas-association),
  genotype QC (use pop-genotype-qc), or Mendelian randomization.
compatibility: Python 3.10+, PLINK 1.9+, pandas, numpy, matplotlib
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-prs.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Polygenic Risk Score（群体多基因风险评分）

从 GWAS summary statistics 计算个体的多基因风险评分。

## Use When

- 有了 GWAS summary stats，要计算目标群体的 PRS
- 评估遗传风险预测能力（AUC / R2）
- 对比不同 PRS 方法（PRSice2 / PRS-CS / LDpred2 / PLINK score）
- PRS 分层分析（高分段 vs 低分段疾病风险）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS 关联分析 | `pop-gwas-association` |
| 基因型质控 | `pop-genotype-qc` |
| 精细定位 | `pop-finemapping`（待建） |
| 孟德尔随机化 | `pop-mr-smr`（待建） |

## Workflow

1. **Gather**：确认 GWAS summary stats、目标基因型、方法选择
2. **Clumping**：LD-based SNP 剪枝（PLINK --clump，使用参考 LD 面板）
3. **Scoring**：
   - PLINK --score：简单加权累加
   - PRSice2：多阈值扫描（best p-value threshold）
   - PRS-CS：贝叶斯收缩（需 Python + LD 参考面板）
   - LDpred2：LD 调整（需 R + bigsnakes）
4. **Evaluation**：AUC（二分类）/ R2（连续型）→ PRS 分布图
5. **Output**：per-individual PRS + performance metrics + plots

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --sumstats <gwas.txt> --target <prefix> --output <outdir>` |
| Clumping | `python ./scripts/query.py clump run --sumstats <gwas.txt> --target <prefix> --output <outdir> --p1 5e-8 --p2 1e-2 --r2 0.1` |
| PLINK score | `python ./scripts/query.py score plink --sumstats <gwas.txt> --target <prefix> --output <outdir>` |
| PRSice2 | `python ./scripts/query.py score prsice2 --sumstats <gwas.txt> --target <prefix> --output <outdir> --binary` |
| PRS-CS | `python ./scripts/query.py score prscs --sumstats <gwas.txt> --target <prefix> --output <outdir>` |
| LDpred2 | `python ./scripts/query.py score ldpred2 --sumstats <gwas.txt> --target <prefix> --output <outdir>` |
| 评估 AUC | `python ./scripts/query.py evaluate auc --scores <scores.txt> --pheno <pheno.txt> --output <outdir>` |
| 评估 R2 | `python ./scripts/query.py evaluate r2 --scores <scores.txt> --pheno <pheno.txt> --output <outdir>` |
| 分布图 | `python ./scripts/query.py plot distribution --scores <scores.txt> --output <dist.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --method | plink | 方法（plink/prsice2/prscs/ldpred2） |
| --p1 | 5e-8 | Clumping p1 阈值（index SNP） |
| --p2 | 1e-2 | Clumping p2 阈值（companion SNP） |
| --r2 | 0.1 | Clumping LD r2 阈值 |
| --kb | 250 | Clumping 窗口（kb） |
| --binary | False | 是否二分类性状 |

## Guardrails

- GWAS summary stats 需含 SNP, A1, BETA/OR, P 列
- 目标基因型需 QC 后
- PRSice2/PRS-CS/LDpred2 需单独安装，脚本自动检测
- LD 参考面板可选（默认用目标样本自身的 LD）

## Citation

- PRSice2: Choi & Mak, 2018
- PRS-CS: Ge et al., Nature Communications 2019
- LDpred2: Privé et al., 2020
- PGS Catalog: Lambert et al., Nature Genetics 2021
