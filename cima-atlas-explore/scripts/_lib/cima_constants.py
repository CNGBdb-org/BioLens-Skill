"""CIMA (TrueBlood) atlas constants."""

from __future__ import annotations

FTP_BASE = "https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource"
GITHUB_RESPONSE = "https://raw.githubusercontent.com/CIMA-Project/CIMA/main/Response"

CIMA_VIEWS: list[dict[str, str]] = [
    {"stem": "PBMCs", "explore_id": "CIMA_PBMCs", "label": "All PBMCs"},
    {"stem": "CD4T", "explore_id": "CIMA_CD4T", "label": "CD4+ T"},
    {"stem": "CD8T", "explore_id": "CIMA_CD8T", "label": "CD8+ T"},
    {"stem": "B", "explore_id": "CIMA_B", "label": "B cells"},
    {"stem": "Myeloid", "explore_id": "CIMA_Myeloid", "label": "Myeloid"},
    {"stem": "NK", "explore_id": "CIMA_NK", "label": "NK"},
]

VIEW_STEMS = [v["stem"] for v in CIMA_VIEWS]

CLINICAL_COLS = [
    "age", "sex", "BMI", "height", "weight",
    "blood_type", "BMI_group", "smoking_ststus", "smoking_history",
]

CELLTYPE_LEVELS = ["cell_type_l1", "cell_type_l2", "cell_type_l3", "cell_type_l4"]

AGE_BINS: list[tuple[int, int]] = [
    (20, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 79),
]

FTP_TABLES: dict[str, str] = {
    "sample_metadata": "Metadata/CIMA_Sample_Information_Metadata.csv",
    "lead_xqtl": "xQTL/CIMA_Lead_cis-xQTL.csv",
    "smr": "xQTL/CIMA_caQTL_eQTL_SMR.csv",
    "dynamic_eqtl": "xQTL/CIMA_Dynamic_eQTL_of_Bcells_and_Monocytes.csv",
    "eregulon_meta": "GRN/CIMA_eRegulons_Metadata.csv",
    "eregulon_hq": "GRN/CIMA_Selected_High_Quality_eRegulons.csv",
    "eregulon_age": "GRN/CIMA_Age_Related_eRegulons.csv",
    "eregulon_sex": "GRN/CIMA_Sex_Related_eRegulons.csv",
}

GITHUB_TABLES: dict[str, str] = {
    "age_group": "CIMA_AgeGroup.csv",
    "age_sex_prop": "CIMA_celltype_l4_Proportion_age～sex.csv",
    "celltype_age_summary": "CIMA_cell_type_analysis_summary.csv",
    "dc2_age_corr": "DC2_CD1C_RNA_corr_with_age.csv",
}

DEFAULT_VIEW = "PBMCs"
