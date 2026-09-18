---
name: pharmgkb
description: >-
  Query PharmGKB / ClinPGx REST API for pharmacogenomics. Supports gene info, variant by
  rsID, CPIC guideline annotations, clinical annotations, drug/chemical search, and
  pharmacokinetic pathways. Use for PGx, CPIC guidelines, drug-gene. Not for Mendelian
  ClinVar pathogenicity (use clinvar), Open Targets genetics scores (use opentargets), or
  general drug chemistry. Not for local VCF star-allele calling (use pop-pharmacogenomics).
compatibility: Python 3.10+, HTTPS (PharmGKB / ClinPGx)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: pharmacogenomics
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# PharmGKB 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因 PGx 概况 | `gene` | CPIC/PharmVar 基因、坐标 |
| 变异 PGx 注释 | `variant` | rsID 临床意义与变异分类 |
| 用药指南 | `guideline` | CPIC 等 guideline annotation |
| 临床注释 | `clinical` | 基因相关 allele-表型证据 |
| 药物检索 | `drug` | 化学物/药物 PharmGKB ID |
| 代谢/作用通路 | `pathway` | 药代动力学/药效学通路 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（CYP2D6、SLCO1B1）+ 药物基因/ PGx | `gene` |
| rsID（rs4244285） | `variant` |
| 基因 + 指南/CPIC/用药建议 | `guideline` |
| 基因 + 临床注释/证据等级 | `clinical` |
| 药物名（warfarin、clopidogrel） | `drug` |
| 通路关键词（CYP450、thiopurine） | `pathway` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. API 基址：`https://api.clinpgx.org/v1/data`（ClinPGx / 原 PharmGKB REST）
3. 坐标默认 **GRCh38**（`chrStartPosB38` / `chrStopPosB38`）
4. 临床注释须标注 **证据等级**（Level of Evidence），**不可**将低等级证据表述为强推荐
5. 指南注释区分是否含 **dosingInformation**、**hasTestingInfo**
6. CPIC 基因（`cpicGene`）与 PharmVar 基因（`pharmVarGene`）分别标注
7. 输出关键字段：PharmGKB ID、rsID、证据等级、指南名、药物 ID

## 运行脚本

```bash
python ./scripts/query.py gene <基因名>
python ./scripts/query.py variant <rsID>
python ./scripts/query.py guideline <基因名>
python ./scripts/query.py clinical <基因名>
python ./scripts/query.py drug <药物名>
python ./scripts/query.py pathway <关键词>
```

示例：

```bash
python ./scripts/query.py gene CYP2D6
python ./scripts/query.py variant rs4244285
python ./scripts/query.py guideline CYP2C19
python ./scripts/query.py clinical SLCO1B1
python ./scripts/query.py drug warfarin
python ./scripts/query.py pathway CYP450
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 gene

```markdown
## {基因} PharmGKB 基因

- **PharmGKB ID**：
- **名称 / 坐标（GRCh38）**：
- **CPIC 基因**：是 / 否
- **PharmVar 基因**：是 / 否
```

### 按 variant

```markdown
## {rsID} PharmGKB 变异

- **PharmGKB ID**：
- **临床意义**：
- **变异类型（changeClassification）**：
- **解读**：（与用药/代谢的相关性，注明需结合基因型）
```

### 按 guideline / clinical

```markdown
## {基因} PharmGKB {指南|临床注释}

| ID / 名称 | 证据等级 / 用药信息 | 检测建议 |
|-----------|---------------------|----------|
| ...       | ...                 | ...      |

共 X 条，展示前 N 条。
```

### 按 drug / pathway

```markdown
## PharmGKB {药物|通路}：{关键词}

| 名称 | PharmGKB ID |
|------|-------------|
| ...  | ...         |
```

## 示例

**用户**：CYP2C19 有没有 CPIC 用药指南？

**Agent**：
1. 运行 `gene CYP2C19` 确认 CPIC 基因
2. 运行 `guideline CYP2C19` 列出指南
3. 标注是否含剂量调整与检测建议

**用户**：rs4244285 和 clopidogrel 有关系吗？

**Agent**：
1. 运行 `variant rs4244285`
2. 运行 `clinical CYP2C19`（若变异属 CYP2C19）
3. 联动 `dbsnp`/`gnomad` 查人群频率

**用户**：warfarin 在 PharmGKB 里对应什么 ID？

**Agent**：
1. 运行 `drug warfarin`
2. 返回化学物 ID，可再查相关基因指南

## Do Not Use When

| 需求 | 交给 |
|------|------|
| ClinVar 致病性 | `clinvar` |
| 靶点-疾病 OT 评分 | `opentargets` |
| 本地 VCF star allele / 代谢表型 | `pop-pharmacogenomics` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | PharmGKB / ClinPGx |

## Citation

PharmGKB · https://www.pharmgkb.org/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| rsID 坐标与功能 | `dbsnp` |
| 人群等位基因频率 | `gnomad` |
| 基因坐标与转录本 | `ensembl`、`gencode` |
| 疾病/靶点背景 | `opentargets` |

## 详细解读路径

见 [reference.md](reference.md)
