---
name: pop-heritability-ldsc
description: >-
  SNP heritability estimation and genetic correlation analysis using
  LD score regression (LDSC): supports h2 estimation, partitioned
  heritability by functional annotation, and bivariate genetic
  correlation (rg) between traits. Accepts GWAS summary statistics.
  Use for estimating how much phenotypic variance is explained by
  common SNPs, comparing genetic architecture across traits, and
  enrichment analysis. Not for GWAS association (use pop-gwas-association),
  fine-mapping (use pop-finemapping), or PRS (use pop-prs).
compatibility: Python 3.10+, pandas, numpy; LDSC (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-heritability.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Heritability & LDSC（群体遗传度与 LD 评分回归）

使用 LD 评分回归估计 SNP 遗传度、分区富集和性状间遗传相关。

## Use When

- 估计性状的 SNP 遗传度（h2）
- 计算两个性状之间的遗传相关（rg）
- 分区遗传度（哪些功能注释富集遗传信号）
- 检查 GWAS 是否存在混淆因素（λGC vs LD score intercept）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS 关联分析 | `pop-gwas-association` |
| 精细定位 | `pop-finemapping` |
| 共定位分析 | `pop-colocalization` |
| 通路富集 | `pop-pathway-enrichment` |

## Workflow

1. **Gather**：确认 GWAS sumstats 格式、LD 参考面板
2. **Sumstats Munge**：格式化 sumstats 为 LDSC 兼容格式
3. **h2 Estimation**：单性状 SNP 遗传度
4. **Partitioned h2**：按功能注释（编码区/增强子/启动子等）分解 h2
5. **Genetic Correlation**：双性状 rg
6. **Output**：h2 + rg + enrichment table + intercept

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --sumstats <gwas.txt> --output <outdir>` |
| Munge sumstats | `python ./scripts/query.py munge run --sumstats <gwas.txt> --output <outdir>` |
| h2 估计 | `python ./scripts/query.py h2 estimate --sumstats <munged.gz> --output <outdir>` |
| 分区 h2 | `python ./scripts/query.py h2 partitioned --sumstats <munged.gz> --ld-annot <dir> --output <outdir>` |
| 遗传相关 | `python ./scripts/query.py rg estimate --sumstats1 <munged1.gz> --sumstats2 <munged2.gz> --output <outdir>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --ld-ref | (required) | LD 参考面板目录 |
| --n | (auto) | 样本量（从 sumstats 推断） |
| --chi2-threshold | 0.001 | 需要的 chi2 阈值 |
| --freq-threshold | 0.01 | MAF 过滤 |

## Guardrails

- LDSC 需单独安装（conda install -c bioconda ldsc）
- 未安装 LDSC 时使用 Python 近似（基于 intercept 和 chi2）
- GWAS sumstats 需 munge 后才能分析
- LD 参考面板需下载（1000G 或 HapMap）

## Citation

- LDSC: Finucane et al., Nature Genetics 2015
- Partitioned h2: Finucane et al., Nature Genetics 2015
- Bulik-Sullivan et al., Nature Genetics 2015
