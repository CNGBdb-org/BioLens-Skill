# PharmGKB 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| PGx 基因入门 | `gene` | CPIC/PharmVar 标志与坐标 |
| 单 SNP PGx | `variant` | rsID 临床意义 |
| 用药指南 | `guideline` | CPIC guideline annotation |
| 等位基因-表型证据 | `clinical` | 临床注释与证据等级 |
| 药物实体 | `drug` | 化学物 PharmGKB ID |
| 代谢通路 | `pathway` | PK/PD 通路图入口 |

## 输入 → 输出

### 按基因（gene）

```
CYP2D6
  → GET /v1/data/gene?symbol=CYP2D6
  → id, symbol, name, GRCh38 坐标, cpicGene, pharmVarGene
```

### 按变异（variant）

```
rs4244285
  → GET /v1/data/variant?symbol=rs4244285&view=base
  → clinicalSignificance, changeClassification
```

### 按指南（guideline）

```
CYP2C19
  → GET /v1/data/guidelineAnnotation?relatedGenes.symbol=CYP2C19&view=base
  → name, dosingInformation, hasTestingInfo
```

### 按临床注释（clinical）

```
SLCO1B1
  → GET /v1/data/clinicalAnnotation?location.genes.symbol=SLCO1B1&view=base
  → levelOfEvidence, allelePhenotypes
```

### 按药物（drug）

```
warfarin
  → GET /v1/data/chemical?name=warfarin&view=base
  → 化学物名称与 ID
```

### 按通路（pathway）

```
CYP450
  → GET /v1/data/pathway?name=CYP450&view=base
  → 通路名称与 ID
```

## 核心字段

| 字段 | 说明 |
|------|------|
| cpicGene | 是否为 CPIC 关注基因 |
| pharmVarGene | 是否有 PharmVar 等位基因定义 |
| levelOfEvidence | 临床注释证据等级（须如实引用） |
| dosingInformation | 指南是否含剂量信息 |
| hasTestingInfo | 是否建议基因检测 |
| clinicalSignificance | 变异 PGx 临床意义摘要 |

## 注意点

- 证据等级低时**不可**表述为强临床推荐
- Star allele（*1、*2）详情常需 PharmVar + 实验室分型，不仅 rsID
- 坐标 GRCh38；与 GRCh37 项目注意 build 一致
- 与 gnomAD 联动评估等位基因频率对 PGx 预测的影响

## API 参考

- [ClinPGx API](https://api.clinpgx.org/swagger/)
- [ClinPGx / PharmGKB 官网](https://www.pharmgkb.org/)
- [CPIC](https://cpicpgx.org/)
