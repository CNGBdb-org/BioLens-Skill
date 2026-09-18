# KEGG 使用说明

**KEGG**（Kyoto Encyclopedia of Genes and Genomes）提供代谢通路、疾病、化合物与人类基因关联注释。本 skill 通过 KEGG REST API 查询，**仅限学术用途**。

在聊天框用自然语言提问即可；写清 **基因名**、**通路 ID**、**疾病/化合物关键词** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 基因 | 人类基因 KEGG 条目、关联通路 |
| 通路 | 按 ID 查通路描述与基因成员 |
| 疾病 | 疾病关键词 → KEGG 疾病条目 |
| 化合物 | 代谢物/药物化合物信息 |
| 通路搜索 | 关键词搜索人类（hsa）通路 |

---

## 示例问法

### 基因

- TP53 在 KEGG 里关联哪些通路？
- 查 BRCA1 的 KEGG 基因条目
- EGFR 参与什么信号通路？

### 通路

- hsa04110 是什么通路？
- KEGG 细胞周期通路（04110）里有哪些基因？

### 疾病 / 化合物

- KEGG 里和 diabetes 相关的疾病条目有哪些？
- glucose 在 KEGG 化合物库里的 ID 是什么？

### 通路搜索

- 和 apoptosis 相关的人类 KEGG 通路有哪些？
- 搜一下 MAPK 信号通路

---

## 与其他 skill 配合

| 数据库 / skill | 侧重 |
| -------------- | ---- |
| **gencode** | 基因坐标、GENCODE 转录本 |
| **eggnog** | 直系同源组、GO 功能注释 |
| **ucsc** | 基因组浏览器 track 与保守性 |

---

## 数据说明

- 来源：[KEGG](https://www.kegg.jp/) REST API（`rest.kegg.jp`）
- 默认物种：**人类（hsa）**
- 使用须遵守 KEGG 学术用途条款
