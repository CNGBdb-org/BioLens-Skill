# CIMA 免疫图谱专家：用问答打开中国人免疫多组学

> 面向产品推介 / 对内同步 / 对外简报。配套 Agent Skill 位于本仓库 `skills/cima/`。

---

## 一句话

把 [CIMA / TrueBlood](https://db.cngb.org/trueblood/cima/)（Chinese Immune Multi-Omics Atlas）收成一套 **Agent 专家 Skill**：用自然语言提问，即可完成图谱浏览、组成与衰老、调控与遗传查询，以及本地分析流水线。

文献：Yin et al., *Science* 2026；DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)

---

## 为什么做

CIMA 数据体量大（428 名中国成人 donor、千万级 PBMC、73 种 `cell_type_l4`），门户和 FTP 资源齐全，但日常使用仍常卡在：

- 「有哪些数据、文件在哪」说不清  
- 组成 / 年龄 / 性别 / 基因表达要会点门户或写脚本  
- GRN、xQTL、SMR 分表存放，问法不统一  
- 本地想跑一遍预处理 → 注释 → 多组学，门槛高  

这套专家把上述能力拆成可安装的 Skill，**按问题路由**，而不是让用户自己翻目录、记命令。

---

## 能问什么（示例）

### 资源与图谱

- CIMA 有哪些可下载数据？FTP 在哪？  
- 门户上可以探索哪些谱系子集（全血 PBMC、CD4T、CD8T、B、髓系、NK）？  
- 428 人队列的年龄、性别大概怎么分布？  

### 组成与衰老（对齐论文 Fig.2 叙事）

- B / NK 等子集里，各亚型大概占多少？  
- 随着年龄增长，哪些免疫亚型比例会升高或下降？按年龄段分层画图。  
- 男性和女性的免疫亚型组成有什么不同？  

### 基因表达

- 基因列表（如 MS4A1、CD8A、NKG7、LYZ、FOXP3、IKZF4、IL12B）在哪些细胞类型高表达？  
- 某基因在不同谱系子集里谁表达最高？  

### 调控与遗传

- Treg 关键因子 FOXP3 调控哪些下游基因？  
- 基因 CDC42 有没有 cis-eQTL？  
- 基因 CTLA4 在显著 SMR 里和哪些免疫相关疾病有关联？  

### 本地流水线（配对 demo）

用 `paired_demo_rna` / `paired_demo_atac` / `paired_demo_atac_gene` 可跑通：

scRNA 预处理与 L1–L4 注释 → pseudobulk → scATAC → 多组学标签迁移 → metacell 配对。

---

## Skill 分工（避免重叠）

| Skill | 用途 |
|-------|------|
| `cima-resource` | 数据清单与公开 FTP 位置 |
| `cima-atlas-explore` | 谱系子集浏览、donor、组成、基因 UMAP（不含 GRN/xQTL/SMR/清单） |
| `cima-scrna-preprocessing` | scRNA QC → 聚类 → 系群拆分 |
| `cima-cell-annotation` | TrueBlood L1–L4 marker 注释 |
| `cima-pseudobulk-variance` | Pseudobulk + age/sex 方差分解 |
| `cima-scratac-preprocessing` | scATAC 预处理（可选 gene activity） |
| `cima-multiomics-integration` | RNA→ATAC 标签迁移 |
| `cima-metacell` | Metacell 聚合与配对 |
| `cima-grn-scenicplus` | 预计算 eRegulon / GRN |
| `cima-xqtl` | 预计算 cis-xQTL |
| `cima-smr-gwas` | 预计算 SMR（含疾病性状表场景） |
| `cima-clm` | CIMA-CLM 变异效应 **预计算 demo** 可视化 |

同源门户探索代码亦保留在 `skills/single-cell/cima`（短名 `cima`）。  
`--category cima` 安装本目录叶子 Skill 即可部署到各类 Agent。

---

## 数据位置提示

本 Skill 包**不附带** CIMA Resource 本地数据。问「有哪些 / 在哪」时回答公开 FTP：

`https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/`

门户：https://db.cngb.org/trueblood/cima/resource  
大文件可用 RaySync：https://ftp.cngb.org/pub/course/tool/raysync/

---

## 一句话对外口径

> 覆盖图谱浏览、组成衰老、调控与遗传，再到本地分析流水线——让「读一篇 Science」变成「对着专家把问题问清楚」。

---

## 链接

- 门户：https://db.cngb.org/trueblood/cima/  
- 文献：https://doi.org/10.1126/science.adt3130  
- 本仓库 Skill：`skills/cima/`（说明见 [`README.md`](README.md)）
