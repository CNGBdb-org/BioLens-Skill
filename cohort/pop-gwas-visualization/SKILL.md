---
name: pop-gwas-visualization
description: >-
  Comprehensive GWAS visualization: Manhattan plots, QQ plots, regional
  association plots, forest plots for meta-analysis, and summary
  statistics tables. Supports customizable thresholds, multi-trait
  comparison, and publication-ready figures. Accepts GWAS summary
  statistics in standard format. Use for visualizing GWAS results,
  generating publication figures, and comparing multiple GWAS. Not for
  running GWAS analysis (use pop-gwas-association), fine-mapping
  (use pop-finemapping), or PRS evaluation (use pop-prs).
compatibility: Python 3.10+, pandas, numpy, matplotlib, seaborn
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L4
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-vis.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population GWAS Visualization（群体 GWAS 可视化）

GWAS 结果综合可视化，生成 publication-ready 图表。

## Use When

- Manhattan plot（全基因组关联可视化）
- QQ plot（检查关联膨胀/混淆）
- Regional association plot（locus zoom）
- Forest plot（meta-analysis 或 MR 结果）
- 多性状 GWAS 对比图
- Summary statistics 汇总表

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS 关联分析 | `pop-gwas-association` |
| 精细定位 | `pop-gwins-finemapping` |
| 共定位 | `pop-colocalization` |
| PRS | `pop-prs` |

## Workflow

1. **Gather**：确认 GWAS sumstats 格式、输出需求
2. **Manhattan**：全基因组 -log10(p) 散点图
3. **QQ**：期望 vs 观测 p 值
4. **Regional**：特定 locus 的关联信号 + 基因注释
5. **Forest**：效应值 + 置信区间（meta-analysis / MR）
6. **Output**：PNG/PDF 图 + 汇总表

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --sumstats <gwas.txt> --output <outdir>` |
| Manhattan | `python ./scripts/query.py plot manhattan --sumstats <file> --output <man.png> --threshold 5e-8` |
| QQ | `python ./scripts/query.py plot qq --sumstats <file> --output <qq.png>` |
| Regional | `python ./scripts/query.py plot regional --sumstats <file> --locus <chr:start-end> --output <reg.png>` |
| Forest | `python ./scripts/query.py plot forest --data <forest.tsv> --output <forest.png>` |
| 对比 Manhattan | `python ./scripts/query.py plot compare --sumstats1 <f1> --sumstats2 <f2> --output <compare.png>` |
| 汇总表 | `python ./scripts/query.py report summary --sumstats <file> --output <summary.tsv>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --threshold | 5e-8 | 显著性阈值线 |
| --dpi | 150 | 图片分辨率 |
| --format | png | 输出格式（png/pdf/svg） |
| --highlight | None | 高亮 SNP 列表 |
| --top-n | 20 | 汇总表 top N |

## Citation

- QQ plot: McCarthy et al., 2008
- Manhattan: Turner et al., 2011
- LocusZoom: Pruim et al., 2010
