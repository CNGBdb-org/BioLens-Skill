---
name: refseq
description: >-
  Query NCBI RefSeq via E-utilities for human genes, transcripts, proteins, and regional
  gene lookup. Supports gene symbol search, NM/NP accession lookup, and genomic interval
  gene lists. Use for RefSeq Gene ID, transcript accession,. Not for Ensembl-centric
  annotation (use ensembl), GENCODE release details (use gencode), or ClinVar (use
  clinvar).
compatibility: Python 3.10+, HTTPS, optional NCBI_API_KEY
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

# RefSeq 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因检索 | `gene` | RefSeq Gene ID、坐标、描述 |
| 转录本 | `transcript` | NM_ accession 详情 |
| 蛋白 | `protein` | NP_ accession 详情 |
| 区域基因 | `region` | 区间内 RefSeq 基因 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（BRCA1、TP53） | `gene` |
| 转录本 accession（NM_007294） | `transcript` |
| 蛋白 accession（NP_009225） | `protein` |
| 坐标区域（chr17:43044295-43170245） | `region` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 默认限定 **人类**（homo sapiens[orgn]）
3. NCBI E-utilities 有频率限制，脚本内置 ~0.34s 间隔，**不要**连续批量调用
4. 区域格式：`chr17:43044295-43170245` 或 `17 43044295 43170245`
5. 输出关键字段：Gene ID、符号、描述、染色体坐标、accession、序列长度

## 运行脚本

```bash
python ./scripts/query.py gene <基因名>
python ./scripts/query.py transcript <NM_accession>
python ./scripts/query.py protein <NP_accession>
python ./scripts/query.py region <区域>
```

示例：

```bash
python ./scripts/query.py gene BRCA1
python ./scripts/query.py transcript NM_007294
python ./scripts/query.py protein NP_009225
python ./scripts/query.py region chr17:43044295-43170245
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 gene / region

```markdown
## {标题} RefSeq 基因

| Gene ID | 符号 | 描述 | 染色体 | 坐标 |
|---------|------|------|--------|------|
| ...     | ...  | ...  | ...    | ...  |

共检索到 X 条，展示前 N 条。
```

### 按 transcript / protein

```markdown
## RefSeq {accession}

- **Accession**：
- **标题**：
- **长度**：（bp / aa）
- **更新日期**：
```

## 示例

**用户**：BRCA1 的 RefSeq Gene ID 和坐标？

**Agent**：
1. 运行 `gene BRCA1`
2. 列出 Gene ID、染色体坐标

**用户**：NM_007294 是什么转录本？

**Agent**：
1. 运行 `transcript NM_007294`
2. 输出标题、长度与关联基因

## Do Not Use When

| 需求 | 交给 |
|------|------|
| Ensembl ID / VEP | `ensembl` |
| GENCODE 版本与转录本集 | `gencode` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | NCBI RefSeq |
| 物种 | 默认人类 |

## Citation

NCBI RefSeq · https://www.ncbi.nlm.nih.gov/refseq/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| Ensembl 转录本对比 | `ensembl gene` |
| 蛋白功能 | `uniprot` |
| SNP / 变异 | `dbsnp` |
| 临床意义 | `clinvar` |
| GO 注释 | `go gene` |

## 详细解读路径

见 [reference.md](reference.md)
