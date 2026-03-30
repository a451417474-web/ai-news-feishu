# 🤖 AI News Daily Bot

每天北京时间 09:00 自动聚合 AI 领域热点资讯，通过飞书 Webhook 推送到群组。

## 功能特性

- **多渠道聚合**：覆盖 HackerNews、Reddit、OpenAI/Anthropic/DeepMind 官博、机器之心、量子位等 19 个渠道
- **智能排序**：综合优先级（社媒 > 聚合社区 > 官方博客 > 学术前沿）与时效性评分
- **中英对照**：英文资讯自动生成中文摘要，中英双语对照展示
- **比例控制**：英文 : 中文 = 6 : 4，每日推送 ≤ 10 条热点
- **飞书卡片**：富文本卡片消息，支持标题、摘要、来源标签、超链接

## 渠道列表

### 英文渠道（6 条）

| 渠道 | 类型 | 优先级 |
|------|------|--------|
| Hacker News (AI) | 聚合社区 | ★★★ |
| Reddit r/MachineLearning | 聚合社区 | ★★★ |
| Reddit r/artificial | 聚合社区 | ★★★ |
| OpenAI Blog | 官方博客 | ★★ |
| Anthropic Blog | 官方博客 | ★★ |
| Google DeepMind Blog | 官方博客 | ★★ |
| Meta AI Blog | 官方博客 | ★★ |
| Microsoft AI Blog | 官方博客 | ★★ |
| VentureBeat AI | 聚合社区 | ★★★ |
| The Verge AI | 聚合社区 | ★★★ |
| Wired AI | 聚合社区 | ★★★ |
| MIT Technology Review | 聚合社区 | ★★★ |
| ArXiv cs.AI | 学术前沿 | ★ |
| ArXiv cs.LG | 学术前沿 | ★ |

### 中文渠道（4 条）

| 渠道 | 类型 | 优先级 |
|------|------|--------|
| 机器之心 | 聚合社区 | ★★★ |
| 量子位 | 聚合社区 | ★★★ |
| 新智元 | 聚合社区 | ★★★ |
| 36氪 AI | 聚合社区 | ★★★ |
| ArXiv cs.CL | 学术前沿 | ★ |

## 部署方法

### 1. Fork 本仓库

点击右上角 **Fork** 按钮，将仓库 Fork 到您的 GitHub 账号。

### 2. 配置 Secrets

进入仓库 **Settings → Secrets and variables → Actions**，添加以下 Secrets：

| Secret 名称 | 说明 | 必填 |
|-------------|------|------|
| `FEISHU_WEBHOOK` | 飞书群机器人 Webhook URL | ✅ |
| `OPENAI_API_KEY` | OpenAI API Key（用于摘要生成） | ✅ |
| `OPENAI_BASE_URL` | API Base URL（默认 `https://api.openai.com/v1`） | 可选 |
| `LLM_MODEL` | 使用的模型（默认 `gpt-4.1-mini`） | 可选 |

### 3. 启用 Actions

进入仓库 **Actions** 标签页，点击 **Enable GitHub Actions**。

### 4. 测试运行

进入 **Actions → AI News Daily Push → Run workflow**，手动触发一次测试。

### 5. 自动运行

配置完成后，每天 **北京时间 09:00**（UTC 01:00）自动运行。

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
export OPENAI_API_KEY="sk-xxx"

# 运行
python -m src.main
```

## 项目结构

```
ai-news-bot/
├── .github/
│   └── workflows/
│       └── daily_run.yml      # GitHub Actions 定时任务
├── src/
│   ├── __init__.py
│   ├── config.py              # 渠道配置与系统参数
│   ├── fetcher.py             # 资讯抓取（RSS + HN API）
│   ├── processor.py           # 热点提取、评分、LLM 摘要
│   ├── notifier.py            # 飞书消息格式化与推送
│   └── main.py                # 主入口
├── requirements.txt
└── README.md
```

## 消息格式预览

```
🤖 AI 每日热点 · 2025年01月01日 周三
共 10 条热点 | 🇺🇸 英文 6 条 · 🇨🇳 中文 4 条
───────────────────────────────────────
🇺🇸 🔥 聚合 · Hacker News (AI)
1. [OpenAI 发布 GPT-5，推理能力大幅提升](https://...)
   *OpenAI releases GPT-5 with dramatically improved reasoning*
   > OpenAI 正式发布 GPT-5 模型，在数学推理、代码生成等多项基准测试中刷新记录...
───────────────────────────────────────
🇨🇳 🔥 聚合 · 机器之心
7. [国产大模型再突破：xxx 发布新版本](https://...)
   > 该模型在中文理解、多模态任务上表现优异...
```

## License

MIT
