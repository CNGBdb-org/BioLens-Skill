---
name: clinvar
description: >-
  Query NCBI ClinVar for variant clinical significance. Supports gene pathogenic variants,
  rsID/HGVS/VCV lookup, disease-associated variants, genomic region search, VUS catalog,
  conflicting interpretations, gene classification stats, and evidence depth
  (submitter/trait). Use for ClinVar lookup, pathogenicity, ACMG interpretation support,
  VUS research, conflict detection, or disease-variant association. Not for population
  allele frequency (use gnomad), rsID/coordinate resolve without clinical context (use
  dbsnp), or spatial gene expression (use hesta).
compatibility: Python 3.10+, HTTPS, optional NCBI_API_KEY
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L4
  domain: genomics-variation
  capability_id: cngbdb.genomics.clinical-significance.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# ClinVar 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因致病突变谱 | `gene` | 文献/Panel 设计、突变热点分析 |
| 单点致病性判断 | `rsid` / `hgvs` / `vcv` | 临床报告、WES/VGS 变异注释 |
| 疾病-变异关联 | `disease` | 遗传病基因发现、表型驱动检索 |
| 区域批量注释 | `region` | 靶向测序、CNV 边界、局部热点 |
| VUS 研究 | `vus` | 意义未明变异清单、功能验证候选 |
| 解读冲突 | `conflict` | 实验室间分歧、需重评变异 |
| 基因变异谱概览 | `stats` | 致病/VUS/良性比例、基因负担评估 |
| 证据深度 | `evidence` | 提交者 SCV/RCV、性状/xref、评审状态 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（BRCA1、TP53）+ 致病/突变 | `gene` |
| rsID（rs80357906） | `rsid` |
| HGVS（c.5266dup、p.V600E） | `hgvs` |
| 疾病名（Noonan、乳腺癌、自闭症） | `disease` |
| 坐标区域（chr17:43044295-43044305） | `region` |
| 基因 + VUS/意义未明 | `vus` |
| 基因 + 冲突/分歧解读 | `conflict` |
| 基因 + 统计/有多少致病 | `stats` |
| ClinVar ID / VCV 编号 | `vcv` |
| 为什么致病 / 提交者 / 证据 | `evidence` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 根据脚本输出整理结果，用中文解读给用户
3. 链式调用或程序消费时优先 `--format json`（schema: `cngbdb.skill-result.v2`）
4. 列表类查询可用 `--retmax` 控制检索量；输出含 `total` / `returned` / truncated 提示
5. 致病性表述：
   - Pathogenic / Likely pathogenic → 可报告致病或可能致病
   - VUS → 单独标注「意义未明」，**不可**表述为致病
   - Conflicting → 标注「解读存在冲突」，列出不同意见
   - Benign / Likely benign → 良性，可用于过滤
6. 评审状态优先级：reviewed by expert panel > practice guideline > criteria provided, multiple submitters > single submitter
7. 多条记录冲突时，列出差异，注明提交数量与最后评估日期
8. 输出关键字段：ClinVar ID、变异描述、临床意义、评审状态、坐标、rsID、关联疾病
9. 可选：`export NCBI_API_KEY=...`（使用本 Skill `scripts/_lib/ncbi_http.py`，含 429 重试）

## 运行脚本

```bash
# 按基因查致病位点
python ./scripts/query.py gene <基因名>

# 按 rsID 查致病性
python ./scripts/query.py rsid <rsID>

# 按疾病查相关变异（默认仅致病/可能致病）
python ./scripts/query.py disease <疾病关键词>
python ./scripts/query.py disease <疾病关键词> --all

# 按 HGVS 查变异
python ./scripts/query.py hgvs <HGVS片段> [--gene <基因>]

# 按基因组区域查变异（GRCh38）
python ./scripts/query.py region <区域>

# 查基因 VUS 列表
python ./scripts/query.py vus <基因名>

# 查解读冲突变异
python ./scripts/query.py conflict [<基因名>]

# 查基因变异分类统计
python ./scripts/query.py stats <基因名>

# 按 ClinVar variation ID 或 VCV 编号查
python ./scripts/query.py vcv <ID>

# 证据深度（提交者 / 性状 / 评审）
python ./scripts/query.py evidence <基因|rsID|VCV>

# 通用选项
python ./scripts/query.py <子命令> ... --format json
python ./scripts/query.py <子命令> ... --retmax 50
```

示例：

```bash
python ./scripts/query.py gene BRCA1
python ./scripts/query.py rsid rs80357906 --format json
python ./scripts/query.py disease noonan
python ./scripts/query.py hgvs c.5266dup --gene BRCA1
python ./scripts/query.py region chr17:43057060-43057065
python ./scripts/query.py vus BRCA1 --retmax 50
python ./scripts/query.py conflict BRCA1
python ./scripts/query.py stats TP53
python ./scripts/query.py vcv 17677
python ./scripts/query.py evidence rs80357906 --format json
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按基因 / 疾病 / 区域 / VUS

```markdown
## {标题} ClinVar 变异

| ClinVar ID | 变异 | 临床意义 | 评审状态 | 坐标 | rsID |
|------------|------|----------|----------|------|------|
| ...        | ...  | ...      | ...      | ...  | ...  |

共检索到 X 条，展示前 N 条。
```

### 按 rsID / HGVS / VCV

```markdown
## 变异 {标识} ClinVar 解读

- **ClinVar ID**：
- **基因 / 变异**：
- **坐标 / rsID**：
- **临床意义**：
- **评审状态**：
- **关联疾病 / OMIM**：
- **提交数**：
- **解读结论**：（一句话，区分高置信 / VUS / 冲突 / 需进一步验证）
```

### 按 stats

```markdown
## {基因} ClinVar 变异谱

| 分类 | 数量 | 占比 |
|------|------|------|
| Pathogenic | ... | ... |
| ... | ... | ... |

摘要：致病 X 条，VUS Y 条，冲突 Z 条。
```

### 按 evidence

```markdown
## {标识} ClinVar 证据摘要

- **评审状态 / 提交数**：
- **主要性状 / xref**：
- **SCV/RCV 要点**：
- **结论**：结合评审等级说明置信度
```

## 示例

**用户**：BRCA1 有多少致病变异，VUS 多吗？

**Agent**：
1. 运行 `stats BRCA1` 获取分类统计
2. 若用户需要详情，再运行 `gene BRCA1` 或 `vus BRCA1`
3. 解读致病/VUS 比例及研究意义

**用户**：这个 c.5266dup 变异致病吗？

**Agent**：
1. 运行 `hgvs c.5266dup --gene BRCA1`
2. 按模板输出，注明 expert panel 评审状态
3. 可并行 `dbsnp` 查 rsID 与坐标，`gnomad rsid` 查人群频率

**用户**：为什么 rs80357906 判为致病？有哪些实验室提交？

**Agent**：
1. 运行 `evidence rs80357906 --format json`
2. 汇总提交者、性状与评审状态

**用户**：Noonan 综合征有哪些已知致病变异？

**Agent**：
1. 运行 `disease noonan`
2. 表格展示，按评审状态排序解读

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 人群 AF / MAF / 罕见常见判断 | `gnomad` |
| 仅查 rsID 坐标 / 功能类型 | `dbsnp` |
| 基因坐标 / Ensembl 注释（无临床语境） | `ensembl` |
| 空间表达 | `hesta` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | NCBI ClinVar（E-utilities） |
| 物种 | 默认人类相关 ClinVar 记录 |
| 参考基因组 | 坐标展示优先 GRCh38 |
| 标识符 | rsID / HGVS / VCV / 基因符号 / 疾病关键词 |

## Citation

NCBI ClinVar · https://www.ncbi.nlm.nih.gov/clinvar/ · 注明查询时间与 ClinVar ID

## 联动

| 需求 | 联动 skill |
|------|-----------|
| SNP 坐标、功能类型 | `dbsnp` |
| 人群等位基因频率（AF） | `gnomad` |
| 完整变异解读 | `dbsnp` → `gnomad rsid` → `clinvar rsid` |

## 详细解读路径

见 [reference.md](reference.md)
