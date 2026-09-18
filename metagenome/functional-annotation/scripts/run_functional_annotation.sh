#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

geneset_root=""
eggnog_db_dir=""
cazy_db=""
threads="20"
conda_env_name="metagenome-annotation-stack"
conda_env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --geneset-root) geneset_root="$2"; shift 2 ;;
    --eggnog-db-dir) eggnog_db_dir="$2"; shift 2 ;;
    --cazy-db) cazy_db="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_functional_annotation.sh --geneset-root result/geneset --eggnog-db-dir /path/eggnog_v5 --cazy-db /path/cazy.dmnd [--threads 20] [--conda-env-name ... | --conda-env-prefix ...]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -d "$geneset_root" ]] || { echo "geneset root not found: $geneset_root" >&2; exit 1; }
[[ -d "$eggnog_db_dir" ]] || { echo "eggNOG db dir not found: $eggnog_db_dir" >&2; exit 1; }
[[ -f "$cazy_db" ]] || { echo "CAZy database not found: $cazy_db" >&2; exit 1; }
activate_conda_env "$conda_env_name" "$conda_env_prefix"
ensure_command_after_activation emapper.py
ensure_command_after_activation diamond
ensure_command_after_activation rgi
print_active_conda_env

shopt -s nullglob
for biome_dir in "$geneset_root"/*; do
  [[ -d "$biome_dir" ]] || continue
  biome="$(basename "$biome_dir")"
  input_faa="$biome_dir/${biome}_nr_rep_seq.fasta"
  [[ -f "$input_faa" ]] || continue
  mkdir -p "$biome_dir/eggnog" "$biome_dir/cazy" "$biome_dir/card"
  emapper.py -i "$input_faa" -o "$biome_dir/eggnog/${biome}" --cpu "$threads" --data_dir "$eggnog_db_dir"
  diamond blastp --db "$cazy_db" --query "$input_faa" -e 0.00001 --more-sensitive --outfmt 6 --max-target-seqs 1 --threads "$threads" --quiet --out "$biome_dir/cazy/${biome}_cazy.tsv"
  rgi main --input_sequence "$input_faa" --output_file "$biome_dir/card/${biome}_card" --local --clean --include_loose -t protein
done

echo "Functional annotation completed"
