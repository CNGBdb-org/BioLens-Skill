# 使用指南：证据报告

适用于“生成最终 HCC 分析报告”“给我一个结果导航页”。运行前收集 `analysis_manifest.json`、结构化结论与产物路径；输出 `RESULTS_INDEX.md`、`REPORT.md` 和 `report.json`。

```powershell
python examples/generate_research_report.py --task-dir <run> --evidence-synthesis <run>/evidence_synthesis.json --manifest-evaluation <run>/manifest_evaluation.json
python examples/build_results_index.py --task-dir <run>
```

审查状态为 `fail` 或 `not_reviewed` 时，报告只能交付数据事实、限制与下一步，不能交付确定性生物学结论。
