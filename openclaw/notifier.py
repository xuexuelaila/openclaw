from __future__ import annotations

from .config import NOTIFY_CHANNEL, TG_BOT_TOKEN, TG_CHAT_ID
from .feishu import FeishuNotifier
from .telegram import TelegramNotifier


def get_notifier():
    if NOTIFY_CHANNEL == "telegram":
        return TelegramNotifier()
    if NOTIFY_CHANNEL == "feishu":
        return FeishuNotifier()
    if TG_BOT_TOKEN and TG_CHAT_ID:
        return TelegramNotifier()
    return FeishuNotifier()
