---
name: pop-finemapping
description: >-
  Fine-mapping of GWAS loci to identify credible causal variants: supports
  SuSiE (sum of single effects), FINEMAP, and CAVIAR. Computes posterior
  inclusion probability (PIP), credible sets (95%/99%), and LD-based
  refinement. Accepts GWAS summary statistics + LD reference panel.
  Use for narrowing GWAS loci to candidate causal variants. Not for
  GWAS association testing (use pop-gwas-association), colocalization
  (use pop-colocalization), or variant annotation (use pop-variant-annotation).
compatibility: Python 3.10+, pandas, numpy; SuSiE-R/FINEMAP/CAVIAR (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-finemapping.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Fine-Mapping（群体精细定位）

将 GWAS 信号精细定位到候选因果变异，支持 SuSiE / FINEMAP / CAVIAR。

## Use When

- GWAS 发现显著 loci 后，需要缩小到候选因果变异
- 计算每个变异的后验包含概率（PIP）
- 构建 95%/99% 可信集（credible set）
- 多个因果变异共存的 locus 分析

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS 关联分析 | `pop-gwas-association` |
| 共定位分析（GWAS vs eQTL） | `pop-colocalization` |
| 变异功能注释 | `pop-variant-annotation` |
| 遗传度估计 | `pop-heritability-ldsc` |

## Workflow

1. **Gather**：确认 GWAS summary stats、LD 参考面板、locus 范围
2. **Locus Extraction**：从全基因组 sumstats 提取目标 locus ± flank
3. **LD Matrix**：从参考面板计算 SNP×SNP LD 矩阵
4. **Fine-Mapping**：
   - SuSiE：贝叶斯变量选择（R 包 susieR）
   - FINEMAP：贝叶斯模型（外部二进制）
   - CAVIAR：穷举/采样（外部二进制）
5. **Output**：PIP 排序 + credible set + locus zoom plot

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --sumstats <gwas.txt> --ld-ref <plink_prefix> --locus <chr:start-end> --output <outdir>` |
| SuSiE | `python ./scripts/query.py run susie --sumstats <gwas.txt> --ld-ref <prefix> --locus <chr:start-end> --output <outdir>` |
| FINEMAP | `python ./scripts/query.py run finemap --sumstats <gwas.txt> --ld-ref <prefix> --locus <chr:start-end> --output <outdir>` |
| CAVIAR | `python ./scripts/query.py run caviar --sumstats <gwas.txt> --ld-ref <prefix> --locus <chr:start-end> --output <outdir>` |
| LocusZoom plot | `python ./scripts/query.py plot locuszoom --sumstats <gwas.txt> --pip <pip_file> --output <plot.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --credible-level | 0.95 | 可信集置信水平 |
| --max-causal | 10 | 最大因果变异数 |
| --flank | 500000 | locus 两侧扩展（bp） |
| --ld-ref | (required) | LD 参考面板 PLINK 前缀 |
| --tool | susie | 默认工具（susie/finemap/caviar） |

## Guardrails

- 输入 GWAS sumstats 需含 SNP, CHR, BP, A1, BETA, P 列
- LD 参考面板需与 sumstats 基因组版本一致
- SuSiE 通过 Rscript 调用 susieR 包（需安装）
- FINEMAP/CAVIAR 需单独安装，脚本自动检测

## Citation

- SuSiE: Wang et al., Nature Genetics 2020
- FINEMAP: Benner et al., 2016
- CAVIAR: Hormozdiari et al., 2014
