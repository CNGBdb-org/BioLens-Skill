# GWAS Catalog 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| SNP 关联查询 | `rsid` | 某 rsID 的全部 GWAS 命中 |
| 性状驱动 | `trait` | 某性状的 GWAS 研究列表 |
| 基因层面 | `gene` | 基因区域 GWAS SNP |
| 文献追溯 | `study` | GCST 研究详情与 PubMed |

## 输入 → 输出

### 按 rsID（rsid）

```
rs7903146
  → GET /singleNucleotidePolymorphisms/{rsId}
  → GET /associations/search/findByRsId?rsId={rs}
  → 性状、pvalueMantissa/Exponent、orPerCopyNum、riskAllele
```

### 按性状（trait）

```
diabetes
  → GET /studies/search/findByDiseaseTrait?diseaseTrait={keyword}
  → 研究列表、样本量、PubMed、GCST accession
```

### 按基因（gene）

```
TCF7L2
  → GET /singleNucleotidePolymorphisms/search/findByGene?geneName={symbol}
  → 基因映射 SNP 及功能类别
```

### 按研究（study）

```
GCST000001
  → GET /studies/{accessionId}
  → 性状、样本量、平台、SNP 数、PubMed
```

## 核心字段

| 字段 | 说明 |
|------|------|
| efoTraits | EFO 标准化性状名 |
| pvalueMantissa/Exponent | 科学计数法 p 值 |
| orPerCopyNum | 每拷贝 OR |
| strongestRiskAlleles | 风险等位基因 |
| accessionId | GCST 研究编号 |

## 注意点

- GWAS 为关联证据，非因果或临床致病结论
- 多 SNP 连锁时需注意 LD 与 fine-mapping
- 与 `opentargets` 联动可查看整合靶点分数

## API 参考

- [GWAS Catalog REST API](https://www.ebi.ac.uk/gwas/docs/api)
- [GWAS Catalog](https://www.ebi.ac.uk/gwas/)
