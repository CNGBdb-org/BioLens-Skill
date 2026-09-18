---
name: pop-selection-scan
description: >-
  Selection scan for detecting recent and long-term positive selection:
  supports iHS (integrated haplotype score), XP-EHH (cross-population
  extended haplotype homozygosity), Fst (population differentiation),
  and PBS (population branch statistic). Accepts phased genotype data
  and/or PLINK format. Use for identifying genomic regions under
  selective pressure, comparing selection across populations, and
  detecting local adaptation. Not for genotype QC (use pop-genotype-qc),
  population structure (use pop-structure-pca), or LD analysis
  (use pop-ld-haplotype).
compatibility: Python 3.10+, PLINK 1.9+, pandas, numpy, matplotlib; selscan (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-selection.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Selection Scan（群体选择信号检测）

检测近期和长期自然选择信号，支持 iHS / XP-EHH / Fst / PBS。

## Use When

- 检测基因组中的正向选择区域
- 比较不同群体间的选择信号（如非洲 vs 东亚 vs 欧洲）
- 识别局部适应（如高海拔、饮食适应）
- iHS（单体型长度，近期选择）、XP-EHH（跨群体，固定选择）、Fst（群体分化）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 基因型质控 | `pop-genotype-qc` |
| 群体结构 PCA | `pop-structure-pca` |
| LD 衰减 / 单倍型 | `pop-ld-haplotype` |
| 近交 / ROH | `pop-roh-inbreeding` |

## Workflow

1. **Gather**：确认 phased 基因型（或 PLINK 前缀）、群体标签、选择方法
2. **iHS**：selscan 计算 integrated haplotype score（需 phased VCF）
3. **XP-EHH**：selscan 跨群体扩展单体型纯合度
4. **Fst**：PLINK --fst 或 Weir-Cockerham 计算
5. **PBS**：用三个群体的 Fst 计算 population branch statistic
6. **Output**：标准化 iHS/XP-EHH + Fst + PBS + 选择信号 manhattan plot

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --input <prefix> --pop <pop_file> --output <outdir>` |
| iHS | `python ./scripts/query.py run ihs --input <prefix> --output <outdir>` |
| XP-EHH | `python ./scripts/query.py run xpehh --pop1 <prefix1> --pop2 <prefix2> --output <outdir>` |
| Fst | `python ./scripts/query.py run fst --input <prefix> --pop <pop_file> --output <outdir>` |
| PBS | `python ./scripts/query.py run pbs --fst1 <f1> --fst2 <f2> --fst3 <f3> --output <outdir>` |
| Manhattan plot | `python ./scripts/query.py plot manhattan --results <file> --output <plot.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --method | ihs | 方法（ihs/xpehh/fst/pbs/all） |
| --maf | 0.05 | MAF 下限 |
| --pct-threshold | 0.01 | top percentile 阈值 |

## Guardrails

- iHS/XP-EHH 需要 phased 基因型（Eagle/SHAPEIT4 phasing 后）
- selscan 需单独安装（conda install -c bioconda selscan）
- 未安装 selscan 时 Fst 仍可用（PLINK --fst）
- PBS 需要三个群体的成对 Fst

## Citation

- iHS: Voight et al., PLoS Biology 2006
- XP-EHH: Sabeti et al., Science 2007
- selscan: Szpiech & Hernandez, 2014
- Fst: Weir & Cockerham, 1984
