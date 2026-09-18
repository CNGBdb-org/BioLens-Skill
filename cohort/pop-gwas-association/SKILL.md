---
name: pop-gwas-association
description: >-
  Genome-wide association study (GWAS) analysis: supports REGENIE, SAIGE,
  BOLT-LMM, and PLINK association testing for quantitative and binary traits.
  Includes covariate correction (PCA, age, sex), multiple testing correction,
  Manhattan/QQ plots, and summary statistics output. Use for GWAS from
  imputed genotypes with phenotype data. Not for genotype QC (use
  pop-genotype-qc), rare variant burden testing (use pop-rare-variant-burden),
  PRS (use pop-prs), or published GWAS Catalog lookup (use gwascatalog).
compatibility: Python 3.10+, PLINK 1.9+, REGENIE/SAIGE/BOLT-LMM (optional), pandas, matplotlib
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-gwas.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population GWAS Association（群体 GWAS 关联分析）

支持 REGENIE / SAIGE / BOLT-LMM / PLINK 的全基因组关联分析。

## Use When

- 对填充后基因型做 GWAS 关联分析
- 连续型性状（身高、BMI、血脂等）或二分类性状（病例/对照）
- 需要协变量校正（PCA、年龄、性别）
- 生成 Manhattan plot、QQ plot
- 输出 summary statistics（用于后续 PRS、MR 分析）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 样本/变异质控 | `pop-genotype-qc` |
| 群体结构 PCA | `pop-structure-pca` |
| 基因型填充 | `pop-imputation` |
| 罕见变异 burden 检验 | `pop-rare-variant-burden` |
| 多基因风险评分 | `pop-prs` |
| 精细定位 | `pop-finemapping` |
| 已发表 GWAS Catalog 查询 | `gwascatalog` |
| 综合可视化（已有 sumstats） | `pop-gwas-visualization` |

## Workflow

1. **Gather**：确认基因型格式、表型文件、协变量、工具选择
2. **Covariate Prep**：合并 PCA + 临床协变量 → 协变量文件
3. **Association**：
   - PLINK2: `--glm` （简单快速）
   - REGENIE: Step1 (null model) → Step2 (association)
   - SAIGE: Step1 (null) → Step2 (SPA)
   - BOLT-LMM: 混合模型
4. **Post-processing**：genomic inflation factor (λGC) → 多重检验校正
5. **Visualization**：Manhattan plot + QQ plot
6. **Output**：summary statistics (.sumstats) + plots

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --input <prefix> --pheno <pheno.txt> --output <outdir>` |
| PLINK 关联 | `python ./scripts/query.py association plink --input <prefix> --pheno <pheno.txt> --covar <covar.txt> --output <outdir>` |
| REGENIE | `python ./scripts/query.py association regenie --input <prefix> --pheno <pheno.txt> --covar <covar.txt> --output <outdir> --binary` |
| SAIGE | `python ./scripts/query.py association saige --input <prefix> --pheno <pheno.txt> --covar <covar.txt> --output <outdir> --binary` |
| BOLT-LMM | `python ./scripts/query.py association bolt --input <prefix> --pheno <pheno.txt> --covar <covar.txt> --output <outdir>` |
| Manhattan plot | `python ./scripts/query.py plot manhattan --sumstats <file> --output <manhattan.png>` |
| QQ plot | `python ./scripts/query.py plot qq --sumstats <file> --output <qq.png>` |
| λGC 计算 | `python ./scripts/query.py stats lambdagc --sumstats <file> --output <outdir>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --pval-threshold | 5e-8 | 全基因组显著性阈值 |
| --tool | plink | 默认工具（plink/regenie/saige/bolt） |
| --binary | False | 是否二分类性状 |
| --maf | 0.01 | 分析 MAF 下限 |
| --n-pcs | 10 | 协变量中 PCA 数量 |

## Guardrails

- 输入应为填充后 + QC 后的基因型
- 表型文件格式：FID IID PHENO（空格分隔，第一行表头）
- REGENIE/SAIGE/BOLT-LMM 需单独安装，脚本自动检测
- PLINK 的 --glm 替代旧版 --linear/--logistic

## Citation

- REGENIE: Mbatchou et al., Nature Genetics 2021
- SAIGE: Zhou et al., Nature Genetics 2018
- BOLT-LMM: Loh et al., Nature Genetics 2015
- PLINK2: Chang et al., 2015
