import random
import time
from typing import Any, Dict, Iterable, Set

import requests

from .config import (
    BILI_COOKIE,
    BILI_SESSDATA,
    REQUEST_BACKOFF,
    REQUEST_RETRIES,
    REQUEST_SLEEP,
    REQUEST_TIMEOUT,
    USER_AGENT,
)


class HttpClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Referer": "https://www.bilibili.com/",
                "Origin": "https://www.bilibili.com",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )
        if BILI_SESSDATA:
            self.session.cookies.set("SESSDATA", BILI_SESSDATA)
        if BILI_COOKIE:
            self._load_cookie_string(BILI_COOKIE)

    def _load_cookie_string(self, cookie: str) -> None:
        # Format: "key=value; key2=value2"
        for part in cookie.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            self.session.cookies.set(k.strip(), v.strip())

    def _sleep(self, attempt: int) -> None:
        jitter = random.random() * 0.2
        time.sleep(REQUEST_SLEEP + REQUEST_BACKOFF * (2**attempt) + jitter)

    def get_json(
        self,
        url: str,
        params: Dict[str, Any] | None = None,
        retry_on_statuses: Iterable[int] | None = None,
        retry_on_codes: Set[int] | None = None,
    ) -> Dict[str, Any]:
        retry_on_statuses = set(retry_on_statuses or [])
        for attempt in range(REQUEST_RETRIES + 1):
            self._sleep(attempt)
            resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code in retry_on_statuses and attempt < REQUEST_RETRIES:
                continue
            resp.raise_for_status()
            data = resp.json()
            if retry_on_codes and data.get("code") in retry_on_codes and attempt < REQUEST_RETRIES:
                continue
            return data
        # should not reach here
        resp.raise_for_status()
        return resp.json()

    def post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        for attempt in range(REQUEST_RETRIES + 1):
            self._sleep(attempt)
            resp = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (412, 429) and attempt < REQUEST_RETRIES:
                continue
            resp.raise_for_status()
            return resp.json()
