"""
配置文件：定义资讯渠道、优先级权重和系统参数
所有 RSS URL 均经过实测验证可访问
"""

import os

# ─────────────────────────────────────────────
# 飞书 Webhook
# ─────────────────────────────────────────────
FEISHU_WEBHOOK = os.environ.get(
    "FEISHU_WEBHOOK",
    "https://open.feishu.cn/open-apis/bot/v2/hook/bfdb04c5-3da7-4ff7-99a2-89270660cb2e",
)

# ─────────────────────────────────────────────
# OpenAI / LLM 配置（用于热点提取与翻译）
# ─────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")

# ─────────────────────────────────────────────
# 热点数量上限
# ─────────────────────────────────────────────
MAX_ITEMS = 10
# 英文 : 中文 = 6 : 4
EN_COUNT = 6
ZH_COUNT = 4

# ─────────────────────────────────────────────
# 优先级权重（数值越大越优先）
# 社媒 > 聚合社区 > 官方博客 > 学术前沿
# ─────────────────────────────────────────────
PRIORITY = {
    "social_media": 4,
    "aggregator":   3,
    "official_blog": 2,
    "academic":     1,
}

# ─────────────────────────────────────────────
# 英文渠道（均经过实测验证）
# ─────────────────────────────────────────────
EN_SOURCES = [
    # ── 聚合社区（HN 使用特殊抓取器）────────────────────────
    {
        "name": "Hacker News (AI)",
        "type": "hn_top",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Reddit r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/.rss",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Reddit r/artificial",
        "url": "https://www.reddit.com/r/artificial/.rss",
        "category": "aggregator",
        "lang": "en",
    },
    # ── 官方博客 ──────────────────────────────────────────────
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "category": "official_blog",
        "lang": "en",
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "official_blog",
        "lang": "en",
    },
    # ── 聚合媒体 ──────────────────────────────────────────────
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/feed/",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "The Guardian AI",
        "url": "https://www.theguardian.com/technology/artificialintelligenceai/rss",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "aggregator",
        "lang": "en",
    },
    # ── 学术前沿 ──────────────────────────────────────────────
    {
        "name": "ScienceDaily AI",
        "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
        "category": "academic",
        "lang": "en",
    },
]

# ─────────────────────────────────────────────
# 中文渠道（均经过实测验证）
# ─────────────────────────────────────────────
ZH_SOURCES = [
    # ── 聚合社区 ──────────────────────────────────────────────
    {
        "name": "量子位",
        "url": "https://www.qbitai.com/feed",
        "category": "aggregator",
        "lang": "zh",
    },
    {
        "name": "新智元",
        "url": "https://www.aiyjs.com/feed",
        "category": "aggregator",
        "lang": "zh",
    },
    {
        "name": "36氪 AI",
        "url": "https://36kr.com/feed",
        "category": "aggregator",
        "lang": "zh",
    },
    # ── Google News 中文 AI 聚合 ──────────────────────────────
    {
        "name": "Google News AI (中文)",
        "url": "https://news.google.com/rss/search?q=人工智能+大模型&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "aggregator",
        "lang": "zh",
    },
    {
        "name": "Google News 机器之心",
        "url": "https://news.google.com/rss/search?q=机器之心+AI&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "aggregator",
        "lang": "zh",
    },
]

# ─────────────────────────────────────────────
# HTTP 请求超时（秒）
# ─────────────────────────────────────────────
REQUEST_TIMEOUT = 15

# ─────────────────────────────────────────────
# 每个渠道最多抓取条数
# ─────────────────────────────────────────────
MAX_ITEMS_PER_SOURCE = 20
