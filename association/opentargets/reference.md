# Open Targets 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 靶点药物 | `gene` | 已知药物与成药性 |
| 疾病映射 | `disease` | EFO ID 与标准名 |
| 变异整合 | `variant` | rsID 与 GWAS colocalisation |
| 药物检索 | `drug` | 药物实体搜索 |
| 靶点验证 | `target` | 基因-疾病关联分数 |

## 输入 → 输出

### 靶点（gene）

```
基因符号
  → search entityNames: target → ensemblId
  → target(ensemblId) → approvedSymbol、knownDrugs、tractability
```

### 疾病（disease）

```
关键词
  → search entityNames: disease
  → hits: id (EFO)、name、description
```

### 变异（variant）

```
rsID
  → variant(variantId) → 坐标、ref/alt、colocalisation count
  → 或 search entityNames: variant
```

### 药物（drug）

```
药物名
  → search entityNames: drug → id、name
```

### 靶点-疾病（target）

```
基因 + 疾病
  → resolve Ensembl ID + EFO disease ID
  → disease.associatedTargets → 匹配基因的 score、datatypeScores
```

## 核心字段

| 字段 | 说明 |
|------|------|
| score | 0–1 综合关联分数 |
| datatypeScores | genetic_association、known_drug 等分项 |
| maximumClinicalTrialPhase | 药物最高临床阶段（4=批准） |
| efoId | 疾病 EFO 标识 |

## 注意点

- 分数为多维证据整合，需结合 `gwascatalog`/`clinvar` 看原始数据
- 疾病搜索取 top hit，歧义时确认 EFO 名称
- 不可将关联分数直接等同于临床有效性

## API 参考

- [Open Targets Platform API](https://platform.opentargets.org/api)
- [Open Targets Documentation](https://platform-docs.opentargets.org/)
