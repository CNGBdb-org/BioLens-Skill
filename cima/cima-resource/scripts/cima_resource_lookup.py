#!/usr/bin/env python3
"""List / locate CIMA resources (TrueBlood Resource catalog).

On CNGBdb deploy, prefer local paths under local_root (default:
/public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource).
Portal/FTP are secondary mirrors for external download.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parent / "cima_resource_catalog.json"
DEFAULT_LOCAL_ROOT = "/public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource"


def load_catalog(path: Path | None = None) -> dict:
    p = path or CATALOG
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def resolve_local_root(cat: dict, override: str | None = None) -> str:
    if override:
        return override.rstrip("/")
    env_key = cat.get("local_root_env") or "CIMA_RESOURCE_ROOT"
    env = os.environ.get(env_key)
    if env:
        return env.rstrip("/")
    return (cat.get("local_root") or DEFAULT_LOCAL_ROOT).rstrip("/")


def local_path_for(r: dict, local_root: str) -> str | None:
    rel = r.get("relative_path")
    if rel:
        return f"{local_root}/{rel}"
    if r.get("local_path"):
        # rewrite catalog default root if env override
        catalog_root = DEFAULT_LOCAL_ROOT
        lp = r["local_path"]
        if lp.startswith(catalog_root):
            return local_root + lp[len(catalog_root) :]
        return lp
    return None


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


def print_overview(cat: dict, local_root: str):
    print("CIMA / TrueBlood resources")
    print(f"  Local  : {local_root}/   ← prefer this on deploy")
    print(f"  Portal : {cat['source']}")
    print(f"  FTP    : {cat['ftp_root']}")
    print(f"  RaySync: {cat['raysync_tool']}")
    print(f"  Readme : {cat['readme']}")
    print(f"  Files  : {cat['n_files']} (catalog snapshot)")
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
            lp = local_path_for(r, local_root)
            if lp:
                print(f"      path: {lp}")
        print()
    print("Location tips:")
    for tip in cat.get("download_tips", []):
        print(f"  • {tip}")


def print_rows(rows: list[dict], *, local_root: str, show_path: bool, show_url: bool):
    if not rows:
        print("No resources matched.")
        return
    for r in rows:
        print(f"{r['category']}\t{r['size']}\t{r['name']}")
        if r.get("note"):
            print(f"  note: {r['note']}")
        if r.get("related_skill"):
            print(f"  skill: {r['related_skill']}")
        if show_path:
            lp = local_path_for(r, local_root)
            print(f"  path: {lp or f'(under {local_root}/ — confirm subdirectory)'}")
        if show_url:
            print(f"  url: {r['url'] or '(use portal / RaySync — no direct FTP in catalog)'}")
        print()


def print_howto(cat: dict, local_root: str):
    print("How to get CIMA data")
    print("====================")
    print(f"1. On CNGBdb deploy, read files under: {local_root}/")
    print(f"   (override root with env {cat.get('local_root_env', 'CIMA_RESOURCE_ROOT')})")
    print(f"2. Catalog / external browse: {cat['source']}")
    print(f"3. Public FTP mirror (external): {cat['ftp_root']}")
    print(f"4. Large external downloads: RaySync {cat['raysync_tool']}")
    print(f"5. Details: {cat['readme']}")
    print("6. Support: CNGBdb@genomics.cn")
    print()
    print("Quick picks by need (local paths preferred):")
    picks = [
        ("sample metadata", "Metadata"),
        ("full / lineage scRNA h5ad", "RNA_"),
        ("scATAC peaks", "ATAC_"),
        ("L4 markers / ontology", "Marker"),
        ("GRN eRegulons", "eRegulon"),
        ("xQTL / SMR tables", "xQTL"),
        ("CIMA-CLM demo", "CIMA-CLM_Demo"),
    ]
    for label, q in picks:
        hits = filter_resources(cat, category=None, query=q, small_only=False)[:2]
        if not hits:
            print(f"  - {label}: (see catalog)")
            continue
        for h in hits:
            lp = local_path_for(h, local_root) or h["name"]
            print(f"  - {label}: {lp}")


def main():
    p = argparse.ArgumentParser(description="CIMA resource catalog lookup")
    p.add_argument("--catalog", default=None, help="Override catalog JSON path")
    p.add_argument(
        "--local-root",
        default=None,
        help=f"Local CIMA_Resource root (default: env CIMA_RESOURCE_ROOT or {DEFAULT_LOCAL_ROOT})",
    )
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("overview", help="Category summary (default)")
    s = sub.add_parser("list", help="List / filter files")
    s.add_argument("--category", "-c", default=None, help="Metadata|Cell Atlas|GRN|xQTL|CIMA-CLM|Full Length")
    s.add_argument("--query", "-q", default=None, help="Substring filter on name/note/skill")
    s.add_argument("--small", action="store_true", help="Only ≤200MB files")
    s.add_argument("--path", action="store_true", default=True, help="Print local paths (default on)")
    s.add_argument("--no-path", action="store_true", help="Hide local paths")
    s.add_argument("--url", action="store_true", help="Also print public FTP URLs")
    s = sub.add_parser("get-path", help="Print local path(s) matching a name substring")
    s.add_argument("name", help="File name substring")
    s = sub.add_parser("get-url", help="Print public FTP URL(s) matching a name substring")
    s.add_argument("name", help="File name substring")
    sub.add_parser("howto", help="Location / download instructions")
    sub.add_parser("categories", help="List category names")

    args = p.parse_args()
    cat = load_catalog(Path(args.catalog) if args.catalog else None)
    local_root = resolve_local_root(cat, args.local_root)
    cmd = args.cmd or "overview"

    if cmd == "overview":
        print_overview(cat, local_root)
    elif cmd == "list":
        rows = filter_resources(
            cat, category=args.category, query=args.query, small_only=args.small
        )
        show_path = not getattr(args, "no_path", False)
        print_rows(rows, local_root=local_root, show_path=show_path, show_url=args.url)
        print(f"Matched: {len(rows)}")
    elif cmd == "get-path":
        rows = filter_resources(cat, category=None, query=args.name, small_only=False)
        if not rows:
            print("No match.", file=sys.stderr)
            sys.exit(1)
        for r in rows:
            lp = local_path_for(r, local_root)
            if lp:
                print(lp)
            else:
                print(f"# no relative path for {r['name']} — check under {local_root}/", file=sys.stderr)
                sys.exit(1)
    elif cmd == "get-url":
        rows = filter_resources(cat, category=None, query=args.name, small_only=False)
        if not rows:
            print("No match.", file=sys.stderr)
            sys.exit(1)
        for r in rows:
            print(r["url"] or f"# no direct URL for {r['name']} — use {cat['source']}")
    elif cmd == "howto":
        print_howto(cat, local_root)
    elif cmd == "categories":
        for c in cat["categories"]:
            n = sum(1 for r in cat["resources"] if r["category"] == c)
            print(f"{c}\t{n}")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
