---
name: pop-sv-cnv
description: >-
  Structural variant (SV) and copy number variant (CNV) analysis:
  supports SV detection (DELLY/Manta), CNV calling (GATK-gCNV/PennCNV),
  CNV frequency analysis, and SV annotation. Accepts BAM/VCF input.
  Use for detecting deletions, duplications, inversions, translocations,
  and copy number changes at population scale. Not for SNP/indel
  genotyping (use pop-genotype-qc), GWAS (use pop-gwas-association),
  or variant annotation of SNPs (use pop-variant-annotation).
compatibility: Python 3.10+, pysam, pandas; DELLY/Manta/GATK-gCNV (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-sv-cnv.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population SV & CNV（群体结构变异与拷贝数变异）

检测和分析群体水平的结构变异和拷贝数变异。

## Use When

- 从 WGS 数据检测结构变异（DEL/DUP/INV/TRA）
- CNV calling 和频率分析
- 群体 SV/CNV 频率比较
- SV 功能注释

## Do Not Use When

| 需求 | 交给 |
|------|------|
| SNP/indel 质控 | `pop-genotype-qc` |
| GWAS 关联分析 | `pop-gwas-association` |
| SNP 功能注释 | `pop-variant-annotation` |
| 罕见变异 burden | `pop-rare-variant-burden` |

## Workflow

1. **Gather**：确认输入（BAM/VCF）、SV/CNV 工具
2. **SV Detection**：DELLY/Manta 检测 DEL/DUP/INV/TRA
3. **CNV Calling**：GATK-gCNV 或 PennCNV
4. **Frequency**：统计 SV/CNV 群体频率
5. **Annotation**：注释 SV 对基因的影响
6. **Output**：SV VCF + CNV calls + 频率表

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --bam <bam_list> --output <outdir>` |
| SV 检测 | `python ./scripts/query.py sv detect --bam <bam_list> --output <outdir> --tool delly` |
| CNV 检测 | `python ./scripts/query.py cnv call --vcf <vcf.gz> --output <outdir>` |
| 频率统计 | `python ./scripts/query.py freq compute --sv <sv.vcf> --output <outdir>` |
| SV 注释 | `python ./scripts/query.py annotate sv --sv <sv.vcf> --output <outdir>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --tool | delly | SV 检测工具（delly/manta） |
| --min-size | 50 | 最小 SV 长度（bp） |
| --min-af | 0.01 | 最小等位基因频率 |
| --cnv-cnv | 0 | CNV 默认拷贝数 |

## Guardrails

- DELLY/Manta 需 BAM 输入（不是 VCF）
- GATK-gCNV 需特殊预处理（collect read counts）
- SV VCF 可直接用 pysam 解析
- 未安装工具时使用 pysam 做基础 SV 统计

## Citation

- DELLY: Rausch et al., 2012
- Manta: Chen et al., 2016
- GATK-gCNV: Poplin et al., 2019
- PennCNV: Wang et al., 2007
