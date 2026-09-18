"""Path setup and shared-script launcher for STOmics atlas skills."""

from __future__ import annotations

import os
import runpy
import sys

from atlas_registry import (
    atlas_lib_dir,
    atlas_root,
    datasets_root,
    detect_atlas_from_path,
    set_atlas,
    shared_lib_dir,
    shared_root,
)


def prepare_atlas_paths(atlas: str | None = None) -> str:
    if atlas is None:
        atlas = os.environ.get("STOMICS_ATLAS", "").strip().lower() or None
    if not atlas:
        raise RuntimeError(
            "STOMICS_ATLAS not set; run via datasets/run.py --atlas <name> or prepare_atlas_paths('hesta')."
        )
    set_atlas(atlas)
    paths = [shared_lib_dir()]
    lib = atlas_lib_dir(atlas)
    if lib:
        paths.insert(0, lib)
    for path in paths:
        if path and path not in sys.path:
            sys.path.insert(0, path)
    return atlas


def run_shared_script(caller_file: str, relative_script: str, *, atlas: str | None = None) -> None:
    """Run _shared/<module>/scripts/<script>.py; atlas from caller path unless given."""
    caller_file = os.path.realpath(caller_file)
    if atlas is None:
        atlas = detect_atlas_from_path(caller_file)
    if not atlas:
        raise RuntimeError(f"Cannot detect atlas from path: {caller_file}")
    os.environ["STOMICS_ATLAS"] = atlas
    prepare_atlas_paths(atlas)
    target = os.path.join(shared_root(), relative_script)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"Shared script not found: {target}")
    runpy.run_path(target, run_name="__main__")


def atlas_module_scripts_dir(atlas: str, module: str) -> str:
    root = atlas_root(atlas) or os.path.join(datasets_root(), atlas)
    return os.path.join(root, module, "scripts")
