---
name: pop-variant-annotation
description: >-
  Functional annotation of genomic variants: VEP, ANNOVAR, SnpEff, and
  bcftools csq integration. Annotates consequences (missense, synonymous,
  frameshift), gene mapping, transcript info, ClinVar/COSMIC cross-reference,
  and ACMG-AMP classification. Accepts VCF or variant list input. Use for
  annotating GWAS hits, rare variant analysis, or clinical variant
  interpretation. Not for genotype QC, GWAS association, or PRS.
compatibility: Python 3.10+, pysam, pandas; VEP/ANNOVAR/SnpEff/bcftools (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L4
  domain: genomics-annotation
  capability_id: cngbdb.genomics.pop-annotation.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Variant Annotation（群体变异功能注释）

对 VCF 或变异列表做功能注释，支持 VEP / ANNOVAR / SnpEff / bcftools csq。

## Use When

- GWAS 发现显著变异后需要注释功能影响
- 罕见变异需要判断是否为 protein-coding / missense / LOF
- 批量变异需要基因映射和转录本信息
- 需要 ACMG-AMP 变异分类辅助

## Do Not Use When

| 需求 | 交给 |
|------|------|
| ClinVar 临床意义查询 | `clinvar` |
| gnomAD 人群频率 | `gnomad` |
| dbSNP rsID 查询 | `dbsnp` |
| GWAS 关联分析 | `pop-gwas-association` |
| 基因型质控 | `pop-genotype-qc` |

## Workflow

1. **Gather**：确认输入（VCF / TSV / 变异列表）、参考基因组版本、注释工具
2. **Tool Selection**：自动检测 VEP → ANNOVAR → SnpEff → bcftools csq → pysam
3. **Annotation**：功能后果 → 基因映射 → 转录本 → 蛋白影响
4. **Cross-reference**：可选关联 ClinVar / gnomAD（通过对应 skill）
5. **Output**：annotated VCF / TSV + summary table

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --input <vcf> --output <outdir> --genome GRCh38` |
| VEP 注释 | `python ./scripts/query.py annotate vep --input <vcf> --output <outdir>` |
| ANNOVAR | `python ./scripts/query.py annotate annovar --input <vcf> --output <outdir>` |
| SnpEff | `python ./scripts/query.py annotate snpeff --input <vcf> --output <outdir>` |
| bcftools csq | `python ./scripts/query.py annotate bcftools --input <vcf> --output <outdir>` |
| pysam 基础注释 | `python ./scripts/query.py annotate pysam --input <vcf> --output <outdir>` |
| 注释汇总 | `python ./scripts/query.py report summary --input <annotated_dir> --output <summary.csv>` |
| 变异列表注释 | `python ./scripts/query.py annotate list --input <variants.txt> --output <outdir>` |

## Guardrails

- VEP 需单独安装（conda install -c bioconda ensembl-vep）
- ANNOVAR 需下载数据库
- SnpEff 需下载数据库
- 无外部工具时使用 pysam 做基础注释（坐标、ref/alt）
- 参考基因组版本必须指定（GRCh37/GRCh38）

## Citation

- VEP: McLaren et al., Genome Biology 2016
- ANNOVAR: Wang et al., 2010
- SnpEff: Cingolani et al., 2012
- bcftools: Li et al., 2016
