"""
热点提取与排序模块：
1. 对每条资讯用 LLM 生成中文摘要（英文条目同时保留原文）
2. 按优先级 + 时效性综合评分排序
3. 按 EN:ZH = 6:4 比例选出最终 10 条热点
"""

import json
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from .config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL,
    EN_COUNT, ZH_COUNT, PRIORITY,
)

logger = logging.getLogger(__name__)

CST = timezone(timedelta(hours=8))


# ─────────────────────────────────────────────
# LLM 调用（使用 requests 直接调用，避免 SDK 版本问题）
# ─────────────────────────────────────────────
import requests as _requests

def _llm_chat(messages: list, max_tokens: int = 300, temperature: float = 0.3) -> str:
    """直接调用 OpenAI 兼容 API，返回 assistant 消息内容。"""
    if not OPENAI_API_KEY:
        return ""
    base = OPENAI_BASE_URL.rstrip("/")
    url = f"{base}/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = _requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("LLM API call failed: %s", exc)
        return ""


# ─────────────────────────────────────────────
# 评分函数
# ─────────────────────────────────────────────
def _time_decay(pub_dt: datetime) -> float:
    """
    时效性衰减：距离现在越近分数越高。
    24h 内满分 1.0，每超过 1h 衰减 0.02，最低 0.1。
    """
    now = datetime.now(tz=CST)
    hours_ago = max(0, (now - pub_dt).total_seconds() / 3600)
    score = max(0.1, 1.0 - hours_ago * 0.02)
    return score


def _compute_score(item: Dict[str, Any]) -> float:
    """综合评分 = 优先级权重 * 时效性衰减 + 热度分（归一化）"""
    priority_weight = PRIORITY.get(item.get("category", "aggregator"), 1)
    time_score = _time_decay(item["pub_dt"])
    hot_score = min(item.get("score", 0) / 500.0, 1.0)
    return priority_weight * time_score + hot_score * 0.5


# ─────────────────────────────────────────────
# 去重
# ─────────────────────────────────────────────
def _deduplicate(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """基于标题指纹去重。"""
    seen: List[str] = []
    result: List[Dict[str, Any]] = []
    for item in items:
        title = item["title"].lower().strip()
        fingerprint = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", title)[:30]
        if fingerprint in seen:
            continue
        seen.append(fingerprint)
        result.append(item)
    return result


# ─────────────────────────────────────────────
# LLM 摘要与翻译
# ─────────────────────────────────────────────
def _summarize_en(item: Dict[str, Any]) -> Dict[str, Any]:
    """英文条目：生成中文标题 + 中文摘要（中英对照）。"""
    title = item["title"]
    raw_summary = item.get("summary", "")

    prompt = (
        "You are an AI news editor. Given the following English AI news title and snippet, produce:\n"
        "1. A concise Chinese title translation\n"
        "2. A Chinese summary of 2-3 sentences (核心要点，不超过120字)\n\n"
        f"Title: {title}\n"
        f"Snippet: {raw_summary[:300]}\n\n"
        'Respond ONLY with valid JSON:\n{"zh_title": "...", "zh_summary": "..."}'
    )

    content = _llm_chat([{"role": "user", "content": prompt}], max_tokens=300)

    if content:
        try:
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                item["zh_title"] = data.get("zh_title", title)
                item["zh_summary"] = data.get("zh_summary", "")
                return item
        except Exception:
            pass

    item["zh_title"] = title
    item["zh_summary"] = ""
    return item


def _summarize_zh(item: Dict[str, Any]) -> Dict[str, Any]:
    """中文条目：生成 2~3 句中文摘要。"""
    title = item["title"]
    raw_summary = item.get("summary", "")

    if not raw_summary:
        item["zh_summary"] = ""
        return item

    prompt = (
        "你是一位AI资讯编辑。请根据以下标题和摘要，用2~3句话（不超过100字）提炼核心要点，语言简洁专业。\n\n"
        f"标题：{title}\n"
        f"摘要：{raw_summary[:300]}\n\n"
        "只输出摘要文本，不要其他内容。"
    )

    content = _llm_chat([{"role": "user", "content": prompt}], max_tokens=200)
    item["zh_summary"] = content if content else raw_summary[:100]
    return item


# ─────────────────────────────────────────────
# 主处理流程
# ─────────────────────────────────────────────
def process(raw: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    输入：fetch_all() 返回的 {"en": [...], "zh": [...]}
    输出：最终热点列表（≤10条，EN:ZH ≈ 6:4）
    """
    en_items = raw.get("en", [])
    zh_items = raw.get("zh", [])

    # 1. 计算综合评分
    for item in en_items:
        item["_score"] = _compute_score(item)
    for item in zh_items:
        item["_score"] = _compute_score(item)

    # 2. 排序
    en_items.sort(key=lambda x: x["_score"], reverse=True)
    zh_items.sort(key=lambda x: x["_score"], reverse=True)

    # 3. 去重
    en_items = _deduplicate(en_items)
    zh_items = _deduplicate(zh_items)

    # 4. 取 Top-N
    top_en = en_items[:EN_COUNT]
    top_zh = zh_items[:ZH_COUNT]

    # 5. LLM 摘要（带速率保护）
    processed_en = []
    for item in top_en:
        processed_en.append(_summarize_en(item))
        time.sleep(0.5)

    processed_zh = []
    for item in top_zh:
        processed_zh.append(_summarize_zh(item))
        time.sleep(0.5)

    # 6. 合并：英文在前，中文在后
    final = processed_en + processed_zh

    logger.info(
        "Processing complete: EN=%d, ZH=%d, Total=%d",
        len(processed_en), len(processed_zh), len(final),
    )
    return final
