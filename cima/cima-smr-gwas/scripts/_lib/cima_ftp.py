"""Resolve CIMA tables: FTP/cache by default; use local only if already present."""
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
    """Return a readable table path for *key* (CSV or XLSX).

    Use local mirror only if present;
    otherwise (typical) download FTP into ~/.cache/cima-spatial/tables/.
    """
    if key not in FTP_TABLES:
        raise KeyError(f"Unknown table key: {key!r}")
    rel = FTP_TABLES[key]
    local = os.path.join(local_resource_root(), rel)
    if os.path.isfile(local) and os.path.getsize(local) > 0:
        return local

    cache = table_cache_dir()
    name = rel.replace("/", "__")
    dest = os.path.join(cache, name)
    # Older caches may store basename only (no xQTL__ prefix).
    alt = os.path.join(cache, os.path.basename(rel))
    for candidate in (dest, alt):
        if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
            return candidate

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


def load_table(path: str):
    """Load CSV or Excel SMR table into a DataFrame."""
    import pandas as pd

    lower = path.lower()
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    return pd.read_csv(path, low_memory=False)
