# UCSC 使用说明

**UCSC Genome Browser** 提供丰富的基因组 track 与注释。本 skill 通过 UCSC **Genome Browser API** 查询基因、track 数据与保守性。默认基因组 **hg38**。

在聊天框用自然语言提问；写清 **基因名**、**track 名** 或 **坐标区域** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 基因 | UCSC 基因组内基因搜索与坐标 |
| 区域 | 区间内 knownGene 基因 |
| Track | 任意 UCSC track 在区间的记录 |
| 保守性 | phastCons 保守性数据探测 |

---

## 示例问法

### 基因

- BRCA1 在 UCSC hg38 上的坐标是多少？
- 在 UCSC 里搜一下 TP53

### 区域 / Track

- chr17:43044295-43170245 有哪些基因？
- chr1:1000000-1010000 的 RepeatMasker 重复元件有哪些？
- 查一下 refGene track 在这个区域的注释

### 保守性

- chr17:7577000-7579000 区域保守性如何？
- 这个位点 phastCons 分数有吗？

### 其他组装

- TP53 在 hg19 上的坐标（加 `--genome hg19`）

---

## 与其他 skill 配合

| 数据库 / skill | 侧重 |
| -------------- | ---- |
| **gencode** | GENCODE 转录本与版本 |
| **dfam** | 重复元件家族；区域重复查 UCSC RepeatMasker |
| **clinvar** | 变异临床意义 |

---

## 数据说明

- 来源：[UCSC Genome Browser API](https://api.genome.ucsc.edu/)
- 默认组装：**hg38**（可用 `--genome` 切换）
