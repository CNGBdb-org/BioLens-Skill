# GENCODE 使用说明

**GENCODE** 是人类基因组高质量基因注释集。本 skill 通过 **Ensembl REST API** 查询 GENCODE 注释（与 GENCODE 官网同步）。默认组装 **GRCh38**。

在聊天框用自然语言提问；写清 **基因名**、**转录本 ID** 或 **基因组坐标** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 基因 | GENCODE/Ensembl ID、描述、转录本列表 |
| 转录本 | 外显子数、坐标、生物型 |
| 版本 | 当前 Ensembl/GENCODE 发布版本 |
| 区域 | 指定区间内蛋白编码转录本 |

---

## 示例问法

### 基因

- BRCA1 有哪些 GENCODE 转录本？
- 查 TP53 的 GENCODE 基因注释和坐标
- EGFR 的 Ensembl ID 是什么？

### 转录本

- ENST00000357654 这个转录本有多少外显子？
- 查一下这个 Ensembl 转录本的详情

### 版本 / 区域

- 当前 GENCODE 是什么版本？
- chr17:43044295-43170245 区域有哪些蛋白编码基因？

---

## 与其他 skill 配合

| 数据库 / skill | 侧重 |
| -------------- | ---- |
| **ensembl** | 变异 VEP、同源基因（同一 API） |
| **ucsc** | 基因组浏览器 track |
| **kegg** | 通路层面功能 |

---

## 数据说明

- 来源：[GENCODE](https://www.gencodegenes.org/) via [Ensembl REST](https://rest.ensembl.org/)
- 组装：**GRCh38**
