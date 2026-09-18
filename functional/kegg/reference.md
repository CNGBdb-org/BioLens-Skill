# KEGG 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因功能通路 | `gene` | 从基因符号到 KEGG 条目与 pathway link |
| 通路基因列表 | `pathway` | 查看通路内全部基因与描述 |
| 疾病背景 | `disease` | 疾病条目检索 |
| 代谢物注释 | `compound` | 化合物 ID 与化学信息 |
| 通路发现 | `map` | 关键词模糊搜人类通路 |

## 输入 → 输出

### 按基因（gene）

```
基因符号（TP53）
  → find/genes/{symbol} → 匹配 hsa: 人类基因 ID
  → get/{kid} → 条目文本（NAME、PATHWAY 等）
  → link/pathway/{kid} → 关联通路 ID 列表
```

### 按通路（pathway）

```
通路 ID（hsa04110 或 04110）
  → 规范化为 hsa 前缀
  → get/{pid} → 通路名称、描述、基因列表
```

### 按疾病（disease）

```
疾病关键词（diabetes, Parkinson）
  → find/disease/{keyword}
  → 疾病 ID + 名称（前 N 条）
```

### 按化合物（compound）

```
化合物名（glucose, ATP）
  → find/compound/{name} → 取首条 compound ID
  → get/{cid} → 化学式、名称等
```

### 通路搜索（map）

```
关键词（apoptosis, MAPK）
  → find/pathway/{keyword}
  → 过滤含 hsa 的人类通路
```

## 核心字段

| 字段 | 说明 |
|------|------|
| KEGG Gene ID | `hsa:10413` 等形式 |
| Pathway ID | `hsa04110` 等，`map` 编号对应通路图 |
| Disease ID | `H00001` 等 |
| Compound ID | `C00031` 等 |
| PATHWAY | 基因条目中的关联通路行 |

## 注意点

- **学术用途限定**：KEGG API 要求非商业、低频访问；勿批量爬取
- `gene` 优先精确匹配基因符号，否则取首条 hsa 结果
- 通路、疾病检索为模糊匹配，英文关键词效果更好
- KEGG 侧重通路层面，精细基因注释可联动 `gencode` / `eggnog`

## API 参考

- [KEGG REST API](https://rest.kegg.jp/)
- [KEGG 使用条款](https://www.kegg.jp/kegg/legal.html)
