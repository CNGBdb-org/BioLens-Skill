"""Locate peer skill directories (for orchestration)."""

from __future__ import annotations

from pathlib import Path

# Stop climbing once we hit these skill-container names.
_STOP_NAMES = frozenset(
    {
        "skills",
        ".cursor",
        ".claude",
        ".agents",
        ".codex",
        ".gemini",
        ".windsurf",
        ".continue",
    }
)


def find_skill_dir(name: str, start: Path | None = None) -> Path | None:
    """Find a sibling or nearby skill by leaf name (e.g. dbsnp).

    Supports:
    - category layout: skills/genomics/<name>
    - flat Agent install: .cursor/skills/<name>
    """
    here = (start or Path(__file__)).resolve()
    if here.is_file():
        here = here.parent
    # scripts/_lib -> scripts -> skill dir
    skill_dir = here.parent if here.name == "_lib" else here
    if skill_dir.name == "scripts":
        skill_dir = skill_dir.parent

    seen: set[Path] = set()
    candidates: list[Path] = []

    def add(p: Path) -> None:
        try:
            ap = p.resolve()
        except OSError:
            return
        if ap in seen:
            return
        seen.add(ap)
        candidates.append(ap)

    # Same category sibling first (skills/genomics/dbsnp)
    add(skill_dir.parent / name)

    for root in [skill_dir.parent, *skill_dir.parents]:
        # Never scan filesystem root (macOS Path.glob('/') can raise Errno 22)
        if root == Path("/") or len(root.parts) <= 1:
            break
        add(root / name)
        try:
            for p in root.glob(f"*/{name}"):
                add(p)
        except OSError:
            pass
        if root.name in _STOP_NAMES:
            break
        if (root / "requirements.txt").is_file() and (root / "CATALOG.md").is_file():
            break
        if len(candidates) > 40:
            break

    for p in candidates:
        if (p / "scripts" / "query.py").is_file():
            return p
    return None
