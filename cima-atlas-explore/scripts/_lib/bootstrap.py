"""Path setup for CIMA skill scripts."""

from __future__ import annotations

import os
import runpy
import sys

from atlas_registry import atlas_lib_dir, set_atlas, shared_lib_dir, shared_root


def prepare_atlas_paths(atlas: str | None = None) -> str:
    set_atlas("cima")
    for path in (shared_lib_dir(), atlas_lib_dir()):
        if path and path not in sys.path:
            sys.path.insert(0, path)
    return "cima"


def run_shared_script(caller_file: str, relative_script: str, *, atlas: str | None = None) -> None:
    prepare_atlas_paths("cima")
    target = os.path.join(shared_root(), relative_script)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"Script not found: {target}")
    runpy.run_path(target, run_name="__main__")


def atlas_module_scripts_dir(atlas: str, module: str) -> str:
    return os.path.join(shared_root(), module, "scripts")
