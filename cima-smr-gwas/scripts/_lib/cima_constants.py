"""CIMA table constants for standalone query skills."""
from __future__ import annotations

import os

FTP_BASE = "https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource"
DEFAULT_LOCAL_ROOT = "/public/database/CNGBdb/pub/SciRAID/cdcp/cima/CIMA_Resource"

FTP_TABLES: dict[str, str] = {
    "sample_metadata": "Metadata/CIMA_Sample_Information_Metadata.csv",
    "lead_xqtl": "xQTL/CIMA_Lead_cis-xQTL.csv",
    "smr": "xQTL/CIMA_caQTL_eQTL_SMR.csv",
    "smr_disease": "xQTL/CIMA_Significant_SMR_Pleiotropic_Associations.xlsx",
    "dynamic_eqtl": "xQTL/CIMA_Dynamic_eQTL_of_Bcells_and_Monocytes.csv",
    "eregulon_meta": "GRN/CIMA_eRegulons_Metadata.csv",
    "eregulon_hq": "GRN/CIMA_Selected_High_Quality_eRegulons.csv",
    "eregulon_age": "GRN/CIMA_Age_Related_eRegulons.csv",
    "eregulon_sex": "GRN/CIMA_Sex_Related_eRegulons.csv",
}


def local_resource_root() -> str:
    return os.environ.get("CIMA_RESOURCE_ROOT", DEFAULT_LOCAL_ROOT).rstrip("/")
