# LOVD 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因符号规范化 | `gene` | HGNC 校验 |
| HGVS 写法检查 | `hgvs` / `check` | 语法与类型 |
| 位点是否进公共 LOVD | `coord` / `region` | UCSC Beacon lovd |
| 临床意义 | 联动 `clinvar` | LOVD 本 skill 不提供分级 |

## 输入 → 输出

### 按基因（gene）

```
DMD
  → GET https://api.lovd.nl/v2/checkGene/DMD
  → valid, hgnc_id, corrected_values
```

### 按 HGVS（hgvs / check）

```
c.1234A>G 或 chr17:g.43057060G>A
  → GET https://api.lovd.nl/v2/checkHGVS/{encoded}
  → valid, identified_as, warnings, corrected_values, position/type
```

### 按坐标（coord）

```
17 43057060 [G]
  → UCSC hgBeacon: dataset=lovd, 0-based position
  → 公共 LOVD 聚合是否收录
```

### 按区域（region）

```
chr17:g.43057060G>A 或 chr17:43057060
  → 解析 chrom, pos, alt → coord
```

## 核心字段

| 字段 | 说明 |
|------|------|
| valid | 基因符号或 HGVS 是否通过 LOVD 校验 |
| hgnc_id | HGNC 官方 ID |
| identified_as | HGVS 识别类型（genomic/coding/protein 等） |
| warnings | 语法或命名警告 |
| corrected_values | 建议的官方写法 |
| Beacon response | 公共 LOVD 位点存在性 |

## LOVD API vs Beacon

| 接口 | 能力 |
|------|------|
| api.lovd.nl v2 | 基因/HGVS **验证**，非变异检索 |
| UCSC Beacon lovd | 位点**存在性**，无疾病库细节 |
| lovd.nl/3.0/search | 人工/Web 全球 LOVD 变异搜索 |

序列级 HGVS 验证：https://variantvalidator.org

## 注意点

- HGVS valid=true 不保证临床致病性
- Beacon false 可能因 alt 不匹配（默认 N）
- 各疾病 LOVD 实例数据分散；Beacon 为公共聚合子集
- 与 HGMD Beacon 并行可交叉验证位点是否被突变库收录

## API 参考

- [LOVD API v2](https://api.lovd.nl/v2)
- [LOVD 全球搜索](https://lovd.nl/3.0/search)
- [UCSC hgBeacon lovd](https://genome.ucsc.edu/cgi-bin/hgBeacon?dataset=lovd)
