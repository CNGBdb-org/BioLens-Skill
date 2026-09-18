---
name: pop-pharmacogenomics
description: >-
  Pharmacogenomics (PGx) genotyping from VCF: supports star allele
  calling for CYP2D6, CYP2C19, CYP2C9, CYP3A5, SLCO1B1, and TPMT.
  Predicts drug metabolism phenotype (poor/intermediate/normal/rapid/
  ultrarapid metabolizer), checks drug-gene interactions against
  PharmGKB guidelines, and generates population PGx summary. Accepts
  VCF input. Use for precision medicine dosing, drug response
  prediction, and population PGx profiling. Not for GWAS
  (use pop-gwas-association), variant annotation of all SNPs
  (use pop-variant-annotation), or PharmGKB/CPIC API lookup (use pharmgkb).
compatibility: Python 3.10+, pysam, pandas
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L4
  domain: pharmacogenomics
  capability_id: cngbdb.genomics.pop-pgx.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Pharmacogenomics（群体药物基因组学）

从 VCF 做药物代谢酶 star allele 分型和表型预测。

## Use When

- CYP2D6 / CYP2C19 / CYP2C9 / CYP3A5 / SLCO1B1 / TPMT star allele 分型
- 预测药物代谢表型（PM / IM / NM / RM / UM）
- 群体 PGx 频率统计
- 药物剂量调整建议（参考 PharmGKB）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS 关联分析 | `pop-gwas-association` |
| SNP 功能注释 | `pop-variant-annotation` |
| 基因型质控 | `pop-genotype-qc` |
| 变异临床意义 | `clinvar` |
| PharmGKB / CPIC 指南查询 | `pharmgkb` |

## Workflow

1. **Gather**：确认 VCF、目标基因列表
2. **Star Allele Calling**：按定义 SNP 集合判断 star allele
3. **Phenotype Prediction**：基于 diplotype → phenotype 映射
4. **Population Summary**：等位基因频率 + 表型分布
5. **Output**：per-individual PGx report + population summary

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --vcf <file.vcf.gz> --output <outdir>` |
| Star allele 分型 | `python ./scripts/query.py genotype call --vcf <file.vcf.gz> --gene CYP2D6 --output <outdir>` |
| 表型预测 | `python ./scripts/query.py phenotype predict --genotype <pgx.tsv> --output <outdir>` |
| 群体统计 | `python ./scripts/query.py population summary --vcf <file.vcf.gz> --output <outdir>` |
| 剂量建议 | `python ./scripts/query.py dosing recommend --genotype <pgx.tsv> --drug codeine --output <outdir>` |

## Supported Genes & Star Alleles

| 基因 | 关键 star alleles | 主要药物 |
|------|-------------------|---------|
| CYP2D6 | *1, *2, *3, *4, *5, *10, *14 | 可待因、他莫昔芬、抗抑郁药 |
| CYP2C19 | *1, *2, *3, *17 | 氯吡格雷、PPI、抗抑郁药 |
| CYP2C9 | *1, *2, *3 | 华法林、NSAIDs |
| CYP3A5 | *1, *3 | 他克莫司 |
| SLCO1B1 | *1, *5 | 他汀类 |
| TPMT | *1, *2, *3A, *3C | 硫唑嘌呤 |

## Citation

- CPIC guidelines: https://cpicpgx.org/
- PharmGKB: Whirl-Carrillo et al., 2021
- CYP2D6: Gaedigk et al., 2018
- DPWG guidelines: https://www.uppsalamonitoring.org/
