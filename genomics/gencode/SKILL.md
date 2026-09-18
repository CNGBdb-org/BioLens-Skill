---
name: gencode
description: >-
  Query GENCODE human gene annotations via Ensembl REST API. Supports gene lookup with
  transcript list, transcript details, GENCODE/Ensembl release version, and protein-coding
  transcripts in a genomic region. Use for GENCODE ID, transcript. Not for RefSeq NM/NP
  lookup (use refseq), ClinVar (use clinvar), or HESTA spatial (use hesta).
compatibility: Python 3.10+, HTTPS (via Ensembl REST)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: genomics-annotation
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# GENCODE 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因注释 | `gene` | GENCODE/Ensembl ID、坐标、转录本列表 |
| 转录本详情 | `transcript` | 外显子数、坐标、生物型 |
| 版本信息 | `version` | 当前 Ensembl/GENCODE 发布版本与组装 |
| 区域基因 | `region` | 区间内蛋白编码转录本重叠 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（BRCA1、TP53） | `gene` |
| 转录本 ID（ENST00000357654） | `transcript` |
| GENCODE/Ensembl 版本 | `version` |
| 坐标区域（chr17:43044295-43170245） | `region` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. GENCODE 注释通过 **Ensembl REST API** 提供，与 GENCODE 官网同步发布
3. 默认物种：`homo_sapiens`，组装 **GRCh38**
4. 区域格式：`chr17:43044295-43170245` 或 `17 43044295 43170245`
5. `region` 默认仅返回 **protein_coding** 转录本
6. 输出关键字段：Ensembl/GENCODE ID、biotype、坐标、版本、logic_name

## 运行脚本

```bash
# 按基因符号查 GENCODE 注释
python ./scripts/query.py gene <基因名>

# 按转录本 ID 查详情
python ./scripts/query.py transcript <转录本ID>

# 查当前 GENCODE/Ensembl 版本
python ./scripts/query.py version

# 查区域内蛋白编码转录本
python ./scripts/query.py region <区域>
```

示例：

```bash
python ./scripts/query.py gene BRCA1
python ./scripts/query.py transcript ENST00000357654
python ./scripts/query.py version
python ./scripts/query.py region chr17:43044295-43170245
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按基因（gene）

```markdown
## {基因} GENCODE 注释

- **Ensembl/GENCODE ID**：
- **描述**：
- **生物型**：
- **坐标**：chr…:…-…（GRCh38）
- **版本**：

| 转录本 ID | 生物型 | 版本 | 坐标 | logic_name |
|-----------|--------|------|------|------------|
| ... | ... | ... | ... | ... |
```

### 按转录本（transcript）

```markdown
## 转录本 {ID}

- **基因**：
- **生物型**：
- **坐标**：
- **外显子数**：
```

### 按区域（region）

```markdown
## 区域 {chr:start-end} 蛋白编码转录本

| # | 转录本 ID | 基因 | 生物型 | 坐标 |
|---|-----------|------|--------|------|
| ... | ... | ... | ... | ... |

共 X 条，展示前 N 条。
```

## 示例

**用户**：BRCA1 有哪些 GENCODE 转录本？

**Agent**：
1. 运行 `gene BRCA1`
2. 表格列出主要转录本及 biotype

**用户**：当前 GENCODE 是什么版本？

**Agent**：
1. 运行 `version`
2. 说明 Ensembl release 与 GRCh38 组装

**用户**：chr17:43044295-43170245 有哪些基因？

**Agent**：
1. 运行 `region chr17:43044295-43170245`
2. 列出重叠蛋白编码转录本

## Do Not Use When

| 需求 | 交给 |
|------|------|
| RefSeq accession | `refseq` |
| 临床致病性 | `clinvar` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | GENCODE via Ensembl |
| 组装 | GRCh38 |

## Citation

GENCODE · https://www.gencodegenes.org/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 变异后果、VEP | `ensembl` |
| 基因组浏览器 | `ucsc` |
| 通路注释 | `kegg` |

## 详细解读路径

见 [reference.md](reference.md)
