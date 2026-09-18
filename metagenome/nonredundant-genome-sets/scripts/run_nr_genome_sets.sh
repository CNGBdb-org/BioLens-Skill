#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

biome_list_dir=""
temp_root=""
output_root=""
cog_db=""
kegg_db=""
gtdb_db_dir=""
threads="20"
conda_env_name="metagenome-mag-stack"
conda_env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --biome-list-dir) biome_list_dir="$2"; shift 2 ;;
    --temp-root) temp_root="$2"; shift 2 ;;
    --output-root) output_root="$2"; shift 2 ;;
    --cog-db) cog_db="$2"; shift 2 ;;
    --kegg-db) kegg_db="$2"; shift 2 ;;
    --gtdb-db-dir) gtdb_db_dir="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_nr_genome_sets.sh --biome-list-dir biome_list --temp-root temp --output-root result/genomeset --cog-db /path/cog.dmnd --kegg-db /path/kegg.dmnd --gtdb-db-dir /path/gtdbtk_db [--threads 20] [--conda-env-name ... | --conda-env-prefix ...]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
activate_conda_env "$conda_env_name" "$conda_env_prefix"
ensure_command_after_activation dRep
ensure_command_after_activation gtdbtk
ensure_command_after_activation prodigal
ensure_command_after_activation diamond
print_active_conda_env
mkdir -p "$output_root"

shopt -s nullglob
for biome_file in "$biome_list_dir"/*.txt; do
  biome="$(basename "$biome_file" .txt)"
  outdir="$output_root/$biome"
  mkdir -p "$outdir/genomes" "$outdir/annotation"
  while IFS= read -r sample || [[ -n "$sample" ]]; do
    [[ -n "$sample" ]] || continue
    for fa in "$temp_root/$sample/metawrap/CheckM/metabat2_bins_50_10"/*.fa; do
      [[ -f "$fa" ]] || continue
      cp "$fa" "$outdir/genomes/"
    done
  done < "$biome_file"
  ls "$outdir/genomes"/*.fa > "$outdir/${biome}_genome_path.txt" 2>/dev/null || true
  echo "dRep dereplicate $outdir/${biome}_drep_genome -g $outdir/${biome}_genome_path.txt -p $threads --length 0 --completeness 50 --contamination 10 --S_algorithm ANImf --P_ani 0.9 --S_ani 0.95 --cov_thresh 0.3 --strain_heterogeneity_weight 0" > "$outdir/${biome}_drep_command.sh"
  echo "gtdbtk classify_wf --skip_ani_screen --genome_dir $outdir/genomes --out_dir $outdir/gtdbtk --cpus $threads -x fa" > "$outdir/${biome}_gtdbtk_command.sh"
done

echo "Non-redundant genome-set scaffold completed"
