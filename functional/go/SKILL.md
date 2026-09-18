---
name: go
description: >-
  Query Gene Ontology via QuickGO for term details, keyword search, gene annotations, and
  term ancestry. Supports GO ID lookup, term definition, gene GO annotations (BP/MF/CC),
  and ancestor hierarchy. Use for GO term, gene function ontology, biological process,
  molecular function, or cellular. Not for statistical GO enrichment/GSEA (planned
  enrichment skill), KEGG pathways (use kegg), variant pathogenicity (use clinvar), or
  MAGMA/GWAS pathway enrichment (use pop-pathway-enrichment).
compatibility: Python 3.10+, HTTPS (QuickGO)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: functional-annotation
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Gene Ontology (GO) 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| GO 术语详情 | `term` | 定义、命名空间、同义词 |
| 关键词搜索 | `search` | 按名称/定义搜 GO term |
| 基因注释 | `gene` | 基因的 BP/MF/CC 注释 |
| 术语层级 | `ancestors` | 祖先 term 与上位概念 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| GO ID（GO:0006915、6915） | `term` / `ancestors` |
| 功能关键词（apoptosis、kinase） | `search` |
| 基因名（TP53、BRCA1） | `gene` |
| GO term + 上级/祖先 | `ancestors` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. GO ID 可带或不带 `GO:` 前缀，脚本自动规范化
3. 命名空间（aspect）：**P**=生物过程、**F**=分子功能、**C**=细胞组分
4. 基因注释含证据码（goEvidence）与来源（assignedBy），注明实验/推断证据
5. 输出关键字段：GO ID、名称、定义、证据码、参考 PMID

## 运行脚本

```bash
python ./scripts/query.py term <GO_ID>
python ./scripts/query.py search <关键词>
python ./scripts/query.py gene <基因名>
python ./scripts/query.py ancestors <GO_ID>
```

示例：

```bash
python ./scripts/query.py term GO:0006915
python ./scripts/query.py search apoptosis
python ./scripts/query.py gene TP53
python ./scripts/query.py ancestors GO:0006915
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 term / search

```markdown
## GO Term {ID}

- **名称**：
- **命名空间**：（BP / MF / CC）
- **定义**：
- **同义词**：
```

### 按 gene

```markdown
## {基因} GO 注释

| GO ID | 名称 | 证据 | 来源 |
|-------|------|------|------|
| ...   | ...  | ...  | ...  |

展示前 N 条。
```

### 按 ancestors

```markdown
## {GO ID} 祖先术语

| GO ID | 名称 | 命名空间 |
|-------|------|----------|
| ...   | ...  | ...      |
```

## 示例

**用户**：TP53 有哪些 GO 功能注释？

**Agent**：
1. 运行 `gene TP53`
2. 按 BP/MF/CC 分类解读，注明证据码

**用户**：apoptosis 相关的 GO term 有哪些？

**Agent**：
1. 运行 `search apoptosis`
2. 列出匹配 term 及定义摘要

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GO/KEGG 富集分析（统计） | `planned enrichment / 外部工具` |
| 代谢通路图 | `kegg` |
| 变异致病性 | `clinvar` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | QuickGO / Gene Ontology |

## Citation

Gene Ontology / QuickGO · https://www.ebi.ac.uk/QuickGO/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 蛋白功能文本 | `uniprot function` |
| 基因基因组注释 | `ensembl gene` |
| 疾病/靶点 | `opentargets` |
| 通路 | `kegg`（若可用） |

## 详细解读路径

见 [reference.md](reference.md)
