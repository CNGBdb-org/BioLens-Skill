"""Lazy import of CIMA catalog module."""

from __future__ import annotations

import cima_catalog as _cat


def __getattr__(name):
    return getattr(_cat, name)
