# eggNOG 使用说明

**eggNOG** 基于直系同源组（OG）提供跨物种功能注释。本 skill 通过 **UniProt 交叉引用** 定位人类基因的 eggNOG OG，再调用 **eggNOG API v5** 获取 GO 术语与蛋白结构域。

在聊天框用自然语言提问；写清 **基因名** 或 **OG ID** 更容易命中。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 基因注释 | 人类基因 → UniProt → eggNOG OG + GO 摘要 |
| 同源组 | 按 OG ID 查 GO 与结构域 |
| 同源映射 | 基因对应多条 UniProt 与 OG 列表 |
| 功能 | 基于 OG 的 GO 功能术语 |

---

## 示例问法

### 基因

- TP53 的 eggNOG 直系同源组是什么？
- 查 BRCA1 的 eggNOG 和 GO 注释
- EGFR 在 eggNOG 里属于哪个 OG？

### 同源组

- 4PQUD@1|root 这个 OG 有哪些 GO 和结构域？
- 帮我查一下这个 eggNOG OG 的功能

### 功能 / 同源

- TP53 有哪些 GO 生物过程？
- BRCA1 对应几个 UniProt 和 eggNOG ID？

---

## 与其他 skill 配合

| 数据库 / skill | 侧重 |
| -------------- | ---- |
| **kegg** | 代谢与信号通路 |
| **gencode** | 基因坐标、转录本注释 |
| **ucsc** | 基因组 track 与保守性 |

---

## 数据说明

- 物种默认：**人类（9606）**
- 数据源：UniProt + eggNOG API v5（EMBL）
