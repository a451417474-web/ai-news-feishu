"""
main.py — 程序主入口

流程：fetch → process → send
"""

import sys
import traceback

sys.path.insert(0, "/home/ubuntu/ai_news_bot/src")

from .fetcher  import fetch_all
from .processor import process
from .notifier import send, send_error


def run():
    try:
        print("=" * 50)
        print("[main] 开始抓取 AI 设计资讯...")
        raw = fetch_all()

        print("[main] 开始处理与过滤...")
        hot_items = process(raw)

        if not hot_items:
            send_error("未找到符合「AI 赋能设计」主题的资讯，请检查渠道或关键词配置。")
            print("[main] 无符合条件的资讯，已发送告警")
            return

        print(f"[main] 准备推送 {len(hot_items)} 条资讯...")
        ok = send(hot_items)
        print(f"[main] 推送{'成功' if ok else '失败'}")
        print("=" * 50)

    except Exception:
        err = traceback.format_exc()
        print(f"[main] 异常:\n{err}")
        send_error(err)
        sys.exit(1)


if __name__ == "__main__":
    run()
