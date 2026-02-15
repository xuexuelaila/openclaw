from __future__ import annotations

import datetime as dt
from typing import Dict, Iterable, List


def _fmt_ts(ts: int | None) -> str:
    if not ts:
        return "-"
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _line_video(v: Dict) -> str:
    title = v.get("title") or "(no title)"
    url = v.get("url") or ""
    author = v.get("author") or v.get("owner", {}).get("name") or ""
    play = v.get("play") or v.get("stat", {}).get("view") or 0
    comment = v.get("comment") or v.get("stat", {}).get("reply") or 0
    pub = _fmt_ts(v.get("pubdate"))
    return f"- {title}\n  UP: {author} | 播放: {play} | 评论: {comment} | 发布: {pub}\n  {url}"


def up_watch_message(up: Dict, videos: Iterable[Dict]) -> str:
    header = f"UP 更新提醒: {up.get('name') or up.get('uname') or up.get('mid')}"
    lines = [header]
    for v in videos:
        lines.append(_line_video(v))
    return "\n".join(lines)


def keyword_daily_message(keyword: str, items: List[Dict]) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d")
    header = f"关键词日报: {keyword} ({now})"
    lines = [header]
    if not items:
        lines.append("- 无符合条件的视频")
        return "\n".join(lines)
    for idx, v in enumerate(items, start=1):
        title = v.get("title") or "(no title)"
        url = v.get("url") or ""
        author = v.get("author") or ""
        play = v.get("play") or 0
        follower = v.get("follower") or 0
        pub = _fmt_ts(v.get("pubdate"))
        lines.append(
            f"{idx}. {title}\n   UP: {author} | 粉丝: {follower} | 播放: {play} | 发布: {pub}\n   {url}"
        )
    return "\n".join(lines)


def daily_summary_message(items: Dict[str, List[Dict]]) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d")
    lines = [f"关键词日报汇总 ({now})"]
    for keyword, vids in items.items():
        lines.append(f"\n[{keyword}]\n")
        if not vids:
            lines.append("- 无符合条件的视频")
            continue
        for idx, v in enumerate(vids, start=1):
            title = v.get("title") or "(no title)"
            url = v.get("url") or ""
            author = v.get("author") or ""
            play = v.get("play") or 0
            follower = v.get("follower") or 0
            pub = _fmt_ts(v.get("pubdate"))
            lines.append(
                f"{idx}. {title}\n   UP: {author} | 粉丝: {follower} | 播放: {play} | 发布: {pub}\n   {url}"
            )
    return "\n".join(lines)

