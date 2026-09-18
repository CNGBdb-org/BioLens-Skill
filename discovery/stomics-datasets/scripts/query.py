#!/usr/bin/env python3
"""CNGB stomics-datasets CLI (multi-atlas discovery + explore).

  python ./scripts/query.py search --tissue Brain --limit 20
  python ./scripts/query.py --atlas STDS0000001 catalog list_datasets
  python ./scripts/query.py --atlas STDS0000001 spatial gene_expression <section> -g GENE --fast

Prefer dedicated skills hesta / mosta / cima when the user names those atlases.
"""

from __future__ import annotations

import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_SHARED_LIB = os.path.join(_DIR, "_shared", "lib", "scripts")
if _SHARED_LIB not in sys.path:
    sys.path.insert(0, _SHARED_LIB)

from atlas_runner import main  # noqa: E402

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
