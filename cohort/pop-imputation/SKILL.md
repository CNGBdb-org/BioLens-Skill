---
name: pop-imputation
description: >-
  Genotype imputation pipeline: pre-imputation QC, phasing preparation
  (Eagle/SHAPEIT4), imputation submission for TOPMed/HRC reference panels,
  and post-imputation QC (info score, allele frequency concordance).
  Use for filling untyped variants from typed SNPs via reference panel.
  Accepts QC'd PLINK bed/bim/fam. Not for genotype QC (use pop-genotype-qc),
  population structure (use pop-structure-pca), or GWAS association.
compatibility: Python 3.10+, PLINK 1.9+, Eagle2/SHAPEIT4 (optional), Minimac4 (optional)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-imputation.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Genotype Imputation（群体基因型填充）

从已分型 SNP 推断未分型变异，支持 TOPMed / HRC 参考面板。

## Use When

- GWAS 前做基因型填充（提升变异覆盖率和统计功效）
- 需要将基因芯片数据填充到全基因组变异
- 已有填充结果需要做后质控（info score 过滤）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 样本/变异质控 | `pop-genotype-qc` |
| 群体结构 PCA | `pop-structure-pca` |
| GWAS 关联分析 | `pop-gwas-association` |
| 变异功能注释 | `pop-variant-annotation` |

## Workflow

1. **Pre-imputation QC**：检查 genome build → allele alignment → strand check
2. **Phasing**：Eagle2 或 SHAPEIT4（自动检测，未安装则提示）
3. **Imputation**：准备 TOPMed/HRC Server 提交文件（或本地 Minimac4）
4. **Post-imputation QC**：info score 过滤 → AF concordance → 跨批次合并
5. **Output**：imputed genotype + QC report

## Commands

| 任务 | 命令 |
|------|------|
| 全流程准备 | `python ./scripts/query.py pipeline prepare --input <prefix> --output <outdir> --ref TOPMed` |
| 前质控 | `python ./scripts/query.py preqc check --input <prefix> --output <outdir>` |
| Phasing 准备 | `python ./scripts/query.py phase prepare --input <prefix> --output <outdir>` |
| 填充后质控 | `python ./scripts/query.py postqc filter --input <imputed_dir> --output <outdir> --info 0.3 --r2 0.3` |
| AF 一致性检查 | `python ./scripts/query.py postqc afcheck --typed <prefix> --imputed <imputed_dir> --output <outdir>` |
| 生成提交文件 | `python ./scripts/query.py submit prepare --input <prefix> --ref TOPMed --output <submit_dir>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --ref | TOPMed | 参考面板（TOPMed / HRC / 1000G） |
| --info | 0.3 | info score 下限 |
| --r2 | 0.3 | imputation r2 下限 |
| --maf-imp | 0.005 | 填充后 MAF 下限 |

## Guardrails

- 输入应为 QC 后的 PLINK 格式
- Phasing 工具（Eagle/SHAPEIT4）需单独安装，脚本会自动检测
- TOPMed/HRC Server 需在线提交，脚本仅准备提交文件
- 本地 Minimac4 需单独安装

## Citation

- Das et al., 2016 (genotype imputation review)
- Browning & Browning, 2016 (phasing methods)
- TOPMed Imputation Server: https://imputation.biodatacatalyst.nhlbi.nih.gov/
- HRC Imputation Server: https://imputation.hrc.umich.edu/
