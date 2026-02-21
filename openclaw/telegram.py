from __future__ import annotations

from typing import Dict, Iterable, List

import requests

from .config import TG_BOT_TOKEN, TG_CHAT_ID, TG_POLL_TIMEOUT, TG_POLL_INTERVAL


class TelegramClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or TG_BOT_TOKEN
        if not self.token:
            raise RuntimeError("TG_BOT_TOKEN is not configured")
        self.base = f"https://api.telegram.org/bot{self.token}"

    def send_text(self, chat_id: str, text: str) -> Dict:
        payload = {"chat_id": chat_id, "text": text}
        resp = requests.post(f"{self.base}/sendMessage", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_updates(self, offset: int | None = None) -> List[Dict]:
        params: Dict[str, int] = {"timeout": TG_POLL_TIMEOUT}
        if offset is not None:
            params["offset"] = offset
        resp = requests.get(
            f"{self.base}/getUpdates",
            params=params,
            timeout=TG_POLL_TIMEOUT + 10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram getUpdates error: {data}")
        return data.get("result") or []


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self.client = TelegramClient(token=token)
        self.chat_id = chat_id or TG_CHAT_ID
        if not self.chat_id:
            raise RuntimeError("TG_CHAT_ID is not configured")

    def send_text(self, text: str) -> Dict:
        return self.client.send_text(self.chat_id, text)


def poll_interval() -> float:
    return TG_POLL_INTERVAL
