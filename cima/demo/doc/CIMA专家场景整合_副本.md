# CIMA 专家场景（整合稿）

> 由 `demo/doc/CIMA笔记——专家场景.md` **过滤 CIMA 相关内容**整理，并与当前仓库 `skills/cima/` 分工对齐。  
> 已去掉：variant-interpretation / ClinVar / dbSNP / gnomAD / Ensembl / GO·KEGG·UniProt / 通用 scanpy-\* 等非 CIMA 专属场景。

文献：Yin et al., *Science* 2026；DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)  
门户：https://db.cngb.org/trueblood/cima/

---

## 一、总体优势（CIMA 专属）

### 1. 降低多组学分析门槛

传统 CIMA 多组学需同时掌握 scRNA、scATAC、QTL、GWAS 整合、GRN 等，工具链长（scanpy、SnapATAC2、SCENIC+、tensorQTL、SMR…）。CIMA 专家 Skills 封装为自然语言可触发的能力：

- Agent 按问题自动路由到对应 Skill  
- 参数默认对齐论文流程，便于复现  
- 流水线以 **CPU** 为主路径，适配常见实验室环境  

### 2. 千万级细胞：即时查询 + 本地流水线

数据规模约 648 万 scRNA + 376 万 scATAC（合计 1000 万+）。专家拆成两条轨：

| 轨 | 做什么 | 代表 Skill |
|----|--------|------------|
| **解读轨** | 预计算表 / 门户图谱缓存，秒级～分钟级问答 | `cima-resource`、`cima-atlas-explore`、`cima-grn-scenicplus`、`cima-xqtl`、`cima-smr-gwas`、`cima-clm` |
| **分析轨** | 用户/demo h5ad 本地跑通预处理→注释→多组学 | `cima-scrna-*` … `cima-metacell` |

### 3. 从「重计算」到「即时查询」

| 传统方式 | CIMA Skills |
|----------|-------------|
| 下载百 GB h5ad → 写脚本 → 久等 | 自然语言 → 路由 → 预计算/缓存返回 |
| SCENIC+ 集群重跑数天 | 查 eRegulon 预计算表 |
| tensorQTL + WGS 数小时 | 查 lead xQTL 表 |
| SMR + GCTA + GWAS 手工多步 | 查 SMR / 疾病性状表 |
| Enformer + GPU 推理 | CLM Demo 预计算结果出图 |

### 4. 标准化与可复现

- 遵循 Agent Skills 规范，可部署到多种 Agent  
- 输出统一：表格 / 图路径 / 数据源说明  
- 部署环境数据优先本地：`/public/.../CIMA_Resource/`（`CIMA_RESOURCE_ROOT` 可覆盖）

---

## 二、CIMA Skill 清单（当前仓库）

路径均在 `skills/cima/<name>/`（安装后展平为叶子目录）。

| Skill | 类型 | 用途 |
|-------|------|------|
| `cima-resource` | 资源 L3 | 可下载数据清单、本地/FTP 路径 |
| `cima-atlas-explore` | 图谱浏览 L4 | 谱系子集、donor、组成、基因 UMAP；**不含** GRN/xQTL/SMR/清单 |
| `cima-scrna-preprocessing` | 流水线 L5 | scRNA QC→聚类→系群拆分 |
| `cima-cell-annotation` | 流水线 L5 | TrueBlood L1–L4 marker 注释 |
| `cima-pseudobulk-variance` | 流水线 L5 | Pseudobulk + age/sex 方差 |
| `cima-scratac-preprocessing` | 流水线 L5 | scATAC + 可选 gene activity |
| `cima-multiomics-integration` | 流水线 L5 | RNA→ATAC 标签迁移 |
| `cima-metacell` | 流水线 L5 | Metacell 聚合与配对 |
| `cima-grn-scenicplus` | 预计算 L4 | eRegulon / GRN |
| `cima-xqtl` | 预计算 L4 | cis-eQTL / cis-caQTL |
| `cima-smr-gwas` | 预计算 L4 | SMR（含疾病性状场景时用显著表） |
| `cima-clm` | Demo L5 | CIMA-CLM 预计算变异效应可视化 |

> 同源探索代码亦保留 `skills/single-cell/cima`（短名 `cima`）。分类安装：`--category cima`。

**术语**：论文写 **谱系 / lineage / L1–L4**；门户 ExploreId 如 `CIMA_B`。Skill 里旧称「视图」≈ 谱系子集数据集，对外演示建议说「谱系子集」。

---

## 三、演示场景（仅 CIMA）

### 场景 A：资源与谱系图谱探索

**Skill：** `cima-resource` + `cima-atlas-explore`

**优势：** 无需先下全量 h5ad；清单、donor、组成、基因表达可问答。

**触发问题：**

1. CIMA 有哪些可下载数据？本地路径在哪？  
2. 门户上可以探索哪些谱系子集（PBMC / CD4T / CD8T / B / Myeloid / NK）？  
3. CIMA B 细胞子集有哪些亚型？各占多少比例？  
4. CD8A 在不同免疫谱系里怎么表达？哪个更高？  
5. 428 名供体年龄和性别分布怎样？  
6. （组成衰老）随年龄增长哪些亚型比例升/降？按年龄段分层画图。  
7. 基因列表 MS4A1、CD8A、NKG7、LYZ、FOXP3、IKZF4、IL12B 在哪些细胞类型高表达？  

**预期：** 秒级～分钟级（全量 PBMCs UMAP 更慢）；路由到 resource / atlas-explore。

---

### 场景 B：基因调控网络（GRN）

**Skill：** `cima-grn-scenicplus`（独立，不依赖 explore `cima`）

**优势：** 免 SCENIC+ 重算；按 TF / 靶基因 / 谱系列 eRegulon。

**触发问题：**

1. Treg 关键因子 FOXP3 调控哪些下游基因？  
2. B 细胞有哪些高质量 eRegulon？  
3. NK 谱系的转录因子调控网络有哪些 regulon？  

**预期：** 预计算表查询，秒级（首次拉表除外）。

---

### 场景 C：cis-xQTL

**Skill：** `cima-xqtl`

**优势：** 免 tensorQTL + WGS；按基因 / 变异 / 细胞类型 / eQTL·caQTL 过滤。

**触发问题：**

1. 基因 CDC42 在 CIMA 里有没有 cis-eQTL？在哪些细胞类型？  
2. Bn_TCL1A（或 B 相关亚型）里有哪些 cis-caQTL？  
3. 某 variant（如 chr12_56050848）影响哪个基因？  

**预期：** 秒级返回 lead 关联（p 值、效应等）。

---

### 场景 D：SMR 与免疫相关性状

**Skill：** `cima-smr-gwas`

**优势：** 免本地 SMR/GCTA 工具链；可查基因–疾病/性状显著关联（注意：默认 CSV 与「疾病显著表」用途不同，演示疾病请用有命中的基因）。

**触发问题（推荐有命中的例子）：**

1. 基因 **CTLA4** 在 CIMA 显著 SMR 里和哪些免疫相关疾病有关联？  
2. 基因 **BLK** 和类风湿关节炎（RA）有没有 SMR 关联？  
3. 基因 **ORMDL3** / **IL18R1** 和哮喘等相关性状的关联？  

> 不推荐再用 ARL14EP 当「免疫病」例子（疾病显著表中无记录；CSV 侧多为 caQTL→基因）。

**预期：** 秒级；讲清「统计关联 / SMR 证据，非临床诊断」。

---

### 场景 E：CIMA-CLM 变异效应 Demo

**Skill：** `cima-clm`

**优势：** 免 GPU/Enformer 现场推理；预计算 in silico mutagenesis 出热图/折线/logo。

**触发问题：**

1. 帮我跑 CIMA-CLM 的变异效应 demo，生成热图和折线图。  
2. CLM demo 能做什么？（解释预计算边界）  

**前提：** 本地需 `CIMA-CLM_Demo` 或 `CIMA_CLM_DEMO`。

---

### 场景 F：本地分析流水线（demo / 自有 h5ad）

**Skill：**  
`cima-scrna-preprocessing` → `cima-cell-annotation` →（可选）`cima-pseudobulk-variance`  
→ `cima-scratac-preprocessing` → `cima-multiomics-integration` → `cima-metacell`

**优势：** 论文向 CPU 流程封装；配对 demo 可跑通标签迁移与 metacell 配对。

**触发问题：**

1. 用 `paired_demo_rna` / `paired_demo_atac` / `paired_demo_atac_gene`，按 CIMA 流程依次做预处理、L1–L4 注释、pseudobulk、scATAC、多组学整合、metacell 配对。  
2. 只用 paired_demo_rna 跑 scRNA 预处理 + L1–L4 注释。  
3. 已有 Step1 RNA 与 gene-level ATAC，做多组学标签迁移再 metacell，报告配对对数。  

**预期：** 数分钟级；验收看 `Pseudo_multiomics_barcode_info.csv` 与 metacell h5ad shape。

---

## 四、推荐演示顺序

### 快问快答（约 1 分钟内可连问）

| 顺序 | 问法 | Skill | 量级 |
|------|------|-------|------|
| 1 | 有哪些可下载数据 / 本地路径？ | `cima-resource` | 秒 |
| 2 | 可探索哪些谱系子集？ | `cima-atlas-explore` | 秒 |
| 3 | CD8A 跨谱系怎么表达？ | `cima-atlas-explore` | 秒～分 |
| 4 | FOXP3 调控哪些基因？ | `cima-grn-scenicplus` | 秒 |
| 5 | CDC42 有没有 cis-eQTL？ | `cima-xqtl` | 秒 |
| 6 | CTLA4 的 SMR 疾病关联？ | `cima-smr-gwas` | 秒 |

### 中等（组成衰老 / 表达）

| 顺序 | 问法 | Skill |
|------|------|-------|
| 7 | 年龄分层亚型比例升/降并出图 | `cima-atlas-explore` |
| 8 | marker 基因列表在哪些细胞类型高表达 | `cima-atlas-explore` |

### 慢（本地计算）

| 顺序 | 问法 | Skill |
|------|------|-------|
| 9 | 配对 demo 跑通多组学+metacell | 流水线 1–6 |
| 10 | （可选）CLM demo 出图 | `cima-clm` |

---

## 五、场景问题速查（仅 CIMA）

**资源 / 图谱**

1. CIMA 有哪些可下载数据？本地路径在哪？  
2. 可探索哪些谱系子集？各大约多少细胞？  
3. B 子集亚型组成？CD8A 跨谱系谁高？  
4. 428 人年龄性别分布？随年龄哪些亚型比例变？  

**GRN**

1. FOXP3 的 eRegulon / 靶基因？  
2. B / NK 高质量 eRegulon 列表？  

**xQTL**

1. CDC42 的 cis-eQTL（按细胞类型）？  
2. 指定亚型的 cis-caQTL？  

**SMR**

1. CTLA4 / BLK / ORMDL3 等与免疫病性状关联？  

**CLM**

1. 跑 CIMA-CLM demo，出热图与折线图。  

**流水线**

1. paired_demo 全流程；或仅预处理+注释；或整合+metacell。  

---

## 六、与原稿差异说明

| 原稿内容 | 本整合稿处理 |
|----------|----------------|
| 场景 6 变异三库、场景 7 Ensembl | **删除**（非 CIMA 专家范围） |
| Skill 列表中 clinvar/dbsnp/…/scanpy-\* | **删除** |
| 门户统一叫 `cima` | 拆为 `cima-resource` + `cima-atlas-explore` |
| 「数据视图」 | 改为「谱系子集」并注明术语 |
| SMR 示例偏 ARL14EP/笼统 | 改为 CTLA4 等有疾病表命中的例子 |
| 流水线仅写到 scrna+annotation | 补全 ATAC / 多组学 / metacell / 配对 demo |
| 绝对机位路径 `/home/makailong/...` | 改为仓库相对路径 `skills/cima/` |

---

## 链接

- 门户：https://db.cngb.org/trueblood/cima/  
- 分类说明：[`skills/cima/README.md`](../README.md)  
- 推介短文：[`skills/cima/CIMA专家推介.md`](../CIMA专家推介.md)  
- 原稿：[`CIMA笔记——专家场景.md`](./CIMA笔记——专家场景.md)
