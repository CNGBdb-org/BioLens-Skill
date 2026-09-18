---
name: kegg
description: >-
  Query KEGG for human gene entries, metabolic pathways, disease associations, compounds,
  and pathway keyword search. Supports gene-to-pathway links and pathway map lookup.
  Academic use only per KEGG API terms. Use for pathway. Not for GO term ontology (use
  go), statistical pathway enrichment, or drug-target genetics scores (use opentargets).
compatibility: Python 3.10+, HTTPS (KEGG API)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: pathway
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# KEGG 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因通路注释 | `gene` | 人类基因 KEGG 条目、关联代谢/信号通路 |
| 通路详情 | `pathway` | 按通路 ID 查基因列表与通路描述 |
| 疾病关联 | `disease` | 疾病关键词检索 KEGG 疾病条目 |
| 化合物 | `compound` | 代谢物/药物化合物 ID 与属性 |
| 通路搜索 | `map` | 按关键词搜索人类通路（hsa） |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（TP53、BRCA1）+ 通路/KEGG | `gene` |
| 通路 ID（hsa04110、04110） | `pathway` |
| 疾病名（diabetes、Parkinson） | `disease` |
| 化合物名（glucose、ATP） | `compound` |
| 通路关键词（apoptosis、MAPK） | `map` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. **仅限学术用途**：KEGG REST API 禁止商业/大规模自动化爬取，遵守 [KEGG 使用条款](https://www.kegg.jp/kegg/legal.html)
3. 默认物种：**人类（hsa）**；`gene` / `map` 检索优先匹配人类基因与通路
4. 通路 ID 可带或不带 `hsa` 前缀（如 `04110` → `hsa04110`）
5. 输出关键字段：KEGG ID、基因/通路/疾病/化合物名称、关联通路列表、条目摘要行

## 运行脚本

```bash
# 按基因查 KEGG 条目与关联通路
python ./scripts/query.py gene <基因名>

# 按通路 ID 查详情
python ./scripts/query.py pathway <通路ID>

# 按疾病关键词搜索
python ./scripts/query.py disease <关键词>

# 按化合物名搜索
python ./scripts/query.py compound <名称>

# 按关键词搜索人类通路
python ./scripts/query.py map <关键词>
```

示例：

```bash
python ./scripts/query.py gene TP53
python ./scripts/query.py pathway hsa04110
python ./scripts/query.py disease diabetes
python ./scripts/query.py compound glucose
python ./scripts/query.py map apoptosis
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按基因（gene）

```markdown
## {基因} KEGG 注释

- **KEGG ID**：
- **条目摘要**：（脚本输出的 NAME、DEFINITION 等前几行）
- **关联通路**：

| 通路 ID | 通路名 |
|---------|--------|
| ...     | ...    |

展示前 N 条关联通路。
```

### 按通路 / 疾病 / 化合物 / map

```markdown
## {标题} KEGG 检索

| ID | 名称 / 描述 |
|----|-------------|
| ... | ... |

共检索到 X 条，展示前 N 条。
```

## 示例

**用户**：TP53 参与哪些 KEGG 通路？

**Agent**：
1. 运行 `gene TP53`
2. 列出关联通路，简述 p53 信号与细胞周期相关通路

**用户**：KEGG 里 apoptosis 相关的人类通路有哪些？

**Agent**：
1. 运行 `map apoptosis`
2. 表格展示 hsa 通路 ID 与名称

**用户**：糖尿病在 KEGG 里对应什么条目？

**Agent**：
1. 运行 `disease diabetes`
2. 展示疾病 ID 与名称，可进一步查关联基因（需用户指定）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GO 术语/祖先 | `go` |
| 通路富集统计 | `外部 enrichment 工具` |
| Open Targets 关联评分 | `opentargets` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | KEGG |
| 物种 | 人类基因默认 hsa |

## Citation

KEGG · https://www.kegg.jp/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 基因坐标、转录本 | `gencode` |
| 直系同源与 GO 注释 | `eggnog` |
| 基因组浏览器 track | `ucsc` |

## 详细解读路径

见 [reference.md](reference.md)
