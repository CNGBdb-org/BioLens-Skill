# dbSNP 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 变异注释（WES/WGS/VCF） | `coord` / `rsid` | 坐标→rsID，或 rsID→功能/频率 |
| 基因变异目录 | `gene` + `stats` | Panel 设计、突变谱概览 |
| 功能筛选 | `function` | 找 missense / frameshift 等 |
| 频率过滤 | `rare` / `common` | 辅助 ACMG PS4/BS1 证据 |
| 临床相关位点 | `clinical` | 有 ClinVar 致病标签的 SNP |
| 批量注释 | `batch` | 多个 rsID 快速查表 |
| 区域注释 | `region` | 靶向测序区间 |

## 输入 → 输出

### 按 rsID（rsid）

```
rsID → esearch: {rsID}[RS] → esummary
  → 坐标(GRCh38/37)、等位基因(SPDI)、功能类型、多来源 MAF、CLIN 标签
```

### 坐标反查（coord）

```
chr + pos → esearch: {chr}[CHR] AND {pos}[POSITION]
  → 该位置所有 RefSNP（同一坐标可有多个等位基因）
```

### 按基因（gene）

```
基因 → esearch: {gene}[GENE] → esummary
```

### 按区域（region）

```
chr17:43057060-43057065 → 17[CHR] AND 43057060:43057065[POSITION]
  支持 --assembly GRCh37 使用 POSITION_GRCH37
```

### 功能类型（function）

```
TP53 + missense → TP53[GENE] AND "missense_variant"[Function Class]
  常见值：missense, frameshift, synonymous, stop_gained, splice
```

### 罕见/常见（rare / common）

```
rare:  MAF 0.0–0.00999（GLOBAL_MAF 范围查询）
common: MAF 0.01–1.0
```

### 临床相关（clinical）

```
{gene}[GENE] AND ("pathogenic"[CLIN] OR "likely pathogenic"[CLIN])
  dbSNP CLIN 标签来自 ClinVar 汇总，详情需查 ClinVar skill
```

### 批量（batch）

```
80357906,328 → 逗号分隔 rs 编号 → 表格输出
```

### 统计（stats）

```
按 SNPCLASS 统计 SNV/INS/DEL/DELINS/MNV 数量
附加：致病相关、罕见、常见计数
```

## 核心字段

| 字段 | 说明 |
|------|------|
| chrpos | GRCh38 坐标 |
| chrpos_prev_assm | GRCh37 坐标 |
| spdi | 标准化等位基因描述 REF>ALT |
| snp_class | snv / ins / del / delins / mnv |
| fxn_class | 分子功能后果（SO terms） |
| global_mafs | 各研究频率（ExAC, gnomAD, ALFA, TOPMED 等） |
| clinical_significance | ClinVar 汇总 CLIN 标签 |
| validated | by-frequency / by-alfa / by-cluster |

## dbSNP vs gnomAD vs ClinVar

| 库 | 回答什么 |
|----|----------|
| dbSNP | 在哪、是什么类型、有哪些研究频率、是否有 CLIN 标签 |
| gnomAD | 精确人群 AF、各族群频率、基因约束 |
| ClinVar | 是否致病、评审状态、关联疾病 |

标准联动：坐标/rsID → dbSNP 定位 → gnomAD 查频率 → ClinVar 查致病性

## 注意点

- 同一坐标可有多个 RefSNP（多等位基因），coord 会返回全部
- dbSNP MAF 为各研究汇总，精确 AF 用 gnomAD
- CLIN 标签仅为摘要，临床解读需查 ClinVar
- GLOBAL_MAF 范围查询需零填充格式（脚本已内置）

## API 参考

- [dbSNP Entrez 检索帮助](https://www.ncbi.nlm.nih.gov/snp/docs/entrez_help/)
- [E-utilities 使用指南](https://www.ncbi.nlm.nih.gov/snp/docs/eutils_help/)
