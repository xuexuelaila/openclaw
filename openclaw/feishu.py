from __future__ import annotations

from typing import Dict

from .config import FEISHU_WEBHOOK
from .http import HttpClient


class FeishuNotifier:
    def __init__(self, webhook: str | None = None) -> None:
        self.webhook = webhook or FEISHU_WEBHOOK
        self.http = HttpClient()

    def send_text(self, text: str) -> Dict:
        if not self.webhook:
            raise RuntimeError("FEISHU_WEBHOOK is not configured")
        payload = {
            "msg_type": "text",
            "content": {"text": text},
        }
        return self.http.post_json(self.webhook, payload)

