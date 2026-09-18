# ClinVar 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 变异注释（WES/WGS） | `rsid` → 必要时 `dbsnp` | ACMG 致病性判断 |
| 基因突变谱 / Panel 设计 | `gene` + `stats` | 了解热点与 VUS 负担 |
| 遗传病候选基因 | `disease` | 表型驱动变异检索 |
| VUS 功能研究 | `vus` | 筛选待验证变异 |
| 报告质量审核 | `conflict` | 发现实验室间分歧 |
| 文献 HGVS 验证 | `hgvs` | 核对 c./p. 命名 |
| 靶向区域注释 | `region` | 局部变异批量查询 |
| 已知 ClinVar 条目 | `vcv` | 按 ID 精确调取 |

## 输入 → 输出

### 按基因（gene）

```
基因符号（BRCA1）
  → esearch: {gene}[gene] AND Pathogenic/Likely pathogenic
  → esummary → 坐标、rsID、疾病、评审状态
  → 表格输出
```

### 按 rsID（rsid）

```
rsID（rs80357906）
  → esearch: {rsID}[rs]
  → esummary → 聚合临床意义 + 提交数
  → 中文解读结论
```

### 按疾病（disease）

```
疾病关键词（noonan, breast, autism）
  → esearch: {keyword}[dis] AND Pathogenic/Likely pathogenic
  → esummary → 基因、变异、疾病
```

疾病检索为模糊匹配，建议使用英文关键词或疾病核心词（如 noonan 而非 Noonan syndrome）。

### 按 HGVS（hgvs）

```
HGVS 片段（c.5266dup, p.V600E）
  → esearch: "{hgvs}"[varnam] [AND {gene}[gene]]
  → esummary → 结果按 title/cdna 精确过滤
  → 若无法精确匹配则提示并展示模糊结果
```

### 按区域（region）

```
chr17:43057060-43057065  或  17 43057060 43057065
  → 解析为 {chr}[chr] AND {start}:{end}[chrpos38]
  → esummary → 区域内所有 ClinVar 变异
```

默认 GRCh38 坐标。

### VUS 清单（vus）

```
基因 + VUS
  → esearch: {gene}[gene] AND "Uncertain significance"[Clinical Significance]
  → 展示意义未明变异（聚合分类可能与检索条件不同，需看临床意义字段）
```

### 解读冲突（conflict）

```
基因 + 冲突
  → esearch: {gene}[gene] AND "conflicting interpretations"[Clinical Significance]
  → 标注 Conflicting classifications，建议结合 ACMG 重评
```

ClinVar 不仲裁冲突，仅展示各实验室提交的分歧。

### 变异谱统计（stats）

```
基因 + 统计
  → 分别 esearch 各 Clinical Significance 分类并计数
  → 输出分类表 + 摘要
```

注意：ClinVar 按变异-疾病对计数，同一变异可跨分类出现，占比之和可能超过 100%。

### 按 VCV / Variation ID（vcv）

```
17677 或 VCV000017677
  → esearch 直接查 ID 或 {VCV}[clv_acc]
  → 精确调取单条变异记录
```

## 核心字段

| 字段 | 说明 |
|------|------|
| Clinical significance | Pathogenic / Likely pathogenic / VUS / Benign / Conflicting |
| Review status | expert panel > practice guideline > multiple submitters > single submitter |
| Title | HGVS 变异描述 |
| variation_loc | GRCh38/GRCh37 坐标 |
| trait_set | 关联疾病 + OMIM/MedGen 交叉引用 |
| supporting_submissions | SCV（提交者）/ RCV（变异-疾病对）数量 |
| last_evaluated | 最后评估日期 |

## 致病性判断

| 临床意义 | 解读 |
|----------|------|
| Pathogenic | 致病，高置信 |
| Likely pathogenic | 可能致病 |
| Uncertain significance (VUS) | 意义未明，需进一步验证 |
| Conflicting | 实验室间解读不一致，不可直接下结论 |
| Benign / Likely benign | 良性，可用于过滤 |

## 评审状态优先级

1. reviewed by expert panel
2. practice guideline
3. criteria provided, multiple submitters, no conflicts
4. criteria provided, single submitter

## 注意点

- VUS 不可当致病结论
- Conflicting 需列出分歧，建议查原文/重新 ACMG 评级
- 提交记录不一致时列出冲突，以 review status 较高者为主
- stats 分类计数有交叉，不代表互斥变异数
- 与 dbSNP 联动：dbSNP 负责定位与 MAF，ClinVar 负责临床意义

## API 参考

- [ClinVar 程序化访问](https://www.ncbi.nlm.nih.gov/clinvar/docs/programmatic_access/)
- [ClinVar 检索帮助](https://www.ncbi.nlm.nih.gov/clinvar/docs/help/)
- [临床意义与冲突说明](https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/)
