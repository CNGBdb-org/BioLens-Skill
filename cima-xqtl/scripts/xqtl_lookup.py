#!/usr/bin/env python3
"""Query CIMA cis-xQTL lead associations."""

from __future__ import annotations

import argparse
import json
import sys

from cima_ftp import fetch_ftp_table, iter_csv_chunks


def search(*, gene: str = "", variant: str = "", celltype: str = "", qtype: str = "", max_rows: int = 40) -> list[dict]:
    path = fetch_ftp_table("lead_xqtl")
    hits = []
    gene_u = gene.upper()
    for chunk in iter_csv_chunks(path):
        for _, row in chunk.iterrows():
            phen = str(row.get("phenotype_id", ""))
            var = str(row.get("variant_id", ""))
            ct = str(row.get("celltype", ""))
            analysis = str(row.get("analysis", ""))
            if gene_u and gene_u not in phen.upper():
                continue
            if variant and variant not in var:
                continue
            if celltype and celltype.lower() not in ct.lower():
                continue
            if qtype and qtype.lower() not in analysis.lower():
                continue
            hits.append({
                "phenotype_id": phen,
                "variant_id": var,
                "celltype": ct,
                "analysis": analysis,
                "pval_nominal": row.get("pval_nominal"),
                "slope": row.get("slope"),
                "af": row.get("af"),
            })
            if len(hits) >= max_rows:
                return hits
    return hits


def main():
    p = argparse.ArgumentParser(description="Query CIMA cis-xQTL lead table.")
    p.add_argument("--gene", "-g", help="Gene / phenotype_id")
    p.add_argument("--variant", help="variant_id e.g. chr1_814733")
    p.add_argument("--celltype", help="cell_type_l4 name substring")
    p.add_argument("--type", "--analysis", dest="qtype", help="cis-eQTL or cis-caQTL")
    p.add_argument("--max", type=int, default=40)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    if not any([args.gene, args.variant, args.celltype, args.qtype]):
        p.error("Provide at least one of --gene, --variant, --celltype, --type/--analysis")

    print("Loading xQTL table (cached after first run)…", file=sys.stderr)
    hits = search(
        gene=args.gene or "",
        variant=args.variant or "",
        celltype=args.celltype or "",
        qtype=args.qtype or "",
        max_rows=args.max,
    )

    if args.format == "json":
        print(json.dumps({"hits": hits}, indent=2))
        return

    print(f"xQTL hits: {len(hits)}\n")
    print(f"{'gene':<16} {'variant':<18} {'celltype':<22} {'analysis':<12} {'pval':>12}")
    for h in hits:
        print(
            f"{h['phenotype_id']:<16} {h['variant_id']:<18} {h['celltype']:<22} "
            f"{h['analysis']:<12} {h['pval_nominal']!s:>12}"
        )


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
