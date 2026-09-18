---
name: gnomad
description: >-
  Query gnomAD for population allele frequencies, per-population AF, FAF95/grpmax, gene
  constraint (pLI, LOEUF), region variants, gene LoF/missense/rare/common filters, batch
  rsIDs, and coordinate lookup. Supports --dataset (gnomad_r4/r3/r2_1). Use for gnomAD,
  allele frequency, MAF, how common a. Not for ClinVar clinical significance (use
  clinvar), dbSNP coordinate-only lookup (use dbsnp), or gene ontology enrichment (use
  go).
compatibility: Python 3.10+, HTTPS (gnomAD GraphQL; rate-limited)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L4
  domain: genomics-variation
  capability_id: cngbdb.genomics.population-af.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# gnomAD 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 变异人群频率 | `rsid` / `variant` / `coord` | ACMG PM2/BA1 证据、罕见/常见判断 |
| 基因 LoF 约束 | `gene` | pLI、LOEUF，评估基因对功能缺失的耐受性 |
| 区域批量频率 | `region` | 靶向测序区间、局部变异频率 |
| 基因罕见/常见变异 | `rare` / `common` | 按 AF 筛选基因内变异 |
| LoF / missense 筛选 | `lof` / `missense` | 功能类别分析 |
| 批量注释 | `batch` | 多个 rsID 频率（限 5 个/次） |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| rsID（rs80357906） | `rsid` |
| variant ID（17-43057062-T-TG） | `variant` |
| 坐标 + 等位基因（17 43057062 T TG） | `coord` |
| 基因名 + 约束/pLI/LOEUF | `gene` |
| 坐标区域 | `region` |
| 基因 + 罕见/常见/LoF/missense | `rare` / `common` / `lof` / `missense` |
| 多个 rsID | `batch` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 默认数据集：`gnomad_r4`（GRCh38）；可用 `--dataset gnomad_r4|gnomad_r3|gnomad_r2_1`
3. 链式调用优先 `--format json`（schema: `cngbdb.skill-result.v2`）
4. 保守稀有度陈述优先看 **FAF95 / grpmax**（`popmax`、`popmax_population`），不要只看 raw AF
5. AF 解读（脚本自动输出）：
   - absent / AF≈0 → 支持 PM2（人群罕见）
   - AF ≥ 5% → 支持 BA1（良性），致病可能性低
   - AF ≥ 1% → 较常见，致病可能性较低
6. 基因约束：pLI > 0.9 或 LOEUF < 0.35 → 基因对 LoF 不耐受
7. API 限流 10 次/分钟，脚本内置 ~6.5s 间隔；**不要**连续批量调用
8. `batch` 最多 5 个 rsID；基因变异筛选（rare/lof 等）单次 API 调用

## 运行脚本

```bash
# 按 rsID 查人群频率
python ./scripts/query.py rsid <rsID>

# 按 variant ID 查（CHROM-POS-REF-ALT）
python ./scripts/query.py variant <variant_id>

# 按坐标+等位基因查
python ./scripts/query.py coord <chr> <pos> <ref> <alt>

# 按基因查约束分数
python ./scripts/query.py gene <基因名>

# 按区域查变异频率
python ./scripts/query.py region <区域>

# 基因变异筛选
python ./scripts/query.py rare <基因名>
python ./scripts/query.py common <基因名>
python ./scripts/query.py lof <基因名>
python ./scripts/query.py missense <基因名>

# 批量 rsID（最多 5 个）
python ./scripts/query.py batch <rsID1> <rsID2> ...

# 通用选项
python ./scripts/query.py <子命令> ... --format json
python ./scripts/query.py <子命令> ... --dataset gnomad_r4
```

示例：

```bash
python ./scripts/query.py rsid rs80357906 --format json
python ./scripts/query.py variant 17-43057062-T-TG
python ./scripts/query.py coord 17 43057062 T TG
python ./scripts/query.py gene BRCA1
python ./scripts/query.py region chr17:43057060-43057065
python ./scripts/query.py rare BRCA1 --dataset gnomad_r4
python ./scripts/query.py lof TP53
python ./scripts/query.py batch rs80357906 rs11591147
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 rsID / variant / coord

```markdown
## {rsID/variant} gnomAD 频率

| 项目 | 内容 |
|------|------|
| variant_id | ... |
| 坐标 | chr:pos ref>alt |
| Exome AF | ... |
| Genome AF | ... |
| FAF95 / grpmax | ... |
| 主要人群 AF | afr/nfe/eas/... |
| 解读 | 极罕见 / 低频 / 常见 / absent |
```

### 按基因（约束）

```markdown
## {基因} gnomAD 约束

| 指标 | 值 | 解读 |
|------|-----|------|
| pLI | ... | LoF 不耐受 |
| LOEUF | ... | 约束强度 |
| oe_lof / oe_mis | ... | 观察/期望比 |
| lof_z / mis_z | ... | Z 分数 |
```

### 按 region / rare / lof

```markdown
## {区域/基因} gnomAD 变异

| rsID | variant_id | 坐标 | 后果 | AF |
|------|------------|------|------|-----|
| ...  | ...        | ...  | ...  | ... |
```

## 示例

**用户**：rs80357906 在 gnomAD 里频率多少？

**Agent**：
1. 运行 `rsid rs80357906`
2. 报告 exome/genome AF、FAF95/grpmax 及主要人群频率
3. 结合 ClinVar 给出「罕见致病变异」或「常见良性」等结论

**用户**：BRCA1 有哪些罕见 LoF 变异？

**Agent**：
1. 运行 `lof BRCA1` 或 `rare BRCA1`
2. 按 AF 排序展示

**用户**：chr17:43057060-43057065 区域有哪些变异？

**Agent**：
1. 运行 `region chr17:43057060-43057065`

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 临床致病性终判 | `clinvar` |
| 仅 rsID→坐标 | `dbsnp` |
| GO 富集 | `go` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | gnomAD GraphQL |
| 数据集 | 默认 gnomad_r4（GRCh38） |
| 标识符 | rsID / variant_id / chrom-pos-ref-alt |

## Citation

gnomAD · https://gnomad.broadinstitute.org/ · 注明 dataset 与查询时间

## 联动

| 问题类型 | 联动 skill |
|----------|-----------|
| SNP 定位 + 频率 + 致病性 | `dbsnp` → `gnomad` → `clinvar` |
| 仅定位 | `dbsnp` |
| 仅致病性 | `clinvar` |

## 详细解读路径

见 [reference.md](reference.md)
