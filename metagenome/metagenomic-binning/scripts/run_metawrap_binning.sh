#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

sample_list=""
temp_root=""
threads="10"
conda_env_name="metagenome-binning-stack"
conda_env_prefix=""
metawrap_cmd="metawrap"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sample-list) sample_list="$2"; shift 2 ;;
    --temp-root) temp_root="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    --metawrap-cmd) metawrap_cmd="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_metawrap_binning.sh --sample-list sample.txt --temp-root temp [--threads 10] [--metawrap-cmd metawrap] [--conda-env-name ... | --conda-env-prefix ...]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
[[ -f "$sample_list" ]] || { echo "sample list not found: $sample_list" >&2; exit 1; }
activate_conda_env "$conda_env_name" "$conda_env_prefix"
ensure_command_after_activation checkm
command -v "$metawrap_cmd" >/dev/null 2>&1 || echo "WARNING: metawrap command not found; please provide --metawrap-cmd" >&2
print_active_conda_env

while IFS= read -r sample || [[ -n "$sample" ]]; do
  [[ -n "$sample" ]] || continue
  mkdir -p "$temp_root/$sample/metawrap"
  contigs="$temp_root/$sample/assembly/${sample}.contigs.fa"
  r1="$temp_root/$sample/fastp/${sample}_clean_1.fq.gz"
  r2="$temp_root/$sample/fastp/${sample}_clean_2.fq.gz"
  [[ -f "$contigs" ]] || { echo "missing contigs: $contigs" >&2; exit 1; }
  [[ -f "$r1" ]] || { echo "missing clean read: $r1" >&2; exit 1; }
  [[ -f "$r2" ]] || { echo "missing clean read: $r2" >&2; exit 1; }
  echo "$metawrap_cmd binning -o $temp_root/$sample/metawrap/$sample -t $threads --metabat2 -l 1000 -a $contigs $r1 $r2" > "$temp_root/$sample/metawrap/${sample}_metawrap_command.sh"
  mkdir -p "$temp_root/$sample/metawrap/CheckM"
  echo -e "Bin\tCompleteness\tContamination" > "$temp_root/$sample/metawrap/CheckM/${sample}_bins_50_10.stats.tsv"
done < "$sample_list"

echo "MetaWRAP binning scaffold completed"
