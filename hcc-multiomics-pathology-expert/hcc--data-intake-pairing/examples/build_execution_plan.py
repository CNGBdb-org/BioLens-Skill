#!/usr/bin/env python3
"""Translate a capability plan into an auditable, non-executing analysis plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STEPS = {
    "pathology_qc": {"skill": "hcc--pathology-qc-evidence", "depends_on": ["data_intake"], "entrypoints": ["examples/run_he_qc.py", "examples/tile_he_image.py"]},
    "spatial_tme": {"skill": "hcc--spatial-tme-analysis", "depends_on": ["data_intake"], "entrypoints": ["examples/run_visium_qc.py", "examples/analyze_spatial_domains.py"]},
    "bulk_pathway": {"skill": "hcc--bulk-pathway-analysis", "depends_on": ["data_intake"], "entrypoints": ["examples/score_hcc_bulk_pathways.py"]},
    "scrna_handoff": {"skill": "hcc--scrna-coordination", "depends_on": ["data_intake"], "manual_handoff": True},
    "multimodal_association": {"skill": "hcc--multimodal-association", "depends_on": ["pathology_qc", "spatial_tme", "bulk_pathway"], "entrypoints": ["examples/link_visium_spots_to_he_tiles.py"]},
    "statistical_review": {"skill": "hcc--statistical-evidence-review", "depends_on": []},
    "reporting": {"skill": "hcc--evidence-reporting", "depends_on": ["statistical_review"], "entrypoints": ["examples/generate_research_report.py", "examples/build_results_index.py"]},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capability-plan", required=True, type=Path)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--selected", default="all", help="Comma-separated capability names, or all")
    args = parser.parse_args()
    capability = json.loads(args.capability_plan.read_text(encoding="utf-8"))
    available = capability.get("capabilities", {})
    wanted = set(STEPS) if args.selected == "all" else {item.strip() for item in args.selected.split(",") if item.strip()}
    unknown = wanted - set(STEPS)
    if unknown:
        raise SystemExit(f"unknown selected steps: {sorted(unknown)}")
    steps = []
    for name, config in STEPS.items():
        if name not in wanted:
            continue
        state = available.get(name, "ready")
        reason = ""
        if name == "multimodal_association":
            ready_modalities = sum(available.get(item) == "ready" for item in ("pathology_qc", "spatial_tme", "bulk_pathway"))
            if ready_modalities < 2:
                state = "blocked"
                reason = "at least two locally paired analysis modalities are required"
        if state == "blocked":
            steps.append({"id": name, "state": "blocked", "reason": reason or "input or environment capability is unavailable", **config})
        elif state == "requires_handoff":
            steps.append({"id": name, "state": "manual_handoff_required", "reason": "switch to scrna-seq-expert and return a validated result", **config})
        else:
            steps.append({"id": name, "state": "awaiting_confirmation", **config})
    args.task_dir.mkdir(parents=True, exist_ok=True)
    execution = {"status": "awaiting_confirmation", "steps": steps, "source_capability_plan": str(args.capability_plan)}
    state = {"status": "awaiting_confirmation", "completed": [], "blocked": [step["id"] for step in steps if step["state"] == "blocked"], "pending_confirmation": [step["id"] for step in steps if step["state"] == "awaiting_confirmation"]}
    (args.task_dir / "execution_plan.json").write_text(json.dumps(execution, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.task_dir / "analysis_state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.task_dir / "execution_plan.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
