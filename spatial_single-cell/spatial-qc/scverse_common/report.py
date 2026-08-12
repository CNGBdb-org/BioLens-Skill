"""Output directory + markdown report helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def ensure_outdir(path: str | Path | None, prefix: str) -> Path:
    if path:
        out = Path(path)
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = Path("out") / f"{prefix}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    (out / "tables").mkdir(exist_ok=True)
    return out


def write_report(outdir: Path, title: str, lines: list[str]) -> Path:
    path = outdir / "report.md"
    body = [f"# {title}", "", *lines, ""]
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def print_header(skill: str, msg: str) -> None:
    print(f"【{skill}】{msg}")
