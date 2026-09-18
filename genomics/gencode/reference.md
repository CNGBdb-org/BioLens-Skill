# GENCODE 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因注释 | `gene` | 符号 → Ensembl ID、转录本列表 |
| 转录本结构 | `transcript` | 外显子布局与 biotype |
| 注释版本核对 | `version` | 确认 Ensembl/GENCODE release |
| 靶向区域注释 | `region` | 区间内蛋白编码基因 |

## 输入 → 输出

### 按基因（gene）

```
基因符号（BRCA1）
  → GET /lookup/symbol/homo_sapiens/{symbol}?expand=1
  → id, description, biotype, 坐标, version
  → Transcript 子节点（优先 GENCODE/Havana 来源）
```

### 按转录本（transcript）

```
转录本 ID（ENST00000357654）
  → GET /lookup/id/{tx_id}?expand=1
  → Parent 基因、外显子列表、坐标
```

### 版本（version）

```
version
  → GET /info/data/
  → release, api_version, assembly（GRCh38）
```

### 按区域（region）

```
chr17:43044295-43170245
  → GET /overlap/region/homo_sapiens/{chrom}:{start}-{end}
     ?feature=transcript&biotype=protein_coding
  → 重叠转录本列表
```

## 核心字段

| 字段 | 说明 |
|------|------|
| id | Ensembl 稳定 ID（ENSG/ENST） |
| biotype | protein_coding、lncRNA 等 |
| logic_name | 注释来源（ensembl_havana 等） |
| version | 注释版本号 |
| seq_region_name | 染色体 |

## 注意点

- GENCODE 数据托管于 Ensembl，API 与 `ensembl` skill 同源但侧重 GENCODE 注释视角
- `region` 默认过滤 protein_coding，非编码 RNA 需 Ensembl overlap 扩展
- 坐标均为 **GRCh38**
- 转录本 ID 需完整 Ensembl stable ID（含版本可选）

## API 参考

- [Ensembl REST API](https://rest.ensembl.org/)
- [GENCODE](https://www.gencodegenes.org/)
