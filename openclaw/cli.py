from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List

from .bili import BiliClient
from .storage import (
    add_keyword,
    add_up,
    load_state,
    remove_keyword,
    remove_up,
    save_state,
)
from .tasks import run_all, run_keyword_daily, run_up_watch


def _print(obj) -> None:
    if isinstance(obj, (dict, list)):
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(obj)


def cmd_up_add(args: argparse.Namespace) -> None:
    state = load_state()
    client = BiliClient()
    identifier = args.identifier

    up: Dict[str, str] | None = None

    if identifier.isdigit():
        up = client.get_up_info(identifier)
    elif "bilibili.com" in identifier and "space" in identifier:
        # URL: https://space.bilibili.com/{mid}
        try:
            mid = identifier.rstrip("/").split("/")[-1]
            if mid.isdigit():
                up = client.get_up_info(mid)
        except Exception:
            up = None
    else:
        # search by name
        results = client.search_user(identifier, page=1, page_size=5)
        if results:
            mid = results[0].get("mid")
            if mid:
                up = client.get_up_info(str(mid))

    if not up:
        print("UP not found. Provide MID or space URL.")
        sys.exit(1)

    add_up(state, {"mid": up.get("mid"), "name": up.get("name")})
    save_state(state)
    _print({"added": up})


def cmd_up_list(_: argparse.Namespace) -> None:
    state = load_state()
    _print(state.get("ups", []))


def cmd_up_remove(args: argparse.Namespace) -> None:
    state = load_state()
    ok = remove_up(state, args.mid)
    save_state(state)
    _print({"removed": ok})


def cmd_kw_add(args: argparse.Namespace) -> None:
    state = load_state()
    add_keyword(state, args.keyword)
    save_state(state)
    _print({"added": args.keyword})


def cmd_kw_list(_: argparse.Namespace) -> None:
    state = load_state()
    _print(state.get("keywords", []))


def cmd_kw_remove(args: argparse.Namespace) -> None:
    state = load_state()
    ok = remove_keyword(state, args.keyword)
    save_state(state)
    _print({"removed": ok})


def cmd_run(args: argparse.Namespace) -> None:
    if args.task == "up-watch":
        count, errors = run_up_watch(notify=True)
        _print({"new": count, "errors": errors})
    elif args.task == "keyword-daily":
        count, errors = run_keyword_daily(force=args.force, notify=True)
        _print({"items": count, "errors": errors})
    elif args.task == "all":
        counts, errors = run_all()
        _print({"counts": counts, "errors": errors})
    else:
        raise RuntimeError("Unknown task")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openclaw")
    sub = parser.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("up", help="Manage UP list")
    up_sub = up.add_subparsers(dest="action", required=True)
    up_add = up_sub.add_parser("add", help="Add UP by MID/name/url")
    up_add.add_argument("identifier")
    up_add.set_defaults(func=cmd_up_add)
    up_list = up_sub.add_parser("list", help="List UPs")
    up_list.set_defaults(func=cmd_up_list)
    up_rm = up_sub.add_parser("remove", help="Remove UP by MID")
    up_rm.add_argument("mid")
    up_rm.set_defaults(func=cmd_up_remove)

    kw = sub.add_parser("kw", help="Manage keyword list")
    kw_sub = kw.add_subparsers(dest="action", required=True)
    kw_add = kw_sub.add_parser("add", help="Add keyword")
    kw_add.add_argument("keyword")
    kw_add.set_defaults(func=cmd_kw_add)
    kw_list = kw_sub.add_parser("list", help="List keywords")
    kw_list.set_defaults(func=cmd_kw_list)
    kw_rm = kw_sub.add_parser("remove", help="Remove keyword")
    kw_rm.add_argument("keyword")
    kw_rm.set_defaults(func=cmd_kw_remove)

    run = sub.add_parser("run", help="Run tasks")
    run.add_argument("task", choices=["up-watch", "keyword-daily", "all"])
    run.add_argument("--force", action="store_true", help="force daily report")
    run.set_defaults(func=cmd_run)

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
