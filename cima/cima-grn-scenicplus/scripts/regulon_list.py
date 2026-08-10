#!/usr/bin/env python3
"""List CIMA high-quality eRegulons (FTP table)."""

from __future__ import annotations

import argparse
import json
import sys

from cima_ftp import fetch_ftp_table


def main():
    p = argparse.ArgumentParser(description="List CIMA high-quality eRegulons.")
    p.add_argument("--lineage", choices=["All", "NK", "B", "Myeloid", "CD4T", "CD8T", "Activator", "Repressor"], default="All")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    path = fetch_ftp_table("eregulon_hq")
    import pandas as pd

    df = pd.read_csv(path)
    col = f"selected_eRegulons_{args.lineage}"
    if col not in df.columns:
        p.error(f"Column {col!r} not in table")
    regs = [x for x in df[col].dropna().astype(str).tolist() if x.strip()]
    regs = sorted(set(regs))

    if args.format == "json":
        print(json.dumps({"lineage": args.lineage, "n": len(regs), "eregulons": regs}, indent=2))
        return

    print(f"CIMA high-quality eRegulons ({args.lineage}): {len(regs)}\n")
    for r in regs:
        print(r)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
