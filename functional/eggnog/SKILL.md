---
name: eggnog
description: >-
  Query eggNOG ortholog groups via UniProt cross-references and eggNOG API v5. Supports
  gene-to-OG lookup, ortholog group GO terms and domains, multi-isoform ortholog listing,
  and functional annotation. Use for ortholog groups, eggNOG OG. Not for Ensembl
  orthologue REST (use ensembl homology), UniProt entry detail (use uniprot), or GO term
  lookup (use go).
compatibility: Python 3.10+, HTTPS
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: ortholog
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# eggNOG 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因 → 直系同源组 | `gene` | UniProt 交叉引用 eggNOG OG，附 GO 摘要 |
| 同源组详情 | `og` | 按 OG ID 查 GO 术语与蛋白结构域 |
| 同源 ID 列表 | `ortholog` | 基因对应 UniProt 与 eggNOG OG 映射 |
| 功能注释 | `function` | 基于 OG 的 GO 功能术语（BP/MF/CC） |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 人类基因名（TP53、BRCA1） | `gene` / `ortholog` / `function` |
| eggNOG OG ID（如 4PQUD@1\|root） | `og` |
| 基因 + 同源/ortholog | `ortholog` |
| 基因 + GO/功能注释 | `function` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 基因检索路径：**UniProt**（`organism_id:9606`，优先 Swiss-Prot reviewed）→ **eggNOG crossref** → **eggnogapi5**
3. 默认物种：**人类（Homo sapiens, 9606）**
4. GO 术语展示频率（freq%）为 OG 内成员占比，非统计检验
5. 输出关键字段：UniProt accession、eggNOG OG ID、GO ID/名称、蛋白结构域

## 运行脚本

```bash
# 基因 → eggNOG OG 与 GO 摘要
python ./scripts/query.py gene <基因名>

# 按 OG ID 查详情
python ./scripts/query.py og <OG_ID>

# 列出基因对应 UniProt 与 OG
python ./scripts/query.py ortholog <基因名>

# 基因功能 GO 注释（来自 OG）
python ./scripts/query.py function <基因名>
```

示例：

```bash
python ./scripts/query.py gene TP53
python ./scripts/query.py og 4PQUD@1|root
python ./scripts/query.py ortholog BRCA1
python ./scripts/query.py function EGFR
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按基因 / function

```markdown
## {基因} eggNOG 注释

- **UniProt**：
- **eggNOG OG**：

| GO 类别 | GO ID | 术语 | 频率 |
|---------|-------|------|------|
| BP/MF/CC | ... | ... | ...% |
```

### 按 OG（og）

```markdown
## eggNOG 同源组 {OG_ID}

### GO 术语
| 类别 | GO ID | 名称 |
|------|-------|------|
| ... | ... | ... |

### 蛋白结构域
- ...
```

### 按 ortholog

```markdown
## {基因} eggNOG 同源映射

| UniProt | 基因 | eggNOG OG |
|---------|------|-----------|
| ... | ... | ... |
```

## 示例

**用户**：TP53 的 eggNOG 直系同源组是什么，有哪些 GO 功能？

**Agent**：
1. 运行 `gene TP53`
2. 解读 OG ID 与主要 GO 术语（细胞周期、凋亡等）

**用户**：4PQUD@1|root 这个 OG 有哪些结构域？

**Agent**：
1. 运行 `og 4PQUD@1|root`
2. 列出 domains 与 GO 分类

**用户**：BRCA1 对应几个 UniProt 条目和 eggNOG ID？

**Agent**：
1. 运行 `ortholog BRCA1`
2. 说明多转录本/异构体对应关系

## Do Not Use When

| 需求 | 交给 |
|------|------|
| Ensembl 直系同源 | `ensembl homology` |
| UniProt 蛋白详情 | `uniprot` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | eggNOG / UniProt xref |

## Citation

eggNOG · http://eggnog5.embl.de/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 代谢/信号通路 | `kegg` |
| 基因坐标与转录本 | `gencode` |
| 基因组保守性 | `ucsc` |

## 详细解读路径

见 [reference.md](reference.md)
