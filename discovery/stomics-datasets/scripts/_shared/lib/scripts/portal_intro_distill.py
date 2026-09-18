"""Distill CNGB STDS/SCDS portal summaries into HESTA-style Chinese intros."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

_DISTILL_EXAMPLES = """
HESTA 示例：原肠胚后人类胚胎 Stereo-seq 时空 atlas（HESTA）：13 个胚胎 CS12–23 共 77 张 sagittal 切片，建立 50 个器官发育轨迹与调控图谱，解析病毒易感性、印记基因等关键问题。
MOSTA 示例：C57BL/6 小鼠 E9.5–E16.5 器官发生 Stereo-seq 全景 atlas（MOSTA）：53 张 sagittal 切片，提供组织注释、基因表达、共表达模块与 regulon 空间检索。
ABSNA 示例：汇集鳖、雀、鸽、小鼠、猕猴五种羊膜动物完整全脑 snRNA 单细胞图谱；并与既有小鼠、猕猴脑图谱整合比较，用于解析羊膜动物脑细胞类型演化。
""".strip()

_SYSTEM = (
    "你是 CNGBdb 数据库简介编辑。根据门户英文 title/summary 等信息，"
    "写 1–2 句中文简介（80–200 字），风格与下列专题库简介一致：\n"
    f"{_DISTILL_EXAMPLES}\n\n"
    "要求：说明物种、组织/疾病/发育阶段、组学技术与核心科学问题；"
    "用完整中文句子；不要 bullet；不要「本数据库」「门户收录」等套话；"
    "不要复述数据库编号；只输出简介正文。"
)


def _truncate(text: str, max_len: int = 200) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1]
    if "，" in cut[ max_len // 2 :]:
        cut = cut[: cut.rfind("，") + 1]
    elif "。" in cut:
        cut = cut[: cut.rfind("。") + 1]
    else:
        cut = cut.rstrip("，、；; ") + "…"
    return cut


def _call_distill_llm(prompt: str) -> str:
    """Prefer deepseek-v4-pro with enough tokens for non-reasoning reply."""
    try:
        from web.llm_router import (
            DEEPSEEK_API_KEY,
            DEEPSEEK_BASE_URL,
            DEEPSEEK_MODEL,
            DEEPSEEK_TIMEOUT,
            OLLAMA_HOST,
            OLLAMA_MODEL,
            OLLAMA_TIMEOUT,
            llm_provider_for_enhance,
        )
    except ImportError:
        return ""

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": prompt},
    ]

    if DEEPSEEK_API_KEY:
        for model in (DEEPSEEK_MODEL, "deepseek-v4-pro"):
            body = json.dumps({
                "model": model,
                "messages": messages,
                "temperature": 0.25,
                "max_tokens": 1200,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=max(DEEPSEEK_TIMEOUT, 90)) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                msg = (data.get("choices") or [{}])[0].get("message") or {}
                text = (msg.get("content") or "").strip()
                if text:
                    return text
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                continue

    if llm_provider_for_enhance() == "ollama":
        body = json.dumps({
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.25, "num_predict": 512},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return (data.get("message") or {}).get("content", "").strip()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return ""
    return ""


def _build_distill_prompt(record: dict[str, str]) -> str:
    parts = [
        f"数据库 ID：{record.get('atlas_id') or ''}",
        f"英文标题：{record.get('title') or ''}",
    ]
    if record.get("species"):
        parts.append(f"物种：{record['species']}")
    if record.get("tissues"):
        parts.append(f"组织/部位：{record['tissues']}")
    if record.get("technology"):
        parts.append(f"技术：{record['technology']}")
    if record.get("sample_number"):
        parts.append(f"样本规模：{record['sample_number']}")
    if record.get("citation"):
        parts.append(f"引用：{record['citation'][:280]}")
    summary = (record.get("summary") or "").strip()
    if summary:
        parts.append(f"门户摘要：{summary[:1400]}")
    return "\n".join(parts)


def fallback_intro_from_record(record: dict[str, str]) -> str:
    """Registry-free fallback when portal fetch or LLM fails."""
    from web.catalog_zh import portal_intro_zh

    atlas_id = (record.get("atlas_id") or "").upper()
    title = record.get("title") or ""
    return portal_intro_zh(
        atlas_id,
        display=title,
        species=record.get("species") or "",
        technology=record.get("technology") or "",
        n_rows=int(record.get("sample_number") or 0) if str(record.get("sample_number") or "").isdigit() else 0,
        max_len=200,
    )


def distill_portal_intro_zh(
    record: dict[str, str],
    *,
    use_llm: bool = True,
) -> str:
    """Return HESTA-style Chinese intro from a portal record."""
    if not record:
        return ""
    prompt = _build_distill_prompt(record)
    if use_llm:
        text = _call_distill_llm(prompt)
        text = re.sub(r"^[\"'「『]+|[\"'」』]+$", "", text.strip())
        text = re.sub(r"^(简介|说明)[：:]\s*", "", text)
        if text and re.search(r"[\u4e00-\u9fff]", text) and len(text) >= 24:
            return _truncate(text, 220)
    fb = fallback_intro_from_record(record)
    return fb if fb and fb != "—" else ""
