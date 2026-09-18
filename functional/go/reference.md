# GO 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 术语定义 | `term` | GO ID → 名称、定义、aspect |
| 概念探索 | `search` | 关键词 → 相关 GO terms |
| 基因功能谱 | `gene` | 基因的全部 GO 注释 |
| 层级分析 | `ancestors` | term 的上位概念链 |

## 输入 → 输出

### Term 详情（term）

```
GO:0006915 或 0006915
  → GET QuickGO /ontology/go/terms/{GO:xxxxxxx}
  → name、aspect、definition、synonyms
```

### 搜索（search）

```
关键词（apoptosis）
  → GET /ontology/go/search?query={keyword}
  → 匹配 term 列表及定义
```

### 基因注释（gene）

```
基因符号
  → GET /annotation/search?geneSymbol={symbol}&taxonId=9606
  → goId、goName、goEvidence、assignedBy、reference
```

### 祖先（ancestors）

```
GO ID
  → GET /ontology/go/term/{GO:xxx}/ancestors
  → 全部祖先 term（含 aspect）
```

## 核心字段

| 字段 | 说明 |
|------|------|
| aspect | P=生物过程, F=分子功能, C=细胞组分 |
| goEvidence | IDA、IEA、TAS 等证据码 |
| assignedBy | 注释来源数据库 |
| reference | 支持文献（PMID 等） |

## 证据码提示

| 类型 | 含义 |
|------|------|
| IDA/IEP/IMP 等 | 实验支持，较可靠 |
| IEA | 电子推断，需谨慎 |
| TAS | 可追溯摘要 |

## API 参考

- [QuickGO API](https://www.ebi.ac.uk/QuickGO/api/index.html)
- [Gene Ontology](http://geneontology.org/)
