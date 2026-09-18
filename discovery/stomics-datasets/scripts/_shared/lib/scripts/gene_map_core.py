"""Cross-sample gene × group matrices (susceptibility / disease)."""

from atlas_registry import DEFAULT_OBS_LABEL, get_atlas
import catalog_bridge as cat
from gene_stats_core import summarize_gene


def pick_atlas_samples(*, stages=None, max_per_stage=2, tissue=None):
    spec = get_atlas()
    if spec.name == "hesta":
        catalog = cat.load_catalog()
        entries = [e for e in catalog if cat.is_primary_section(e)]
        if stages:
            stage_list = [s.strip() for s in stages.split(",") if s.strip()]
            filtered = []
            for st in stage_list:
                hits = cat.search_catalog(stage=st, tissue=tissue)
                hits = [e for e in hits if cat.is_primary_section(e)]
                hits.sort(key=lambda e: (-len(e.tissues), e.section))
                filtered.extend(hits[:max_per_stage])
            entries = filtered
        elif tissue:
            t = tissue.lower()
            entries = [e for e in entries if any(t in x.lower() for x in e.tissues)]
        entries.sort(key=lambda e: (e.stage, e.section))
    elif spec.name == "mccsta":
        entries = [e for e in cat.load_catalog() if cat.is_parquet_section(e)]
        if stages:
            stage_list = [s.strip() for s in stages.split(",") if s.strip()]
            filtered = []
            for st in stage_list:
                hits = [e for e in entries if st.lower() in e.stem.lower() or st.lower() in e.stage.lower()]
                hits.sort(key=lambda e: cat.slice_sort_key(e))
                filtered.extend(hits[:max_per_stage])
            entries = filtered
        entries.sort(key=lambda e: cat.slice_sort_key(e))
    else:
        entries = [e for e in cat.load_catalog() if cat.is_sagittal_section(e)]
        if stages:
            stage_list = [s.strip() for s in stages.split(",") if s.strip()]
            filtered = []
            for st in stage_list:
                hits = [e for e in entries if st in e.stage]
                hits.sort(key=lambda e: (-len(e.tissues), e.section))
                filtered.extend(hits[:max_per_stage])
            entries = filtered
        entries.sort(key=lambda e: (cat.stage_sort_key(e.stage), e.section))
    seen = set()
    out = []
    for e in entries:
        if e.dataset_id not in seen:
            seen.add(e.dataset_id)
            out.append(e)
    return out


def gene_group_matrix(entries, genes, *, groups_focus=None):
    by_col = DEFAULT_OBS_LABEL
    key = "by_" + by_col
    rows = []
    for e in entries:
        for gene in genes:
            try:
                data = summarize_gene(e.dataset_id, gene, group_by=by_col)
            except FileNotFoundError:
                continue
            for item in data.get(key, []):
                organ = item[by_col]
                if groups_focus and not any(g.lower() in str(organ).lower() for g in groups_focus):
                    continue
                rows.append({
                    "gene": data["gene"],
                    "dataset_id": e.dataset_id,
                    "stage": e.stage,
                    "organ": organ,
                    "mean_expression": item["mean_expression"],
                    "pct_expressing": item["pct_expressing"],
                    "n_spots": item["n_spots"],
                })
    return rows


def top_hits(rows, *, top=5, sort_key="mean_expression"):
    by_gene = {}
    for r in rows:
        by_gene.setdefault(r["gene"], []).append(r)
    out = {}
    for g, items in by_gene.items():
        items.sort(key=lambda x: x[sort_key], reverse=True)
        out[g] = items[:top]
    return out


def filter_catalog_entries(entries, *, all_sections=False, sagittal_only=None):
    spec = get_atlas().name
    if spec == "hesta":
        if all_sections:
            return entries
        return [e for e in entries if cat.is_primary_section(e)]
    if spec == "mccsta":
        if all_sections:
            return entries
        return [e for e in entries if cat.is_parquet_section(e)]
    if all_sections or sagittal_only is False:
        return entries
    return [e for e in entries if cat.is_sagittal_section(e)]
