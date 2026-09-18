---
name: dfam
description: >-
  Query Dfam repetitive DNA family database. Supports family lookup by name or accession,
  keyword search, HMM model details, repeat type filtering, and region guidance (no direct
  coordinate API — links to UCSC RepeatMasker). Use for. Not for genomic-interval
  RepeatMasker track annotation (use ucsc track RepeatMasker), or gene annotation (use
  ensembl).
compatibility: Python 3.10+, HTTPS (Dfam API)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: repeats
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Dfam 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 家族详情 | `family` | 按名称或 accession 查重复元件家族 |
| 关键词搜索 | `search` | 家族名称模糊检索 |
| HMM 模型 | `model` | 家族 HMM 参数、长度、阈值 |
| 重复类型 | `repeat` | 按 LINE/SINE/LTR 等类型筛选 |
| 基因组区域 | `region` | **无直接 API**；引导联动 UCSC RepeatMasker |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 家族名（Alu、L1MC）或 accession（DF0000001） | `family` / `model` |
| 关键词（Alu、MER） | `search` |
| 重复类型（LINE、SINE、LTR、DNA） | `repeat` |
| 坐标区域（chr1:1000000-1010000） | `region` → 联动 `ucsc` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. `family` 先按名称搜，无结果再按 accession 搜
3. `region` **不提供**基因组坐标区间重复注释；脚本输出说明并建议：
   ```bash
   python ../ucsc/scripts/query.py track RepeatMasker <区域>
   ```
4. 输出关键字段：accession、name、title、repeat_type、物种、HMM 长度与 gathering threshold

## 运行脚本

```bash
# 按家族名或 accession 查详情
python ./scripts/query.py family <名称或accession>

# 关键词搜索家族
python ./scripts/query.py search <关键词>

# 查 HMM 模型详情
python ./scripts/query.py model <accession>

# 按重复类型筛选
python ./scripts/query.py repeat <类型或关键词>

# 区域查询（输出 UCSC 联动指引）
python ./scripts/query.py region <区域>
```

示例：

```bash
python ./scripts/query.py family Alu
python ./scripts/query.py search MER
python ./scripts/query.py model DF0000001
python ./scripts/query.py repeat LINE
python ./scripts/query.py region chr1:1000000-1010000
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 family / search / repeat

```markdown
## {标题} Dfam 家族

| Accession | 名称 | 类型 | 描述摘要 |
|-----------|------|------|----------|
| ... | ... | ... | ... |

共 X 条，展示前 N 条。
```

### 按 model

```markdown
## Dfam HMM 模型 {accession}

- **名称**：
- **长度**：
- **Gathering threshold**：
- **分类（repeat_type）**：
```

### 按 region（指引）

```markdown
## 区域 {chr:start-end} 重复元件

Dfam API **不支持**坐标区间查询。

**建议**：使用 UCSC RepeatMasker track：
`python ../ucsc/scripts/query.py track RepeatMasker {区域}`

查到元件名后，可用 `dfam family <名称>` 查家族详情。
```

## 示例

**用户**：Alu 元件在 Dfam 里是什么家族？

**Agent**：
1. 运行 `family Alu`
2. 展示 accession、类型与描述

**用户**：chr1:1000000-1010000 有哪些重复序列？

**Agent**：
1. 运行 `region chr1:1000000-1010000` 说明 API 限制
2. 运行 `ucsc track RepeatMasker chr1:1000000-1010000`
3. 对典型元件名再查 `dfam family`

**用户**：LINE 重复有哪些 Dfam 家族？

**Agent**：
1. 运行 `repeat LINE`
2. 表格列出家族

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 坐标区间重复注释 | `ucsc track RepeatMasker` |
| 基因注释 | `ensembl` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | Dfam |

## Citation

Dfam · https://www.dfam.org/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 区域 RepeatMasker 注释 | `ucsc`（`track RepeatMasker`） |
| 基因与转录本坐标 | `gencode` |

## 详细解读路径

见 [reference.md](reference.md)
