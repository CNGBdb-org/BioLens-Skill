"""Donor-level metadata from CIMA explore obs."""

from __future__ import annotations

from collections import Counter

from io_core import load_obs_column, validate_dataset_dir

from cima_constants import CLINICAL_COLS, DEFAULT_VIEW


def load_donor_table_from_ftp() -> list[dict]:
    """428 donor cohort table from cached FTP metadata (no h5ad scan)."""
    import pandas as pd

    from cima_ftp import fetch_ftp_table

    path = fetch_ftp_table("sample_metadata")
    df = pd.read_csv(path)
    ftp_to_clinical = {
        "Age": "age",
        "sex": "sex",
        "BMI": "BMI",
        "height": "height",
        "weight": "weight",
        "blood_type": "blood_type",
        "BMI_group": "BMI_group",
    }
    out: list[dict] = []
    for _, row in df.iterrows():
        sample = str(row.get("Sample_name") or "").strip()
        if not sample:
            continue
        rec: dict = {"sample": sample, "n_cells": 0}
        for ftp_col, name in ftp_to_clinical.items():
            if ftp_col not in df.columns:
                continue
            val = row.get(ftp_col)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                continue
            rec[name] = val
        if "age" in rec:
            out.append(rec)
    return sorted(out, key=lambda x: x["sample"])


def load_donor_table(view: str = DEFAULT_VIEW, *, fast: bool = False) -> list[dict]:
    """One row per unique obs.sample with clinical fields."""
    if fast:
        return load_donor_table_from_ftp()
    ds = validate_dataset_dir(view)
    samples = load_obs_column(ds, "sample")
    cols = {}
    for name in CLINICAL_COLS:
        try:
            cols[name] = load_obs_column(ds, name)
        except FileNotFoundError:
            continue
    if "age" not in cols:
        raise FileNotFoundError(f"No sample/age obs in view {view!r}")

    donor: dict[str, dict] = {}
    n_cells = Counter()
    for i, sid in enumerate(samples):
        sid = str(sid)
        n_cells[sid] += 1
        if sid in donor:
            continue
        row = {"sample": sid, "n_cells": 0}
        for name, arr in cols.items():
            row[name] = arr[i]
        donor[sid] = row
    out = []
    for sid, row in sorted(donor.items()):
        row["n_cells"] = n_cells[sid]
        out.append(row)
    return out


def age_bin(age: float) -> str:
    a = int(float(age))
    for lo, hi in [(20, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 79)]:
        if lo <= a <= hi:
            return f"{lo}-{hi}"
    return "other"
