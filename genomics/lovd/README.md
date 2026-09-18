# LOVD 使用说明

**LOVD**（Leiden Open Variation Database）是全球分散的遗传变异库网络。本 skill 提供：

1. **api.lovd.nl v2** — 基因符号与 **HGVS 语法**验证（`checkGene` / `checkHGVS`）
2. **UCSC Beacon（dataset=lovd）** — 公共 LOVD 聚合中位点**是否存在**

具体疾病库详情请在 [lovd.nl 搜索](https://lovd.nl/3.0/search) 或联动 **ClinVar**。

---

## 能查什么

| 类型 | 说明 |
| ---- | ---- |
| 基因验证 | 符号是否有效、HGNC ID、建议修正 |
| HGVS 验证 | c./g./p. 语法与类型、警告 |
| 位点 Beacon | 坐标是否在公共 LOVD 中 |
| 区域 | 解析 `chr:g.` 或 `chr:pos` 后查 Beacon |

---

## 示例问法

### 基因

- DMD 基因符号在 LOVD 里对吗？
- LOVD 验证 BRCA1 基因名

### HGVS

- c.1234A>G 这个 HGVS 写法对不对？
- 帮我 check chr17:g.43057060G>A
- c.5266dupC 语法有没有问题？

### 位点 / 区域

- chr17:43057060 在 LOVD 里有记录吗？
- 查 chr17:g.43057060G>A 是否进公共 LOVD

### 联动

- 这个 HGVS LOVD 验证通过后 ClinVar 致病性是什么？
- LOVD 和 HGMD Beacon 这个位点都命中吗？

---

## 与其他库配合

| 数据库 | 侧重 |
| ------ | ---- |
| **LOVD（本 skill）** | **符号/HGVS 验证、公共 Beacon** |
| **ClinVar** | 临床致病性 |
| **HGMD Beacon** | HGMD 公共位点 |
| **Ensembl** | 坐标、VEP 注释 |

序列级 HGVS 验证：[VariantValidator](https://variantvalidator.org)

---

## 数据说明

- LOVD API：[api.lovd.nl/v2](https://api.lovd.nl/v2)
- Beacon：[UCSC hgBeacon lovd](https://genome.ucsc.edu/cgi-bin/hgBeacon?dataset=lovd)
- HGVS 验证为语法级，非序列比对
