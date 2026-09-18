# UniProt 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因→蛋白映射 | `gene` | 列出人类蛋白条目 |
| 单条目详情 | `protein` | accession 精确查询 |
| 快速定位 | `id` | accession/ID/基因名 |
| 功能研究 | `function` | 功能、定位、通路 |
| 疾病蛋白 | `disease` | 疾病相关蛋白列表 |

## 输入 → 输出

### 按基因（gene）

```
基因符号
  → GET /uniprotkb/search?query=gene:{symbol} AND organism_id:9606
  → accession、蛋白名、长度、Ensembl xref、疾病
```

### 按 accession（protein）

```
P38398
  → GET /uniprotkb/{accession}
  → 完整条目 JSON 摘要
```

### 按 ID（id）

```
accession / uniProtkbId / 基因名
  → search (accession OR id OR gene) AND organism_id:9606
  → 最佳匹配条目
```

### 功能（function）

```
基因符号
  → search reviewed:true（优先 Swiss-Prot）
  → FUNCTION / SUBCELLULAR LOCATION / PATHWAY 注释
```

### 疾病（disease）

```
疾病关键词
  → search disease:{keyword} AND organism_id:9606
  → 关联蛋白列表
```

## 核心字段

| 字段 | 说明 |
|------|------|
| primaryAccession | UniProt accession（如 P38398） |
| proteinDescription | 推荐蛋白名 |
| comments[FUNCTION] | 功能描述 |
| comments[DISEASE] | 疾病关联（含 diseaseId） |
| uniProtKBCrossReferences | Ensembl、RefSeq 等交叉引用 |

## 注意点

- Swiss-Prot（reviewed）优先于 TrEMBL（unreviewed）
- 疾病注释为 curated 关联，需与 `clinvar`/`opentargets` 区分层次
- 序列变异后果请用 `ensembl vep` 或 `clinvar`

## API 参考

- [UniProt REST API](https://www.uniprot.org/help/api)
- [UniProtKB search fields](https://www.uniprot.org/help/query-fields)
