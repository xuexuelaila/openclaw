from __future__ import annotations

import datetime as dt
import re

from .bili import BiliClient, within_days
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


def _strip_bot_name(text: str, bot_name: str) -> str:
    if not bot_name:
        return text
    name = bot_name.strip()
    if not name:
        return text
    name_plain = name.lstrip("@")
    t = text.replace(name, "")
    if name_plain:
        t = t.replace(f"@{name_plain}", "")
        t = t.replace(name_plain, "")
    return t


def _clean_identifier(text: str, days: int, bot_name: str | None) -> str:
    t = text
    if bot_name:
        t = _strip_bot_name(t, bot_name)
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


def parse_command(text: str, bot_name: str | None = None) -> str | None:
    t = text.strip()
    if not t:
        return "请发送指令，例如：查询 xxx 近3天"

    if bot_name:
        if bot_name not in t and f"@{bot_name.lstrip('@')}" not in t:
            return None
        t = _strip_bot_name(t, bot_name).strip()

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
    ident = _clean_identifier(t, days, bot_name)
    if not ident:
        return "请提供UP名称/MID/空间链接，例如：查询 爱研究的摸鱼君 近3天"
    client = BiliClient()
    return _handle_query(client, ident, days)
