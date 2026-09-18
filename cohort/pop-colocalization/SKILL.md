---
name: pop-colocalization
description: >-
  Colocalization analysis between GWAS and QTL (eQTL/caQTL/mQTL) signals
  to test shared causal variants: supports coloc.abf, eCAVIAR, and HyPrColoc.
  Computes posterior probability of colocalization (PP4), regional plots,
  and SNP-level evidence. Use for determining whether GWAS and eQTL share
  the same causal variant. Not for fine-mapping (use pop-finemapping),
  GWAS association (use pop-gwas-association), or MR (use pop-mr-smr).
compatibility: Python 3.10+, pandas, numpy, matplotlib; R+coloc (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-coloc.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Colocalization（群体共定位分析）

检验 GWAS 与 QTL 信号是否共享因果变异，支持 coloc.abf / eCAVIAR / HyPrColoc。

## Use When

- GWAS 信号与 eQTL/caQTL 是否共定位（同一因果变异）
- 鉴定 GWAS locus 中的功能基因（通过 eQTL 共定位）
- 多个 QTL 数据集与 GWAS 的共定位比较
- 计算共定位后验概率（PP4）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 精细定位 | `pop-finemapping` |
| GWAS 关联分析 | `pop-gwas-association` |
| 孟德尔随机化 | `pop-mr-smr` |
| 变异功能注释 | `pop-variant-annotation` |

## Workflow

1. **Gather**：确认 GWAS sumstats + QTL sumstats + locus 范围
2. **Locus Extraction**：提取两个数据集在同一 locus 的变异
3. **SNP Alignment**：按 SNP ID 或 CHR:BP 对齐两个数据集
4. **Colocalization**：
   - coloc.abf：贝叶斯共定位（R 包 coloc）
   - eCAVIAR：穷举共定位（外部工具）
   - HyPrColoc：多位点共定位（R 包）
5. **Output**：PP4 + 5 假设后验概率 + regional plot

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --gwas <gwas.txt> --qtl <qtl.txt> --locus <chr:start-end> --output <outdir>` |
| coloc.abf | `python ./scripts/query.py run coloc --gwas <gwas.txt> --qtl <qtl.txt> --locus <chr:start-end> --output <outdir>` |
| eCAVIAR | `python ./scripts/query.py run ecaviar --gwas <gwas.txt> --qtl <qtl.txt> --locus <chr:start-end> --output <outdir>` |
| HyPrColoc | `python ./scripts/query.py run hyprcoloc --gwas <gwas.txt> --qtl <qtl.txt> --locus <chr:start-end> --output <outdir>` |
| Regional plot | `python ./scripts/query.py plot regional --gwas <gwas.txt> --qtl <qtl.txt> --locus <chr:start-end> --output <plot.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --pp4-threshold | 0.8 | PP4 共定位判定阈值 |
| --n-gwas | (auto) | GWAS 样本量（从 sumstats 推断或手动指定） |
| --n-qtl | (auto) | QTL 样本量 |
| --tool | coloc | 默认工具（coloc/ecaviar/hyprcoloc） |
| --flank | 500000 | locus 两侧扩展（bp） |

## Guardrails

- GWAS 和 QTL sumstats 需含 SNP, BETA/OR, SE, P 列
- 两个数据集的变异需可按 SNP ID 或 CHR:BP 对齐
- coloc 通过 Rscript 调用 R coloc 包
- PP4 > 0.8 通常认为共定位证据强

## Citation

- coloc.abf: Giambartolomei et al., PLOS Genetics 2014
- eCAVIAR: Hormozdiari et al., 2016
- HyPrColoc: Foley et al., Nature Genetics 2021
