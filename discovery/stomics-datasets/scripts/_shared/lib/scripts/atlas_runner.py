"""Unified script resolution for all STOmics atlases."""

from __future__ import annotations

import argparse
import os
import runpy
import sys

from atlas_registry import atlas_root, set_atlas, shared_root
from bootstrap import prepare_atlas_paths

ALIASES: dict[str, tuple[str, str]] = {
    "plot_celltype_mask": ("spatial", "plot_obs_mask"),
    "plot_annotation_mask": ("spatial", "plot_obs_mask"),
    "list_celltypes": ("markers", "list_obs_groups"),
    "list_annotations": ("markers", "list_obs_groups"),
    "search": ("catalog", "search_catalog"),
    "search_catalog": ("catalog", "search_catalog"),
}

# Prefer dedicated skills when these atlases are named explicitly by the user.
DEDICATED_ATLAS_SKILLS: dict[str, str] = {
    "hesta": "hesta",
    "mosta": "mosta",
    "cima": "cima",
}

SHARED_SCRIPTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("spatial", "plot_spatial_clusters"),
        ("spatial", "gene_expression"),
        ("spatial", "gene_summary"),
        ("spatial", "plot_spatial_gene"),
        ("spatial", "plot_spatial_qc"),
        ("spatial", "plot_spatial_batch"),
        ("spatial", "plot_obs_mask"),
        ("spatial", "list_markers"),
        ("markers", "compare_organs_gene"),
        ("markers", "list_obs_groups"),
        ("markers", "organ_overview"),
        ("markers", "top_genes_by_group"),
        ("cross-sample", "gene_across_samples"),
        ("cross-sample", "gene_presence"),
        ("catalog", "list_datasets"),
        ("catalog", "recommend_sample"),
        ("catalog", "dataset_info"),
        ("catalog", "filter_datasets"),
        ("catalog", "paper_to_samples"),
        ("catalog", "pseudobulk_design"),
        ("catalog", "search_catalog"),
        ("atlas-stats", "organ_stage_landscape"),
        ("susceptibility", "virus_receptor_map"),
        ("disease-genes", "disease_gene_map"),
        ("paper-markers", "paper_panel"),
    }
)


def resolve_script(atlas: str, module: str, name: str) -> tuple[str, str]:
    if name in ALIASES:
        module, name = ALIASES[name]
    root = atlas_root(atlas)
    if root:
        local = os.path.join(root, module, "scripts", f"{name}.py")
        if os.path.isfile(local):
            return root, f"{module}/scripts/{name}.py"
    if (module, name) in SHARED_SCRIPTS:
        return shared_root(), f"{module}/scripts/{name}.py"
    raise FileNotFoundError(f"No script {module}/{name} for atlas {atlas!r}")


def run_atlas_script(atlas: str, module: str, script: str, args: list[str]) -> None:
    key = (atlas or "").strip().lower()
    if key in DEDICATED_ATLAS_SKILLS:
        skill = DEDICATED_ATLAS_SKILLS[key]
        print(
            f"Note: atlas {key!r} has a dedicated skill `{skill}`. "
            f"Prefer that skill for deep exploration; continuing via stomics-datasets shared tools.",
            file=sys.stderr,
        )
    os.environ["STOMICS_ATLAS"] = atlas
    prepare_atlas_paths(atlas)
    root, rel = resolve_script(atlas, module, script)
    target = os.path.join(root, rel)
    sys.argv = [target] + args
    runpy.run_path(target, run_name="__main__")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        description="Run a STOmics atlas skill script (shared catalog/spatial tools).",
        epilog=(
            "Examples:\n"
            "  query.py search --tissue Brain --limit 20\n"
            "  query.py --atlas STDS0000001 catalog list_datasets\n"
            "  query.py --atlas STDS0000001 spatial gene_expression <section> -g GENE --fast\n"
            "Dedicated atlases: prefer skills hesta / mosta / cima when the user names them."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--atlas",
        "-a",
        required=False,
        metavar="NAME",
        help="Named atlas (hesta, mosta, …), STDS0000xxx, or SCDS0000xxx. Optional for module=search.",
    )
    p.add_argument("module", help="search | catalog | spatial | markers | …")
    p.add_argument("script", nargs="?", default=None, help="Script name without .py (omit for module=search)")
    p.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the target script")
    ns = p.parse_args(argv)

    module = ns.module
    script = ns.script
    args = list(ns.args or [])

    # Convenience: `query.py search --tissue Brain` → catalog/search_catalog
    if module in ("search", "search_catalog") and script and script.startswith("-"):
        args = [script, *args]
        script = "search_catalog"
        module = "catalog"
    elif module in ("search", "search_catalog") and script is None:
        module, script = "catalog", "search_catalog"
    elif module == "search" and script == "search_catalog":
        module = "catalog"
    elif script is None:
        p.error("script is required (unless module is search)")

    if module == "catalog" and script == "search_catalog":
        atlas = ns.atlas or "hesta"  # path bootstrap only; search ignores atlas scope unless --atlas passed to script
        run_atlas_script(atlas, module, script, args)
        return

    if not ns.atlas:
        p.error("--atlas/-a is required except for: search")

    try:
        set_atlas(ns.atlas)
    except ValueError as e:
        p.error(str(e))
    run_atlas_script(ns.atlas, module, script, args)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
