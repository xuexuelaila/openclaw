from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from .bili import BiliClient, within_days
from .config import DEBUG, FEISHU_BOT_NAME, FEISHU_ENCRYPT_KEY, FEISHU_VERIFICATION_TOKEN
from .feishu_app import FeishuAppClient
from .storage import add_up, load_state, remove_up, save_state


def _fmt_ts(ts: int | None) -> str:
    if not ts:
        return "-"
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _parse_days(text: str) -> int:
    m = re.search(r"(近|最近|进)\s*(\d+)\s*天", text)
    if m:
        try:
            return max(1, int(m.group(2)))
        except Exception:
            return 3
    return 3


def _clean_identifier(text: str, days: int) -> str:
    t = text
    if FEISHU_BOT_NAME:
        t = t.replace(FEISHU_BOT_NAME, "")
    t = re.sub(r"(我要|帮我|给我|查询|查|看看|看|获取)", "", t)
    t = re.sub(r"(近|最近|进)\s*\d+\s*天.*", "", t)
    t = re.sub(r"(发布的内容|发布内容|发布|内容|的视频|视频)", "", t)
    return t.strip()


def _resolve_up(identifier: str) -> dict | None:
    client = BiliClient()
    if identifier.isdigit():
        return client.get_up_info(identifier)
    if "bilibili.com" in identifier and "space" in identifier:
        try:
            mid = identifier.rstrip("/").split("/")[-1]
            if mid.isdigit():
                return client.get_up_info(mid)
        except Exception:
            return None
    results = client.search_user(identifier, page=1, page_size=5)
    if results:
        mid = results[0].get("mid")
        if mid:
            return client.get_up_info(str(mid))
    return None


def _handle_query(client: BiliClient, identifier: str, days: int) -> str:
    up = _resolve_up(identifier)
    if not up:
        return "没找到该UP，请提供MID或空间链接。"
    mid = str(up.get("mid"))
    videos = client.list_up_videos(mid, page=1, page_size=30)
    items = [v for v in videos if within_days(v.get("pubdate"), days)]
    if not items:
        return f"{up.get('name')} 近{days}天没有发布新视频。"
    lines = [f"{up.get('name')} 近{days}天发布："]
    for v in items[:15]:
        lines.append(
            f"- {v.get('title')} | { _fmt_ts(v.get('pubdate')) }\n  {v.get('url')}"
        )
    return "\n".join(lines)


def _handle_follow(identifier: str) -> str:
    up = _resolve_up(identifier)
    if not up:
        return "没找到该UP，请提供MID或空间链接。"
    state = load_state()
    add_up(state, {"mid": up.get("mid"), "name": up.get("name")})
    save_state(state)
    return f"已关注：{up.get('name')} (MID: {up.get('mid')})"


def _handle_unfollow(identifier: str) -> str:
    up = _resolve_up(identifier)
    if not up and identifier.isdigit():
        mid = identifier
    elif up:
        mid = str(up.get("mid"))
    else:
        return "没找到该UP，请提供MID或空间链接。"
    state = load_state()
    ok = remove_up(state, mid)
    save_state(state)
    return "已取消关注" if ok else "未找到该关注" 


def _handle_list() -> str:
    state = load_state()
    ups = state.get("ups", [])
    if not ups:
        return "当前没有关注任何UP。"
    lines = ["当前关注UP列表:"]
    for u in ups:
        lines.append(f"- {u.get('name') or u.get('mid')} (MID: {u.get('mid')})")
    return "\n".join(lines)


def _parse_command(text: str) -> str:
    t = text.strip()
    if not t:
        return "请发送指令，例如：丸子 查询 xxx 近3天"

    if "取消关注" in t:
        ident = t.split("取消关注", 1)[1].strip()
        return _handle_unfollow(ident)

    if "列出关注" in t or "关注列表" in t or "我的关注" in t:
        return _handle_list()

    if "关注" in t:
        ident = t.split("关注", 1)[1].strip()
        return _handle_follow(ident)

    # query
    days = _parse_days(t)
    ident = _clean_identifier(t, days)
    if not ident:
        return "请提供UP名称/MID/空间链接，例如：丸子 查询 爱研究的摸鱼君 近3天"
    client = BiliClient()
    return _handle_query(client, ident, days)


def _verify_token(payload: dict) -> bool:
    if not FEISHU_VERIFICATION_TOKEN:
        return True
    token = None
    if isinstance(payload.get("header"), dict):
        token = payload["header"].get("token")
    if not token:
        token = payload.get("token")
    return token == FEISHU_VERIFICATION_TOKEN


def _handle_event(payload: dict) -> None:
    if not _verify_token(payload):
        if DEBUG:
            print("[event] invalid token")
        return
    event = payload.get("event", {}) or {}
    message = event.get("message", {}) or {}
    if message.get("message_type") != "text":
        if DEBUG:
            print(
                "[event] ignored non-text",
                {"message_type": message.get("message_type"), "event_type": event.get("type")},
            )
        return
    chat_id = message.get("chat_id")
    if not chat_id:
        if DEBUG:
            print("[event] missing chat_id")
        return
    content = message.get("content") or ""
    try:
        content = json.loads(content)
        text = content.get("text", "")
    except Exception:
        text = ""

    if not text:
        if DEBUG:
            print("[event] empty text", {"event_type": event.get("type")})
        return
    if FEISHU_BOT_NAME and FEISHU_BOT_NAME not in text:
        # In group chat, only respond if mentioned by name
        if DEBUG:
            print("[event] filtered by bot name", {"bot_name": FEISHU_BOT_NAME})
        return

    if DEBUG:
        print(
            "[event] received text",
            {
                "event_type": event.get("type"),
                "chat_id": chat_id,
                "text_preview": text[:80],
            },
        )
    reply = _parse_command(text)
    client = FeishuAppClient()
    client.send_text_to_chat(chat_id, reply)


class FeishuHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/feishu/callback":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            self._send_json({"error": "invalid json"}, status=400)
            return

        if payload.get("type") == "url_verification":
            if not _verify_token(payload):
                self._send_json({"error": "invalid token"}, status=403)
                return
            self._send_json({"challenge": payload.get("challenge")})
            return

        if not _verify_token(payload):
            self._send_json({"error": "invalid token"}, status=403)
            return

        # async handle
        threading.Thread(target=_handle_event, args=(payload,), daemon=True).start()
        self._send_json({"status": "ok"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), FeishuHandler)
    print(f"Feishu callback server running on {args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
