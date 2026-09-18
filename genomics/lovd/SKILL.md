---
name: lovd
description: >-
  Query LOVD via api.lovd.nl v2 (checkGene, checkHGVS) and UCSC Beacon (dataset=lovd).
  Supports gene symbol validation, HGVS nomenclature check, coordinate presence in public
  LOVDs, and genomic region parsing. Use for LOVD. Not for primary ClinVar clinical
  assertions (use clinvar), gnomAD AF (use gnomad), or dbSNP catalog (use dbsnp).
compatibility: Python 3.10+, HTTPS (LOVD / Beacon)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: genomics-variation
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# LOVD 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因符号验证 | `gene` | HGNC 官方符号、拼写纠正 |
| HGVS 语法验证 | `hgvs` / `check` | c./g./p. 命名合法性 |
| 位点公共 LOVD 收录 | `coord` | UCSC Beacon dataset=lovd |
| 基因组区域格式 | `region` | 解析 chr:g. 或 chr:pos 后查 Beacon |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（DMD、BRCA1）+ LOVD/符号验证 | `gene` |
| HGVS（c.1234A>G、chr17:g.43057060G>A） | `hgvs` 或 `check` |
| 坐标 chr17 43057060 或 chr17:43057060 | `coord` |
| 区域 chr17:g.43057060G>A | `region` |
| 可选 alt 等位基因 | `coord` 第三参数 |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. **基因/HGVS 验证**：`https://api.lovd.nl/v2/checkGene/{symbol}`、`checkHGVS/{hgvs}`
3. **位点收录**：UCSC Beacon `dataset=lovd`（0-based，脚本接受 1-based 输入）
4. HGVS 验证为**语法与类型**检查，**非**序列级验证；序列验证见 [VariantValidator](https://variantvalidator.org)
5. Beacon 命中仅表示公共 LOVD 聚合中有记录，**不含**具体疾病库与提交者详情；详情见 [lovd.nl 搜索](https://lovd.nl/3.0/search)
6. 输出关键字段：valid、HGNC ID、HGVS 类型、警告、Beacon 命中、建议修正

## 运行脚本

```bash
python ./scripts/query.py gene <基因名>
python ./scripts/query.py hgvs <HGVS>
python ./scripts/query.py check <HGVS>
python ./scripts/query.py coord <染色体> <位置> [alt]
python ./scripts/query.py region <区域>
```

示例：

```bash
python ./scripts/query.py gene DMD
python ./scripts/query.py hgvs c.1234A>G
python ./scripts/query.py check chr17:g.43057060G>A
python ./scripts/query.py coord 17 43057060 G
python ./scripts/query.py region chr17:g.43057060G>A
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 gene

```markdown
## LOVD 基因验证：{symbol}

- **有效**：是 / 否
- **HGNC ID**：
- **官方符号**：（若有 corrected_values）
- **后续**：全球 LOVD 变异搜索见 lovd.nl/3.0/search
```

### 按 hgvs / check

```markdown
## LOVD HGVS 验证：{hgvs}

- **语法有效**：是 / 否
- **识别类型**：
- **位置 / 变异类型**：（若有）
- **警告**：（逐条列出）
- **建议修正**：（若有）
- **说明**：序列级验证请用 VariantValidator
```

### 按 coord / region

```markdown
## LOVD Beacon：chr{chrom}:{pos}

- **公共 LOVD 有记录**：是 / 否
- **详情搜索**：[lovd.nl/3.0/search](https://lovd.nl/3.0/search)
- **未命中说明**：可能未收录或 alt 不匹配
```

## 示例

**用户**：DMD 这个基因符号对吗？

**Agent**：
1. 运行 `gene DMD`
2. 输出 valid 与 HGNC ID
3. 若有拼写建议，列出 corrected_values

**用户**：c.5266dupC 写法对不对？

**Agent**：
1. 运行 `hgvs c.5266dupC` 或带基因上下文的完整 HGVS
2. 列出 warnings
3. 联动 `clinvar hgvs` 查临床意义

**用户**：chr17:43057060 在 LOVD 里有吗？

**Agent**：
1. 运行 `region chr17:43057060` 或 `coord 17 43057060`
2. 解读 Beacon 结果
3. 若命中，提示用户在 lovd.nl 搜索详情

## Do Not Use When

| 需求 | 交给 |
|------|------|
| ClinVar 主解读 | `clinvar` |
| 人群 AF | `gnomad` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | LOVD / UCSC Beacon dataset=lovd |

## Citation

LOVD · https://www.lovd.nl/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 临床致病性 | `clinvar` |
| HGMD 公共位点 | `hgmd coord` |
| 坐标与 rsID | `dbsnp`、`ensembl` |
| 转录本与 HGVS 注释 | `ensembl`、`gencode` |

## 详细解读路径

见 [reference.md](reference.md)
