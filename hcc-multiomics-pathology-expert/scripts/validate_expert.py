#!/usr/bin/env python3
"""Validate the DCS Expert package without external dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("unterminated YAML frontmatter")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def parse_inline_list(value: str) -> list[str]:
    match = re.fullmatch(r"\[(.*)]", value.strip())
    if not match:
        raise ValueError("skills must use an inline YAML list")
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    soul = root / "SOUL.md"
    agents = root / "AGENTS.md"
    if not soul.exists():
        return ["missing SOUL.md"]
    if not agents.exists():
        errors.append("missing AGENTS.md")
    try:
        meta = frontmatter(soul)
    except ValueError as exc:
        return [f"SOUL.md: {exc}"]
    for field in ("name", "description", "skills"):
        if not meta.get(field):
            errors.append(f"SOUL.md: missing {field}")
    try:
        skills = parse_inline_list(meta.get("skills", ""))
    except ValueError as exc:
        errors.append(f"SOUL.md: {exc}")
        skills = []
    if len(skills) != len(set(skills)):
        errors.append("SOUL.md: duplicate skill name")
    actual = {path.name for path in root.iterdir() if path.is_dir() and path.name.startswith("hcc--")}
    if set(skills) != actual:
        errors.append(f"SOUL.md skills mismatch: listed={sorted(skills)} actual={sorted(actual)}")
    for skill in skills:
        skill_root = root / skill
        for required in ("SKILL.md", "usage-guide.md"):
            if not (skill_root / required).exists():
                errors.append(f"{skill}: missing {required}")
        skill_file = skill_root / "SKILL.md"
        if skill_file.exists():
            try:
                skill_meta = frontmatter(skill_file)
            except ValueError as exc:
                errors.append(f"{skill}/SKILL.md: {exc}")
                continue
            for field in ("name", "description"):
                if not skill_meta.get(field):
                    errors.append(f"{skill}/SKILL.md: missing {field}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        print("INVALID")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
