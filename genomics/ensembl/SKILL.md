---
name: ensembl
description: >-
  Query Ensembl REST API for human genes, variants, genomic regions, orthologues, and VEP
  consequence prediction. Supports gene lookup, rsID/COSMIC variant, region overlap,
  cross-species homology, and HGVS-based VEP annotation. Use for Ensembl ID, transcript,
  coordinates, variant consequence, SIFT/PolyPhen. Not for ClinVar pathogenicity (use
  clinvar), gnomAD AF (use gnomad), UniProt protein function detail (use uniprot), or
  HESTA spatial maps (use hesta).
compatibility: Python 3.10+, HTTPS (Ensembl REST)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2-L4
  domain: genomics-annotation
  capability_id: cngbdb.genomics.ensembl-annotation.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# Ensembl 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 基因注释 | `gene` | Ensembl ID、坐标、转录本列表 |
| 变异信息 | `variant` | rsID/COSMIC 坐标、等位基因、频率 |
| 区域基因 | `region` | 区间内重叠基因 |
| 进化保守 | `homology` | 跨物种直系同源基因 |
| 变异后果 | `vep` | HGVS → 功能后果、SIFT/PolyPhen |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 基因名（BRCA1、TP53） | `gene` |
| rsID（rs80357906）或 COSMIC ID | `variant` |
| 坐标区域（chr17:43044295-43170245） | `region` |
| 基因 + 同源/orthologue | `homology` |
| HGVS（c.5266dup、p.V600E） | `vep` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 默认物种：`homo_sapiens`，组装版本 **GRCh38**
3. 链式调用优先 `--format json`（schema: `cngbdb.skill-result.v2`）
4. VEP 结果按 `impact`（HIGH/MODERATE/LOW）解读，注明 SIFT/PolyPhen 预测
5. 区域格式：`chr17:43044295-43170245` 或 `17 43044295 43170245`
6. 输出关键字段：Ensembl ID、坐标、转录本、后果术语、同源物种与 identity

## 运行脚本

```bash
python ./scripts/query.py gene <基因名>
python ./scripts/query.py variant <rsID或COSMIC>
python ./scripts/query.py region <区域>
python ./scripts/query.py homology <基因名>
python ./scripts/query.py vep <HGVS>
python ./scripts/query.py <子命令> ... --format json
```

示例：

```bash
python ./scripts/query.py gene BRCA1
python ./scripts/query.py variant rs80357906 --format json
python ./scripts/query.py region chr17:43044295-43170245
python ./scripts/query.py homology TP53
python ./scripts/query.py vep ENST00000357654:c.5266dup
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按基因 / 区域 / 同源

```markdown
## {标题} Ensembl 注释

| ID | 名称 | 类型 | 坐标 | 链 |
|----|------|------|------|-----|
| ... | ... | ... | ... | ... |

共检索到 X 条，展示前 N 条。
```

### 按 variant / VEP

```markdown
## 变异 {标识} Ensembl 注释

- **名称 / rsID**：
- **坐标**：
- **等位基因**：
- **VEP 后果**：（consequence_terms、impact）
- **转录本 / HGVS**：
- **SIFT / PolyPhen**：
- **解读结论**：（一句话）
```

## 示例

**用户**：BRCA1 的 Ensembl ID 和主要转录本是什么？

**Agent**：
1. 运行 `gene BRCA1`
2. 列出 Ensembl ID、坐标与前几个转录本

**用户**：p.V600E 有什么功能后果？

**Agent**：
1. 运行 `vep` 配合正确 HGVS（必要时先用 `gene` 确认转录本）
2. 解读 HIGH/MODERATE 后果及 SIFT/PolyPhen

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 临床致病性 | `clinvar` |
| 人群 AF | `gnomad` |
| 蛋白功能长摘要 | `uniprot` |
| 空间表达 | `hesta` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | Ensembl REST |
| 物种 | 默认 homo_sapiens |
| 组装 | GRCh38 |

## Citation

Ensembl · https://rest.ensembl.org/ · 注明 Ensembl release（若脚本输出含版本）

## 联动

| 需求 | 联动 skill |
|------|-----------|
| RefSeq 转录本 / Gene ID | `refseq` |
| 蛋白功能与疾病 | `uniprot` |
| 人群 AF | `gnomad` |
| 临床致病性 | `clinvar` |
| GWAS 关联 | `gwascatalog` |
| 靶点-疾病证据 | `opentargets` |

## 详细解读路径

见 [reference.md](reference.md)
