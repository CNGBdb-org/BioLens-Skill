#!/usr/bin/env python3
"""Query CIMA enhancer–gene regulatory network (eRegulons metadata)."""

from __future__ import annotations

import argparse
import json
import sys

from cima_ftp import fetch_ftp_table, iter_csv_chunks


def _match(row, *, tf: str, gene: str, region: str) -> bool:
    if tf and tf.upper() not in str(row.get("TF", "")).upper():
        return False
    if gene and gene.upper() not in str(row.get("Gene", "")).upper():
        return False
    if region and region not in str(row.get("Region", "")):
        return False
    return True


def search(*, tf: str = "", gene: str = "", region: str = "", max_rows: int = 50) -> list[dict]:
    path = fetch_ftp_table("eregulon_meta")
    hits = []
    for chunk in iter_csv_chunks(path):
        for _, row in chunk.iterrows():
            if not _match(row, tf=tf, gene=gene, region=region):
                continue
            hits.append({
                "TF": row.get("TF"),
                "Gene": row.get("Gene"),
                "Region": row.get("Region"),
                "Consensus_name": row.get("Consensus_name"),
                "R2G_rho": row.get("R2G_rho"),
                "TF2G_regulation": row.get("TF2G_regulation"),
            })
            if len(hits) >= max_rows:
                return hits
    return hits


def main():
    p = argparse.ArgumentParser(description="Query CIMA GRN (TF → gene / enhancer).")
    p.add_argument("--tf", help="Transcription factor symbol")
    p.add_argument("--gene", "-g", help="Target gene symbol")
    p.add_argument("--region", help="Enhancer region substring")
    p.add_argument("--max", type=int, default=30)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    if not any([args.tf, args.gene, args.region]):
        p.error("Provide at least one of --tf, --gene, --region")

    print("Loading GRN table (cached after first run)…", file=sys.stderr)
    hits = search(tf=args.tf or "", gene=args.gene or "", region=args.region or "", max_rows=args.max)

    if args.format == "json":
        print(json.dumps({"query": {"tf": args.tf, "gene": args.gene, "region": args.region}, "hits": hits}, indent=2))
        return

    print(f"GRN hits: {len(hits)} (max {args.max})\n")
    print(f"{'TF':<12} {'Gene':<12} {'reg':>4} {'R2G_rho':>8}  Region / regulon")
    for h in hits:
        reg = h.get("TF2G_regulation", "")
        rho = h.get("R2G_rho", "")
        cn = h.get("Consensus_name", "")
        region = str(h.get("Region", ""))[:40]
        print(f"{h.get('TF',''):<12} {h.get('Gene',''):<12} {reg!s:>4} {rho!s:>8}  {region}  ({cn})")
    if not hits:
        print("No matches. Try broader symbols or download full table from FTP GRN/.")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
