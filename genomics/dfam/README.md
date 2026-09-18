# Dfam 使用说明

**Dfam** 收录转座子与重复 DNA **家族**的共识序列与 HMM 模型。本 skill 通过 Dfam REST API 查询家族元数据。**基因组坐标区间的重复注释**需联动 **UCSC RepeatMasker** track。

在聊天框用自然语言提问；写清 **家族名**、**accession** 或 **重复类型** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 家族 | 按名称或 accession 查重复元件家族 |
| 搜索 | 关键词搜索 Dfam 家族 |
| HMM 模型 | 家族模型长度、阈值、分类 |
| 重复类型 | LINE、SINE、LTR 等类型筛选 |
| 区域 | **无直接 API**；提供 UCSC 联动指引 |

---

## 示例问法

### 家族 / 搜索

- Alu 在 Dfam 里是什么家族？
- 搜一下 MER 相关的重复元件
- DF0000001 这个家族的 HMM 模型参数是什么？

### 重复类型

- Dfam 里有哪些 LINE 重复家族？
- 查 SINE 类型的重复元件

### 区域（需联动 UCSC）

- chr1:1000000-1010000 有哪些重复序列？
- 这个基因组区域 RepeatMasker 注释是什么？

区域查询流程：`dfam region` 说明限制 → `ucsc track RepeatMasker` → `dfam family` 查详情。

---

## 与其他 skill 配合

| 数据库 / skill | 侧重 |
| -------------- | ---- |
| **ucsc** | RepeatMasker track 区域重复注释 |
| **gencode** | 基因转录本坐标（区分基因与重复） |

---

## 数据说明

- 来源：[Dfam](https://dfam.org/) REST API
- 区域注释：通过 UCSC Genome Browser RepeatMasker track
