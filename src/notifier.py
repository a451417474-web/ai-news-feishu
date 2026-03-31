"""
notifier.py — 飞书卡片消息（Interactive Card）构建与推送

消息样式（对标图二）：
  蓝色 header + 每条资讯独立分区 + 分隔线
  来源行（小字）→ 加粗蓝色标题链接 → 斜体英文原标题 → > 引用摘要
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import requests

from .config import FEISHU_WEBHOOK

CST = timezone(timedelta(hours=8))
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _today_str() -> str:
    now = datetime.now(CST)
    return now.strftime(f"%Y年%m月%d日 {WEEKDAYS[now.weekday()]}")


def _today_short() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d")


def _cat_icon(category: str) -> str:
    return {"social": "💬", "aggregator": "🔥", "blog": "🔥", "academic": "📄"}.get(category, "🔥")


def _item_markdown(idx: int, item: Dict[str, Any]) -> str:
    """
    格式：
      🌐 🔥 英文精选 · Creative Bloq
      **1. [中文标题](url)** 🛠️实操
      *EN: 英文原标题*
      > 中文摘要
    """
    lang       = item.get("lang", "en")
    title      = item.get("title", "")
    zh_title   = item.get("zh_title", title)
    zh_sum     = item.get("zh_summary", "")
    url        = item.get("url", "")
    source     = item.get("source", "")
    category   = item.get("category", "aggregator")
    actionable = item.get("actionable", False)

    lang_flag  = "🌐" if lang == "en" else "🇨🇳"
    cat_icon   = _cat_icon(category)
    lang_label = "英文精选" if lang == "en" else "中文精选"
    action_tag = "  🛠️实操" if actionable else ""

    lines = []
    lines.append(f"{lang_flag} {cat_icon} {lang_label} · {source}")

    display_title = zh_title if lang == "en" else title
    if url:
        lines.append(f"**{idx}. [{display_title}]({url})**{action_tag}")
    else:
        lines.append(f"**{idx}. {display_title}**{action_tag}")

    if lang == "en" and title:
        short_title = title if len(title) <= 80 else title[:77] + "..."
        lines.append(f"*{short_title}*")

    if zh_sum:
        lines.append(f"> {zh_sum}")

    return "\n".join(lines)


def _build_card_payload(items: List[Dict[str, Any]]) -> dict:
    today_long = _today_str()
    en_items   = [i for i in items if i.get("lang") == "en"]
    zh_items   = [i for i in items if i.get("lang") == "zh"]
    act_cnt    = sum(1 for i in items if i.get("actionable"))

    sources = list(dict.fromkeys(i.get("source", "") for i in items))[:6]
    sources_str = " · ".join(sources) + (" 等" if len(sources) >= 6 else "")

    elements = []

    # 摘要行
    summary = (
        f"**共 {len(items)} 条热点** | "
        f"🌐 英文 {len(en_items)} 条 · 🇨🇳 中文 {len(zh_items)} 条"
    )
    if act_cnt:
        summary += f" · 🛠️实操 {act_cnt} 条"
    summary += f"\n数据来源：{sources_str}"
    elements.append({"tag": "markdown", "content": summary})

    # 英文资讯
    for idx, item in enumerate(en_items, 1):
        elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": _item_markdown(idx, item)})

    # 中文分区标题
    if zh_items and en_items:
        elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": "**🇨🇳 中文精选**"})

    # 中文资讯
    for idx, item in enumerate(zh_items, 1):
        elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": _item_markdown(idx, item)})

    # 底部提示
    elements.append({"tag": "hr"})
    elements.append({"tag": "markdown", "content": "🛠️ 标注「实操」的资讯含可直接应用的工具/教程/技巧，优先阅读"})

    return {
        "msg_type": "interactive",
        "card": {
            "schema": "2.0",
            "header": {
                "title": {"tag": "plain_text", "content": f"🎨 AI 设计早报 · {today_long}"},
                "template": "blue"
            },
            "body": {"elements": elements}
        }
    }


def send(items: List[Dict[str, Any]]) -> bool:
    payload = _build_card_payload(items)
    try:
        resp = requests.post(
            FEISHU_WEBHOOK,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=15,
        )
        result = resp.json()
        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print(f"[notifier] 卡片推送成功，共 {len(items)} 条")
            return True
        else:
            print(f"[notifier] 推送失败: {result}")
            return False
    except Exception as e:
        print(f"[notifier] 推送异常: {e}")
        return False


def send_error(msg: str) -> None:
    today = _today_short()
    payload = {
        "msg_type": "interactive",
        "card": {
            "schema": "2.0",
            "header": {
                "title": {"tag": "plain_text", "content": f"⚠️ AI 资讯推送异常 [{today}]"},
                "template": "red"
            },
            "body": {
                "elements": [{"tag": "markdown", "content": f"```\n{msg[:800]}\n```"}]
            }
        }
    }
    try:
        requests.post(
            FEISHU_WEBHOOK,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=15,
        )
    except Exception:
        pass
