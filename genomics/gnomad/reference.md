# gnomAD 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| ACMG 变异解读 | `rsid` + `clinvar` | PM2（罕见）/ BA1（AF>5%）证据 |
| 基因约束评估 | `gene` | 判断 LoF 变异在该基因的致病先验 |
| VCF 坐标注释 | `coord` / `region` | 查等位基因频率 |
| 基因功能研究 | `lof` / `missense` / `rare` | 筛选候选变异 |
| 关联分析 MAF 过滤 | `common` / `rare` | GWAS 常见变异 vs 罕见变异 |

## 输入 → 输出

### 按 rsID（rsid）

```
rsID
  → gnomAD GraphQL variant(rsid, dataset=gnomad_r4)
  → 若未命中：NCBI variation API 解析坐标 → variant(variantId)
  → exome/genome AC/AN/AF、分人群频率、ACMG 解读提示
```

### 按 variant ID / coord（variant / coord）

```
17-43057062-T-TG  或  coord 17 43057062 T TG
  → variant(variantId)
  → 频率输出
```

### 按基因约束（gene）

```
基因符号
  → gene(gene_symbol) → gnomad_constraint
  → pLI / LOEUF / oe_lof / oe_mis / lof_z / mis_z / syn_z
```

### 按区域（region）

```
chr17:43057060-43057065
  → region(chrom, start, stop) → variants(dataset=gnomad_r4)
  → 表格输出区域内变异及 AF
```

### 基因变异筛选（rare / common / lof / missense）

```
基因
  → gene.variants(dataset=gnomad_r4)  [CDS ±75bp]
  → 客户端按 AF 或 consequence 过滤
  → 展示前 N 条
```

### 批量（batch）

```
rsID 列表（最多 5 个）
  → 逐个 rsid 查询（含限流间隔）
  → 表格输出 AF 与解读
```

## 核心字段

| 字段 | 说明 |
|------|------|
| ac / an | 等位基因计数 / 总等位基因数 |
| af | ac/an，人群等位基因频率 |
| ac_hom | 纯合子计数 |
| populations.id | afr, amr, eas, nfe, sas, asj, fin, mid, oth |
| pLI | LoF 不耐受概率，>0.9 高度不耐受 |
| LOEUF (oe_lof_upper) | LoF 约束上界，<0.35 高度约束 |
| oe_mis / mis_z | missense 约束指标 |

## 三库分工

| 库 | 回答什么 |
|----|----------|
| dbSNP | 在哪、是什么、功能类型、多研究频率摘要 |
| gnomAD | 精确人群 AF、各族群频率、基因约束 |
| ClinVar | 是否致病、临床意义 |

## ACMG 解读要点

| gnomAD 结果 | ACMG 证据方向 |
|-------------|---------------|
| absent / AF ≈ 0 | PM2_supporting（人群罕见） |
| AF ≥ 5% | BA1（良性 standalone） |
| ClinVar=Pathogenic + AF≈0 | 典型罕见致病变异 |
| ClinVar=VUS + AF>1% | 人群常见，致病可能性低 |

## 注意点

- API 限流：10 req/min/IP，脚本内置 ~6.5s 间隔
- 默认 `gnomad_r4`（GRCh38）
- rsID 查不到时脚本自动尝试 NCBI 坐标转换
- 基因变异筛选范围为 CDS ±75bp（与 browser 一致），不含全部 intronic
- batch 最多 5 个 rsID，避免触发限流

## API 参考

- [gnomAD Browser API](https://gnomad.broadinstitute.org/api)
- [gnomAD 帮助文档](https://gnomad.broadinstitute.org/help)
