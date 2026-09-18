---
name: variant-interpretation
description: >-
  Orchestrate cross-database variant triage: dbsnp (resolve rsID/location) →
  gnomad (population AF) → clinvar (clinical significance). Use when the user
  asks for comprehensive variant interpretation, ACMG-style evidence triage,
  or “这个变异怎么看/综合解读”. Not for single-database lookup only (use dbsnp /
  gnomad / clinvar), gene constraint alone (use gnomad gene), spatial expression
  (use hesta), or replacing expert ACMG clinical diagnosis.
compatibility: Python 3.10+, HTTPS; requires sibling skills dbsnp, gnomad, clinvar
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L4
  domain: genomics-variation
  capability_id: cngbdb.genomics.variant-interpretation.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
  orchestrates: [dbsnp, gnomad, clinvar]
---

# 变异综合解读（编排）

跨库固定链路，**不复制**各库查询逻辑：

```text
dbsnp（定位 / 解析 rsID）→ gnomad（人群频率）→ clinvar（临床意义）
```

## Use When

- 用户要**综合解读**某个变异（同时关心坐标、频率、致病性）
- 问法类似：「这个变异怎么看」「帮我解读 rs…」「ACMG 相关证据梳理」
- 输入为 **rsID**、**HGVS**，或 **染色体+坐标**（先经 dbSNP 解析 rsID）

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 只要 rsID / 坐标解析 | `dbsnp` |
| 只要人群 AF / pLI | `gnomad` |
| 只要 ClinVar 致病性 | `clinvar` |
| 空间表达 / HESTA | `hesta` |
| 正式临床报告 / 替代专家 ACMG 终判 | 人工流程；本 skill 仅科研辅助 |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 优先标识 | **rsID**（`rs80357906`） |
| HGVS | 先 `dbsnp hgvs` 解析 rsID，再继续 |
| 坐标 | `--chrom` + `--pos`（默认 GRCh38） |
| gnomAD 数据集 | 默认 `gnomad_r4` |
| 输出 | 可部分成功；某步失败仍报告已有步骤 |

## Required inputs

| 输入方式 | 必填 |
|----------|------|
| rsID | `--rsid` |
| HGVS | `--hgvs`（由 dbSNP 解析 rsID） |
| 坐标 | `--chrom` + `--pos`（可选 `--assembly`） |

## Necessary questions

缺参时**必须补问**，禁止静默猜测等位基因或组装版本：

1. 无 rsID / HGVS / 坐标 → 问用户提供哪一种  
2. 仅有坐标且未说明组装 → 默认 GRCh38，并注明；用户说 hg19/GRCh37 时改 `--assembly`  
3. 用户只要「致病吗」且明确只要 ClinVar → 转 `clinvar`，不必强行跑全链路  

## Workflow

1. **Gather**：确认输入类型与组装 / 数据集  
2. **Act**：只运行本目录 `./scripts/query.py`（内部 subprocess 调各库 `query.py --format json`）  
3. **Verify**：核对 rsID；分别注明 dbSNP / gnomAD / ClinVar 是否命中；附免责声明  

## Commands

```bash
# 工作目录：本 skill 根目录；需与 dbsnp/gnomad/clinvar 同级（skills/）
python ./scripts/query.py --rsid rs80357906
python ./scripts/query.py --rsid rs80357906 --format json
python ./scripts/query.py --hgvs 'NC_000017.11:g.43057063dup'
python ./scripts/query.py --chrom 17 --pos 43057063 --assembly GRCh38
python ./scripts/query.py --rsid rs80357906 --dataset gnomad_r4 --skip-gnomad  # 调试用
```

依赖：`pip install -r ../../requirements.txt`；可选 `NCBI_API_KEY`。

## Output contract

- **文本**：rsID、位置摘要、人群频率解读、临床意义、分步状态、免责声明  
- **JSON**：`cngbdb.skill-result.v2`；`record.steps` 含各库原始 envelope；`record.summary` 为编排摘要  
- **禁止**：无脚本结果时编造 AF 或致病性；不得声称已完成正式 ACMG 分类  

## Guardrails

1. **必须**调用本包脚本；**不得**手写 E-utilities / gnomAD GraphQL 冒充编排  
2. 不得跳过 dbSNP 解析、直接用未确认的 rsID 调后两步（除非用户已给 rsID）  
3. VUS / Conflicting 必须原样标注，不可说成「致病」  
4. 任一步失败：报告失败原因并继续或停止（无 rsID 则停止后两步）  

## Errors and fallback

| 情况 | 处理 |
|------|------|
| dbSNP 解析不到 rsID | 停止；建议核对 HGVS/坐标/组装 |
| gnomAD 未命中 | 继续 ClinVar；摘要注明 absent |
| ClinVar 未命中 | 仍给出定位+AF；注明无临床记录 |
| 网络 / 限流 | 提示重试或设置 `NCBI_API_KEY` |
| 用户只要单库 | 改道对应单库 skill |

## Examples

**用户**：rs80357906 综合解读一下  

**Agent**：
1. 运行 `python ./scripts/query.py --rsid rs80357906 --format json`  
2. 用中文整理 summary + 各步要点，并声明非临床诊断  

**用户**：这个 HGVS 变异怎么看？`NC_000017.11:g.43057063dup`  

**Agent**：`--hgvs ...`；若解析出多个 rsID，说明取第一个继续，并提示可再查其余  

## Citation

- dbSNP / ClinVar：NCBI  
- gnomAD：Broad Institute  
- 输出注明查询时间与各库来源  

## 目录结构

```text
variant-interpretation/
├── SKILL.md
├── README.md
├── scripts/query.py    # 编排入口
└── evals/
```
