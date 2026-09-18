# 使用指南：bulk RNA

适用于“比较 HCC 队列通路”“把 RNA 通路与病理特征关联”。先检查 manifest 的 `tissue_role`、`etiology` 和 `background_liver`；癌旁与肿瘤的比较必须将背景肝混杂写入报告。

基础通路评分使用一个透明、内置的小型 HCC/TME 基因集：

```powershell
python examples/score_hcc_bulk_pathways.py --expression <gene-by-sample.tsv> --input-scale counts --output <run>/bulk
```

第一列必须为唯一 gene symbol，其余列为样本；`counts` 会转为 `log1p(CP10K)`，`normalized` 则按输入原样评分。输出不包含组间显著性或临床预测；后续比较须由统计审查 Skill 读取 manifest 后单独执行。
