# Ensembl 使用说明

**Ensembl** 提供人类基因、转录本、变异注释与 **VEP** 功能预测。默认物种人类，组装 **GRCh38**。

在聊天框用自然语言提问；写清 **基因名**、**rsID**、**坐标区域** 或 **HGVS** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 基因 | Ensembl ID、描述、坐标、转录本 |
| 变异 | rsID/COSMIC → 坐标、等位基因 |
| 区域 | 指定区间内的基因 |
| 同源 | 跨物种直系同源基因 |
| VEP | HGVS → 功能后果、SIFT/PolyPhen |

---

## 示例问法

### 基因

- BRCA1 的 Ensembl ID 是什么？
- TP53 有哪些主要转录本？
- BRCA1 在基因组上的坐标？

### 变异 / VEP

- rs80357906 在 Ensembl 里怎么注释？
- p.V600E 的功能后果是什么？
- c.5266dup 的 VEP 预测结果？

### 区域 / 同源

- chr17:43044295-43170245 有哪些基因？
- TP53 在小鼠里的同源基因是什么？

### 与其他库配合

- rs80357906 的 Ensembl 坐标、gnomAD 频率和 ClinVar 致病性一起查
- BRCA1 的 Ensembl 转录本和 RefSeq 转录本对比

---

## 数据说明

- 来源：[Ensembl REST API](https://rest.ensembl.org/)
- 物种：人类（homo_sapiens），**GRCh38**
