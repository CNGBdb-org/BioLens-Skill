---
name: pop-ld-haplotype
description: >-
  Linkage disequilibrium (LD) analysis and haplotype structure:
  supports LD decay calculation (r2 vs distance), haplotype frequency
  estimation, LD pruning, and recombination rate estimation. Accepts
  PLINK bed/bim/fam. Use for comparing LD structure across populations,
  generating LD matrices for fine-mapping, and haplotype block detection.
  Not for genotype QC (use pop-genotype-qc), population structure
  (use pop-structure-pca), or phasing (use pop-imputation).
compatibility: Python 3.10+, PLINK 1.9+, pandas, numpy, matplotlib
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-ld.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population LD & Haplotype（群体 LD 与单倍型分析）

LD 衰减、单倍型频率、LD 矩阵和重组率分析。

## Use When

- LD 衰减分析（r2 vs 距离，比较群体 LD 结构）
- 生成 LD 矩阵（用于精细定位）
- LD 剪枝（获取独立 SNP）
- 单倍型频率估计
- LD block 检测

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 基因型质控 | `pop-genotype-qc` |
| 群体结构 PCA | `pop-structure-pca` |
| 基因型填充/Phasing | `pop-imputation` |
| 精细定位 | `pop-finemapping` |

## Workflow

1. **Gather**：确认 PLINK 前缀、分析区域（全基因组/特定 locus）
2. **LD Decay**：按距离 bin 计算 mean r2 → 衰减曲线
3. **LD Matrix**：特定区域的 SNP×SNP r2 矩阵
4. **LD Pruning**：--indep-pairwise 获取独立 SNP 集
5. **Haplotype**：估计常见单倍型频率
6. **Output**：衰减曲线 + 矩阵 + SNP 列表 + plot

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --input <prefix> --output <outdir>` |
| LD 衰减 | `python ./scripts/query.py decay compute --input <prefix> --output <outdir> --max-dist 500` |
| LD 矩阵 | `python ./scripts/query.py matrix compute --input <prefix> --region <chr:start-end> --output <outdir>` |
| LD 剪枝 | `python ./scripts/query.py prune run --input <prefix> --output <outdir> --r2 0.2` |
| 衰减曲线 | `python ./scripts/query.py plot decay --data <decay_file> --output <plot.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --max-dist | 500 | 最大距离（kb） |
| --bin-size | 10 | 距离 bin（kb） |
| --r2 | 0.2 | LD r2 阈值 |
| --window | 50 | 剪枝窗口（kb） |
| --step | 5 | 剪枝步长 |

## Citation

- PLINK --r/--r2: Purcell et al., 2007
- LD decay: Abecasis et al., 2012
- Haploview: Barrett et al., 2005
