---
name: opentargets
description: >-
  Query Open Targets Platform for target-disease associations, drug-target links, disease
  and variant search, and integrated genetics evidence scores. Supports gene/target info,
  disease lookup, variant colocalisation, drug search, and target-disease association
  scores. Use for drug target, therapeutic hypothesis,. Not for raw GWAS Catalog rows only
  (use gwascatalog), ClinVar clinical assertions (use clinvar), or PharmGKB CPIC
  guidelines (use pharmgkb).
compatibility: Python 3.10+, HTTPS (Open Targets GraphQL)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: target-disease
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Open Targets 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 靶点概览 | `gene` | 基因信息、已知药物、成药性 |
| 疾病检索 | `disease` | EFO 疾病 ID 与描述 |
| 变异 | `variant` | rsID 坐标与 GWAS colocalisation |
| 药物 | `drug` | 药物名称搜索 |
| 靶点-疾病 | `target` | 基因与疾病的关联分数 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（BRCA1、EGFR） | `gene` |
| 疾病名（breast cancer、diabetes） | `disease` |
| rsID（rs7903146） | `variant` |
| 药物名（imatinib、trastuzumab） | `drug` |
| 基因 + 疾病关联 | `target`（两参数） |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 基因解析为 Ensembl ID 后查询 Open Targets GraphQL API
3. `target` 需两个参数：基因符号 + 疾病关键词
4. 关联分数（score）及 datatypeScores 为 **整合证据**，非单一 GWAS p 值
5. 已知药物展示最高临床阶段（maximumClinicalTrialPhase）
6. 输出关键字段：Ensembl ID、EFO ID、关联分数、药物名、临床阶段

## 运行脚本

```bash
python ./scripts/query.py gene <基因名>
python ./scripts/query.py disease <疾病关键词>
python ./scripts/query.py variant <rsID>
python ./scripts/query.py drug <药物名>
python ./scripts/query.py target <基因名> <疾病关键词>
```

示例：

```bash
python ./scripts/query.py gene EGFR
python ./scripts/query.py disease breast cancer
python ./scripts/query.py variant rs7903146
python ./scripts/query.py drug imatinib
python ./scripts/query.py target BRCA1 breast cancer
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 gene

```markdown
## {基因} Open Targets 靶点

- **Ensembl ID**：
- **名称 / 类型**：
- **已知药物**：（名称、临床阶段、适应症）
```

### 按 target

```markdown
## {基因} ↔ {疾病} 关联

- **EFO ID / 疾病名**：
- **综合分数**：
- **分项证据**：（genetic_association、known_drug 等）
- **解读**：（是否强关联靶点）
```

### 按 disease / drug / variant

```markdown
## {标题} Open Targets

| ID | 名称 | 备注 |
|----|------|------|
| ... | ...  | ...  |
```

## 示例

**用户**：EGFR 有哪些已知药物？

**Agent**：
1. 运行 `gene EGFR`
2. 列出 knownDrugs 及临床阶段

**用户**：BRCA1 和乳腺癌有关联吗，分数多少？

**Agent**：
1. 运行 `target BRCA1 breast cancer`
2. 解读 score 与各 datatypeScores

## Do Not Use When

| 需求 | 交给 |
|------|------|
| GWAS Catalog 原始关联表 | `gwascatalog` |
| ClinVar 致病性 | `clinvar` |
| CPIC 用药指南 | `pharmgkb` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | Open Targets Platform |

## Citation

Open Targets · https://platform.opentargets.org/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| GWAS 原始关联 | `gwascatalog` |
| 基因注释 | `ensembl` |
| 蛋白功能 | `uniprot` |
| 临床变异 | `clinvar` |
| 人群 AF | `gnomad` |

## 详细解读路径

见 [reference.md](reference.md)
