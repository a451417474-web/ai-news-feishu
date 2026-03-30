"""
fetcher.py — 多渠道 RSS 抓取器

支持：
  - 标准 RSS / Atom feed（feedparser）
  - 所有渠道均通过 RSS URL 抓取，无需特殊 API
"""

import re
import time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Dict, Any

import feedparser
import requests

from config import (
    EN_SOURCES, ZH_SOURCES,
    REQUEST_TIMEOUT, MAX_ITEMS_PER_SOURCE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# 只抓取 48 小时内的内容（设计类资讯时效性要求稍宽松）
MAX_AGE_HOURS = 48


# ─────────────────────────────────────────────────────────────────────────────
# 时间解析
# ─────────────────────────────────────────────────────────────────────────────

def _parse_ts(entry) -> float:
    """从 feedparser entry 中解析发布时间戳，失败返回当前时间"""
    for attr in ("published", "updated", "created"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return dt.timestamp()
            except Exception:
                pass
    # feedparser 有时会解析为 time.struct_time
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).timestamp()
            except Exception:
                pass
    return time.time()


# ─────────────────────────────────────────────────────────────────────────────
# 清理 HTML 摘要
# ─────────────────────────────────────────────────────────────────────────────

def _clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


# ─────────────────────────────────────────────────────────────────────────────
# 抓取单个 RSS 源
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_rss(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    url      = source.get("url", "")
    name     = source.get("name", url)
    category = source.get("category", "aggregator")
    lang     = source.get("lang", "en")

    if not url:
        return []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"[fetcher] {name} 抓取失败: {e}")
        return []

    now = time.time()
    items = []
    for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
        pub_ts = _parse_ts(entry)
        age_h  = (now - pub_ts) / 3600
        if age_h > MAX_AGE_HOURS:
            continue

        title   = getattr(entry, "title", "") or ""
        link    = getattr(entry, "link", "") or ""
        summary = _clean_html(
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
            or ""
        )

        if not title or not link:
            continue

        items.append({
            "title":        title.strip(),
            "url":          link.strip(),
            "summary":      summary,
            "source":       name,
            "category":     category,
            "lang":         lang,
            "published_ts": pub_ts,
        })

    print(f"[fetcher] {name}: {len(items)} 条（{MAX_AGE_HOURS}h 内）")
    return items


# ─────────────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all() -> List[Dict[str, Any]]:
    """抓取所有渠道，返回合并后的原始条目列表"""
    all_items: List[Dict[str, Any]] = []

    all_sources = EN_SOURCES + ZH_SOURCES
    for source in all_sources:
        items = _fetch_rss(source)
        all_items.extend(items)
        time.sleep(0.5)   # 礼貌性延迟，避免触发限速

    print(f"[fetcher] 共抓取 {len(all_items)} 条原始资讯")
    return all_items
