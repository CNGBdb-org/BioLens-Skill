---
name: pop-pathway-enrichment
description: >-
  Gene-based and pathway enrichment analysis from GWAS summary statistics:
  supports MAGMA gene-set analysis, competitive/self-contained tests,
  GO/KEGG/Reactome pathway enrichment, and tissue/cell-type specificity.
  Accepts GWAS summary statistics + gene annotation. Use for identifying
  biological pathways and gene sets enriched in GWAS signals. Not for
  GWAS association (use pop-gwas-association), heritability (use
  pop-heritability-ldsc), or variant annotation (use pop-variant-annotation).
compatibility: Python 3.10+, pandas, numpy; MAGMA (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-association
  capability_id: cngbdb.genomics.pop-pathway.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Pathway Enrichment（群体通路富集分析）

从 GWAS summary statistics 做基因水平和通路富集分析，支持 MAGMA / Python 富集。

## Use When

- GWAS 发现信号后，需要鉴定富集的生物学通路
- 基因水平关联（将 SNP p-value 聚合到基因）
- 组织/细胞类型特异性富集（哪个组织受影响最大）
- GO / KEGG / Reactome 通路富集

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS 关联分析 | `pop-gwas-association` |
| 遗传度估计 | `pop-heritability-ldsc` |
| 变异功能注释 | `pop-variant-annotation` |
| 精细定位 | `pop-finemapping` |
| GO/KEGG 术语查询（非 GWAS 富集） | `go` / `kegg` |

## Workflow

1. **Gather**：确认 GWAS sumstats、基因注释文件
2. **Gene-Based Test**：MAGMA 将 SNP 关联聚合到基因
3. **Pathway Enrichment**：GO/KEGG/Reactome 基因集富集
4. **Tissue Specificity**：按组织表达模式富集
5. **Output**：基因 p-value + 通路富集表 + 组织富集图

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --sumstats <gwas.txt> --output <outdir> --genome GRCh38` |
| 基因水平 | `python ./scripts/query.py gene test --sumstats <gwas.txt> --output <outdir> --genome GRCh38` |
| 通路富集 | `python ./scripts/query.py pathway enrich --gene-results <gene.txt> --output <outdir>` |
| 组织特异性 | `python ./scripts/query.py tissue enrich --gene-results <gene.txt> --expression <gtex.txt> --output <outdir>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --genome | GRCh38 | 参考基因组版本 |
| --gene-window | 35000 | 基因上下游窗口（bp） |
| --pval-threshold | 0.05 | 通路富集显著性阈值 |
| --n-permutations | 1000 | 置换检验次数 |

## Guardrails

- MAGMA 需单独安装（conda install -c bioconda magma）
- 基因注释文件需与基因组版本一致
- 通路富集需基因集数据库（GO/KEGG/Reactome）
- 未安装 MAGMA 时使用 Python 聚合近似

## Citation

- MAGMA: de Leeuw et al., PLOS Computational Biology 2015
- DEPICT: Pers et al., Nature Genetics 2015
- PASCAL: Lamparter et al., 2016
