#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

biome_list_dir=""
temp_root=""
output_root=""
threads="20"
conda_env_name="metagenome-mmseqs2-14-7e28"
conda_env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --biome-list-dir) biome_list_dir="$2"; shift 2 ;;
    --temp-root) temp_root="$2"; shift 2 ;;
    --output-root) output_root="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_mmseqs2_gene_sets.sh --biome-list-dir biome_list --temp-root temp --output-root result/geneset [--threads 20] [--conda-env-name ... | --conda-env-prefix ...]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -d "$biome_list_dir" ]] || { echo "biome list dir not found: $biome_list_dir" >&2; exit 1; }
[[ -n "$temp_root" ]] || { echo "--temp-root is required" >&2; exit 1; }
[[ -n "$output_root" ]] || { echo "--output-root is required" >&2; exit 1; }
activate_conda_env "$conda_env_name" "$conda_env_prefix"
ensure_command_after_activation mmseqs
print_active_conda_env

shopt -s nullglob
for biome_file in "$biome_list_dir"/*.txt; do
  biome="$(basename "$biome_file" .txt)"
  outdir="$output_root/$biome"
  mkdir -p "$outdir"
  all_faa="$outdir/${biome}_all_prot.fa"
  : > "$all_faa"
  while IFS= read -r sample || [[ -n "$sample" ]]; do
    [[ -n "$sample" ]] || continue
    faa="$temp_root/$sample/metagenemark/${sample}_prot.fa"
    [[ -f "$faa" ]] || { echo "missing protein fasta: $faa" >&2; exit 1; }
    cat "$faa" >> "$all_faa"
  done < "$biome_file"

  mmseqs easy-cluster "$all_faa" "$outdir/${biome}_nr" "$outdir/${biome}_nr_tmp" \
    --min-seq-id 0.95 -c 0.90 --cov-mode 1 --cluster-mode 3 --threads "$threads"

  mmseqs easy-cluster "$outdir/${biome}_nr_rep_seq.fasta" "$outdir/${biome}_family" "$outdir/${biome}_family_tmp" \
    --min-seq-id 0.20 -c 0.50 --cov-mode 1 --cluster-mode 3 --threads "$threads"

done

echo "MMseqs2 gene-set clustering completed"
