"""
资讯抓取模块：支持 RSS Feed 和 Hacker News Algolia API
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import (
    EN_SOURCES, ZH_SOURCES, REQUEST_TIMEOUT,
    MAX_ITEMS_PER_SOURCE, PRIORITY,
)

logger = logging.getLogger(__name__)

# 北京时间 = UTC+8
CST = timezone(timedelta(hours=8))


def _now_cst() -> datetime:
    return datetime.now(tz=CST)


def _parse_pub_date(entry) -> datetime:
    """从 feedparser entry 中解析发布时间，返回 CST datetime。"""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return dt.astimezone(CST)
            except Exception:
                pass
    return _now_cst()


def _clean_html(html_text: str) -> str:
    """去除 HTML 标签，返回纯文本（最多 500 字符）。"""
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
    except Exception:
        text = html_text
    return text[:500]


def _fetch_rss(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """抓取单个 RSS 源，返回标准化条目列表。"""
    url = source.get("url", "")
    name = source.get("name", "Unknown")
    category = source.get("category", "aggregator")
    lang = source.get("lang", "en")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        logger.warning("RSS fetch failed [%s]: %s", name, exc)
        return []

    items: List[Dict[str, Any]] = []
    # 只取近 48 小时内的内容（放宽时间窗口）
    cutoff = _now_cst() - timedelta(hours=48)

    for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
        pub_dt = _parse_pub_date(entry)
        if pub_dt < cutoff:
            continue

        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()

        # 摘要：优先 summary，其次 content
        summary_raw = ""
        if hasattr(entry, "summary"):
            summary_raw = entry.summary
        elif hasattr(entry, "content") and entry.content:
            summary_raw = entry.content[0].get("value", "")

        summary = _clean_html(summary_raw)

        if not title or not link:
            continue

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "source": name,
            "category": category,
            "lang": lang,
            "pub_dt": pub_dt,
            "priority": PRIORITY.get(category, 1),
            "score": 0,
        })

    logger.info("Fetched %d items from [%s]", len(items), name)
    return items


def _fetch_hn_ai() -> List[Dict[str, Any]]:
    """
    通过 HN Algolia API 抓取与 AI/ML 相关的热门故事。
    策略：先用 search_by_date 取最新内容，再用 search 取高热度内容，合并去重。
    """
    keywords = ["AI", "LLM", "GPT", "machine learning", "neural network", "Claude", "Gemini"]
    items: List[Dict[str, Any]] = []
    seen_ids: set = set()

    cutoff = _now_cst() - timedelta(hours=48)

    # ── 策略1：最新内容（search_by_date）──────────────────────
    for kw in keywords[:4]:
        url = (
            "https://hn.algolia.com/api/v1/search_by_date?"
            f"query={requests.utils.quote(kw)}"
            "&tags=story"
            "&hitsPerPage=8"
        )
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("HN search_by_date failed for [%s]: %s", kw, exc)
            continue

        for hit in data.get("hits", []):
            obj_id = hit.get("objectID", "")
            if obj_id in seen_ids:
                continue

            created_at = hit.get("created_at", "")
            try:
                pub_dt = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).astimezone(CST)
            except Exception:
                pub_dt = _now_cst()

            if pub_dt < cutoff:
                continue

            title = hit.get("title", "").strip()
            if not title:
                continue

            link = hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}"
            points = hit.get("points", 0) or 0
            num_comments = hit.get("num_comments", 0) or 0

            seen_ids.add(obj_id)
            items.append({
                "title": title,
                "link": link,
                "summary": f"Points: {points} | Comments: {num_comments}",
                "source": "Hacker News (AI)",
                "category": "aggregator",
                "lang": "en",
                "pub_dt": pub_dt,
                "priority": PRIORITY["aggregator"],
                "score": points + num_comments * 0.5,
            })

        time.sleep(0.3)

    # ── 策略2：高热度内容（search，放宽时间到7天）────────────
    for kw in ["AI", "LLM"]:
        url = (
            "https://hn.algolia.com/api/v1/search?"
            f"query={requests.utils.quote(kw)}"
            "&tags=story"
            "&numericFilters=points>50"
            "&hitsPerPage=10"
        )
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("HN search failed for [%s]: %s", kw, exc)
            continue

        for hit in data.get("hits", []):
            obj_id = hit.get("objectID", "")
            if obj_id in seen_ids:
                continue

            created_at = hit.get("created_at", "")
            try:
                pub_dt = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).astimezone(CST)
            except Exception:
                pub_dt = _now_cst()

            # 高热度内容放宽到 7 天
            if pub_dt < _now_cst() - timedelta(days=7):
                continue

            title = hit.get("title", "").strip()
            if not title:
                continue

            link = hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}"
            points = hit.get("points", 0) or 0
            num_comments = hit.get("num_comments", 0) or 0

            seen_ids.add(obj_id)
            items.append({
                "title": title,
                "link": link,
                "summary": f"Points: {points} | Comments: {num_comments}",
                "source": "Hacker News (AI)",
                "category": "aggregator",
                "lang": "en",
                "pub_dt": pub_dt,
                "priority": PRIORITY["aggregator"],
                "score": points + num_comments * 0.5,
            })

        time.sleep(0.3)

    # 去重并按 score 排序
    unique: Dict[str, Dict] = {}
    for item in items:
        key = item["title"].lower()[:50]
        if key not in unique or item["score"] > unique[key]["score"]:
            unique[key] = item

    result = sorted(unique.values(), key=lambda x: x["score"], reverse=True)
    logger.info("Fetched %d items from [Hacker News AI]", len(result))
    return result[:MAX_ITEMS_PER_SOURCE]


def fetch_all() -> Dict[str, List[Dict[str, Any]]]:
    """
    抓取所有渠道，返回 {"en": [...], "zh": [...]}。
    """
    en_items: List[Dict[str, Any]] = []
    zh_items: List[Dict[str, Any]] = []

    # 英文渠道
    for source in EN_SOURCES:
        if source.get("type") == "hn_top":
            en_items.extend(_fetch_hn_ai())
        else:
            en_items.extend(_fetch_rss(source))
        time.sleep(0.5)

    # 中文渠道
    for source in ZH_SOURCES:
        zh_items.extend(_fetch_rss(source))
        time.sleep(0.5)

    logger.info(
        "Total fetched: EN=%d, ZH=%d", len(en_items), len(zh_items)
    )
    return {"en": en_items, "zh": zh_items}
