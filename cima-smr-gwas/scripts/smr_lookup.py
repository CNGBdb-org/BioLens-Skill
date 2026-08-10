#!/usr/bin/env python3
"""Query CIMA SMR associations.

Default: significant gene–trait (disease) SMR table.
Optional: caQTL→eQTL SMR CSV (--source caqtl).
"""

from __future__ import annotations

import argparse
import json
import sys

from cima_ftp import fetch_ftp_table, iter_csv_chunks, load_table

# Short trait codes used in BBJ_diseases sheet → readable labels for text output
TRAIT_LABELS = {
    "RA": "RA (rheumatoid arthritis)",
    "As": "As (asthma)",
    "AD": "AD (atopic dermatitis)",
    "GD": "GD (Graves disease)",
    "T2D": "T2D (type 2 diabetes)",
    "T1D": "T1D (type 1 diabetes)",
    "SLE": "SLE",
    "COPD": "COPD",
    "UC": "UC (ulcerative colitis)",
    "AR": "AR (allergic rhinitis)",
    "Urt": "Urt (urticaria)",
    "Hype": "Hype (hypertension)",
}


def _search_disease(
    *,
    gene: str = "",
    snp: str = "",
    celltype: str = "",
    trait: str = "",
    max_rows: int = 40,
) -> list[dict]:
    path = fetch_ftp_table("smr_disease")
    df = load_table(path)
    gene_u = gene.upper()
    trait_u = trait.upper()
    hits: list[dict] = []
    for _, row in df.iterrows():
        g = str(row.get("Gene") or "")
        topsnp = str(row.get("topSNP") or "")
        ct = str(row.get("celltype") or "")
        tr = str(row.get("trait") or "")
        if gene_u and gene_u not in g.upper():
            continue
        if snp and snp not in topsnp:
            continue
        if celltype and celltype.lower() not in ct.lower():
            continue
        if trait_u and trait_u not in tr.upper() and trait_u not in TRAIT_LABELS.get(tr, "").upper():
            continue
        hits.append({
            "gene": g,
            "trait": tr,
            "trait_label": TRAIT_LABELS.get(tr, tr),
            "trait_category": str(row.get("trait_category") or ""),
            "celltype": ct,
            "topSNP": topsnp,
            "p_SMR": row.get("p_SMR"),
            "p_HEIDI": row.get("p_HEIDI"),
            "QTL": str(row.get("QTL") or ""),
        })
        if len(hits) >= max_rows:
            break
    return hits


def _search_caqtl(
    *,
    gene: str = "",
    snp: str = "",
    celltype: str = "",
    max_rows: int = 40,
) -> list[dict]:
    path = fetch_ftp_table("smr")
    hits: list[dict] = []
    gene_u = gene.upper()
    for chunk in iter_csv_chunks(path):
        for _, row in chunk.iterrows():
            expo = str(row.get("Expo_Gene") or row.get("Expo_ID") or "")
            outco = str(row.get("Outco_Gene") or row.get("Outco_ID") or "")
            topsnp = str(row.get("topSNP", ""))
            ct = str(row.get("celltype", ""))
            if gene_u and gene_u not in expo.upper() and gene_u not in outco.upper():
                continue
            if snp and snp not in topsnp:
                continue
            if celltype and celltype.lower() not in ct.lower():
                continue
            hits.append({
                "exposure": expo or row.get("Expo_ID"),
                "outcome": outco or row.get("Outco_ID"),
                "topSNP": topsnp,
                "celltype": ct,
                "p_SMR": row.get("p_SMR"),
                "b_SMR": row.get("b_SMR"),
            })
            if len(hits) >= max_rows:
                return hits
    return hits


def main():
    p = argparse.ArgumentParser(description="Query CIMA SMR associations.")
    p.add_argument("--gene", "-g", help="Gene symbol (disease table: Gene; caQTL table: expo/outco)")
    p.add_argument("--snp", help="topSNP id")
    p.add_argument("--celltype", help="cell_type_l4 substring")
    p.add_argument("--trait", help="Trait code or name substring (disease table only), e.g. RA / asthma")
    p.add_argument(
        "--source",
        choices=["disease", "caqtl"],
        default="disease",
        help="disease=显著基因–性状 SMR (default); caqtl=caQTL→eQTL SMR CSV",
    )
    p.add_argument("--max", type=int, default=40)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    if not any([args.gene, args.snp, args.celltype, args.trait]):
        p.error("Provide at least one of --gene, --snp, --celltype, --trait")

    if args.source == "disease":
        print("Loading significant gene–trait SMR table…", file=sys.stderr)
        hits = _search_disease(
            gene=args.gene or "",
            snp=args.snp or "",
            celltype=args.celltype or "",
            trait=args.trait or "",
            max_rows=args.max,
        )
    else:
        if args.trait:
            p.error("--trait requires --source disease")
        print("Loading caQTL→eQTL SMR CSV…", file=sys.stderr)
        hits = _search_caqtl(
            gene=args.gene or "",
            snp=args.snp or "",
            celltype=args.celltype or "",
            max_rows=args.max,
        )

    if args.format == "json":
        print(json.dumps({"source": args.source, "hits": hits}, indent=2, default=str))
        return

    print(f"SMR hits ({args.source}): {len(hits)}\n")
    if args.source == "disease":
        print(f"{'gene':<12} {'trait':<36} {'celltype':<22} {'topSNP':<16} {'p_SMR':>12}")
        for h in hits:
            print(
                f"{str(h['gene']):<12} {str(h['trait_label']):<36} {h['celltype']:<22} "
                f"{h['topSNP']:<16} {h['p_SMR']!s:>12}"
            )
    else:
        print(f"{'exposure':<20} {'outcome':<20} {'celltype':<22} {'topSNP':<16} {'p_SMR':>12}")
        for h in hits:
            print(
                f"{str(h['exposure']):<20} {str(h['outcome']):<20} {h['celltype']:<22} "
                f"{h['topSNP']:<16} {h['p_SMR']!s:>12}"
            )


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
