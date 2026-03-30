"""
主入口：串联抓取 → 处理 → 推送
"""

import logging
import sys
import traceback

from .fetcher import fetch_all
from .processor import process
from .notifier import send, send_error_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def run():
    logger.info("=== AI News Bot starting ===")
    try:
        # Step 1: 抓取
        logger.info("Step 1/3: Fetching news from all sources...")
        raw = fetch_all()
        total = len(raw.get("en", [])) + len(raw.get("zh", []))
        logger.info("Fetched %d raw items total.", total)

        if total == 0:
            msg = "No news items fetched from any source."
            logger.error(msg)
            send_error_alert(msg)
            sys.exit(1)

        # Step 2: 处理（评分 + 去重 + LLM 摘要）
        logger.info("Step 2/3: Processing and ranking hot items...")
        hot_items = process(raw)
        logger.info("Selected %d hot items.", len(hot_items))

        if not hot_items:
            msg = "No hot items after processing."
            logger.error(msg)
            send_error_alert(msg)
            sys.exit(1)

        # Step 3: 推送飞书
        logger.info("Step 3/3: Sending to Feishu...")
        success = send(hot_items)

        if success:
            logger.info("=== AI News Bot finished successfully ===")
        else:
            logger.error("Failed to send Feishu message.")
            sys.exit(1)

    except Exception:
        err = traceback.format_exc()
        logger.error("Unexpected error:\n%s", err)
        send_error_alert(f"未知异常：\n{err[:500]}")
        sys.exit(1)


if __name__ == "__main__":
    run()
