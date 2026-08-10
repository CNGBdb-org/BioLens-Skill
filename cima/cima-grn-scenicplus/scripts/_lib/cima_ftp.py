"""Resolve CIMA tables: local deploy path first, then FTP cache."""
from __future__ import annotations

import os
import ssl
import urllib.error
import urllib.request

import certifi

from cima_constants import FTP_BASE, FTP_TABLES, local_resource_root

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
    req = urllib.request.Request(url, headers={"User-Agent": "cima-query-skill/1.0"})
    with urllib.request.urlopen(req, context=SSL, timeout=120) as resp:
        data = resp.read()
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dest)
    return dest


def fetch_ftp_table(key: str) -> str:
    """Return a readable CSV path for table *key*.

    Prefer local mirror under CIMA_RESOURCE_ROOT / DEFAULT_LOCAL_ROOT;
    otherwise download FTP into ~/.cache/cima-spatial/tables/.
    """
    if key not in FTP_TABLES:
        raise KeyError(f"Unknown table key: {key!r}")
    rel = FTP_TABLES[key]
    local = os.path.join(local_resource_root(), rel)
    if os.path.isfile(local) and os.path.getsize(local) > 0:
        return local

    name = rel.replace("/", "__")
    dest = os.path.join(table_cache_dir(), name)
    url = f"{FTP_BASE}/{rel}"
    try:
        return _download(url, dest)
    except urllib.error.HTTPError as e:
        raise FileNotFoundError(
            f"Table {key!r} not found locally ({local}) and FTP failed ({url}): HTTP {e.code}"
        ) from e
    except Exception as e:
        raise FileNotFoundError(
            f"Table {key!r} not found locally ({local}) and FTP failed ({url}): {e}"
        ) from e


def iter_csv_chunks(path: str, *, chunksize: int = 200_000):
    import pandas as pd

    return pd.read_csv(path, chunksize=chunksize, low_memory=False)
