# Ensembl 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因注释 | `gene` | 获取 Ensembl ID、坐标、转录本 |
| 变异定位 | `variant` | rsID → 基因组坐标与等位基因 |
| 区域浏览 | `region` | 区间内基因列表 |
| 跨物种比较 | `homology` | 直系同源基因与序列一致性 |
| 功能预测 | `vep` | HGVS → 后果、影响等级、预测工具 |

## 输入 → 输出

### 按基因（gene）

```
基因符号（BRCA1）
  → GET /lookup/symbol/homo_sapiens/{symbol}?expand=1
  → Ensembl ID、描述、坐标、转录本列表
```

### 按变异（variant）

```
rsID 或 COSMIC ID
  → GET /variation/homo_sapiens/{id}
  → 等位基因、GRCh38 坐标、人群频率摘要
```

### 按区域（region）

```
chr17:43044295-43170245
  → GET /overlap/region/homo_sapiens/{chr}:{start}-{end}?feature=gene
  → 重叠基因及 biotype
```

### 同源基因（homology）

```
基因符号
  → lookup → GET /homology/id/homo_sapiens/{id}?type=orthologues
  → 其他物种直系同源及 target_perc_id
```

### VEP（vep）

```
HGVS（c./p. 或 转录本:c.xxx）
  → POST /vep/homo_sapiens/hgvs
  → transcript_consequences：consequence_terms、impact、SIFT、PolyPhen
```

## 核心字段

| 字段 | 说明 |
|------|------|
| id | Ensembl 稳定 ID（基因/转录本） |
| biotype | protein_coding、lncRNA 等 |
| consequence_terms | missense、frameshift 等 SO 术语 |
| impact | HIGH / MODERATE / LOW / MODIFIER |
| assembly_name | 默认 GRCh38 |

## 注意点

- VEP 需完整 HGVS，含转录本 ID 时更准确
- Ensembl 频率为内部 cohort，精确 AF 请用 `gnomad`
- 临床意义请联动 `clinvar`，不依赖 VEP 单独下致病结论

## API 参考

- [Ensembl REST API](https://rest.ensembl.org/)
- [Variant Effect Predictor](https://www.ensembl.org/info/docs/tools/vep/index.html)
