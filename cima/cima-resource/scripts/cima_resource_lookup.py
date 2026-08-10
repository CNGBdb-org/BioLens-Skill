#!/usr/bin/env python3
"""List / locate CIMA resources (TrueBlood Resource catalog).

This package does not ship local CIMA data. Prefer public FTP URLs under
https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parent / "cima_resource_catalog.json"


def load_catalog(path: Path | None = None) -> dict:
    p = path or CATALOG
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def filter_resources(cat: dict, *, category: str | None, query: str | None, small_only: bool):
    rows = cat["resources"]
    if category:
        c = category.lower()
        rows = [r for r in rows if c in r["category"].lower()]
    if query:
        q = query.lower()
        rows = [
            r
            for r in rows
            if q in r["name"].lower()
            or q in (r.get("note") or "").lower()
            or q in (r.get("related_skill") or "").lower()
            or q in r["category"].lower()
        ]
    if small_only:

        def is_small(size: str) -> bool:
            s = size.upper().replace(" ", "")
            if s.endswith("KB"):
                return True
            if s.endswith("MB"):
                try:
                    return float(s[:-2]) <= 200
                except ValueError:
                    return False
            return False

        rows = [r for r in rows if is_small(r["size"])]
    return rows


def print_overview(cat: dict):
    print("CIMA / TrueBlood resources")
    print(f"  FTP    : {cat['ftp_root']}   ← answer “where” with this")
    print(f"  Portal : {cat['source']}")
    print(f"  RaySync: {cat['raysync_tool']}")
    print(f"  Readme : {cat['readme']}")
    print(f"  Files  : {cat['n_files']} (catalog snapshot)")
    print("  Note   : no local CIMA_Resource mirror in this skill package")
    print()
    by = {}
    for r in cat["resources"]:
        by.setdefault(r["category"], []).append(r)
    for cat_name in cat["categories"]:
        items = by.get(cat_name, [])
        if not items:
            continue
        print(f"## {cat_name} ({len(items)})")
        for r in items:
            print(f"  - {r['name']}  [{r['size']}]")
            if r.get("note"):
                print(f"      {r['note']}")
            if r.get("url"):
                print(f"      url: {r['url']}")
        print()
    print("Location tips:")
    for tip in cat.get("download_tips", []):
        print(f"  • {tip}")


def print_rows(rows: list[dict], *, show_url: bool):
    if not rows:
        print("No resources matched.")
        return
    for r in rows:
        print(f"{r['category']}\t{r['size']}\t{r['name']}")
        if r.get("note"):
            print(f"  note: {r['note']}")
        if r.get("related_skill"):
            print(f"  skill: {r['related_skill']}")
        if show_url:
            print(f"  url: {r['url'] or '(use portal / RaySync — no direct FTP in catalog)'}")
        print()


def print_howto(cat: dict):
    print("How to get CIMA data")
    print("====================")
    print(f"1. Public FTP (default answer for “where”): {cat['ftp_root']}")
    print(f"2. Portal catalog: {cat['source']}")
    print(f"3. Large downloads: RaySync {cat['raysync_tool']}")
    print(f"4. Details: {cat['readme']}")
    print("5. Support: CNGBdb@genomics.cn")
    print()
    print("This skill package does not include a local CIMA_Resource copy.")
    print()
    print("Quick picks by need (FTP URLs):")
    picks = [
        ("sample metadata", "Metadata"),
        ("full / lineage scRNA h5ad", "RNA_"),
        ("scATAC peaks", "ATAC_"),
        ("L4 markers / ontology", "Marker"),
        ("GRN eRegulons", "eRegulon"),
        ("xQTL / SMR tables", "xQTL"),
        ("CIMA-CLM demo", "CIMA-CLM_Demo"),
        ("NK scRNA h5ad", "NK_"),
    ]
    for label, q in picks:
        hits = filter_resources(cat, category=None, query=q, small_only=False)[:2]
        if not hits:
            print(f"  - {label}: (see catalog)")
            continue
        for h in hits:
            print(f"  - {label}: {h.get('url') or h['name']}")


def main():
    p = argparse.ArgumentParser(description="CIMA resource catalog lookup (FTP-first)")
    p.add_argument("--catalog", default=None, help="Override catalog JSON path")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("overview", help="Category summary (default)")
    s = sub.add_parser("list", help="List / filter files")
    s.add_argument("--category", "-c", default=None, help="Metadata|Cell Atlas|GRN|xQTL|CIMA-CLM|Full Length")
    s.add_argument("--query", "-q", default=None, help="Substring filter on name/note/skill")
    s.add_argument("--small", action="store_true", help="Only ≤200MB files")
    s.add_argument("--url", action="store_true", default=True, help="Print FTP URLs (default on)")
    s.add_argument("--no-url", action="store_true", help="Hide FTP URLs")
    s = sub.add_parser("get-url", help="Print public FTP URL(s) matching a name substring")
    s.add_argument("name", help="File name substring")
    sub.add_parser("howto", help="Location / download instructions")
    sub.add_parser("categories", help="List category names")

    args = p.parse_args()
    cat = load_catalog(Path(args.catalog) if args.catalog else None)
    cmd = args.cmd or "overview"

    if cmd == "overview":
        print_overview(cat)
    elif cmd == "list":
        rows = filter_resources(
            cat, category=args.category, query=args.query, small_only=args.small
        )
        show_url = not getattr(args, "no_url", False)
        print_rows(rows, show_url=show_url)
        print(f"Matched: {len(rows)}")
    elif cmd == "get-url":
        rows = filter_resources(cat, category=None, query=args.name, small_only=False)
        if not rows:
            print("No match.", file=sys.stderr)
            sys.exit(1)
        for r in rows:
            print(r["url"] or f"# no direct URL for {r['name']} — use {cat['source']}")
    elif cmd == "howto":
        print_howto(cat)
    elif cmd == "categories":
        for c in cat["categories"]:
            n = sum(1 for r in cat["resources"] if r["category"] == c)
            print(f"{c}\t{n}")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
