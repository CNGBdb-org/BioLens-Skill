#!/usr/bin/env python3
"""List CIMA donor metadata from FTP (428 samples, no API load)."""

from __future__ import annotations

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from cima_ftp import fetch_ftp_table


def main():
    p = argparse.ArgumentParser(description="CIMA donor metadata from FTP table.")
    p.add_argument("--sex", help="Filter sex")
    p.add_argument("--age-min", type=int)
    p.add_argument("--age-max", type=int)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--max", type=int, default=0)
    args = p.parse_args()

    import pandas as pd

    path = fetch_ftp_table("sample_metadata")
    df = pd.read_csv(path)
    if args.sex:
        df = df[df["sex"].astype(str).str.lower() == args.sex.lower()]
    if args.age_min is not None:
        df = df[df["Age"] >= args.age_min]
    if args.age_max is not None:
        df = df[df["Age"] <= args.age_max]
    if args.max > 0:
        df = df.head(args.max)

    if args.format == "json":
        print(df.to_json(orient="records", indent=2, force_ascii=False))
        return

    print(f"CIMA donors: {len(df)} rows (FTP metadata)\n")
    cols = ["Sample_name", "Age", "sex", "BMI", "BMI_group"]
    cols = [c for c in cols if c in df.columns]
    print("\t".join(cols))
    for _, row in df.iterrows():
        print("\t".join(str(row.get(c, "")) for c in cols))


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
