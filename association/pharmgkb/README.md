# PharmGKB 使用说明

**PharmGKB**（Pharmacogenomics Knowledge Base）收录**药物基因组学**基因、变异、**CPIC 指南**、临床注释与代谢通路。本 skill 调用 **ClinPGx** REST API（`api.clinpgx.org`）。

写清 **基因名**、**rsID** 或 **药物名** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 基因 | PharmGKB ID、CPIC/PharmVar 标志、GRCh38 坐标 |
| 变异 | rsID 的 PGx 临床意义与变异分类 |
| 指南 | 基因相关 CPIC 等 guideline annotation |
| 临床注释 | 等位基因-表型证据与证据等级 |
| 药物 | 化学物/药物名称搜索 |
| 通路 | 药代/药效通路 |

---

## 示例问法

### 基因

- CYP2D6 是 CPIC 基因吗？
- 查 SLCO1B1 的 PharmGKB 信息
- CYP2C19 药物基因组学概况

### 变异

- rs4244285 的 PharmGKB 注释是什么？
- 这个 rsID 和 clopidogrel 有关系吗？

### 指南 / 临床

- CYP2C19 有没有 CPIC 用药指南？
- TPMT 的 PharmGKB 临床注释和证据等级
- warfarin 相关基因检测建议

### 药物 / 通路

- warfarin 在 PharmGKB 的 ID
- 查 CYP450 代谢通路

### 联动

- rs4244285 的 gnomAD 频率和 PharmGKB 注释一起查

---

## 与其他库配合

| 数据库 | 侧重 |
| ------ | ---- |
| **PharmGKB（本 skill）** | **PGx、CPIC 指南、用药证据** |
| **dbSNP / gnomAD** | rsID 坐标与人群频率 |
| **Ensembl / GENCODE** | 基因结构与转录本 |

---

## 数据说明

- 来源：[ClinPGx API](https://api.clinpgx.org/)（PharmGKB / CPIC）
- 坐标：**GRCh38**
- 临床注释须如实引用证据等级，低等级不可表述为强推荐
