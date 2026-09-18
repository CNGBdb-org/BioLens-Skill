# Open Targets 使用说明

**Open Targets Platform** 整合 **靶点–疾病关联**、遗传学证据、已知药物与临床阶段，用于药物靶点发现与优先级排序。

在聊天框用自然语言提问；写清 **基因名**、**疾病名**、**rsID** 或 **药物名** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 靶点/基因 | 基本信息、已知药物、成药性 |
| 疾病 | EFO 疾病搜索 |
| 变异 | rsID 信息与 colocalisation |
| 药物 | 药物名称搜索 |
| 靶点-疾病 | 基因与疾病的关联分数 |

---

## 示例问法

### 靶点 / 药物

- EGFR 有哪些已知药物？
- imatinib 在 Open Targets 里对应什么 ID？

### 疾病 / 关联

- breast cancer 的 EFO ID 是什么？
- BRCA1 和乳腺癌的关联分数是多少？
- TCF7L2 和 type 2 diabetes 有关联吗？

### 变异

- rs7903146 在 Open Targets 里的注释？

### 与其他库配合

- TCF7L2 的 GWAS 关联和 OpenTargets 靶点分数
- EGFR 的 UniProt 功能、已知药物和临床试验阶段

---

## 数据说明

- 来源：[Open Targets Platform](https://platform.opentargets.org/)
- 关联分数为整合证据，需结合原始 GWAS/ClinVar 数据解读
