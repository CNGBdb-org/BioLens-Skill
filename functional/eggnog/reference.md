# eggNOG 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因功能背景 | `gene` / `function` | UniProt → OG → GO 注释 |
| 同源组深挖 | `og` | OG 级 GO 与结构域 |
| 多异构体映射 | `ortholog` | 列出基因所有 UniProt-OG 对 |

## 输入 → 输出

### 按基因（gene）

```
基因符号（TP53）
  → UniProt search: gene:{symbol} AND organism_id:9606 [reviewed优先]
  → uniProtKBCrossReferences[database=eggNOG] → OG ID
  → eggnogapi5/nog_data/json/go_terms/{og_id} → GO 术语 + 频率
```

### 按 OG（og）

```
OG ID（4PQUD@1|root）
  → eggnogapi5/.../go_terms/{og_id}
  → eggnogapi5/.../domains/{og_id}
```

### 按同源（ortholog）

```
基因符号
  → UniProt 多条结果（最多 5 条）
  → 每条: accession, geneName, eggNOG IDs
```

### 按功能（function）

```
基因符号
  → UniProt 首条 → 首个 OG
  → go_terms 全类别展示（前 N 条/类）
```

## 核心字段

| 字段 | 说明 |
|------|------|
| UniProt accession | 如 P04637 |
| eggNOG OG | 直系同源组标识，如 `4PQUD@1\|root` |
| GO terms | BP（生物过程）、MF（分子功能）、CC（细胞组分） |
| freq | OG 内携带该 GO 的成员百分比 |
| domains | 保守蛋白结构域（Pfam 等） |

## 注意点

- 无 UniProt eggNOG 交叉引用时无法查 OG（部分新基因或非编码产物）
- reviewed（Swiss-Prot）优先，无结果时放宽至 TrEMBL
- GO 频率为描述性，非富集分析 p 值；正式富集需专用工具
- eggNOG API 为 EMBL 公共服务，大批量请求请节制

## API 参考

- [UniProt REST API](https://rest.uniprot.org/)
- [eggNOG API v5](http://eggnogapi5.embl.de/)
