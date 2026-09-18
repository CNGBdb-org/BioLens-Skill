---
name: ucsc
description: >-
  Query UCSC Genome Browser API for track data, gene search, regional gene overlap
  (knownGene), and conservation scores (phastCons). Supports custom genome assembly with
  hg38 default. Use for UCSC track lookup, gene coordinates,. Not for Dfam family metadata
  (use dfam), Ensembl gene lookup (use ensembl), or variant clinical significance (use
  clinvar).
compatibility: Python 3.10+, HTTPS (UCSC API)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: genome-browser
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# UCSC 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| Track 数据 | `track` | 指定 track 在区间内的记录 |
| 基因搜索 | `gene` | UCSC 基因组内基因名检索 |
| 区域基因 | `region` | 区间内 knownGene 注释 |
| 保守性 | `conservation` | phastCons 保守性分数可用性 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| track 名 + 区域（RepeatMasker chr1:1-100000） | `track` |
| 基因名（BRCA1、TP53） | `gene` |
| 坐标区域（chr17:43044295-43170245） | `region` / `conservation` |
| 非 hg38 组装 | 加 `--genome`（如 hg19、mm39） |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 默认基因组：**hg38**（人类 GRCh38）；可用 `--genome` 切换
3. 区域格式：`chr17:43044295-43170245` 或 `17 43044295 43170245`（自动补 `chr` 前缀）
4. `region` 等价于 `track knownGene <region>`
5. `conservation` 尝试 phastCons100way / phastCons30way；无数据时提示用 bigWig 或 Ensembl
6. 输出关键字段：基因/track 名、chrom、start、end

## 运行脚本

```bash
# 查指定 track 在区域内的数据
python ./scripts/query.py track <track名> <区域> [--genome hg38]

# 搜索基因
python ./scripts/query.py gene <基因名> [--genome hg38]

# 查区域内基因（knownGene）
python ./scripts/query.py region <区域> [--genome hg38]

# 查保守性分数
python ./scripts/query.py conservation <区域> [--genome hg38]
```

示例：

```bash
python ./scripts/query.py gene BRCA1
python ./scripts/query.py region chr17:43044295-43170245
python ./scripts/query.py track RepeatMasker chr1:1000000-1010000
python ./scripts/query.py conservation chr17:7577000-7579000
python ./scripts/query.py gene TP53 --genome hg19
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 gene / region / track

```markdown
## {标题} UCSC 注释（{genome}）

| # | 名称 | 坐标 |
|---|------|------|
| ... | ... | chr…:…-… |

展示前 N 条。
```

### 按 conservation

```markdown
## 区域 {chr:start-end} 保守性（{genome}）

- **phastCons track**：有/无数据
- **说明**：若无直接数值，建议 UCSC bigWig 或 Ensembl 保守性
```

## 示例

**用户**：BRCA1 在 UCSC hg38 上的坐标？

**Agent**：
1. 运行 `gene BRCA1`
2. 报告 chrom:start-end

**用户**：chr1:1000000-1010000 有哪些 RepeatMasker 重复元件？

**Agent**：
1. 运行 `track RepeatMasker chr1:1000000-1010000`
2. 列出重复元件名称与坐标

**用户**：这个区域保守性怎么样？

**Agent**：
1. 运行 `conservation <区域>`
2. 说明 phastCons 数据可用性或替代方案

## Do Not Use When

| 需求 | 交给 |
|------|------|
| Dfam 家族 HMM 详情 | `dfam` |
| Ensembl 基因注释 | `ensembl` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | UCSC Genome Browser API |
| 基因组 | 默认 hg38 |

## Citation

UCSC Genome Browser · https://genome.ucsc.edu/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| GENCODE 转录本注释 | `gencode` |
| 重复元件家族详情 | `dfam`（`region` → UCSC RepeatMasker） |
| 变异临床意义 | `clinvar` |

## 详细解读路径

见 [reference.md](reference.md)
