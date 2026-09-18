#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

genomeset_root=""
output_root=""
pfam_dir=""
bigscape_cmd="bigscape.py"
threads="20"
conda_env_name="metagenome-bgc-stack"
conda_env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --genomeset-root) genomeset_root="$2"; shift 2 ;;
    --output-root) output_root="$2"; shift 2 ;;
    --pfam-dir) pfam_dir="$2"; shift 2 ;;
    --bigscape-cmd) bigscape_cmd="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_bgc_analysis.sh --genomeset-root result/genomeset --output-root result/bgcset --pfam-dir /path/pfam_dir [--bigscape-cmd bigscape.py] [--threads 20] [--conda-env-name ... | --conda-env-prefix ...]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
activate_conda_env "$conda_env_name" "$conda_env_prefix"
ensure_command_after_activation antismash
command -v "$bigscape_cmd" >/dev/null 2>&1 || echo "WARNING: BiG-SCAPE command not found; please provide --bigscape-cmd" >&2
print_active_conda_env
mkdir -p "$output_root"

for biome_dir in "$genomeset_root"/*; do
  [[ -d "$biome_dir" ]] || continue
  biome="$(basename "$biome_dir")"
  outdir="$output_root/$biome"
  mkdir -p "$outdir/antismash/result" "$outdir/antismash/all_gbk" "$outdir/bigscape_result" "$outdir/microviridin_review"
  for fa in "$biome_dir/genomes"/*.fa; do
    [[ -f "$fa" ]] || continue
    genome="$(basename "$fa" .fa)"
    antismash --genefinding-tool prodigal --cb-knownclusters --output-dir "$outdir/antismash/result/$genome" "$fa"
    find "$outdir/antismash/result/$genome" -name "*.region*.gbk" -exec cp {} "$outdir/antismash/all_gbk/" \;
  done
  $bigscape_cmd -i "$outdir/antismash/all_gbk" -o "$outdir/bigscape_result" --mix --hybrids-off --gcf-cutoffs 0.3,0.7 -m 4.0 --pfam-path "$pfam_dir"
  echo "Manual review: ATP-grasp ligase >350 aa or precursor motif TxKxPSD; trace host MAG; export for iTOL and Clinker" > "$outdir/microviridin_review/README.txt"
done

echo "BGC analysis completed"
