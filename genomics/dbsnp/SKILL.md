---
name: dbsnp
description: >-
  Query NCBI dbSNP for SNP information. Supports rsID lookup, gene/region/coordinate
  search, HGVS→rsID resolve, batch rsIDs, function class filter, rare/common MAF filter,
  clinical significance, and gene variant stats. Use for dbSNP, rsID lookup, SNP
  annotation, coordinate-to-rsID, allele frequency summary. Not for ClinVar
  pathogenicity judgment (use clinvar), gnomAD population AF interpretation (use gnomad),
  or spatial expression (use hesta).
compatibility: Python 3.10+, HTTPS, optional NCBI_API_KEY
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L4
  domain: genomics-variation
  capability_id: cngbdb.genomics.variant-lookup.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# dbSNP 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 变异基本信息 | `rsid` | 坐标、等位基因、功能类型、多来源频率 |
| 坐标反查 rsID | `coord` | VCF/WES 注释、坐标转 rs 号 |
| HGVS 解析 rsID | `hgvs` | HGVS → rsID（Variation Services + 回退） |
| 基因变异目录 | `gene` | 某基因全部 RefSNP |
| 区域批量注释 | `region` | 靶向测序/CNV 边界 |
| 功能类型筛选 | `function` | missense / frameshift 等 |
| 罕见/常见变异 | `rare` / `common` | MAF 过滤，辅助致病性判断 |
| 致病相关 SNP | `clinical` | 有 ClinVar 致病标注的位点 |
| 批量查询 | `batch` | 多个 rsID 一次查 |
| 基因变异谱 | `stats` | SNV/indel 类型比例 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| rsID（rs80357906） | `rsid` |
| 染色体 + 位置（chr17:43057062） | `coord` |
| HGVS（NC_...:g. / c.5266dup） | `hgvs` |
| 基因名（BRCA1、TP53） | `gene` |
| 坐标区域 | `region` |
| 基因 + missense/frameshift 等 | `function` |
| 基因 + 罕见/常见/MAF | `rare` / `common` |
| 基因 + 致病 SNP | `clinical` |
| 多个 rsID | `batch` |
| ss 编号 | `ss` |
| 基因 + 统计/有多少 SNP | `stats` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 链式调用优先 `--format json`（schema: `cngbdb.skill-result.v2`）
3. 列表类可用 `--retmax`；输出含 `total` / `returned` / truncated
4. 输出：rsID、GRCh38/GRCh37 坐标、等位基因、基因、功能类型、多来源 MAF
5. 频率解读：
   - dbSNP 提供 ExAC/gnomAD/ALFA/TOPMED 等汇总频率
   - 精确人群 AF → 联动 `gnomad` skill
6. 致病性 → 联动 `clinvar` skill（dbSNP 仅提供 CLIN 标签摘要）
7. 注明参考基因组版本（默认 GRCh38）
8. 可选：`export NCBI_API_KEY=...`（使用本 Skill `scripts/_lib/ncbi_http.py`）

## 运行脚本

```bash
# 按 rsID 查（兼容旧用法：省略 rsid 子命令）
python ./scripts/query.py rsid <rsID>
python ./scripts/query.py <rsID>

# 坐标反查 rsID
python ./scripts/query.py coord <chr> <pos> [--assembly GRCh38|GRCh37]

# HGVS → rsID
python ./scripts/query.py hgvs <HGVS>

# 按基因 / 区域
python ./scripts/query.py gene <基因名>
python ./scripts/query.py region <区域> [--assembly GRCh38|GRCh37]

# 功能 / 频率 / 临床筛选
python ./scripts/query.py function <基因> <功能类型>
python ./scripts/query.py rare <基因>
python ./scripts/query.py common <基因>
python ./scripts/query.py clinical <基因>

# 批量 / ss / 统计
python ./scripts/query.py batch <rsID1> <rsID2> ...
python ./scripts/query.py ss <ssID>
python ./scripts/query.py stats <基因名>

# 通用选项
python ./scripts/query.py <子命令> ... --format json
python ./scripts/query.py <子命令> ... --retmax 50
```

示例：

```bash
python ./scripts/query.py rs80357906
python ./scripts/query.py rsid rs80357906 --format json
python ./scripts/query.py coord 17 43057062
python ./scripts/query.py hgvs 'NC_000017.11:g.43057063G>A'
python ./scripts/query.py gene BRCA1
python ./scripts/query.py region chr17:43057060-43057065
python ./scripts/query.py function TP53 missense
python ./scripts/query.py rare BRCA1
python ./scripts/query.py clinical BRCA1
python ./scripts/query.py batch rs80357906 rs328
python ./scripts/query.py stats TP53
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 rsID / coord

```markdown
## rs{编号} 基本信息

| 项目 | 内容 |
|------|------|
| rsID | ... |
| 坐标 | chr:pos (GRCh38 / GRCh37) |
| 等位基因 | REF>ALT |
| 基因 | ... |
| 变异类型 | snv / ins / del / ... |
| 功能类型 | ... |
| MAF/频率 | ExAC=...; gnomAD=...; ALFA=... |
| 临床意义 | ...（若有，建议查 ClinVar） |
```

### 按 hgvs

```markdown
## HGVS → rsID

- **输入 HGVS**：...
- **解析到的 rsID**：rs...
- 再按需运行 `rsid` 取详细注释
```

### 按 gene / region / function

```markdown
## {基因/区域} dbSNP 变异

| rsID | 坐标 | 基因 | 功能类型 | MAF |
|------|------|------|----------|-----|
| ...  | ...  | ...  | ...      | ... |

共检索到 X 条，展示前 N 条。
```

### 按 stats

```markdown
## {基因} dbSNP 变异谱

| 变异类型 | 数量 | 占比 |
|----------|------|------|
| SNV | ... | ... |
| INS/DEL/... | ... | ... |

致病相关 X 条，罕见 Y 条，常见 Z 条。
```

## 示例

**用户**：chr17:43057062 这个位置是什么 rs 号？

**Agent**：
1. 运行 `coord 17 43057062`
2. 返回 rsID、等位基因、功能类型
3. 若问频率/致病性，联动 gnomAD / ClinVar

**用户**：这个基因组 HGVS 对应哪个 rs？

**Agent**：
1. 运行 `hgvs 'NC_000017.11:g.43057063G>A'`
2. 再 `rsid` 补全注释

**用户**：TP53 有多少 missense 变异？

**Agent**：
1. 运行 `function TP53 missense`
2. 表格展示，说明 dbSNP 为 RefSNP 总数

**用户**：rs80357906 是什么变异，常见吗，致病吗？

**Agent**：
1. 并行 `dbsnp rsid` + `gnomad rsid` + `clinvar rsid`
2. 合并坐标、频率、致病性解读

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 临床致病性 / VUS 解读 | `clinvar` |
| gnomAD FAF95 / 人群分层 AF | `gnomad` |
| VEP 后果预测 | `ensembl` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | NCBI dbSNP |
| 参考基因组 | 默认 GRCh38，可用 --assembly GRCh37 |
| 标识符 | rsID / 坐标 / HGVS / 基因 |

## Citation

NCBI dbSNP · https://www.ncbi.nlm.nih.gov/snp/ · 注明 rsID 与 assembly

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 精确人群 AF / 各族群频率 | `gnomad` |
| 临床致病性详情 | `clinvar` |
| 完整变异解读 | dbsnp → gnomad → clinvar |

## 详细解读路径

见 [reference.md](reference.md)
