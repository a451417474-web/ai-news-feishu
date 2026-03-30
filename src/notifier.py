"""
notifier.py — 构建飞书富文本消息并推送

飞书 post 消息格式：content 为二维数组
  - 外层数组：每个元素是一行
  - 内层数组：每个元素是行内的 span（text / a）
  注意：飞书 Webhook 不支持 style 字段，不能使用 bold
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import requests

from config import FEISHU_WEBHOOK

CST = timezone(timedelta(hours=8))


def _today_str() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d")


def _t(text: str) -> dict:
    return {"tag": "text", "text": text}


def _a(text: str, url: str) -> dict:
    return {"tag": "a", "text": text, "href": url}


# ─────────────────────────────────────────────────────────────────────────────
# 构建单条资讯行
# ─────────────────────────────────────────────────────────────────────────────

def _item_rows(idx: int, item: Dict[str, Any]) -> List[list]:
    lang       = item.get("lang", "en")
    title      = item.get("title", "")
    zh_title   = item.get("zh_title", title)
    zh_sum     = item.get("zh_summary", "")
    url        = item.get("url", "")
    source     = item.get("source", "")
    actionable = item.get("actionable", False)

    lang_tag   = "🌐 EN" if lang == "en" else "🇨🇳 ZH"
    action_tag = " 🛠️实操" if actionable else ""
    prefix     = f"{idx}. [{lang_tag}{action_tag}]  "

    rows = []

    # 行1：序号 + 标签 + 标题链接
    display_title = zh_title if lang == "en" else title
    if url:
        rows.append([_t(prefix), _a(display_title, url)])
    else:
        rows.append([_t(prefix + display_title)])

    # 行2（仅英文）：英文原标题
    if lang == "en" and title:
        rows.append([_t(f"   EN: {title}")])

    # 行3：中文摘要
    if zh_sum:
        rows.append([_t(f"   {zh_sum}")])

    # 行4：来源
    if source:
        rows.append([_t(f"   📌 来源：{source}")])

    # 空行
    rows.append([_t("")])

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 构建完整 payload
# ─────────────────────────────────────────────────────────────────────────────

def _build_payload(items: List[Dict[str, Any]]) -> dict:
    today   = _today_str()
    en_cnt  = sum(1 for i in items if i.get("lang") == "en")
    zh_cnt  = sum(1 for i in items if i.get("lang") == "zh")
    act_cnt = sum(1 for i in items if i.get("actionable"))
    SEP     = "─" * 32

    content: List[list] = []

    # 头部
    content.append([_t(f"今日精选 {len(items)} 条  |  英文 {en_cnt} · 中文 {zh_cnt}  |  🛠️实操 {act_cnt} 条")])
    content.append([_t("聚焦：平面设计 · 电商设计 · 品牌设计 × AI 工具实践")])
    content.append([_t(SEP)])
    content.append([_t("")])

    # 英文精选
    en_items = [i for i in items if i.get("lang") == "en"]
    if en_items:
        content.append([_t("▌ 英文精选（中英对照）")])
        content.append([_t("")])
        for idx, item in enumerate(en_items, 1):
            content.extend(_item_rows(idx, item))

    # 中文精选
    zh_items = [i for i in items if i.get("lang") == "zh"]
    if zh_items:
        content.append([_t("▌ 中文精选")])
        content.append([_t("")])
        for idx, item in enumerate(zh_items, 1):
            content.extend(_item_rows(idx, item))

    # 底部
    content.append([_t(SEP)])
    content.append([_t("🛠️ 标注「实操」的资讯含可直接应用的工具/教程/技巧，优先阅读")])

    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🎨 AI 设计早报 · {today}",
                    "content": content,
                }
            }
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 推送
# ─────────────────────────────────────────────────────────────────────────────

def send(items: List[Dict[str, Any]]) -> bool:
    payload = _build_payload(items)
    try:
        resp = requests.post(
            FEISHU_WEBHOOK,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=15,
        )
        result = resp.json()
        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print(f"[notifier] 推送成功，共 {len(items)} 条")
            return True
        else:
            print(f"[notifier] 推送失败: {result}")
            return False
    except Exception as e:
        print(f"[notifier] 推送异常: {e}")
        return False


def send_error(msg: str) -> None:
    today = _today_str()
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"⚠️ AI 资讯推送异常 [{today}]",
                    "content": [[_t(f"未知异常:\n{msg[:500]}")]],
                }
            }
        },
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
