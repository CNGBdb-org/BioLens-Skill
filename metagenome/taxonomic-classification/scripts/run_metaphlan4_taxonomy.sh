#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

sample_list=""
temp_root=""
threads="10"
conda_env_name="metagenome-metaphlan4-4.1.0"
conda_env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sample-list) sample_list="$2"; shift 2 ;;
    --temp-root) temp_root="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_metaphlan4_taxonomy.sh --sample-list sample.txt --temp-root temp [--threads 10] [--conda-env-name metagenome-metaphlan4-4.1.0] [--conda-env-prefix /home/USER/software/conda-envs/metagenome-metaphlan4-4.1.0]"
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
ensure_command_after_activation metaphlan
ensure_command_after_activation merge_metaphlan_tables.py
print_active_conda_env
metaphlan --version

profile_files=()
while IFS= read -r sample || [[ -n "$sample" ]]; do
  [[ -n "$sample" ]] || continue
  mkdir -p "$temp_root/$sample/mp4"
  r1="$temp_root/$sample/fastp/${sample}_clean_1.fq.gz"
  r2="$temp_root/$sample/fastp/${sample}_clean_2.fq.gz"
  [[ -f "$r1" ]] || { echo "missing clean read: $r1" >&2; exit 1; }
  [[ -f "$r2" ]] || { echo "missing clean read: $r2" >&2; exit 1; }

  metaphlan "$r1,$r2" \
    --input_type fastq \
    -o "$temp_root/$sample/mp4/${sample}.txt" \
    --nproc "$threads" \
    --bowtie2out "$temp_root/$sample/mp4/bowtie2out_${sample}.bz2"

  profile_files+=("$temp_root/$sample/mp4/${sample}.txt")
done < "$sample_list"

mkdir -p "$temp_root/metaphlan_merged"
merge_metaphlan_tables.py "${profile_files[@]}" > "$temp_root/metaphlan_merged/merged_abundance_table.txt"

grep -E '(s__)|(clade_name)' "$temp_root/metaphlan_merged/merged_abundance_table.txt" | grep -v 't__' | sed 's/^.*s__//g' | awk '{$2=null;print}' | sed 's/\ \ /\ /g' | sed 's/\ /\t/g' > "$temp_root/metaphlan_merged/merged_abundance_species.txt"
grep -E '(g__)|(clade_name)' "$temp_root/metaphlan_merged/merged_abundance_table.txt" | grep -v 's__' | sed 's/^.*g__//g' | awk '{$2=null;print}' | sed 's/\ \ /\ /g' | sed 's/\ /\t/g' > "$temp_root/metaphlan_merged/merged_abundance_genus.txt"
grep -E '(f__)|(clade_name)' "$temp_root/metaphlan_merged/merged_abundance_table.txt" | grep -v 'g__' | sed 's/^.*f__//g' | awk '{$2=null;print}' | sed 's/\ \ /\ /g' | sed 's/\ /\t/g' > "$temp_root/metaphlan_merged/merged_abundance_family.txt"
grep -E '(o__)|(clade_name)' "$temp_root/metaphlan_merged/merged_abundance_table.txt" | grep -v 'f__' | sed 's/^.*o__//g' | awk '{$2=null;print}' | sed 's/\ \ /\ /g' | sed 's/\ /\t/g' > "$temp_root/metaphlan_merged/merged_abundance_order.txt"
grep -E '(c__)|(clade_name)' "$temp_root/metaphlan_merged/merged_abundance_table.txt" | grep -v 'o__' | sed 's/^.*c__//g' | awk '{$2=null;print}' | sed 's/\ \ /\ /g' | sed 's/\ /\t/g' > "$temp_root/metaphlan_merged/merged_abundance_class.txt"
grep -E '(p__)|(clade_name)' "$temp_root/metaphlan_merged/merged_abundance_table.txt" | grep -v 'c__' | sed 's/^.*p__//g' | awk '{$2=null;print}' | sed 's/\ \ /\ /g' | sed 's/\ /\t/g' > "$temp_root/metaphlan_merged/merged_abundance_phylum.txt"

echo "MetaPhlAn4 taxonomic classification completed"
