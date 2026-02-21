from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from .commands import parse_command
from .config import DEBUG, FEISHU_BOT_NAME, FEISHU_ENCRYPT_KEY, FEISHU_VERIFICATION_TOKEN
from .feishu_app import FeishuAppClient


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
    header = payload.get("header", {}) or {}
    event = payload.get("event", {}) or {}
    event_type = header.get("event_type") or event.get("type")
    if DEBUG:
        print(
            "[event] received",
            {"event_type": event_type, "event_keys": sorted(list(event.keys()))},
        )
    message = event.get("message", {}) or {}
    if message.get("message_type") != "text":
        if DEBUG:
            print(
                "[event] ignored non-text",
                {"message_type": message.get("message_type"), "event_type": event_type},
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
            print("[event] empty text", {"event_type": event_type})
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
    reply = parse_command(text, bot_name=FEISHU_BOT_NAME)
    if not reply:
        if DEBUG and FEISHU_BOT_NAME:
            print("[event] filtered by bot name", {"bot_name": FEISHU_BOT_NAME})
        return
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
