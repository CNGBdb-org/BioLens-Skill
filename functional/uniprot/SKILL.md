---
name: uniprot
description: >-
  Query UniProt for human protein entries by gene, accession, or ID. Supports protein
  details, functional annotation, subcellular location, pathways, and disease
  associations. Use for UniProt accession, protein function, reviewed. Not for gene
  genomic coordinates (use ensembl/refseq), ClinVar pathogenicity (use clinvar), or GO
  term hierarchy browsing (use go).
compatibility: Python 3.10+, HTTPS (UniProt REST)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: protein
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# UniProt 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因→蛋白 | `gene` | 人类蛋白条目列表 |
| 蛋白详情 | `protein` | 按 accession 查完整条目 |
| 灵活检索 | `id` | accession / UniProt ID / 基因名 |
| 功能注释 | `function` | 功能、亚细胞定位、通路 |
| 疾病关联 | `disease` | 与疾病相关的蛋白 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（BRCA1、TP53） | `gene` / `function` |
| UniProt accession（P38398） | `protein` |
| UniProt ID 或模糊标识 | `id` |
| 基因 + 功能/定位/通路 | `function` |
| 疾病名（breast、Noonan） | `disease` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 默认限定 **人类**（organism_id:9606）；`function` 优先 Swiss-Prot（reviewed:true）
3. 输出关键字段：Accession、蛋白名、序列长度、功能摘要、疾病关联、Ensembl 交叉引用
4. 功能描述过长时截取核心句，引导用户查看完整条目
5. 疾病关联来自 UniProt 注释，不等同于 ClinVar 致病性

## 运行脚本

```bash
python ./scripts/query.py gene <基因名>
python ./scripts/query.py protein <accession>
python ./scripts/query.py id <accession/ID/基因>
python ./scripts/query.py function <基因名>
python ./scripts/query.py disease <疾病关键词>
```

示例：

```bash
python ./scripts/query.py gene BRCA1
python ./scripts/query.py protein P38398
python ./scripts/query.py id P38398
python ./scripts/query.py function TP53
python ./scripts/query.py disease breast
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 gene / protein / disease

```markdown
## {标题} UniProt 条目

| Accession | 基因 | 蛋白名 | 长度 | 疾病关联 |
|-----------|------|--------|------|----------|
| ...       | ...  | ...    | ...  | ...      |

共检索到 X 条，展示前 N 条。
```

### 按 function

```markdown
## {基因} 功能注释

- **Accession**：
- **功能**：
- **亚细胞定位**：
- **催化活性 / 通路**：
- **解读**：（一句话概括生物学角色）
```

## 示例

**用户**：BRCA1 编码什么蛋白，UniProt 条目是什么？

**Agent**：
1. 运行 `gene BRCA1`
2. 列出 accession、蛋白名与 Ensembl 交叉引用

**用户**：TP53 蛋白的主要功能是什么？

**Agent**：
1. 运行 `function TP53`
2. 输出功能、定位与通路摘要

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 基因组坐标 / 转录本 | `ensembl` |
| 临床致病性 | `clinvar` |
| GO term 详情/祖先 | `go` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | UniProt |
| 物种 | 默认人类 organism_id:9606 |

## Citation

UniProt · https://www.uniprot.org/ · 注明 accession

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 基因组坐标 / 转录本 | `ensembl` / `refseq` |
| GO 功能术语 | `go` |
| 变异临床意义 | `clinvar` |
| 药物靶点证据 | `opentargets` |
| 遗传关联 | `gwascatalog` |

## 详细解读路径

见 [reference.md](reference.md)
