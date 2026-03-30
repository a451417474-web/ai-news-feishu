"""
飞书消息格式化与 Webhook 推送模块
使用飞书「富文本」(post) 消息类型，支持标题、加粗、超链接等格式
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import requests

from .config import FEISHU_WEBHOOK, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

CST = timezone(timedelta(hours=8))

# 类别标签映射
CATEGORY_LABEL = {
    "social_media":  "📱 社媒",
    "aggregator":    "🔥 聚合",
    "official_blog": "📢 官博",
    "academic":      "🎓 学术",
}

LANG_FLAG = {
    "en": "🇺🇸",
    "zh": "🇨🇳",
}


def _build_feishu_card(items: List[Dict[str, Any]]) -> Dict:
    """
    构建飞书「卡片消息」(interactive card) 格式。
    每条资讯独立展示，英文条目中英对照，中文条目直接展示。
    """
    today = datetime.now(tz=CST).strftime("%Y年%m月%d日")
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[datetime.now(tz=CST).weekday()]

    # ── 卡片 Header ──────────────────────────────────────────
    header = {
        "template": "blue",
        "title": {
            "tag": "plain_text",
            "content": f"🤖 AI 每日热点 · {today} {weekday}",
        },
    }

    # ── 卡片 Elements ─────────────────────────────────────────
    elements = []

    # 分隔线 + 统计摘要
    en_count = sum(1 for i in items if i.get("lang") == "en")
    zh_count = sum(1 for i in items if i.get("lang") == "zh")

    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": (
                f"**共 {len(items)} 条热点** | "
                f"🇺🇸 英文 {en_count} 条 · 🇨🇳 中文 {zh_count} 条\n"
                f"数据来源：HackerNews · Reddit · OpenAI · Anthropic · DeepMind · 机器之心 · 量子位 等"
            ),
        },
    })

    elements.append({"tag": "hr"})

    # ── 逐条构建 ──────────────────────────────────────────────
    for idx, item in enumerate(items, start=1):
        lang = item.get("lang", "en")
        category = item.get("category", "aggregator")
        source = item.get("source", "")
        title = item.get("title", "")
        zh_title = item.get("zh_title", "")
        zh_summary = item.get("zh_summary", "")
        link = item.get("link", "")

        cat_label = CATEGORY_LABEL.get(category, "📰")
        lang_flag = LANG_FLAG.get(lang, "")

        if lang == "en":
            # 英文条目：中英对照
            # 第一行：序号 + 标签 + 中文标题（加粗超链接）
            # 第二行：英文原标题（斜体）
            # 第三行：中文摘要
            title_line = f"**{idx}. [{zh_title or title}]({link})**"
            en_line = f"*{title}*"
            summary_line = zh_summary if zh_summary else ""

            content_parts = [
                f"{lang_flag} {cat_label} · {source}",
                title_line,
                en_line,
            ]
            if summary_line:
                content_parts.append(f"> {summary_line}")

        else:
            # 中文条目：直接展示
            title_line = f"**{idx}. [{title}]({link})**"
            summary_line = zh_summary if zh_summary else ""

            content_parts = [
                f"{lang_flag} {cat_label} · {source}",
                title_line,
            ]
            if summary_line:
                content_parts.append(f"> {summary_line}")

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "\n".join(content_parts),
            },
        })

        # 每条之间加分隔线（最后一条不加）
        if idx < len(items):
            elements.append({"tag": "hr"})

    # ── 底部注脚 ──────────────────────────────────────────────
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": (
                    f"⏰ 推送时间：{datetime.now(tz=CST).strftime('%H:%M')} CST  "
                    "| 由 GitHub Actions 自动运行  "
                    "| 资讯仅供参考"
                ),
            }
        ],
    })

    card = {
        "msg_type": "interactive",
        "card": {
            "header": header,
            "elements": elements,
        },
    }
    return card


def send(items: List[Dict[str, Any]]) -> bool:
    """
    发送飞书消息。成功返回 True，失败返回 False。
    """
    if not items:
        logger.warning("No items to send.")
        return False

    payload = _build_feishu_card(items)

    try:
        resp = requests.post(
            FEISHU_WEBHOOK,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 0 or result.get("StatusCode") == 0:
            logger.info("Feishu message sent successfully.")
            return True
        else:
            logger.error("Feishu API error: %s", result)
            return False
    except Exception as exc:
        logger.error("Failed to send Feishu message: %s", exc)
        return False


def send_error_alert(error_msg: str) -> None:
    """发送错误告警到飞书群。"""
    today = datetime.now(tz=CST).strftime("%Y-%m-%d %H:%M")
    payload = {
        "msg_type": "text",
        "content": {
            "text": f"⚠️ AI 资讯推送异常 [{today}]\n{error_msg}"
        },
    }
    try:
        requests.post(FEISHU_WEBHOOK, json=payload, timeout=REQUEST_TIMEOUT)
    except Exception:
        pass
