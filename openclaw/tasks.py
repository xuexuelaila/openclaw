from __future__ import annotations

import datetime as dt
from typing import Dict, List, Tuple

from .bili import BiliClient, within_days
from .config import ENABLE_KEYWORD, FOLLOWER_MAX, KEYWORD_DAYS, KEYWORD_TOPK
from .feishu import FeishuNotifier
from .report import daily_summary_message, up_watch_message
from .storage import (
    get_last_daily_date,
    get_last_seen_bvids,
    load_state,
    save_state,
    set_last_daily_date,
    set_last_seen_bvids,
)
from .utils import parse_count


def _today_str() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")


def run_up_watch(notify: bool = True) -> Tuple[int, List[str]]:
    state = load_state()
    ups = state.get("ups", [])
    client = BiliClient()
    notifier = FeishuNotifier()

    total_new = 0
    errors: List[str] = []

    for up in ups:
        mid = str(up.get("mid"))
        try:
            videos = client.list_up_videos(mid, page=1, page_size=10)
            last_seen = set(get_last_seen_bvids(state, mid))
            new_videos = [v for v in videos if v.get("bvid") not in last_seen]

            if new_videos:
                total_new += len(new_videos)
                if notify:
                    msg = up_watch_message(up, new_videos)
                    notifier.send_text(msg)

            # Update last seen to latest bvids (keep only 20)
            latest_bvids = [v.get("bvid") for v in videos if v.get("bvid")]
            set_last_seen_bvids(state, mid, latest_bvids[:20])
        except Exception as exc:
            errors.append(f"{mid}: {exc}")

    save_state(state)
    return total_new, errors


def _filter_keyword_results(keyword: str) -> List[Dict]:
    client = BiliClient()
    items = []
    page = 1
    while page <= 3 and len(items) < 50:
        results = client.search_videos_by_keyword(keyword, page=page, page_size=20)
        if not results:
            break
        items.extend(results)
        page += 1

    # filter by last 7 days (approx by pubdate)
    items = [v for v in items if within_days(v.get("pubdate"), KEYWORD_DAYS)]

    # enrich follower count and filter < 10k
    filtered: List[Dict] = []
    for v in items:
        mid = v.get("mid")
        if not mid:
            continue
        try:
            stat = client.get_relation_stat(mid)
            follower = stat.get("follower", 0)
        except Exception:
            follower = 0
        v["follower"] = follower
        if follower < FOLLOWER_MAX:
            filtered.append(v)

    # sort by play desc
    def _play(x: Dict) -> int:
        return parse_count(x.get("play", 0))

    filtered.sort(key=_play, reverse=True)
    return filtered[:KEYWORD_TOPK]


def run_keyword_daily(force: bool = False, notify: bool = True) -> Tuple[int, List[str]]:
    state = load_state()
    if not ENABLE_KEYWORD:
        return 0, []
    today = _today_str()
    if not force and get_last_daily_date(state) == today:
        return 0, []

    keywords = state.get("keywords", [])
    if not keywords:
        return 0, []
    notifier = FeishuNotifier()
    errors: List[str] = []

    results: Dict[str, List[Dict]] = {}
    total_items = 0
    for kw in keywords:
        try:
            vids = _filter_keyword_results(kw)
            results[kw] = vids
            total_items += len(vids)
        except Exception as exc:
            errors.append(f"{kw}: {exc}")

    if notify:
        msg = daily_summary_message(results)
        notifier.send_text(msg)

    set_last_daily_date(state, today)
    save_state(state)
    return total_items, errors


def run_all() -> Tuple[Dict[str, int], List[str]]:
    counts = {}
    errors: List[str] = []

    c1, e1 = run_up_watch(notify=True)
    counts["up_watch_new"] = c1
    errors.extend(e1)

    if ENABLE_KEYWORD:
        c2, e2 = run_keyword_daily(force=False, notify=True)
        counts["keyword_items"] = c2
        errors.extend(e2)

    return counts, errors
