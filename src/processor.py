"""
processor.py — 热点提取、设计相关性过滤、评分排序、LLM 摘要与翻译

流程：
  1. 关键词过滤：只保留与「AI 赋能设计」相关的条目
  2. 去重（URL + 标题相似度）
  3. 综合评分（优先级权重 × 时效性衰减）
  4. 分语言排序，取 EN_COUNT / ZH_COUNT 条
  5. LLM 生成摘要：英文条目输出「中英对照」，中文条目输出中文摘要
     摘要聚焦「设计师可操作的实践价值」
"""

import hashlib
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

import requests

from .config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL,
    PRIORITY, EN_COUNT, ZH_COUNT,
    DESIGN_KEYWORDS_EN, DESIGN_KEYWORDS_ZH,
)


# ─────────────────────────────────────────────────────────────────────────────
# 关键词过滤
# ─────────────────────────────────────────────────────────────────────────────

def _is_design_relevant(item: Dict[str, Any]) -> bool:
    """判断条目是否与「AI 赋能设计」相关"""
    lang = item.get("lang", "en")
    text = (
        (item.get("title") or "") + " " +
        (item.get("summary") or "") + " " +
        (item.get("url") or "")
    ).lower()

    keywords = DESIGN_KEYWORDS_ZH if lang == "zh" else DESIGN_KEYWORDS_EN
    for kw in keywords:
        if kw.lower() in text:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# 去重
# ─────────────────────────────────────────────────────────────────────────────

def _url_key(url: str) -> str:
    return re.sub(r"https?://(www\.)?", "", url).rstrip("/").lower()


def _title_key(title: str) -> str:
    return re.sub(r"\W+", "", title).lower()[:60]


def _dedup(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_urls, seen_titles, result = set(), set(), []
    for item in items:
        uk = _url_key(item.get("url", ""))
        tk = _title_key(item.get("title", ""))
        if uk in seen_urls or tk in seen_titles:
            continue
        seen_urls.add(uk)
        seen_titles.add(tk)
        result.append(item)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 评分排序
# ─────────────────────────────────────────────────────────────────────────────

def _score(item: Dict[str, Any]) -> float:
    priority_w = PRIORITY.get(item.get("category", "aggregator"), 1)

    # 时效性衰减：24h 内满分，之后每小时衰减 2%
    pub_ts = item.get("published_ts")
    if pub_ts:
        age_h = max(0, (time.time() - pub_ts) / 3600)
        freshness = max(0.1, 1.0 - max(0, age_h - 24) * 0.02)
    else:
        freshness = 0.5

    return priority_w * freshness


# ─────────────────────────────────────────────────────────────────────────────
# LLM 调用
# ─────────────────────────────────────────────────────────────────────────────

def _llm(messages: list, max_tokens: int = 600) -> str:
    if not OPENAI_API_KEY:
        return ""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }
    try:
        resp = requests.post(
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM] error: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# 英文条目：生成「中英对照」摘要，聚焦设计可操作性
# ─────────────────────────────────────────────────────────────────────────────

def _summarize_en(item: Dict[str, Any]) -> Dict[str, Any]:
    title = item.get("title", "")
    summary = item.get("summary", "")[:800]

    prompt = f"""你是一位专注于「AI 赋能设计」的资讯编辑，服务对象是平面设计师、电商设计师和品牌设计师。

请根据以下英文资讯，完成两件事：
1. 用一句话（≤20字）翻译标题为中文
2. 用 2-3 句话写一段中文摘要，重点回答：
   - 这个 AI 工具/功能/趋势是什么？
   - 设计师可以怎么用？有哪些具体操作场景？
   - 对平面/电商/品牌设计工作流有什么实际价值？

输出格式（严格按此格式，不要多余内容）：
【中文标题】<翻译后的标题>
【中文摘要】<2-3句中文摘要>

---
原标题：{title}
原文摘要：{summary}
"""

    result = _llm([{"role": "user", "content": prompt}], max_tokens=400)

    zh_title = ""
    zh_summary = ""
    if result:
        for line in result.splitlines():
            if line.startswith("【中文标题】"):
                zh_title = line.replace("【中文标题】", "").strip()
            elif line.startswith("【中文摘要】"):
                zh_summary = line.replace("【中文摘要】", "").strip()

    item["zh_title"]   = zh_title or title
    item["zh_summary"] = zh_summary or summary[:120]
    return item


# ─────────────────────────────────────────────────────────────────────────────
# 中文条目：生成设计可操作性摘要
# ─────────────────────────────────────────────────────────────────────────────

def _summarize_zh(item: Dict[str, Any]) -> Dict[str, Any]:
    title = item.get("title", "")
    summary = item.get("summary", "")[:800]

    prompt = f"""你是一位专注于「AI 赋能设计」的资讯编辑，服务对象是平面设计师、电商设计师和品牌设计师。

请根据以下资讯，用 2-3 句话写一段摘要，重点回答：
- 这个 AI 工具/功能/趋势是什么？
- 设计师可以怎么用？有哪些具体操作场景？
- 对平面/电商/品牌设计工作流有什么实际价值？

只输出摘要文字，不要标题、不要序号、不要多余内容。

---
标题：{title}
原文摘要：{summary}
"""

    result = _llm([{"role": "user", "content": prompt}], max_tokens=300)
    item["zh_summary"] = result or summary[:120]
    return item


# ─────────────────────────────────────────────────────────────────────────────
# 判断「可操作性」标签
# ─────────────────────────────────────────────────────────────────────────────

ACTIONABLE_KEYWORDS = [
    # 工具发布/更新
    "launch", "release", "update", "new feature", "tutorial", "how to",
    "workflow", "tips", "guide", "step by step", "plugin", "extension",
    "发布", "上线", "更新", "新功能", "教程", "使用指南",
    "工作流", "技巧", "插件", "实操", "怎么用", "如何",
]

def _tag_actionable(item: Dict[str, Any]) -> Dict[str, Any]:
    """若资讯含有可操作性信号，打上标签"""
    text = (
        (item.get("title") or "") + " " +
        (item.get("summary") or "") + " " +
        (item.get("zh_summary") or "")
    ).lower()
    item["actionable"] = any(kw.lower() in text for kw in ACTIONABLE_KEYWORDS)
    return item


# ─────────────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────────────

def process(raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    输入：fetcher 返回的原始条目列表
    输出：最终推送的 10 条（EN×6 + ZH×4），每条含摘要和标签
    """
    print(f"[processor] 原始条目: {len(raw_items)}")

    # 1. 关键词过滤（只保留设计相关）
    filtered = [item for item in raw_items if _is_design_relevant(item)]
    print(f"[processor] 设计相关过滤后: {len(filtered)}")

    # 2. 去重
    deduped = _dedup(filtered)
    print(f"[processor] 去重后: {len(deduped)}")

    # 3. 分语言
    en_items = [i for i in deduped if i.get("lang") == "en"]
    zh_items = [i for i in deduped if i.get("lang") == "zh"]

    # 4. 评分排序
    en_items.sort(key=_score, reverse=True)
    zh_items.sort(key=_score, reverse=True)

    # 5. 取 Top N
    en_top = en_items[:EN_COUNT]
    zh_top = zh_items[:ZH_COUNT]

    print(f"[processor] 英文候选: {len(en_items)}, 取 {len(en_top)} 条")
    print(f"[processor] 中文候选: {len(zh_items)}, 取 {len(zh_top)} 条")

    # 6. LLM 摘要
    processed_en = []
    for item in en_top:
        try:
            processed_en.append(_summarize_en(item))
        except Exception as e:
            print(f"[processor] EN summarize error: {e}")
            item["zh_title"]   = item.get("title", "")
            item["zh_summary"] = item.get("summary", "")[:120]
            processed_en.append(item)

    processed_zh = []
    for item in zh_top:
        try:
            processed_zh.append(_summarize_zh(item))
        except Exception as e:
            print(f"[processor] ZH summarize error: {e}")
            item["zh_summary"] = item.get("summary", "")[:120]
            processed_zh.append(item)

    # 7. 可操作性标签
    all_items = [_tag_actionable(i) for i in processed_en + processed_zh]

    print(f"[processor] 最终输出: {len(all_items)} 条")
    return all_items
