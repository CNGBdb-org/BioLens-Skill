# DGV 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 区间 CNV 注释 | `region` | WGS/WES CNV 背景 |
| 基因缺失/重复背景 | `gene` | 基因座结构变异频率 |
| nsv 文献 ID | `id` | 精确查 DGV 条目 |
| 临床致病 CNV | 联动 `clinvar` | DGV 为人群研究非临床报告 |

## 输入 → 输出

### 按区域（region）

```
chr16:29500000-29600000
  → Ensembl overlap/region/homo_sapiens/{chr}:{start}-{end}
  → feature=structural_variation, source=DGVa（无则 DGV）
  → 过滤重叠 → id, sv_type, start, end, clin_sig
```

### 按基因（gene）

```
TBX1
  → Ensembl lookup/symbol → 基因坐标
  → overlap region → 基因座 CNV 列表
```

### 按 ID（id）

```
nsv516481
  → Ensembl variation/homo_sapiens/nsv516481
  → name, mappings, variant_class
```

## 核心字段

| 字段 | 说明 |
|------|------|
| id | DGV/DGVa 变异 ID（nsv…） |
| sv_type / variant_class | DEL、DUP、CNV 等 |
| start / end | GRCh38 坐标 |
| clinical_significance | 研究注释（若有） |
| study | 来源研究 |

## DGV vs DGVa vs ClinVar

| 库 | 侧重 |
|----|------|
| DGV | 早期 Database of Genomic Variants |
| DGVa | dbVar 整合归档（Ensembl source=DGVa） |
| ClinVar | **临床** CNV 致病性解读 |

本 skill 通过 Ensembl 查询 DGVa/DGV；个体临床 CNV 应查 ClinVar。

## 注意点

- 结果为**人群研究**汇总，非当前样本判定
- 同一区域多条 CNV 可能来自不同研究、分辨率不同
- 基因 `gene` 查询覆盖基因全长区间，含侧翼 CNV
- 与 UCSC、ClinVar region 联动做 CNV 临床解读

## API 参考

- [Ensembl REST overlap](https://rest.ensembl.org/documentation/info/overlap_region)
- [DGVa at EBI](https://www.ebi.ac.uk/dgva)
- [DGV 官网](http://dgv.tcag.ca/)
