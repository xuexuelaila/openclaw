from __future__ import annotations

import time
from typing import Dict, Tuple

from .commands import parse_command
from .config import DEBUG, TG_BOT_NAME
from .telegram import TelegramClient, poll_interval


def _extract_message(update: Dict) -> Tuple[str | None, str | None]:
    message = update.get("message") or update.get("edited_message") or {}
    text = message.get("text")
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None or text is None:
        return None, None
    return str(chat_id), text


def main() -> None:
    client = TelegramClient()
    offset: int | None = None
    interval = poll_interval()

    while True:
        try:
            updates = client.get_updates(offset=offset)
            for upd in updates:
                offset = int(upd.get("update_id", 0)) + 1
                chat_id, text = _extract_message(upd)
                if not chat_id or not text:
                    if DEBUG:
                        print("[tg] ignored non-text update")
                    continue
                if DEBUG:
                    print("[tg] received", {"chat_id": chat_id, "text_preview": text[:80]})
                reply = parse_command(text, bot_name=TG_BOT_NAME or None)
                if reply:
                    client.send_text(chat_id, reply)
        except Exception as exc:
            if DEBUG:
                print("[tg] error", exc)
            time.sleep(2)
        time.sleep(interval)


if __name__ == "__main__":
    main()
