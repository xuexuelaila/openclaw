from __future__ import annotations

import time
from typing import Dict

import requests

from .config import FEISHU_APP_ID, FEISHU_APP_SECRET

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
SEND_URL = "https://open.feishu.cn/open-apis/im/v1/messages"


class FeishuAppClient:
    def __init__(self, app_id: str | None = None, app_secret: str | None = None) -> None:
        self.app_id = app_id or FEISHU_APP_ID
        self.app_secret = app_secret or FEISHU_APP_SECRET
        self._token = None
        self._token_expire_at = 0.0

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expire_at - 60:
            return self._token
        if not self.app_id or not self.app_secret:
            raise RuntimeError("FEISHU_APP_ID/FEISHU_APP_SECRET not configured")
        resp = requests.post(
            TOKEN_URL,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Feishu token error: {data}")
        self._token = data.get("tenant_access_token")
        self._token_expire_at = now + int(data.get("expire", 0))
        return self._token

    def send_text_to_chat(self, chat_id: str, text: str) -> Dict:
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"receive_id_type": "chat_id"}
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": {"text": text},
        }
        resp = requests.post(SEND_URL, params=params, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Feishu send error: {data}")
        return data
