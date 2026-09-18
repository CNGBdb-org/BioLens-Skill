---
name: pop-rare-variant-burden
description: >-
  Rare variant burden testing using gene-based aggregation: supports
  SKAT-O, SAIGE-GENE, and burden tests (CMC, variable threshold).
  Aggregates rare variants (MAF < 1%) by gene and tests association
  with phenotype. Accepts VCF/genotype + phenotype data. Use for
  analyzing rare variant contribution to disease from WGS/WES data.
  Not for common variant GWAS (use pop-gwas-association), genotype QC
  (use pop-genotype-qc), or variant annotation (use pop-variant-annotation).
compatibility: Python 3.10+, pysam, pandas, numpy, scipy; SKAT-R/SAIGE (auto-detect)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: genomics-variation
  capability_id: cngbdb.genomics.pop-rare-variant.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Population Rare Variant Burden（群体罕见变异 burden 检验）

基因水平的罕见变异聚合检验，支持 SKAT-O / SAIGE-GENE / burden test。

## Use When

- WGS/WES 数据中罕见变异（MAF < 1%）的基因水平关联检验
- SKAT-O（优化加权 burden + 方差分量）
- burden test（CMC / variable threshold）
- 功能区域聚合（编码区 / LOF / missense）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 常见变异 GWAS | `pop-gwas-association` |
| 基因型质控 | `pop-genotype-qc` |
| 变异功能注释 | `pop-variant-annotation` |
| 通路富集 | `pop-pathway-enrichment` |

## Workflow

1. **Gather**：确认 VCF/PLINK + 表型 + 变异注释（功能后果）
2. **Variant Filtering**：按 MAF + 功能后果筛选罕见变异
3. **Gene Aggregation**：将变异映射到基因
4. **Burden Test**：
   - SKAT-O：最优加权 burden + 方差分量
   - SAIGE-GENE：大规模队列基因水平检验
   - CMC：合并罕见变异 burden
5. **Output**：per-gene p-value + burden score + QQ plot

## Commands

| 任务 | 命令 |
|------|------|
| 全流程 | `python ./scripts/query.py pipeline full --vcf <file.vcf.gz> --pheno <pheno.txt> --annot <annotation> --output <outdir>` |
| 变异筛选 | `python ./scripts/query.py filter rare --vcf <file.vcf.gz> --output <outdir> --maf 0.01 --consequence LOF,missense` |
| 基因聚合 | `python ./scripts/query.py aggregate gene --vcf <file.vcf.gz> --annot <annotation> --output <outdir>` |
| SKAT-O | `python ./scripts/query.py test skat --vcf <file.vcf.gz> --pheno <pheno.txt> --gene-map <gene_map.txt> --output <outdir>` |
| Burden | `python ./scripts/query.py test burden --vcf <file.vcf.gz> --pheno <pheno.txt> --gene-map <gene_map.txt> --output <outdir>` |
| QQ plot | `python ./scripts/query.py plot qq --results <file> --output <qq.png>` |

## Default Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --maf | 0.01 | 罕见变异 MAF 上限 |
| --consequence | LOF,missense | 功能后果过滤 |
| --test | skato | 检验方法（skato/burden/skat） |
| --weights | beta | SKAT 权重（beta/fixed） |

## Guardrails

- VCF 需 bgzip + tabix 索引
- SKAT 通过 Rscript 调用 R SKAT 包
- 变异注释需含基因映射（VEP/ANNOVAR 输出）
- 未安装 SKAT 时使用 Python burden 近似

## Citation

- SKAT-O: Lee et al., AJHG 2012
- SAIGE-GENE: Zhou et al., Nature Genetics 2022
- CMC: Li & Leal, 2008
