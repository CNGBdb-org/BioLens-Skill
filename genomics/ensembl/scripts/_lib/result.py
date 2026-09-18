"""Unified JSON envelope for portable skill scripts (cngbdb.skill-result.v2)."""

from __future__ import annotations

import json
from typing import Any


def envelope(
    *,
    source: str,
    mode: str,
    ok: bool = True,
    label: str | None = None,
    total: int | None = None,
    returned: int | None = None,
    truncated: bool | None = None,
    records: list[Any] | None = None,
    record: dict[str, Any] | None = None,
    message: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": ok,
        "source": source,
        "mode": mode,
        "schema": "cngbdb.skill-result.v2",
    }
    if label is not None:
        out["label"] = label
    if total is not None:
        out["total"] = total
    if returned is not None:
        out["returned"] = returned
    if truncated is None and total is not None and returned is not None:
        truncated = returned < total
    if truncated is not None:
        out["truncated"] = truncated
    if records is not None:
        out["records"] = records
    if record is not None:
        out["record"] = record
    if message is not None:
        out["message"] = message
    if extra:
        out.update(extra)
    return out


def emit_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False))
