# Gene Ontology (GO) 使用说明

**Gene Ontology** 提供标准化的基因功能术语，涵盖 **生物过程（BP）**、**分子功能（MF）**、**细胞组分（CC）**。通过 QuickGO API 查询。

在聊天框用自然语言提问；写清 **基因名**、**GO ID** 或 **功能关键词** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| GO 术语 | ID → 名称、定义、命名空间 |
| 搜索 | 关键词 → 相关 GO terms |
| 基因注释 | 某基因的 GO 注释及证据 |
| 祖先 | GO term 的上位层级 |

---

## 示例问法

### 基因

- TP53 有哪些 GO 注释？
- BRCA1 参与哪些生物过程？

### 术语

- GO:0006915 是什么？
- apoptosis 相关的 GO term 有哪些？
- GO:0006915 的上位 term 是什么？

### 与其他库配合

- TP53 的 UniProt 功能和 GO 注释
- BRCA1 的 GO 注释和 OpenTargets 靶点信息

---

## 数据说明

- 来源：[QuickGO REST API](https://www.ebi.ac.uk/QuickGO/)
- 物种：人类（taxonId 9606）
