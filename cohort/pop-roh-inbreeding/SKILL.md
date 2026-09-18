---
name: pop-roh-inbreeding
description: >-
  Runs of homozygosity (ROH) detection and inbreeding coefficient (F)
  estimation: detects autozygous segments, calculates F(ROH), Fhat1,
  Fhat2, Fhat3, and summarizes ROH length distribution. Accepts PLINK
  bed/bim/fam. Use for estimating inbreeding levels, detecting
  autozygosity from recent common ancestors, and identifying samples
  with elevated homozygosity. Not for genotype QC filtering (use
  pop-genotype-qc), population structure (use pop-structure-pca),
  or IBD/kinship detection (use pop-genotype-qc relatedness).
compatibility: Python 3.10+, PLINK 1.9+, pandas, numpy, matplotlib
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-roh.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population ROH & Inbreeding（群体纯合片段与近交系数）

检测连续纯合片段（ROH）并估计近交系数（F）。

## Use When

- 估计个体近交系数 F（autozygosity）
- 检测 ROH 长度分布（短 = 远期，长 = 近期共祖）
- 识别高近交个体（隔离群体、育种群体）
- 比较群体间近交水平

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 基因型质控 | `pop-genotype-qc` |
| 群体结构 PCA | `pop-structure-pca` |
| 亲缘关系检测 | `pop-genotype-qc`（relatedness 模块） |
| 选择信号 | `pop-selection-scan` |

## Workflow

1. **Gather**：确认 PLINK 前缀、ROH 参数
2. **ROH Detection**：PLINK --homozyg（检测连续纯合段）
3. **F Calculation**：F(ROH) = sum(ROH length) / autosomal genome length
4. **PLINK F-stats**：Fhat1, Fhat2, Fhat3
5. **Summary**：ROH 长度分布 + 群体近交水平统计
6. **Output**：per-individual ROH + F coefficients + distribution plot

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --input <prefix> --output <outdir>` |
| ROH 检测 | `python ./scripts/query.py roh detect --input <prefix> --output <outdir> --min-snp 50 --min-kb 100` |
| F 计算 | `python ./scripts/query.py f calc --roh <roh_file> --output <outdir>` |
| Fhat 统计 | `python ./scripts/query.py fhat calc --input <prefix> --output <outdir>` |
| 分布图 | `python ./scripts/query.py plot distribution --roh <roh_file> --output <plot.png>` |

## Default Parameters (PLINK --homozyg)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --min-snp | 50 | ROH 最少 SNP 数 |
| --min-kb | 100 | ROH 最短长度（kb） |
| --max-kb | 5000 | ROH 最大长度（kb） |
| --min-density | 50 | 每 1000kb 最少 SNP 数 |
| --gap | 1000 | 允许的 gap（kb） |

## Citation

- McQuillan et al., AJHG 2008 (ROH in population genetics)
- PLINK --homozyg: Purcell et al., 2007
- F-statistics: Yang et al., AJHG 2011
