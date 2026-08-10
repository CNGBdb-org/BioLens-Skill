# CIMA笔记——专家场景

## 一、总体优势概述

### 1. 降低多组学分析门槛

传统 CIMA 多组学分析需要研究人员同时掌握单细胞 RNA-seq、scATAC-seq、QTL 分析、GWAS 整合、基因调控网络构建等多个领域，涉及 scanpy、SnapATAC2、SCENIC+、tensorQTL、SMR、PLINK、GCTA 等 10+ 工具链，安装配置动辄数天。CIMA 专家 Skills 将这些复杂流程封装为一句话触发的标准化能力：

*   用户只需用自然语言提问，Agent 自动路由到正确的 Skill 并执行
    
*   所有脚本参数使用 CIMA 原始论文的硬编码默认值，保证结果可复现
    
*   CPU 环境即可运行（无需 GPU），适配大多数实验室计算条件
    
*   环境依赖预装完毕（conda cima 环境），开箱即用
    

### 2. 千万级细胞图谱即时探索

CIMA 数据集包含 648 万 scRNA-seq + 376 万 scATAC-seq 细胞（共 1000 万+），总文件约 120GB。传统方式需要下载、加载、编写分析脚本才能查询，单次 UMAP 出图可能需要数小时。CIMA 门户 Skill（cima）通过预计算表和 FTP 缓存，实现：

*   428 名供体的临床元数据（年龄/性别/BMI）秒级查询
    
*   6 大免疫谱系（PBMC/CD4T/CD8T/B/Myeloid/NK）的细胞类型组成即时统计
    
*   基因跨谱系表达比较（如 CD8A 在 6 个视图中的表达差异）秒级返回
    
*   GRN（203 个 eRegulon）、xQTL（223,405 条关联）、SMR（13,826 条关联）预计算表即时查询
    

### 3. 从「重计算」到「即时查询」的范式转变

| 传统方式 | CIMA Skills 方式 |
| --- | --- |
| 下载 120GB h5ad → 加载到内存 → 编写 scanpy 脚本 → 等待计算 | 自然语言提问 → Agent 自动路由 → 秒级返回结果 |
| 安装 SCENIC+ + 配置 96 CPU 集群 → 跑 3 天 | 查询预计算 eRegulon 表 → 即时返回 TF→靶基因 |
| 安装 tensorQTL + PLINK + WGS 数据 → 跑数小时 | 查询预计算 xQTL 表 → 即时返回 lead 关联 |
| 安装 SMR + GCTA + GWAS 汇总数据 → 手动分析 | 查询预计算 SMR 表 → 即时返回因果关联 |
| 安装 Enformer + GPU → 跑数小时 | 运行 CLM demo → 秒级出图 |

### 4. 标准化与可复现

*   所有 Skill 遵循 Agent Skills 开放规范（agentskills.io）
    
*   每个参数使用 CIMA 原始脚本的硬编码值作为默认值
    
*   输出格式统一（表格 + 图文件路径 + provenance 注明数据源）
    
*   多 Agent 一致：同一套 Skill 可部署到 Cursor、Claude Code、Codex 等
    

### 5. 跨数据库知识编排

variant-interpretation Skill 实现了 dbsnp → gnomad → clinvar 的固定链路编排，一条命令完成变异的三库联合解读，用户无需分别查三个数据库再手动整合。

---

## 二、8 个演示场景

### 场景 1：免疫细胞图谱探索

展示 Skill： cima（门户探索）

优势：

*   无需下载 120GB 数据，通过预计算表和 FTP 缓存即时查询
    
*   428 名供体临床信息、6 大谱系细胞组成、基因跨谱系表达比较一问即答
    
*   降低单细胞数据探索门槛：不会编程的研究人员也能通过自然语言探索千万级细胞图谱
    

触发问题（演示用）：

1.  "CIMA 有哪些数据视图？" → 列出 6 个谱系视图
    
2.  "CIMA B 细胞视图有哪些亚型？各占多少比例？" → 10 个 B 细胞亚型及比例
    
3.  "CD8A 在不同免疫谱系中怎么表达？" → 跨 6 个视图的表达统计
    
4.  "CIMA 的供体有什么临床特征？" → 428 名供体的年龄/性别/BMI 分布
    

预期效果： 演示自然语言→Agent 自动识别 CIMA 关键词→路由到 cima skill→执行 query.py→返回表格结果。秒级响应。

---

### 场景 2：基因调控网络查询

展示 Skill： cima-grn-scenicplus

优势：

*   SCENIC+ 原始分析需要 96 CPU + 大量内存 + 数小时运行，Skill 查询预计算表秒级返回
    
*   203 个高质量 eRegulon 覆盖 68 种免疫细胞类型
    
*   支持按转录因子（TF）或靶基因查询，以及按谱系列出 regulon
    
*   自动标注调控区域坐标和相关性强度（R2G\_rho）
    

触发问题：

1.  "FOXP3 调控哪些靶基因？" → 返回 FOXP3 的 eRegulon（含 IL2RA、TIGIT 等已知靶点）
    
2.  "B 细胞有哪些 eRegulon？" → 列出 81 个 B 细胞高质量 regulon
    
3.  "NK 细胞的转录因子调控网络是什么？" → 列出 NK 谱系的 regulon
    

预期效果： 展示从 SCENIC+ 重计算（需 96 CPU）到预计算表查询（秒级）的范式转变。FOXP3→TIGIT 等经典免疫调控关系即时呈现。

---

### 场景 3：cis-xQTL 即时查询

展示 Skill： cima-xqtl

优势：

*   原始 tensorQTL 分析需要 WGS 数据 + PLINK + 数小时计算，Skill 查询预计算表秒级返回
    
*   223,405 条 lead 关联 × 69 种免疫细胞类型
    
*   支持按基因、变异、细胞类型、分析类型（cis-eQTL / cis-caQTL）多维过滤
    
*   降低遗传学分析门槛：不需要理解 QTL 分析流程即可获得关键变异-基因关联
    

触发问题：

1.  "CDC42 在哪些细胞类型有 eQTL？" → 返回跨 69 种细胞类型的 eQTL 结果
    
2.  "B 细胞中有哪些 cis-caQTL？" → 染色质可及性 QTL 查询
    

预期效果： 展示从 tensorQTL 重计算到预计算查询的转变。CDC42 在多种 T 细胞亚型中的 eQTL 关联秒级呈现，包含 p 值和效应大小。

---

### 场景 4：SMR 免疫疾病因果推断

展示 Skill： cima-smr-gwas

优势：

*   SMR 分析需要 SMR + GCTA + PLINK + GWAS 汇总数据 + 手动多步操作，Skill 一条命令完成
    
*   13,826 条 xQTL×GWAS 关联 × 40 种细胞类型
    
*   揭示变异→基因表达→疾病的因果链路（如 rs34415530→IKZF4→哮喘）
    
*   无需安装任何二进制工具，Python + pandas 即可查询
    

触发问题：

1.  "查询 IKZF4 的 SMR 关联" → 返回 IKZF4 与免疫疾病的因果关联
    
2.  "CD4 Treg 中哪些基因与疾病有因果关联？" → 按细胞类型过滤 SMR
    

预期效果： 展示「变异→基因→疾病」因果推断的一键化。传统需要数天搭建 SMR 环境，现在秒级返回结果。

---

### 场景 5：CIMA-CLM 变异效应可视化

展示 Skill： cima-clm

优势：

*   Enformer 原始推理需要 GPU + 模型权重 + 数小时，Demo 使用预计算结果秒级出图
    
*   生成热图、折线图、序列标识图（sequence logo）
    
*   展示 in silico mutagenesis 对基因表达的影响
    
*   无需 GPU，纯 CPU + matplotlib/seaborn 即可运行
    

触发问题：

1.  "帮我跑 CIMA-CLM 的变异效应 demo" → 自动加载预计算数据，生成热图+折线图
    
2.  "CLM demo 能做什么？" → 解释 in silico mutagenesis 可视化能力
    

预期效果： 秒级生成热图和折线图 PDF，展示非编码变异对基因表达的影响。对比 Enformer 原始推理（需 GPU），体现预计算的优势。

---

### 场景 6：变异综合解读（跨数据库编排）

展示 Skill： variant-interpretation（编排 dbsnp → gnomad → clinvar）

优势：

*   传统变异解读需要分别查 dbSNP（定位）、gnomAD（频率）、ClinVar（致病性），再手动整合
    
*   Skill 固定链路编排：一条命令完成三库联合查询
    
*   输出包含坐标、等位基因频率、临床意义、关联疾病、评审状态
    
*   附带免责声明，区分科研辅助与临床诊断
    

触发问题：

1.  "rs80357906 这个变异怎么看？" → 自动执行 dbsnp→gnomAD→ClinVar 三库查询
    
2.  "帮我综合解读 BRCA1 上的这个变异" → 同上
    

预期效果： 30 秒内返回完整变异解读报告（位置、频率、致病性、关联疾病）。展示多数据库编排能力。

---

### 场景 7：基因注释查询

展示 Skill： ensembl

优势：

*   直接对接 Ensembl REST API，无需安装任何工具
    
*   返回 Ensembl ID、坐标、转录本、生物类型等信息
    
*   与 clinvar/dbsnp/gnomad 联动：基因注释→变异查询→临床意义一站式
    

触发问题：

1.  "BRCA1 的 Ensembl ID 和坐标是什么？" → 返回 ENSG ID、chr17 坐标、转录本列表
    
2.  "TP53 在哪个染色体？" → 返回 chr17p13.1
    

预期效果： 秒级返回标准化的基因注释信息，可作为后续变异查询的入口。

---

### 场景 8：scRNA-seq 预处理流水线

展示 Skill： cima-scrna-preprocessing + cima-cell-annotation

优势：

*   将 CIMA 原始预处理脚本（分散在多个 notebook 中）封装为标准化命令行工具
    
*   全流程：QC → 双胞检测 → HVG → PCA → Harmony 批次校正 → UMAP → Leiden → 系群拆分
    
*   199 个参数全部暴露，默认值为 CIMA 原始论文值，保证可复现
    
*   CPU 环境即可运行（支持分层抽样控制内存）
    

触发问题：

1.  "帮我跑 CIMA 的 scRNA 预处理" → Agent 确认输入 h5ad 路径后执行
    
2.  "Pipeline 有哪些步骤？" → python3 cima\_pipeline.py --list
    

预期效果： 展示从原始 h5ad 到注释后分群结果的完整流水线。Pipeline Orchestrator 支持 dry-run 预览、步骤选择、状态恢复。

---

## 三、演示时的推荐问法顺序（5 分钟快速演示）

| 顺序 | 问法 | 展示什么 | 耗时 |
| --- | --- | --- | --- |
| 1 | "CIMA 有哪些数据视图？" | 门户 skill 即时返回 6 个谱系 | 3s |
| 2 | "CD8A 在不同免疫谱系中怎么表达？" | 跨谱系基因比较 | 5s |
| 3 | "FOXP3 调控哪些靶基因？" | GRN 预计算查询 | 3s |
| 4 | "CDC42 在哪些细胞类型有 eQTL？" | xQTL 预计算查询 | 5s |
| 5 | "rs80357906 这个变异怎么看？" | 跨数据库变异编排 | 15s |
| 6 | "帮我跑 CIMA-CLM 的变异效应 demo" | CLM demo 出图 | 10s |

总耗时约 45 秒，覆盖门户探索、GRN、xQTL、变异解读、CLM 五大核心能力。

---

## 四、已部署的 Skill 清单

| Skill | 类型 | 路径 |
| --- | --- | --- |
| cima | 门户探索 | /home/makailong/skills/main/cima/ |
| cima-scrna-preprocessing | 流水线 L5 | /home/makailong/skills/main/cima-scrna-preprocessing/ |
| cima-cell-annotation | 流水线 L5 | /home/makailong/skills/main/cima-cell-annotation/ |
| cima-pseudobulk-variance | 流水线 L5 | /home/makailong/skills/main/cima-pseudobulk-variance/ |
| cima-scratac-preprocessing | 流水线 L5 | /home/makailong/skills/main/cima-scratac-preprocessing/ |
| cima-multiomics-integration | 流水线 L5 | /home/makailong/skills/main/cima-multiomics-integration/ |
| cima-metacell | 流水线 L5 | /home/makailong/skills/main/cima-metacell/ |
| cima-grn-scenicplus | 预计算查询 L4 | /home/makailong/skills/main/cima-grn-scenicplus/ |
| cima-xqtl | 预计算查询 L4 | /home/makailong/skills/main/cima-xqtl/ |
| cima-smr-gwas | 预计算查询 L4 | /home/makailong/skills/main/cima-smr-gwas/ |
| cima-clm | Demo L5 | /home/makailong/skills/main/cima-clm/ |
| variant-interpretation | 跨库编排 L4 | /home/makailong/skills/main/variant-interpretation/ |
| clinvar | 域级 L4 | /home/makailong/skills/main/clinvar/ |
| dbsnp | 域级 L4 | /home/makailong/skills/main/dbsnp/ |
| gnomad | 域级 L4 | /home/makailong/skills/main/gnomad/ |
| ensembl | 域级 L2-L4 | /home/makailong/skills/main/ensembl/ |
| go | 域级 L2 | /home/makailong/skills/main/go/ |
| kegg | 域级 L2 | /home/makailong/skills/main/kegg/ |
| uniprot | 域级 L2 | /home/makailong/skills/main/uniprot/ |
| scanpy-qc | 域级 L5 | /home/makailong/skills/main/scanpy-qc/ |
| scanpy-preprocess | 域级 L5 | /home/makailong/skills/main/scanpy-preprocess/ |
| scanpy-cluster | 域级 L5 | /home/makailong/skills/main/scanpy-cluster/ |
| scanpy-markers | 域级 L5 | /home/makailong/skills/main/scanpy-markers/ |

## 四、场景问题示例

场景 1：免疫细胞图谱探索

1.  CIMA 有哪些数据视图？每个视图有多少细胞？
    
2.  CD8A 在不同免疫谱系中怎么表达？哪个谱系最高？
    
3.  CIMA 的 428 名供体年龄和性别分布是怎样的？
    

场景 2：基因调控网络查询

1.  FOXP3 调控哪些靶基因？列出 eRegulon 信息
    
2.  B 细胞有哪些高质量 eRegulon？按活性排序
    
3.  NK 细胞的转录因子调控网络是什么样的？
    

场景 3：cis-xQTL 即时查询

1.  CDC42 在哪些免疫细胞类型中有 eQTL 关联？
    
2.  B 细胞中有哪些 cis-caQTL？列出前 20 个
    
3.  rs34415530 这个变异在哪些细胞类型有 cis-xQTL？
    

场景 4：SMR 免疫疾病因果推断

1.  IKZF4 的表达与哪些疾病有因果关联？通过哪个细胞类型介导？
    
2.  CD4 FOXP3 调节性 T 细胞中哪些基因与疾病有 SMR 因果关联？
    
3.  哮喘相关的 SMR 多效性关联有哪些？列出 top 10
    

场景 5：CIMA-CLM 变异效应可视化

1.  帮我跑 CIMA-CLM 的变异效应 demo，生成热图和折线图
    
2.  CIMA-CLM 的 in silico mutagenesis 对 CD14 基因表达有什么影响？
    
3.  CLM demo 里 Switched Bm 细胞的变异效应结果看一下
    

场景 6：变异综合解读（跨数据库编排）

1.  rs80357906 这个变异怎么看？帮我做完整解读
    
2.  BRCA1 基因上 rsID rs80357906 的致病性和人群频率是多少？
    
3.  帮我用三库联合解读 rs34415530 这个变异
    

场景 7：基因注释查询

1.  BRCA1 的 Ensembl ID 和染色体坐标是什么？有哪些转录本？
    
2.  TP53 在哪个染色体上？给我它的 Ensembl 注释信息
    
3.  CD4 基因的 Ensembl ID 是什么？蛋白编码区有多长？
    

场景 8：scRNA-seq 预处理流水线

1.  我有一个 10x 的 h5ad 文件在 `++/work/makailong/data/sample.h5ad++`，帮我跑 CIMA 的 scRNA 预处理全流程
    
2.  Pipeline 有哪些步骤？先 dry-run 看看
    
3.  帮我只跑预处理和细胞注释两步，跳过后面的