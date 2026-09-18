---
name: pop-mr-smr
description: >-
  Mendelian randomization (MR) and summary-based MR (SMR) analysis:
  supports SMR/HEIDI testing, TwoSampleMR (IVW, MR-Egger, weighted median),
  and MR-PRESSO. Tests causal effects of exposure (gene expression,
  protein levels) on outcome (disease) using GWAS + QTL summary statistics.
  Use for drug target validation, causal inference between molecular traits
  and disease, and pleiotropy detection. Not for GWAS association
  (use pop-gwas-association), colocalization (use pop-colocalization),
  or fine-mapping (use pop-finemapping). Not for CIMA pre-computed immune-disease
  SMR tables (use cima-smr-gwas).
compatibility: Python 3.10+, pandas, numpy; SMR binary/R+TwoSampleMR (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-mr.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population MR & SMR（群体孟德尔随机化）

使用 GWAS + QTL summary statistics 做因果推断，支持 SMR / TwoSampleMR / MR-PRESSO。

## Use When

- 检验基因表达/蛋白水平对疾病的因果效应
- 药物靶点验证（基因→疾病因果链）
- SMR + HEIDI 检验（变异→基因表达→疾病）
- 多效性检测（MR-Egger intercept）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS 关联分析 | `pop-gwas-association` |
| 共定位分析 | `pop-colocalization` |
| 精细定位 | `pop-finemapping` |
| 遗传度 | `pop-heritability-ldsc` |
| CIMA 预计算免疫病 SMR 表 | `cima-smr-gwas` |

## Workflow

1. **Gather**：确认暴露 sumstats（eQTL/protein QTL）+ 结局 sumstats（GWAS disease）
2. **SMR**：SMR CLI → SMR 关联 + HEIDI 检验
3. **TwoSampleMR**：IVW / MR-Egger / weighted median / weighted mode
4. **MR-PRESSO**：多效性离群检验
5. **Output**：因果效应估计 + HEIDI p + 多效性检验 + 散点图

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --exposure <eqtl.txt> --outcome <gwas.txt> --output <outdir>` |
| SMR | `python ./scripts/query.py run smr --exposure <eqtl.txt> --outcome <gwas.txt> --output <outdir>` |
| TwoSampleMR | `python ./scripts/query.py run twosample --exposure <eqtl.txt> --outcome <gwas.txt> --output <outdir>` |
| MR-PRESSO | `python ./scripts/query.py run presso --exposure <eqtl.txt> --outcome <gwas.txt> --output <outdir>` |
| 散点图 | `python ./scripts/query.py plot scatter --mr-results <file> --output <plot.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --smr-p-threshold | 2.46e-6 | SMR 显著性阈值（0.05/20000） |
| --heidi-threshold | 0.01 | HEIDI 检验 p 值阈值 |
| --pval-instrument | 5e-8 | 工具变量 p 值阈值 |
| --r2-threshold | 0.001 | LD r2 阈值（clumping） |
| --method | ivw | MR 方法（ivw/egger/weighted_median/all） |

## Guardrails

- SMR 需安装 SMR 二进制（http://yanglab.westlake.edu.cn/software/smr/）
- TwoSampleMR 需 R 包（install.packages("TwoSampleMR")）
- MR-PRESSO 需 R 包
- 未安装时使用 Python 近似 IVW

## Citation

- SMR: Zhu et al., Nature Genetics 2016
- TwoSampleMR: Hemani et al., eLife 2018
- MR-PRESSO: Verbanck et al., 2018
