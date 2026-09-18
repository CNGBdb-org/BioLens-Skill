#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

geneset_root=""
temp_root=""
output_root=""
blast_env_name="metagenome-blast-2.16.0"
blast_env_prefix=""
esmfold_cmd=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --geneset-root) geneset_root="$2"; shift 2 ;;
    --temp-root) temp_root="$2"; shift 2 ;;
    --output-root) output_root="$2"; shift 2 ;;
    --blast-env-name) blast_env_name="$2"; shift 2 ;;
    --blast-env-prefix) blast_env_prefix="$2"; shift 2 ;;
    --esmfold-cmd) esmfold_cmd="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_structure_prediction.sh --geneset-root result/geneset --temp-root temp --output-root result/structureset --esmfold-cmd esm-fold [--blast-env-name ... | --blast-env-prefix ...]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -d "$geneset_root" ]] || { echo "geneset root not found: $geneset_root" >&2; exit 1; }
[[ -n "$output_root" ]] || { echo "--output-root is required" >&2; exit 1; }
[[ -n "$esmfold_cmd" ]] || { echo "--esmfold-cmd is required" >&2; exit 1; }
activate_conda_env "$blast_env_name" "$blast_env_prefix"
ensure_command_after_activation blastp
print_active_conda_env
mkdir -p "$output_root"

for biome_dir in "$geneset_root"/*; do
  [[ -d "$biome_dir" ]] || continue
  biome="$(basename "$biome_dir")"
  fam_tsv="$biome_dir/${biome}_family_cluster.tsv"
  rep_fa="$biome_dir/${biome}_family_rep_seq.fasta"
  [[ -f "$fam_tsv" ]] || continue
  [[ -f "$rep_fa" ]] || continue
  outdir="$output_root/$biome"
  mkdir -p "$outdir"
  awk '{print $1}' "$fam_tsv" | sort | uniq -c | awk '$1>30 {print $2}' > "$outdir/eligible_clusters.txt"
  cp "$rep_fa" "$outdir/${biome}_representative_candidates.fa"
  touch "$outdir/${biome}_structure_candidates.tsv"
  echo "ESMFold command placeholder: $esmfold_cmd" > "$outdir/${biome}_esmfold_command.txt"
  echo "Representative selection requires actual ESMFold output parsing" > "$outdir/${biome}_selection_note.txt"
done

echo "Protein structure prediction scaffold completed"
