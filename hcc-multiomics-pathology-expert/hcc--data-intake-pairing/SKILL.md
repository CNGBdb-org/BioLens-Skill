---
name: hcc-data-intake-pairing
description: Inspect and normalize HCC pathology, spatial, single-cell, bulk RNA, and clinical inputs into a patient-aware manifest. Use when starting an HCC multi-omics analysis, checking files, or determining whether modalities can be paired.
tool_type: python
primary_tool: Python standard library
---

# HCC 数据接入与配对

先运行 `examples/inspect_manifest.py`。它只读取 manifest，输出机器可读能力计划和用户可读报告。随后运行 `examples/build_execution_plan.py`，把确认前的执行顺序、阻断项和人工单细胞交接写入任务目录。

要求 `sample_manifest.tsv` 有 `patient_id`、`sample_id`、`modality`、`disease`、`tissue_role`、`input_path`。接受的 `pairing_level` 仅见根目录 v2 计划；缺失时保守标为 `cross_cohort_reference`。

拒绝或降级以下情况：非 HCC、把 `adjacent` 写为健康、同患者即声称同组织块、路径不存在、缺少患者 ID 的患者间统计。用 `capability_plan.json` 的 `ready`、`ready_with_limitations`、`requires_handoff`、`blocked` 表达状态，报告与 JSON 必须一致。

运行前用根目录 `scripts/preflight.py` 检查 core、spatial_bulk 和 pathology 依赖；缺包时只关闭受影响分支，不把它误报成用户数据缺失。参见 `usage-guide.md` 的输入例子和命令行参数。
