---
name: dgv
description: >-
  Query DGV/DGVa copy-number and structural variants via Ensembl REST API. Supports region
  overlap, gene locus CNV catalog, and nsv ID lookup. Use for DGV CNV, structural
  variation overlap, gene deletion/duplication context. Not for small-variant
  ClinVar/dbSNP (use clinvar/dbsnp), or gnomAD SNV AF (use gnomad).
compatibility: Python 3.10+, HTTPS (Ensembl REST / DGVa)
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L2
  domain: structural-variation
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# DGV 查询

## 研究者常见用途

| 场景 | 子命令 | 说明 |
|------|--------|------|
| 区域 CNV 重叠 | `region` | 靶向区、断点、CNV 边界注释 |
| 基因座 CNV | `gene` | 基因全长及侧翼结构变异 |
| DGV 变异 ID | `id` | nsv 编号精确查坐标与类型 |

## 输入识别

| 用户输入 | 子命令 |
|----------|--------|
| 区域（chr16:29500000-29600000） | `region` |
| 基因名（TBX1、APP）+ CNV/缺失/重复 | `gene` |
| nsv ID（nsv516481、516481） | `id` |

## 执行规则

1. **必须**直接运行内置脚本，**不得**重写或临时编写查询代码
2. 通过 **Ensembl REST API** 查询 `structural_variation`，优先 **DGVa** 源，回退 **DGV**
3. 坐标默认 **GRCh38**（Ensembl homo_sapiens）
4. DGV 已整合至 **DGVa/dbVar**；结果为代表性人群 CNV，**非**个体临床 CNV 报告
5. 临床意义字段若有，需注明来源为 DGV 研究注释，临床解读应联动 **ClinVar**
6. 输出关键字段：nsv ID、SV 类型、坐标、临床意义（若有）、研究来源

## 运行脚本

```bash
python ./scripts/query.py region <区域>
python ./scripts/query.py gene <基因名>
python ./scripts/query.py id <nsv编号>
```

区域格式：`chr16:29500000-29600000` 或 `16 29500000 29600000`

示例：

```bash
python ./scripts/query.py region chr16:29500000-29600000
python ./scripts/query.py gene TBX1
python ./scripts/query.py id nsv516481
```

依赖：`pip install -r ../../requirements.txt`（需要 `requests`）

## 输出模板

### 按 region / gene

```markdown
## {区域|基因} DGV/DGVa CNV

| ID | 类型 | 坐标 | 临床意义 |
|----|------|------|----------|
| ... | DEL/DUP/... | chr... | ... |

共 X 条，展示前 N 条。
**说明**：人群 CNV 目录；个体临床 CNV 请查 ClinVar/dbVar。
```

### 按 id

```markdown
## DGV 变异 {nsv_id}

- **名称**：
- **坐标**：（assembly）
- **类型**：
- **解读**：（与查询区域/基因的重叠关系）
```

## 示例

**用户**：chr16:29500000-29600000 有哪些已知 CNV？

**Agent**：
1. 运行 `region chr16:29500000-29600000`
2. 表格展示 DEL/DUP 与坐标
3. 说明 DGV 为人群研究汇总

**用户**：TBX1 基因区域常见缺失吗？

**Agent**：
1. 运行 `gene TBX1`
2. 列出基因座重叠 CNV
3. 联动 `clinvar region` 查临床致病 CNV

**用户**：nsv516481 是什么变异？

**Agent**：
1. 运行 `id nsv516481`
2. 输出坐标与类型
3. 若用户有区域，说明是否与查询区间重叠

## Do Not Use When

| 需求 | 交给 |
|------|------|
| SNV/indel 临床意义 | `clinvar` |
| rsID 小变异 | `dbsnp` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | DGV/DGVa via Ensembl |
| 组装 | GRCh38 |

## Citation

DGV · http://dgv.tcag.ca/

## 联动

| 需求 | 联动 skill |
|------|-----------|
| 临床 CNV 致病性 | `clinvar` |
| 基因坐标 | `ensembl`、`gencode` |
| 区域保守性 | `ucsc` |
| 重复序列背景 | `dfam` |

## 详细解读路径

见 [reference.md](reference.md)
