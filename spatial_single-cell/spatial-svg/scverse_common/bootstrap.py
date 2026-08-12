#!/usr/bin/env python3
"""Path bootstrap: allow `from scverse_common ...` when run from skill scripts."""

from __future__ import annotations

import sys
from pathlib import Path


def repo_root() -> Path:
    # skill/scripts/query.py -> skill -> repo
    return Path(__file__).resolve().parents[2]


def ensure_path() -> Path:
    root = repo_root()
    # When copied under .cursor/skills/<name>/scripts/, parents[2] is .cursor/skills
    # Prefer walking up until scverse_common is found.
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "scverse_common").is_dir():
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
            return p
        # .cursor/skills/<skill>/scripts -> repo root is parents[3]
        if (p / ".." / ".." / ".." / "scverse_common").resolve().is_dir():
            root2 = (p / ".." / ".." / "..").resolve()
            if str(root2) not in sys.path:
                sys.path.insert(0, str(root2))
            return root2
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root
