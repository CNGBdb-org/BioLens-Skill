---
name: gwascatalog
description: >-
  Query NHGRI-EBI GWAS Catalog for SNP-trait associations, trait/study search, gene-mapped
  SNPs, and study metadata. Supports rsID lookup, disease/trait studies, gene-associated
  GWAS SNPs, and GCST study details. Use for GWAS Catalog lookup. Not for ClinVar Mendelian
  pathogenicity (use clinvar), gnomAD AF (use gnomad), Open Targets integrated scores
  (use opentargets), or running GWAS on local genotypes (use pop-gwas-association).
compatibility: Python 3.10+, HTTPS (GWAS Catalog API)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: gwas
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# GWAS Catalog 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| SNP 关联 | `rsid` | rsID → 性状、p 值、OR、风险等位基因 |
| 性状/疾病 | `trait` | 按性状关键词查 GWAS 研究 |
| 基因 SNP | `gene` | 映射到基因的 GWAS SNP |
| 研究详情 | `study` | GCST 研究元数据 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| rsID（rs7903146） | `rsid` |
| 性状/疾病（diabetes、height） | `trait` |
| 基因名（TCF7L2、BRCA1） | `gene` |
| 研究 ID（GCST000001） | `study` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. rsID 可带或不带 `rs` 前缀
3. 报告 p 值、OR（orPerCopyNum）、风险等位基因及 EFO 性状名
4. GWAS 关联为 **统计关联**，不等同于致病性；因果需结合功能证据
5. 性状检索为模糊匹配，建议英文关键词
6. 输出关键字段：rsID、性状、 p 值、OR、风险等位基因、PubMed、GCST ID

## 运行脚本

```bash
python ./scripts/query.py rsid <rsID>
python ./scripts/query.py trait <性状关键词>
python ./scripts/query.py gene <基因名>
python ./scripts/query.py study <GCST_ID>
```

示例：

```bash
python ./scripts/query.py rsid rs7903146
python ./scripts/query.py trait diabetes
python ./scripts/query.py gene TCF7L2
python ./scripts/query.py study GCST000001
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 rsid

```markdown
## {rsID} GWAS 关联

| 性状 | p 值 | OR | 风险等位基因 | 研究 |
|------|------|-----|--------------|------|
| ...  | ...  | ... | ...          | ...  |

展示前 N 条关联。
```

### 按 trait / gene / study

```markdown
## {标题} GWAS Catalog

| 字段 | 值 |
|------|-----|
| ...  | ... |

共 X 条，展示前 N 条。
```

## 示例

**用户**：rs7903146 和什么疾病有关联？

**Agent**：
1. 运行 `rsid rs7903146`
2. 列出性状、p 值、OR 及文献

**用户**：TCF7L2 有哪些 GWAS SNP？

**Agent**：
1. 运行 `gene TCF7L2`
2. 展示基因内/附近 GWAS SNP 列表

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 单基因病 ClinVar | `clinvar` |
| 人群 AF | `gnomad` |
| 靶点-疾病综合评分 | `opentargets` |
| 本地基因型跑 GWAS | `pop-gwas-association` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | NHGRI-EBI GWAS Catalog |

## Citation

GWAS Catalog · https://www.ebi.ac.uk/gwas/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| SNP 坐标 | `dbsnp` |
| 人群频率 | `gnomad` |
| 临床意义 | `clinvar` |
| 靶点-疾病分数 | `opentargets` |
| 变异后果 | `ensembl vep` |

## 详细解读路径

见 [reference.md](reference.md)
