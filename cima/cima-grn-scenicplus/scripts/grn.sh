#!/usr/bin/env bash
# Standalone CIMA GRN / eRegulon lookup (no sibling explore skill required)
# Usage:
#   ./scripts/grn.sh grn_lookup --tf FOXP3 --max 20
#   ./scripts/grn.sh regulon_list --lineage B

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/_lib${PYTHONPATH:+:$PYTHONPATH}"

if [ $# -lt 1 ]; then
  echo "Usage: grn.sh {grn_lookup|regulon_list} [args]" >&2
  exit 1
fi

TOOL="$1"; shift
case "$TOOL" in
  grn_lookup)   exec python3 "$SCRIPT_DIR/grn_lookup.py" "$@" ;;
  regulon_list) exec python3 "$SCRIPT_DIR/regulon_list.py" "$@" ;;
  *) echo "Usage: grn.sh {grn_lookup|regulon_list} [args]" >&2; exit 1 ;;
esac
