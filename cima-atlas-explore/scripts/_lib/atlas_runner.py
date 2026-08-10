"""CIMA script resolver and CLI helpers."""

from __future__ import annotations

import argparse
import os
import runpy
import sys

from atlas_registry import set_atlas, shared_root
from bootstrap import prepare_atlas_paths

ALIASES: dict[str, tuple[str, str]] = {
    "plot_celltype_mask": ("spatial", "plot_obs_mask"),
    "list_celltypes": ("markers", "list_obs_groups"),
    "gene_umap": ("spatial", "gene_expression"),
}


def resolve_script(module: str, name: str) -> str:
    if name in ALIASES:
        module, name = ALIASES[name]
    path = os.path.join(shared_root(), module, "scripts", f"{name}.py")
    if os.path.isfile(path):
        return path
    raise FileNotFoundError(f"No script {module}/{name} (expected {path})")


BLOCKED_MODULES: dict[str, str] = {
    "grn": "cima-grn-scenicplus",
    "xqtl": "cima-xqtl",
    "immune-disease": "cima-smr-gwas",
}


def run_cima_script(module: str, script: str, args: list[str]) -> None:
    if module in BLOCKED_MODULES:
        skill = BLOCKED_MODULES[module]
        raise SystemExit(
            f"Module {module!r} is not part of cima-atlas-explore. "
            f"Use skill {skill!r} instead (dedicated query skill)."
        )
    os.environ["STOMICS_ATLAS"] = "cima"
    prepare_atlas_paths("cima")
    set_atlas("cima")
    target = resolve_script(module, script)
    sys.argv = [target, *args]
    runpy.run_path(target, run_name="__main__")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        description="Run a CIMA skill script.",
        epilog="Example: query.py spatial gene_expression B -g CD8A --fast",
    )
    p.add_argument(
        "module",
        help=(
            "catalog | clinical | composition | spatial | markers | cross-view | "
            "paper-markers | atlas-stats"
        ),
    )
    p.add_argument("script", help="Script name without .py")
    p.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the target script")
    ns = p.parse_args(argv)
    run_cima_script(ns.module, ns.script, ns.args)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
