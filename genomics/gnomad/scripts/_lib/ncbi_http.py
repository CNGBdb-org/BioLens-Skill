"""NCBI / generic HTTP with API key, retry, and backoff."""

from __future__ import annotations

import os
import time
from typing import Any

import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
VARIATION_V0 = "https://api.ncbi.nlm.nih.gov/variation/v0"


def ncbi_api_key() -> str | None:
    key = os.environ.get("NCBI_API_KEY") or os.environ.get("NCBI_KEY")
    return key.strip() if key else None


def request_delay() -> float:
    return 0.12 if ncbi_api_key() else 0.34


def _with_api_key(url: str, params: dict[str, Any]) -> dict[str, Any]:
    key = ncbi_api_key()
    if key and (
        "api.ncbi.nlm.nih.gov" in url or "eutils.ncbi.nlm.nih.gov" in url
    ):
        params = dict(params)
        params.setdefault("api_key", key)
    return params


def http_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
    retries: int = 3,
    allow_404: bool = False,
) -> requests.Response:
    params = _with_api_key(url, dict(params or {}))
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 404 and allow_404:
                return r
            if r.status_code == 429 and attempt < retries:
                time.sleep(2 ** attempt + 1)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(2 ** attempt + 0.5)
                continue
            raise
    assert last_exc is not None
    raise last_exc


def eutils_get(path: str, params: dict[str, Any], *, timeout: int = 30) -> dict:
    r = http_get(f"{EUTILS}/{path}", params=params, timeout=timeout)
    return r.json()


def variation_get(path: str, *, timeout: int = 30) -> dict | None:
    r = http_get(
        f"{VARIATION_V0}/{path.lstrip('/')}",
        timeout=timeout,
        allow_404=True,
    )
    if r.status_code == 404:
        return None
    return r.json()
