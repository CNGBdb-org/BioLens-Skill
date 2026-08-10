#!/usr/bin/env python3
"""CIMA skill CLI — run tools under scripts/."""

from __future__ import annotations

import os
import sys

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from atlas_runner import main  # noqa: E402


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
