# DGV 使用说明

**DGV**（Database of Genomic Variants）与 **DGVa** 收录人群中**拷贝数变异（CNV）**与结构变异。本 skill 通过 **Ensembl REST API** 查询 `structural_variation`（优先 DGVa，回退 DGV）。

结果为**人群研究** CNV 目录，**个体临床 CNV 解读请查 ClinVar**。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 区域 CNV | 指定区间重叠的 DGV/DGVa 结构变异 |
| 基因 CNV | 基因座及侧翼的已知 CNV |
| 变异 ID | nsv 编号查坐标与类型 |

---

## 示例问法

### 区域

- chr16:29500000-29600000 有哪些 DGV CNV？
- 这个区间有没有已知缺失或重复？

### 基因

- TBX1 基因区域有哪些 CNV？
- APP 基因常见拷贝数变异有哪些？

### 变异 ID

- nsv516481 是什么 CNV？
- 查 DGV 变异 ID nsv123456

### 联动

- 这个区域的 DGV CNV 和 ClinVar 临床 CNV 一致吗？
- TBX1 缺失在 DGV 和 ClinVar 里怎么标注？

---

## 与其他库配合

| 数据库 | 侧重 |
| ------ | ---- |
| **DGV/DGVa（本 skill）** | **人群 CNV/结构变异** |
| **ClinVar** | **临床 CNV 致病性** |
| **Ensembl / GENCODE** | 基因坐标 |
| **UCSC** | 保守性、轨道数据 |

---

## 数据说明

- 来源：Ensembl overlap API，`source=DGVa` / `DGV`
- 坐标：**GRCh38**
- DGV 已整合至 DGVa/dbVar
