# OpenClaw Bilibili Watcher

OpenClaw can:
- Watch specific UPs and push new video notifications.
- Build a daily keyword report: top 10 videos in last 7 days, filtered by UP followers < 10k.
  (You can disable keyword reports with `OPENCLAW_ENABLE_KEYWORD=0`.)

State is stored at `data/state.json`. You can manage it by CLI, or ask me to run the CLI for you when chatting.

## Quick Start

1) Install deps

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

2) Configure Feishu webhook

Set env var (auto-loaded from `.env`):

```bash
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
```

Optional: enable Feishu app bot (for chat commands)

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
export FEISHU_VERIFICATION_TOKEN="xxx"
export FEISHU_BOT_NAME="丸子"
```

Optional: use Telegram instead of Feishu

```bash
export TG_BOT_TOKEN="<bot token>"
export TG_CHAT_ID="<chat id for notifications>"
export TG_BOT_NAME="<bot username without @>"
export OPENCLAW_NOTIFY="telegram"
```

Optional for more stable access:

```bash
export BILI_SESSDATA="<your SESSDATA cookie>"
export BILI_COOKIE="<full cookie string>"
```

3) Add UPs or keywords

```bash
openclaw up add "https://space.bilibili.com/123456"
openclaw up add "某个UP昵称"
openclaw kw add "AI"
openclaw kw add "游戏"
```

4) Run tasks

```bash
openclaw run up-watch
openclaw run keyword-daily
openclaw run all
```

5) Start Feishu callback server (for chat commands)

```bash
openclaw-server --host 0.0.0.0 --port 8000
```

Callback URL example:

```
http://<public-ip>:8000/feishu/callback
```

Or start Telegram long polling (for chat commands):

```bash
openclaw-telegram
```

## Scheduling (cron example)

Every hour for UP watch, and daily report at 09:00:

```bash
0 * * * * cd /path/to/openclaw && . .venv/bin/activate && openclaw run up-watch
0 9 * * * cd /path/to/openclaw && . .venv/bin/activate && openclaw run keyword-daily
```

## Notes

- This uses public web APIs. It may require rate limits or cookie if Bilibili blocks requests.
- "7-day views" is approximated by total views for videos published in the last 7 days.
- If you see 412 or -799, increase `OPENCLAW_SLEEP` and/or set `BILI_COOKIE` from browser cookies.
