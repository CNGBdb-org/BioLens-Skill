#!/usr/bin/env bash
set -euo pipefail

archive=""
install_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) archive="$2"; shift 2 ;;
    --install-dir) install_dir="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash install_metagenemark_software.sh --archive /path/to/MetaGeneMark_v3.38.tar.gz --install-dir /home/USER/software/metagenemark-3.38"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$archive" ]] || { echo "--archive is required" >&2; exit 1; }
[[ -n "$install_dir" ]] || { echo "--install-dir is required" >&2; exit 1; }
[[ -f "$archive" ]] || { echo "archive not found: $archive" >&2; exit 1; }
mkdir -p "$install_dir"

tar -xf "$archive" -C "$install_dir" --strip-components=1
chmod +x "$install_dir"/gmhmmp 2>/dev/null || true
[[ -x "$install_dir/gmhmmp" ]] || { echo "gmhmmp not found after extraction" >&2; exit 1; }
[[ -f "$install_dir/MetaGeneMark_v1.mod" ]] || echo "WARNING: MetaGeneMark_v1.mod not found; please place model file manually" >&2
"$install_dir/gmhmmp" -h >/dev/null 2>&1 || true
