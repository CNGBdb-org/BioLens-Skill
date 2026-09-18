"""Normalize STOmics portal species metadata to consistent 中文 labels."""

from __future__ import annotations

import json
import re
from typing import Any

# NCBI taxonomy_id -> 中文（门户学名对应常用中文名）
TAXID_ZH: dict[str, str] = {
    "9606": "人",
    "10090": "小鼠",
    "10116": "褐家鼠",
    "7955": "斑马鱼",
    "9031": "鸡",
    "4577": "玉米",
    "4081": "番茄",
    "3702": "拟南芥",
    "4565": "小麦",
    "4113": "马铃薯",
    "9541": "食蟹猴",
    "9544": "猕猴",
    "9598": "黑猩猩",
    "9615": "犬",
    "9913": "牛",
    "9796": "马",
    "9823": "野猪",
    "8364": "蝾螈",
    "7227": "果蝇",
    "3847": "大豆",
    "38482": "蝴蝶兰",
}

# common / scientific name (lower) -> 中文
NAME_ZH: dict[str, str] = {
    "human": "人",
    "homo sapiens": "人",
    "mouse": "小鼠",
    "house mouse": "小鼠",
    "mus musculus": "小鼠",
    "rat": "褐家鼠",
    "brown rat": "褐家鼠",
    "rattus norvegicus": "褐家鼠",
    "norway rat": "褐家鼠",
    "zebrafish": "斑马鱼",
    "danio rerio": "斑马鱼",
    "chicken": "鸡",
    "gallus gallus": "鸡",
    "maize": "玉米",
    "zea mays": "玉米",
    "corn": "玉米",
    "tomato": "番茄",
    "solanum lycopersicum": "番茄",
    "thale-cress": "拟南芥",
    "thale cress": "拟南芥",
    "arabidopsis thaliana": "拟南芥",
    "bread wheat": "小麦",
    "triticum aestivum": "小麦",
    "wheat": "小麦",
    "potato": "马铃薯",
    "solanum tuberosum": "马铃薯",
    "soybean": "大豆",
    "glycine max": "大豆",
    "cynomolgus monkey": "食蟹猴",
    "cynomolgus monkeys": "食蟹猴",
    "macaca fascicularis": "食蟹猴",
    "crab-eating macaque": "食蟹猴",
    "marmoset": "狨猴",
    "callithrix jacchus": "狨猴",
    "axolotl": "蝾螈",
    "ambystoma mexicanum": "蝾螈",
    "fruit fly": "果蝇",
    "drosophila melanogaster": "果蝇",
    "planarian": "涡虫",
    "schmidtea mediterranea": "涡虫",
    "phalaenopsis aphrodite": "蝴蝶兰",
    "kikko-chiku": "竹",
    "bamboo": "竹",
    "cucumber": "黄瓜",
    "cucumis sativus": "黄瓜",
    "canis lupus familiaris": "犬",
    "caenorhabditis elegans": "秀丽隐杆线虫",
    "oryctolagus cuniculus": "兔",
    "sus scrofa": "猪",
    "ambystoma mexicanum": "蝾螈",
    "macaca mulatta": "猕猴",
    "macaca fascicularis": "食蟹猴",
    "bambusa oldhamii": "竹",
    "phyllostachys edulis": "竹",
}

# 中文 -> 英文（catalog 展示用学名或常用英文名）
ZH_TO_EN: dict[str, str] = {
    "人": "Homo sapiens",
    "小鼠": "Mus musculus",
    "褐家鼠": "Rattus norvegicus",
    "斑马鱼": "Danio rerio",
    "鸡": "Gallus gallus",
    "玉米": "Zea mays",
    "番茄": "Solanum lycopersicum",
    "拟南芥": "Arabidopsis thaliana",
    "小麦": "Triticum aestivum",
    "马铃薯": "Solanum tuberosum",
    "大豆": "Glycine max",
    "食蟹猴": "Macaca fascicularis",
    "猕猴": "Macaca mulatta",
    "狨猴": "Callithrix jacchus",
    "黑猩猩": "Pan troglodytes",
    "犬": "Canis lupus familiaris",
    "牛": "Bos taurus",
    "马": "Equus caballus",
    "野猪": "Sus scrofa",
    "蝾螈": "Ambystoma mexicanum",
    "墨西哥钝口蝾螈（蝾螈）": "Ambystoma mexicanum",
    "果蝇": "Drosophila melanogaster",
    "涡虫": "Schmidtea mediterranea",
    "蝴蝶兰": "Phalaenopsis aphrodite",
    "竹": "Bamboo",
    "黄瓜": "Cucumis sativus",
    "秀丽隐杆线虫": "Caenorhabditis elegans",
    "兔": "Oryctolagus cuniculus",
    "猪": "Sus scrofa",
}

TAXID_EN: dict[str, str] = {
    tid: ZH_TO_EN[zh] for tid, zh in TAXID_ZH.items() if zh in ZH_TO_EN
}

TEXT_KEYWORDS: list[tuple[str, str]] = [
    ("zebrafish", "斑马鱼"),
    ("danio rerio", "斑马鱼"),
    ("house mouse", "小鼠"),
    ("mus musculus", "小鼠"),
    ("rattus norvegicus", "褐家鼠"),
    ("brown rat", "褐家鼠"),
    ("homo sapiens", "人"),
    ("human early embryo", "人"),
    ("human ", "人"),
    ("zea mays", "玉米"),
    ("maize", "玉米"),
    ("solanum lycopersicum", "番茄"),
    ("tomato", "番茄"),
    ("arabidopsis", "拟南芥"),
    ("thale-cress", "拟南芥"),
    ("triticum aestivum", "小麦"),
    ("bread wheat", "小麦"),
    ("glycine max", "大豆"),
    ("soybean", "大豆"),
    ("solanum tuberosum", "马铃薯"),
    ("potato", "马铃薯"),
    ("gallus gallus", "鸡"),
    ("chicken", "鸡"),
    ("drosophila", "果蝇"),
    ("fruit fly", "果蝇"),
    ("axolotl", "蝾螈"),
    ("ambystoma", "蝾螈"),
    ("planarian", "涡虫"),
    ("schmidtea", "涡虫"),
    ("macaca fascicularis", "食蟹猴"),
    ("cynomolgus", "食蟹猴"),
    ("callithrix", "狨猴"),
    ("marmoset", "狨猴"),
    ("phalaenopsis", "蝴蝶兰"),
    ("bamboo", "竹"),
    ("cucumber", "黄瓜"),
    ("mouse", "小鼠"),
    ("rat", "褐家鼠"),
]


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def extract_gsm(text: str) -> str:
    m = re.search(r"(GSM\d+)", text or "")
    if m:
        return m.group(1)
    # Portal filenames occasionally drop the leading G (e.g. SM6177628).
    m = re.search(r"SM(\d{7,})", text or "")
    if m:
        return f"GSM{m.group(1)}"
    return ""


def normalize_species_label(raw: str) -> str:
    """Map portal organism / scientific name to 中文."""
    s = _clean(raw)
    if not s:
        return ""
    low = s.lower()
    if low in NAME_ZH:
        return NAME_ZH[low]
    if re.search(r"[\u4e00-\u9fff]", s):
        return s
    for key, zh in NAME_ZH.items():
        if key in low or low in key:
            return zh
    return s


def species_zh_only(label: str) -> str:
    """Extract canonical 中文 from plain or bilingual catalog label."""
    s = _clean(label)
    if not s:
        return ""
    if " / " in s:
        parts = [p.strip() for p in s.split(" / ")]
        if len(parts) == 2 and re.search(r"[A-Za-z]", parts[0]):
            return normalize_species_label(parts[1]) or parts[1]
        if is_multi_species_cell(s):
            return ""
    zh = normalize_species_label(s)
    if zh:
        return zh
    return s if re.search(r"[\u4e00-\u9fff]", s) else ""


def is_multi_species_cell(label: str) -> bool:
    """True if label lists multiple species (not English / 中文 bilingual)."""
    s = _clean(label)
    if " / " not in s:
        return False
    parts = [p.strip() for p in s.split(" / ")]
    if len(parts) == 2 and re.search(r"[A-Za-z]", parts[0]) and re.search(
        r"[\u4e00-\u9fff]", parts[1]
    ):
        return False
    if len(parts) >= 4 and re.search(r"[A-Za-z]", parts[0]):
        return True
    if all(
        re.search(r"[\u4e00-\u9fff]", p) and not re.search(r"[A-Za-z]", p) for p in parts
    ):
        return len(parts) > 1
    return False


def format_species_bilingual(zh: str, en: str | None = None) -> str:
    """Catalog Species: ``English / 中文`` (single species per row)."""
    zh = normalize_species_label(zh) or _clean(zh)
    if not zh:
        return ""
    if en:
        en_label = _clean(en)
    elif zh in ZH_TO_EN:
        en_label = ZH_TO_EN[zh]
    elif not re.search(r"[\u4e00-\u9fff]", zh):
        en_label = zh
        zh = normalize_species_label(zh) or zh
        if zh in ZH_TO_EN:
            en_label = ZH_TO_EN[zh] if en_label.lower() == zh.lower() else en_label
    else:
        return zh
    if not en_label:
        return zh
    return f"{en_label} / {zh}"


def format_catalog_species(label: str) -> str:
    """Normalize any species cell to bilingual display when possible."""
    if not _clean(label):
        return ""
    if is_multi_species_cell(label):
        return label
    zh = species_zh_only(label)
    if not zh:
        return label
    return format_species_bilingual(zh)


def species_zh_from_entry(entry: dict[str, Any]) -> str:
    tid = str(entry.get("taxonomy_id") or "").strip()
    if tid in TAXID_ZH:
        return TAXID_ZH[tid]
    for name in (entry.get("common_names") or []) + [entry.get("scientific_name") or ""]:
        if name:
            zh = normalize_species_label(str(name))
            if zh:
                return zh
    return ""


def species_from_text(*texts: str) -> str:
    blob = " ".join(_clean(t) for t in texts if t).lower()
    if not blob:
        return ""
    for kw, zh in TEXT_KEYWORDS:
        if kw in blob:
            return zh
    return ""


def all_species_zh_from_data(data: dict[str, Any]) -> list[str]:
    """All dataset-level species (portal Species 字段，保序去重)."""
    labels: list[str] = []
    sp = data.get("species") or []
    if not isinstance(sp, list):
        sp = [sp]
    for entry in sp:
        if isinstance(entry, dict):
            zh = species_zh_from_entry(entry)
        else:
            zh = normalize_species_label(str(entry))
        if zh and zh not in labels:
            labels.append(zh)
    return labels


def dataset_species_summary(data: dict[str, Any], samples: list[dict] | None = None) -> str:
    """Dataset 级物种：多物种用「 / 」连接，与 cbmsta 写法一致."""
    labels = all_species_zh_from_data(data)
    if not labels and samples:
        for s in samples:
            zh = normalize_species_label(s.get("organism") or "")
            if zh and zh not in labels:
                labels.append(zh)
    if labels:
        return " / ".join(labels)

    ref = data.get("reference")
    if ref:
        try:
            ref_obj = json.loads(ref) if isinstance(ref, str) else ref
            if isinstance(ref_obj, list):
                for item in ref_obj:
                    tid = str(item.get("taxid") or item.get("taxonomy_id") or "").strip()
                    if tid in TAXID_ZH:
                        zh = TAXID_ZH[tid]
                        if zh not in labels:
                            labels.append(zh)
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
    if labels:
        return " / ".join(labels)

    zh = species_from_text(data.get("title") or "", data.get("summary") or "")
    return zh


def species_from_portal_data(data: dict[str, Any], samples: list[dict] | None = None) -> str:
    return dataset_species_summary(data, samples)


def tissues_from_data(data: dict[str, Any]) -> str:
    t = data.get("tissues") or []
    if isinstance(t, list):
        return ", ".join(str(x) for x in t)
    return str(t or "")


def format_disease_field(raw: Any) -> str:
    """Normalize portal disease (list or string) to catalog cell text."""
    if raw is None:
        return ""
    if isinstance(raw, list):
        parts = [_clean(str(x)) for x in raw if _clean(str(x))]
        parts = [p for p in parts if p not in ("--", "Normal", "normal", "Healthy", "healthy")]
        return ", ".join(dict.fromkeys(parts))
    s = _clean(str(raw))
    if s in ("--", "Normal", "normal", "Healthy", "healthy"):
        return ""
    return s


def build_gsm_index(samples: list[dict]) -> dict[str, dict[str, str]]:
    """GSM -> per-sample metadata from paginated Sample 表."""
    idx: dict[str, dict[str, str]] = {}
    for s in samples:
        meta = _sample_meta_dict(s)
        for field in (s.get("sample_accession"), s.get("source_sample_id")):
            gsm = extract_gsm(str(field or ""))
            if gsm:
                idx[gsm] = meta
    return idx


def _norm_file_stem(name: str) -> str:
    s = _clean(name)
    if s.endswith(".h5ad"):
        s = s[:-5]
    for suf in ("_10xvisium_processed", "_ST_processed", "_processed", "_ST"):
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    return s.lower()


def _sample_meta_dict(s: dict) -> dict[str, str]:
    tissues = s.get("tissues") or []
    if isinstance(tissues, list):
        tissue = ", ".join(str(x) for x in tissues if x)
    else:
        tissue = str(tissues or "")
    stage = _clean(s.get("sample_title") or "")
    if not tissue and stage:
        tissue = stage
    species = normalize_species_label(s.get("organism") or "")
    if not species:
        tid = str(s.get("taxonomy_id") or "").strip()
        if tid in TAXID_ZH:
            species = TAXID_ZH[tid]
    diseases = s.get("diseases")
    if diseases is None:
        diseases = s.get("disease")
    return {
        "species": species,
        "tissue": tissue,
        "stage": stage,
        "technology": normalize_technology(s.get("technology") or ""),
        "disease": format_disease_field(diseases),
    }


def build_stem_index(samples: list[dict]) -> dict[str, dict[str, str]]:
    """Normalized file stem -> sample metadata (when GSM absent in filename)."""
    idx: dict[str, dict[str, str]] = {}
    for s in samples:
        meta = _sample_meta_dict(s)
        title = _clean(s.get("sample_title") or "")
        if not title:
            continue
        keys = {
            _norm_file_stem(title),
            _norm_file_stem(f"{title}_ST"),
            _norm_file_stem(f"{title}_ST_processed"),
            title.lower(),
        }
        for k in keys:
            if k:
                idx[k] = meta
    return idx


def species_from_section_rules(atlas: str, section: str, stage: str = "") -> str:
    """Single-species inference from atlas + h5ad filename (named / multi-species atlases)."""
    atlas = atlas.strip().lower()
    raw = section or stage
    s = _norm_file_stem(raw) if raw else ""
    low = (section or stage or "").lower()

    if atlas in ("cbmsta", "stds0000244"):
        if "marmoset" in low:
            return "狨猴"
        if "macaque" in low:
            return "猕猴"
        if "mouse" in low:
            return "小鼠"
        if "cynomolgus" in low:
            return "食蟹猴"

    if atlas in ("ctsta", "stds0000379"):
        if "tomato" in low:
            return "番茄"
        if "cucumber" in low or "gy14" in low:
            return "黄瓜"
        if s.startswith("0dpa"):
            return "番茄"
        if s.startswith("fm_"):
            return "黄瓜"
        if re.match(r"s[45]_", s):
            return "黄瓜"
        if re.match(r"s[67]_", s):
            return "番茄"
        if s.startswith("s8_"):
            return "黄瓜"

    if "mob" in low and ("_st" in low or "mob_st" in s):
        return "小鼠"
    if "layer" in low and "_bc" in low:
        return "人"
    if low.startswith("he_") and "mob" in low:
        return "小鼠"
    if low.startswith("he_"):
        return "人"

    if "ratcolon" in low or ("rat" in low and "colon" in low):
        return "褐家鼠"
    if "donor" in low or "pancrea" in low:
        return "人"
    if "b16" in low or "mc38" in low:
        return "小鼠"

    # GSE123187 gastruloid atlas (mouse + human gastruloids; m/h prefix in filenames).
    if atlas == "stds0000074" or "gse123187" in low:
        if re.search(r"mgstrld", low) or "mouseembryo" in low or re.search(r"_mg\d", low):
            return "小鼠"
        if re.search(r"hgstrld", low) or re.search(r"_hg\d", low):
            return "人"

    if atlas == "stds0000069" and ("nucspeckle" in low or "stressgranule" in low):
        return "人"

    if atlas == "stds0000133" and "spleen" in low:
        return "小鼠"

    if atlas == "stds0000153":
        return "人"

    return ""


def build_stsp_index(samples: list[dict]) -> dict[str, dict[str, str]]:
    """STSP sample_id / sample_name -> metadata."""
    idx: dict[str, dict[str, str]] = {}
    for s in samples:
        meta = _sample_meta_dict(s)
        for key in (s.get("sample_id"), s.get("sample_name")):
            k = _clean(str(key or ""))
            if k:
                idx[k] = meta
    return idx


def species_from_file_record(
    file_rec: dict, stsp_index: dict[str, dict[str, str]]
) -> str:
    for key in (file_rec.get("sample_name"), file_rec.get("sample_id")):
        k = _clean(str(key or ""))
        if k and k in stsp_index:
            return stsp_index[k].get("species") or ""
    return ""


def row_metadata_for_h5ad(
    filename: str,
    gsm_index: dict[str, dict[str, str]],
    data: dict[str, Any],
    *,
    dataset_tech: str = "",
    stem_index: dict[str, dict[str, str]] | None = None,
    atlas: str = "",
    file_rec: dict | None = None,
    stsp_index: dict[str, dict[str, str]] | None = None,
) -> dict[str, str]:
    """Per-h5ad Species / Tissue / Technology from matched GSM or sample title."""
    if file_rec and stsp_index:
        sp = species_from_file_record(file_rec, stsp_index)
        if sp:
            stem = filename[:-5] if filename.endswith(".h5ad") else filename
            m = stsp_index.get((file_rec.get("sample_name") or "").strip(), {})
            return {
                "species": sp,
                "tissue": m.get("tissue") or tissues_from_data(data),
                "stage": m.get("stage") or stem,
                "technology": m.get("technology") or dataset_tech,
                "disease": m.get("disease") or "",
            }
    gsm = extract_gsm(filename)
    stem = filename[:-5] if filename.endswith(".h5ad") else filename
    if gsm and gsm in gsm_index:
        m = gsm_index[gsm]
        return {
            "species": m["species"],
            "tissue": m["tissue"],
            "stage": m["stage"] or stem,
            "technology": m["technology"] or dataset_tech,
            "disease": m.get("disease") or "",
        }
    if stem_index:
        key = _norm_file_stem(filename)
        if key in stem_index:
            m = stem_index[key]
            return {
                "species": m["species"],
                "tissue": m["tissue"],
                "stage": m["stage"] or stem,
                "technology": m["technology"] or dataset_tech,
                "disease": m.get("disease") or "",
            }
        stage_key = _norm_file_stem(stem)
        if stage_key in stem_index:
            m = stem_index[stage_key]
            return {
                "species": m["species"],
                "tissue": m["tissue"],
                "stage": m["stage"] or stem,
                "technology": m["technology"] or dataset_tech,
                "disease": m.get("disease") or "",
            }
    ruled = species_from_section_rules(atlas, filename, stem)
    if ruled:
        return {
            "species": ruled,
            "tissue": tissues_from_data(data),
            "stage": stem,
            "technology": dataset_tech,
            "disease": "",
        }
    low = filename.lower()
    species = ""
    if re.search(r"mgstrld", low) or "mouseembryo" in low or re.search(r"_mg\d", low):
        species = "小鼠"
    elif re.search(r"hgstrld", low) or re.search(r"_hg\d", low):
        species = "人"
    elif "ratcolon" in low:
        species = "褐家鼠"
    elif "donor" in low or "pancrea" in low:
        species = "人"
    elif "b16" in low or "mc38" in low:
        species = "小鼠"
    return {
        "species": species,
        "tissue": tissues_from_data(data),
        "stage": stem,
        "technology": dataset_tech,
        "disease": "",
    }


def disease_for_catalog_row(
    section: str,
    stage: str,
    *,
    gsm_index: dict[str, dict[str, str]] | None = None,
    stem_index: dict[str, dict[str, str]] | None = None,
    stsp_index: dict[str, dict[str, str]] | None = None,
    scsp_index: dict[str, dict[str, str]] | None = None,
) -> str:
    """Resolve per-row Disease from pre-built sample indexes."""
    filename = section if section.endswith(".h5ad") else f"{section}.h5ad"
    gsm = extract_gsm(filename) or extract_gsm(stage or "")
    if gsm_index and gsm and gsm in gsm_index:
        d = gsm_index[gsm].get("disease") or ""
        if d:
            return d
    if stem_index:
        for key in (_norm_file_stem(filename), _norm_file_stem(stage or ""), (stage or "").lower()):
            if key and key in stem_index:
                d = stem_index[key].get("disease") or ""
                if d:
                    return d
    if stsp_index:
        for key in (extract_gsm(filename), _norm_file_stem(filename)):
            if key and key in stsp_index:
                d = stsp_index[key].get("disease") or ""
                if d:
                    return d
    if scsp_index:
        m = re.search(r"/(SCSP\d+)/", section or "", re.I)
        if not m:
            m = re.search(r"/(SCSP\d+)/", stage or "", re.I)
        if m:
            scsp = m.group(1).upper()
            if scsp in scsp_index:
                return scsp_index[scsp].get("disease") or ""
        for key in (_norm_file_stem(filename), _norm_file_stem(stage or ""), gsm):
            if key and key in scsp_index:
                d = scsp_index[key].get("disease") or ""
                if d:
                    return d
    return ""


def technology_from_portal_data(data: dict[str, Any], samples: list[dict] | None = None) -> str:
    techs = data.get("stomics_technologies") or []
    if isinstance(techs, list) and techs:
        return normalize_technology(str(techs[0]))
    if samples:
        for s in samples:
            t = _clean(s.get("technology") or "")
            if t:
                return normalize_technology(t)
    return ""


def normalize_technology(raw: str) -> str:
    s = _clean(raw)
    if not s:
        return ""
    mapping = {
        "stereo-seq": "Stereo-seq",
        "stereo seq": "Stereo-seq",
        "stereoseq": "Stereo-seq",
        "10x visium": "10x Visium",
        "10xvisium": "10x Visium",
        "visium": "10x Visium",
        "spatial transcriptomics": "Spatial Transcriptomics",
        "dnbelab c4": "DNBelab C4",
        "scrna": "scRNA-seq",
        "scrna-seq": "scRNA-seq",
    }
    low = s.lower()
    for k, v in mapping.items():
        if k in low:
            return v
    return s
