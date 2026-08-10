# CIMA 专家

面向 Chinese Immune Multi-Omics Atlas 的 Agent Skills 能力说明与使用场景。

文献：Yin et al., *Science* 2026；DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)  
门户：https://db.cngb.org/trueblood/cima/

---

## CIMA 专家是什么

**CIMA 专家**是围绕 [Chinese Immune Multi-Omics Atlas（CIMA / TrueBlood）](https://db.cngb.org/trueblood/cima/) 的一组 Agent Skills：用自然语言提问，即可完成免疫图谱浏览、组成与衰老相关统计、基因调控与遗传关联查询，以及本地 scRNA / scATAC 分析流水线。

CIMA 基于 428 名中国成人、千万级外周血免疫细胞的多组学图谱（scRNA + scATAC），并发布 GRN、xQTL、SMR 等预计算结果。本专家将能力分为两条主线：一是查询已发布的图谱与预计算表；二是在示例数据或自有 h5ad 上跑通分析流程，降低使用门槛，并与论文及门户资源保持对应。

能力覆盖：数据与路径说明、谱系子集探索、细胞组成与年龄/性别分层、基因表达、eRegulon、cis-xQTL、SMR 性状关联、CIMA-CLM 预计算变异效应可视化，以及从预处理到 metacell 的 CPU 流水线。

---

## 一、总体优势

### 1. 降低多组学分析门槛

传统 CIMA 多组学需同时掌握 scRNA、scATAC、QTL、GWAS 整合、GRN 等，工具链长（scanpy、SnapATAC2、SCENIC+、tensorQTL、SMR…）。CIMA 专家 Skills 封装为自然语言可触发的能力：

- Agent 按问题自动路由到对应 Skill  
- 参数默认对齐论文流程，便于复现  
- 流水线以 **CPU** 为主路径，适配常见实验室环境  

### 2. 千万级细胞图谱即时探索

CIMA 数据集包含 648 万 scRNA-seq + 376 万 scATAC-seq 细胞（共 1000 万+），总文件约 120GB。传统方式需要下载、加载、编写分析脚本才能查询，单次 UMAP 出图可能需要数小时。CIMA 专家通过预计算表和 FTP / 本地缓存，实现：

- 428 名供体的临床元数据（年龄/性别/BMI）秒级查询  
- 6 大免疫谱系（PBMC / CD4T / CD8T / B / Myeloid / NK）的细胞类型组成即时统计  
- 基因跨谱系表达比较（如 CD8A 在各谱系子集中的表达差异）秒级返回  
- GRN（203 个 eRegulon）、xQTL（223,405 条关联）、SMR（13,826 条关联）预计算表即时查询  

### 3. 从「重计算」到「即时查询」

| 传统方式 | CIMA Skills |
|----------|-------------|
| 下载百 GB h5ad → 写脚本 → 久等 | 自然语言 → 路由 → 预计算/缓存返回 |
| SCENIC+ 集群重跑数天 | 查 eRegulon 预计算表 |
| tensorQTL + WGS 数小时 | 查 lead xQTL 表 |
| SMR + GCTA + GWAS 手工多步 | 查 SMR / 疾病性状表 |
| Enformer + GPU 推理 | 基于预计算的 CLM 结果出图 |

### 4. 标准化与可复现

- 遵循 Agent Skills 规范，可部署到多种 Agent  
- 输出统一：表格 / 图路径 / 数据源说明  
- 部署环境优先读取本地 CIMA Resource  

---

## 二、Skill 清单

下列 Skill 共同构成 CIMA 专家能力（安装后为可独立调用的叶子目录）。

| Skill | 类型 | 用途 |
|-------|------|------|
| `cima-resource` | 资源 | 可下载数据清单、本地 / FTP 路径 |
| `cima-atlas-explore` | 图谱浏览 | 谱系子集、donor、组成、基因 UMAP（不含 GRN / xQTL / SMR） |
| `cima-scrna-preprocessing` | 分析流水线 | scRNA QC → 聚类 → 系群拆分 |
| `cima-cell-annotation` | 分析流水线 | TrueBlood L1–L4 marker 注释 |
| `cima-pseudobulk-variance` | 分析流水线 | Pseudobulk + age/sex 方差 |
| `cima-scratac-preprocessing` | 分析流水线 | scATAC + 可选 gene activity |
| `cima-multiomics-integration` | 分析流水线 | RNA → ATAC 标签迁移 |
| `cima-metacell` | 分析流水线 | Metacell 聚合与配对 |
| `cima-grn-scenicplus` | 预计算查询 | eRegulon / GRN |
| `cima-xqtl` | 预计算查询 | cis-eQTL / cis-caQTL |
| `cima-smr-gwas` | 预计算查询 | SMR；疾病性状场景请用显著关联表 |
| `cima-clm` | 预计算可视化 | CIMA-CLM 变异效应热图 / 折线等 |

---

## 三、使用场景

### 场景 A：资源与谱系图谱探索

**Skill：** `cima-resource` + `cima-atlas-explore`

**能做什么：** 无需先下载全量 h5ad，即可查询数据清单、供体信息、细胞组成与基因表达。

**可以这样问：**

1. CIMA 有哪些可下载数据？本地路径在哪？  
2. 可以探索哪些谱系子集（PBMC / CD4T / CD8T / B / Myeloid / NK）？  
3. CIMA B 细胞子集有哪些亚型？各占多少比例？  
4. CD8A 在不同免疫谱系里怎么表达？哪个更高？  
5. 428 名供体年龄和性别分布怎样？  
6. 在 B 细胞谱系里，随年龄增长哪些亚型比例升/降？按年龄段分层画图。  
7. 基因列表 MS4A1、CD8A、NKG7、LYZ、FOXP3、IKZF4、IL12B 在哪些细胞类型高表达？  

**响应量级：** 多数为秒级至分钟级；全量 PBMCs UMAP 出图慢一些。

---

### 场景 B：基因调控网络（GRN）

**Skill：** `cima-grn-scenicplus`

**能做什么：** 无需重跑 SCENIC+；可按转录因子、靶基因或谱系列出 eRegulon。

**可以这样问：**

1. Treg 转录因子 FOXP3 调控哪些下游基因？  
2. B 细胞有哪些高质量 eRegulon？  
3. NK 谱系的转录因子调控网络有哪些 regulon？  

**响应量级：** 预计算表查询，通常为秒级（首次拉取表除外）。

---

### 场景 C：cis-xQTL

**Skill：** `cima-xqtl`

**能做什么：** 无需本地 tensorQTL 与全基因组测序重算；可按基因、变异、细胞类型，以及 eQTL / caQTL 过滤查询。

**可以这样问：**

1. 基因 CDC42 在 CIMA 里有没有 cis-eQTL？在哪些细胞类型？  
2. Bn_TCL1A（或 B 相关亚型）里有哪些 cis-caQTL？  
3. 某 variant（如 chr12_56050848）影响哪个基因？  

**响应量级：** 通常秒级返回 lead 关联（含 p 值、效应等）。

---

### 场景 D：SMR 与免疫相关性状

**Skill：** `cima-smr-gwas`

**能做什么：** 无需本地搭建 SMR / GCTA 工具链；可查询基因与免疫相关疾病 / 性状的显著 SMR 关联。查询疾病性状时，请使用显著关联表中有记录的基因（例如 CTLA4、BLK、ORMDL3）。

**可以这样问：**

1. 基因 **CTLA4** 在 CIMA 显著 SMR 里和哪些免疫相关疾病有关联？  
2. 基因 **BLK** 和类风湿关节炎（RA）有没有 SMR 关联？  
3. 基因 **ORMDL3** 和哮喘（As）有没有显著 SMR 关联？  

> 结果为统计关联 / SMR 证据，不能替代临床诊断。

**响应量级：** 通常为秒级。

---

### 场景 E：CIMA-CLM 变异效应可视化

**Skill：** `cima-clm`

**能做什么：** 基于预计算的 in silico mutagenesis 结果生成热图、折线与 logo，无需现场 GPU / Enformer 推理。

**可以这样问：**

1. 帮我运行 CIMA-CLM 变异效应分析，生成热图和折线图。  
2. CIMA-CLM 能做什么？预计算结果的边界是什么？  

**数据前提：** 需提供 `CIMA-CLM_Demo` 目录，或设置环境变量 `CIMA_CLM_DEMO`。

---

### 场景 F：本地分析流水线

**Skill：**  
`cima-scrna-preprocessing` → `cima-cell-annotation` →（可选）`cima-pseudobulk-variance`  
→ `cima-scratac-preprocessing` → `cima-multiomics-integration` → `cima-metacell`

**能做什么：** 按论文向流程在 CPU 上完成预处理、注释、多组学整合与 metacell。可使用配套示例数据（`paired_demo_rna` / `paired_demo_atac` / `paired_demo_atac_gene`），或替换为自有 h5ad。

**可以这样问：**

1. 用配对示例数据按 CIMA 流程依次做预处理、L1–L4 注释、pseudobulk、scATAC、多组学整合、metacell 配对。  
2. 只用 RNA 示例数据跑 scRNA 预处理 + L1–L4 注释。  
3. 已有预处理后的 RNA 与 gene-level ATAC，做多组学标签迁移再 metacell，并报告配对对数。  

**响应量级：** 通常为数分钟级；结果可关注 `Pseudo_multiomics_barcode_info.csv` 与 metacell h5ad 规模。

---

## 四、问题速查

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

1. 运行 CIMA-CLM，生成热图与折线图。  

**流水线**

1. 配对示例数据全流程；或仅预处理 + 注释；或整合 + metacell。  

---

## 相关链接

- CIMA 门户：https://db.cngb.org/trueblood/cima/  
- 文献 DOI：https://doi.org/10.1126/science.adt3130  
