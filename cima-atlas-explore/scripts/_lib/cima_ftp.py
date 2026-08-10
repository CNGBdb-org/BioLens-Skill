"""Download and cache CIMA supplementary tables (FTP / GitHub)."""

from __future__ import annotations

import os
import ssl
import urllib.error
import urllib.parse
import urllib.request

import certifi

from cima_constants import FTP_BASE, FTP_TABLES, GITHUB_RESPONSE, GITHUB_TABLES

SSL = ssl.create_default_context(cafile=certifi.where())


def table_cache_dir() -> str:
    base = os.environ.get("CIMA_CACHE", os.path.expanduser("~/.cache/cima-spatial"))
    path = os.path.join(base, "tables")
    os.makedirs(path, exist_ok=True)
    return path


def _download(url: str, dest: str) -> str:
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        return dest
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "hesta-spatial-cima/1.0"})
    with urllib.request.urlopen(req, context=SSL, timeout=120) as resp:
        data = resp.read()
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dest)
    return dest


def fetch_ftp_table(key: str) -> str:
    rel = FTP_TABLES[key]
    name = rel.replace("/", "__")
    dest = os.path.join(table_cache_dir(), name)
    url = f"{FTP_BASE}/{rel}"
    try:
        return _download(url, dest)
    except urllib.error.HTTPError as e:
        raise FileNotFoundError(f"FTP table {key!r} ({url}): HTTP {e.code}") from e


def fetch_github_table(key: str) -> str:
    fname = GITHUB_TABLES[key]
    # ASCII-safe cache name (GitHub filenames may contain fullwidth ～)
    safe = fname.encode("ascii", "xmlcharrefreplace").decode("ascii")
    dest = os.path.join(table_cache_dir(), f"github__{safe}")
    # quote path segments so non-ASCII (e.g. ～ U+FF5E) survive urllib
    url = f"{GITHUB_RESPONSE}/{urllib.parse.quote(fname)}"
    try:
        return _download(url, dest)
    except urllib.error.HTTPError as e:
        raise FileNotFoundError(f"GitHub table {key!r} ({url}): HTTP {e.code}") from e


def iter_csv_chunks(path: str, *, chunksize: int = 200_000):
    import pandas as pd

    return pd.read_csv(path, chunksize=chunksize, low_memory=False)
