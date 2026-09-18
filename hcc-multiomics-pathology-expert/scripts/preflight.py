#!/usr/bin/env python3
"""Report which HCC Expert capabilities can run in the current environment."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROFILES = {
    "core": ["numpy", "pandas", "scipy", "matplotlib", "h5py"],
    "spatial_bulk": ["anndata", "scanpy", "skimage", "statsmodels"],
    "pathology": ["PIL", "skimage", "openslide"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packages: dict[str, dict[str, object]] = {}
    for name in {item for names in PROFILES.values() for item in names}:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {name}"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode:
                raise RuntimeError((result.stderr or result.stdout).strip().splitlines()[-1])
            packages[name] = {"ready": True}
        except Exception as exc:  # Dependency imports may fail despite a discoverable module.
            packages[name] = {"ready": False, "error": f"{type(exc).__name__}: {exc}"}
    profiles = {
        name: {
            "ready": all(bool(packages[item]["ready"]) for item in names),
            "missing": [item for item in names if not bool(packages[item]["ready"])],
        }
        for name, names in PROFILES.items()
    }
    report = {"python": sys.version.split()[0], "packages": packages, "profiles": profiles}
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if profiles["core"]["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
