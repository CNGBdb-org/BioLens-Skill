# gnomAD 使用说明

**gnomAD**（Genome Aggregation Database）提供人群等位基因频率与基因约束（**pLI**、**LOEUF**），是 ACMG 变异解读中 PM2/BA1 等证据的常用来源。当前默认 **gnomAD v4**，坐标 **GRCh38**。

在下方聊天框用自然语言提问即可；写清 **rsID** 或 **基因名** 更容易命中。

> **注意：** gnomAD 接口有访问频率限制，单次 rsID 查询可能需要 **1–2 分钟**，请耐心等待。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 变异频率 | rsID 或坐标+等位基因 → Exome/Genome AF、主要人群 AF、罕见/常见解读 |
| 基因约束 | 基因 → pLI、LOEUF、oe_lof 等，评估基因对 LoF 的耐受性 |
| 基因变异筛选 | 某基因内罕见 / 常见 / LoF / missense 变异列表 |
| 区域 | 指定区间内的 gnomAD 变异及频率 |
| 批量 | 一次问多个 rsID（建议不超过 5 个） |

---

## 示例问法

### 单点频率

- rs80357906 在 gnomAD 里频率多少？
- 这个变异在人群里常见吗？
- rs80357906 在各个人群中的 AF 是多少？

### 基因约束

- BRCA1 基因约束怎么样？
- TP53 的 pLI 和 LOEUF 是多少？
- 这个基因对 LoF 变异耐受吗？

### 基因 / 区域

- BRCA1 有哪些罕见变异？
- TP53 有多少 LoF 变异？
- chr17:43057060-43057065 区域有哪些 gnomAD 变异？

### 批量 / 联动

- 帮我查 rs80357906 和 rs11591147 的 gnomAD 频率
- rs80357906 的 dbSNP 信息、gnomAD 频率和 ClinVar 致病性一起查

---

## 三库怎么配合

| 数据库 | 侧重 |
| ------ | ---- |
| **dbSNP** | SNP 定位、功能注释、多研究频率摘要 |
| **gnomAD** | **精确人群 AF、各族群频率、基因约束** |
| **ClinVar** | 临床致病性 |

问「这个 SNP 是什么、常见吗、致病吗」时，可直接说 **三库一起查**，系统会依次返回 dbSNP 定位、gnomAD 频率与 ClinVar 致病性。

---

## 数据说明

- 来源：[gnomAD](https://gnomad.broadinstitute.org/)
- 版本：**gnomAD v4**（GRCh38）
