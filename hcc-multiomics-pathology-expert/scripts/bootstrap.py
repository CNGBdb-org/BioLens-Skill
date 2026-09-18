#!/usr/bin/env python3
"""Safely check or provision an isolated Python runtime for this Expert."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def profiles_to_install(profile: str) -> list[str]:
    if profile == "all":
        return ["core", "spatial_bulk", "pathology"]
    return ["core"] if profile == "core" else ["core", profile]


def load_requirement_profiles() -> dict[str, list[str]]:
    """Read the small fixed YAML schema without requiring PyYAML before installation."""
    profiles: dict[str, list[str]] = {}
    active_profile: str | None = None
    collecting_packages = False
    inside_profiles = False
    for raw_line in (ROOT / "requirements.yaml").read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line == "profiles:":
            inside_profiles = True
            active_profile = None
            collecting_packages = False
            continue
        if not raw_line.startswith(" "):
            inside_profiles = False
            active_profile = None
            collecting_packages = False
        if not inside_profiles:
            continue
        match = re.match(r"^  ([a-z_]+):$", raw_line)
        if match:
            active_profile = match.group(1)
            profiles[active_profile] = []
            collecting_packages = False
            continue
        if active_profile and raw_line == "    packages:":
            collecting_packages = True
            continue
        match = re.match(r"^      - (.+)$", raw_line)
        if active_profile and collecting_packages and match:
            profiles[active_profile].append(match.group(1).strip().strip('"\''))
            continue
        if not raw_line.startswith("      "):
            collecting_packages = False
    expected = {"core", "spatial_bulk", "pathology"}
    if set(profiles) != expected or any(not packages for packages in profiles.values()):
        raise SystemExit("requirements.yaml does not match the required profile schema.")
    return profiles


def run_preflight(python: Path, output: Path | None) -> int:
    command = [str(python), str(ROOT / "scripts" / "preflight.py")]
    if output:
        command.extend(["--output", str(output)])
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Install the selected profile into an isolated venv.")
    parser.add_argument("--profile", choices=["core", "spatial_bulk", "pathology", "all"], default="core")
    parser.add_argument("--yes", action="store_true", help="Required acknowledgement before package installation.")
    parser.add_argument("--venv", type=Path, default=Path.cwd() / ".hcc-expert-venv")
    parser.add_argument("--output", type=Path, help="Write the preflight report to this JSON path.")
    args = parser.parse_args()

    if not args.install:
        print("Dependency check only; no package installation will be performed.")
        return run_preflight(Path(sys.executable), args.output)
    if not args.yes:
        parser.error("Refusing installation without --yes. Explain the packages and obtain user confirmation first.")

    python = venv_python(args.venv)
    if not python.exists():
        print(f"Creating isolated environment: {args.venv}")
        result = subprocess.run([sys.executable, "-m", "venv", str(args.venv)], check=False)
        if result.returncode:
            return result.returncode
    pip_check = subprocess.run([str(python), "-m", "pip", "--version"], check=False)
    if pip_check.returncode:
        print("pip is unavailable in the isolated environment; ask the platform administrator to enable pip/ensurepip.", file=sys.stderr)
        return pip_check.returncode

    profiles = load_requirement_profiles()
    selected_profiles = profiles_to_install(args.profile)
    packages = list(dict.fromkeys(package for profile in selected_profiles for package in profiles[profile]))
    print(f"Installing profiles: {', '.join(selected_profiles)}")
    result = subprocess.run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check", *packages],
        check=False,
    )
    if result.returncode:
        print("Installation stopped before the selected profile was ready.", file=sys.stderr)
        return result.returncode
    return run_preflight(python, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
