---
name: pop-genotype-qc
description: >-
  Genotype quality control for population-scale VCF/PLINK data: sample and
  variant missingness, Hardy-Weinberg equilibrium, minor allele frequency
  filtering, sex check, heterozygosity outliers, and relatedness detection.
  Use for GWAS/cohort QC from raw VCF or bed/bim/fam input. Not for
  population structure (use pop-structure-pca), imputation (use pop-imputation),
  GWAS association (use pop-gwas-association), or variant functional annotation
  (use pop-variant-annotation).
compatibility: Python 3.10+, PLINK 1.9+/2.0, pysam, pandas
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-qc.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
  databases: []
---

# Population Genotype QC（群体基因型质控）

群体规模 VCF / PLINK 格式基因型数据的标准质控流程，覆盖样本水平和变异水平。

## Use When

- 拿到群体 VCF 或 PLINK bed/bim/fam 后，需要做 GWAS 前质控
- 样本 missing rate 过高需要剔除
- 变异位点 MAF 过低、HWE 偏离、缺失率过高需要过滤
- 性别检查（基于 X 染色体杂合度）
- 杂合度离群样本检测
- 亲缘关系 / 重复样本检测

## Do Not Use When

| 需求 | 交给 |
|------|------|
| PCA / 群体结构 / ADMIXTURE | `pop-structure-pca` |
| 基因型填充 | `pop-imputation` |
| GWAS 关联分析 | `pop-gwas-association` |
| 变异功能注释 | `pop-variant-annotation` |
| 多基因风险评分 | `pop-prs` |

## Workflow

1. **Gather**：确认输入格式（VCF / PLINK）、参考基因组版本、质控阈值
2. **Convert**（如需）：VCF → PLINK 格式（pysam 或 PLINK --vcf）
3. **Sample QC**：missingness → sex check → heterozygosity → relatedness
4. **Variant QC**：missingness → MAF → HWE → LD pruning（可选）
5. **Report**：生成 QC 报告（剔除样本/变异列表 + 各阶段通过率）
6. **Output**：输出 cleaned genotype + QC summary table

## Commands

```bash
python ./scripts/query.py <module> <subcommand> [args…]
```

| 任务 | 命令 |
|------|------|
| 全流程 QC | `python ./scripts/query.py pipeline full --input <vcf_or_bed_prefix> --output <outdir>` |
| 样本质控 | `python ./scripts/query.py sample qc --input <prefix> --output <outdir>` |
| 变异质控 | `python ./scripts/query.py variant qc --input <prefix> --output <outdir> --maf 0.05 --hwe 1e-6` |
| 性别检查 | `python ./scripts/query.py sample sexcheck --input <prefix> --output <outdir>` |
| 杂合度检测 | `python ./scripts/query.py sample het --input <prefix> --output <outdir>` |
| 亲缘关系 | `python ./scripts/query.py sample relatedness --input <prefix> --output <outdir>` |
| VCF→PLINK | `python ./scripts/query.py convert vcf2plink --input <file.vcf.gz> --output <prefix>` |
| QC 报告 | `python ./scripts/query.py report summary --input <qc_dir> --output <report.html>` |

## Default Thresholds (CIMA / UK Biobank 兼容)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --sample-missing | 0.02 | 样本缺失率上限 |
| --variant-missing | 0.02 | 变异缺失率上限 |
| --maf | 0.05 | MAF 下限（GWAS 常用） |
| --hwe | 1e-6 | HWE p 值下限 |
| --het-threshold | 3 | 杂合度离群 SD 倍数 |
| --kinship-threshold | 0.0884 | 二级亲缘关系阈值 |
| --sex-f-threshold | 0.2 | F-statistic 女性阈值 |
| --sex-m-threshold | 0.8 | F-statistic 男性阈值 |

## Guardrails

- 必须跑包内 `./scripts/query.py`
- VCF 输入需 bgzip + tabix 索引（脚本会自动检测并提示）
- PLINK 路径自动检测：先找 plink2，再找 plink1.9，最后报错
- 输出包含 provenance：输入文件、参数、PLINK 版本、时间戳

## Examples

**用户**：我有一个群体的 VCF 文件，帮我做 GWAS 前质控

```bash
python ./scripts/query.py pipeline full --input cohort.vcf.gz --output qc_results --maf 0.05
```

**用户**：检查样本杂合度

```bash
python ./scripts/query.py sample het --input cohort --output het_results
```

**用户**：检测重复样本和亲缘关系

```bash
python ./scripts/query.py sample relatedness --input cohort --output ibd_results
```

## Citation

- Chang et al., 2015 (PLINK)
- Anderson et al., 2010 (genotype QC best practices)
- Nature Reviews Genetics, 2010 (Genome-wide association studies)
