#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

sample_list=""
temp_root=""
threads="10"
conda_env_name="metagenome-megahit-1.2.9"
conda_env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sample-list) sample_list="$2"; shift 2 ;;
    --temp-root) temp_root="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_megahit_assembly.sh --sample-list sample.txt --temp-root temp [--threads 10] [--conda-env-name metagenome-megahit-1.2.9] [--conda-env-prefix /home/USER/software/conda-envs/metagenome-megahit-1.2.9]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

[[ -n "$sample_list" ]] || { echo "--sample-list is required" >&2; exit 1; }
[[ -n "$temp_root" ]] || { echo "--temp-root is required" >&2; exit 1; }
[[ -f "$sample_list" ]] || { echo "sample list not found: $sample_list" >&2; exit 1; }

activate_conda_env "$conda_env_name" "$conda_env_prefix"
ensure_command_after_activation megahit
print_active_conda_env
megahit --help >/dev/null

while IFS= read -r sample || [[ -n "$sample" ]]; do
  [[ -n "$sample" ]] || continue
  r1="$temp_root/$sample/fastp/${sample}_clean_1.fq.gz"
  r2="$temp_root/$sample/fastp/${sample}_clean_2.fq.gz"
  [[ -f "$r1" ]] || { echo "missing clean read: $r1" >&2; exit 1; }
  [[ -f "$r2" ]] || { echo "missing clean read: $r2" >&2; exit 1; }

  megahit -1 "$r1" -2 "$r2" \
    -o "$temp_root/$sample/assembly" \
    --out-prefix "$sample" \
    --presets meta-sensitive \
    -t "$threads"
done < "$sample_list"

echo "MEGAHIT assembly completed"
