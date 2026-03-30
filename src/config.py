"""
配置文件：聚焦「AI 赋能平面设计 / 电商设计 / 品牌设计」方向
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
# OpenAI / LLM 配置
# ─────────────────────────────────────────────
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL       = os.environ.get("LLM_MODEL", "gpt-4.1-mini")

# ─────────────────────────────────────────────
# 热点数量上限
# ─────────────────────────────────────────────
MAX_ITEMS = 10
EN_COUNT  = 6   # 英文条数
ZH_COUNT  = 4   # 中文条数

# ─────────────────────────────────────────────
# 优先级权重（社媒 > 聚合社区 > 官方博客 > 学术前沿）
# ─────────────────────────────────────────────
PRIORITY = {
    "social_media":  4,
    "aggregator":    3,
    "official_blog": 2,
    "academic":      1,
}

# ─────────────────────────────────────────────
# 设计+AI 关键词过滤表（命中任意一个才保留）
# ─────────────────────────────────────────────
DESIGN_KEYWORDS_EN = [
    # AI 设计工具名
    "midjourney", "stable diffusion", "dall-e", "dall·e",
    "adobe firefly", "firefly", "adobe sensei",
    "canva ai", "canva magic", "canva",
    "figma ai", "figma",
    "runway", "ideogram", "leonardo.ai", "leonardo ai",
    "recraft", "krea", "magnific", "clipdrop",
    "remove.bg", "photoroom", "picsart ai",
    "generative fill", "adobe express",
    # 设计场景关键词
    "graphic design", "brand design", "branding", "brand identity",
    "visual identity", "logo design", "logo generation",
    "ecommerce design", "e-commerce design",
    "packaging design", "banner design", "ad creative",
    "social media design", "poster design", "typography",
    "design system", "ui design", "ux design",
    "image generation", "text to image", "ai image", "ai art",
    "ai illustration", "ai photography", "ai background",
    "ai mockup", "ai template", "design workflow", "design tool",
    "creative ai", "generative ai design", "ai for designers",
    "ai creative", "ai visual", "ai generated",
    # 电商相关
    "product photo", "product image", "ecommerce photo",
    "amazon listing", "shopify design", "product background",
    "ai retouching", "ai editing",
]

DESIGN_KEYWORDS_ZH = [
    # AI 设计工具名
    "midjourney", "stable diffusion", "dall-e", "firefly",
    "adobe firefly", "canva", "即梦", "可图", "通义万相",
    "文心一格", "豆包", "海艺", "liblib", "draft",
    "创客贴", "稿定",
    # AI+设计场景
    "ai绘画", "ai生图", "ai图像", "ai作图", "ai修图",
    "ai抠图", "ai换背景", "ai设计", "ai赋能设计",
    "aigc设计", "aigc创作", "生成式设计",
    "设计师ai", "设计工具", "设计效率", "设计工作流",
    # 设计场景
    "平面设计", "品牌设计", "品牌视觉", "视觉设计",
    "电商设计", "电商美工", "主图设计", "banner设计",
    "海报设计", "logo设计", "vi设计", "包装设计",
    "社媒设计", "图文设计", "创意设计",
    # 电商相关
    "商品图", "产品图", "主图", "详情页",
    "电商视觉", "淘宝美工", "京东设计",
]

# ─────────────────────────────────────────────
# 英文渠道（均经过实测验证）
# ─────────────────────────────────────────────
EN_SOURCES = [
    # ── Google News 精准搜索（设计+AI）────────────────────────
    {
        "name": "Google News · AI Graphic Design",
        "url": "https://news.google.com/rss/search?q=AI+graphic+design+tools+workflow&hl=en-US&gl=US&ceid=US:en",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Google News · Adobe Firefly",
        "url": "https://news.google.com/rss/search?q=Adobe+Firefly+AI+design&hl=en-US&gl=US&ceid=US:en",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Google News · Canva AI",
        "url": "https://news.google.com/rss/search?q=Canva+AI+design+tools&hl=en-US&gl=US&ceid=US:en",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Google News · Midjourney Design",
        "url": "https://news.google.com/rss/search?q=Midjourney+AI+design+workflow&hl=en-US&gl=US&ceid=US:en",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Google News · AI Brand & Ecommerce",
        "url": "https://news.google.com/rss/search?q=AI+brand+design+ecommerce+visual&hl=en-US&gl=US&ceid=US:en",
        "category": "aggregator",
        "lang": "en",
    },
    # ── 官方博客 ──────────────────────────────────────────────
    {
        "name": "Adobe Blog",
        "url": "https://blog.adobe.com/feed",
        "category": "official_blog",
        "lang": "en",
    },
    {
        "name": "Adobe Tech Blog",
        "url": "https://medium.com/feed/adobetech",
        "category": "official_blog",
        "lang": "en",
    },
    # ── 设计媒体 ──────────────────────────────────────────────
    {
        "name": "Creative Bloq",
        "url": "https://www.creativebloq.com/feeds/all",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "Smashing Magazine",
        "url": "https://www.smashingmagazine.com/feed/",
        "category": "aggregator",
        "lang": "en",
    },
    {
        "name": "UX Collective",
        "url": "https://uxdesign.cc/feed",
        "category": "aggregator",
        "lang": "en",
    },
]

# ─────────────────────────────────────────────
# 中文渠道（均经过实测验证）
# ─────────────────────────────────────────────
ZH_SOURCES = [
    # ── Google News 精准搜索（设计+AI）────────────────────────
    {
        "name": "Google News · AI平面设计",
        "url": "https://news.google.com/rss/search?q=AI+平面设计+工具+设计师&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "aggregator",
        "lang": "zh",
    },
    {
        "name": "Google News · AI电商设计",
        "url": "https://news.google.com/rss/search?q=AI+电商设计+品牌视觉&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "aggregator",
        "lang": "zh",
    },
    {
        "name": "Google News · AIGC设计",
        "url": "https://news.google.com/rss/search?q=AIGC+设计+创作+工具&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "aggregator",
        "lang": "zh",
    },
    {
        "name": "Google News · Midjourney中文",
        "url": "https://news.google.com/rss/search?q=Midjourney+AI绘画+设计&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "aggregator",
        "lang": "zh",
    },
    # ── 科技媒体（过滤设计相关）──────────────────────────────
    {
        "name": "量子位",
        "url": "https://www.qbitai.com/feed",
        "category": "aggregator",
        "lang": "zh",
    },
    {
        "name": "36氪",
        "url": "https://36kr.com/feed",
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
