import json
import os
from datetime import datetime
from typing import Any, Dict, List

STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "state.json")

DEFAULT_STATE: Dict[str, Any] = {
    "ups": [],
    "keywords": [],
    "last_seen": {
        "up_videos": {},
        "daily": {"date": None},
    },
}


def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)


def load_state() -> Dict[str, Any]:
    _ensure_dir()
    if not os.path.exists(STATE_PATH):
        save_state(DEFAULT_STATE)
        return json.loads(json.dumps(DEFAULT_STATE))
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict[str, Any]) -> None:
    _ensure_dir()
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def add_up(state: Dict[str, Any], up: Dict[str, Any]) -> None:
    if any(u.get("mid") == up.get("mid") for u in state["ups"]):
        return
    up["added_at"] = datetime.utcnow().isoformat() + "Z"
    state["ups"].append(up)


def remove_up(state: Dict[str, Any], mid: str) -> bool:
    before = len(state["ups"])
    state["ups"] = [u for u in state["ups"] if str(u.get("mid")) != str(mid)]
    return len(state["ups"]) < before


def add_keyword(state: Dict[str, Any], keyword: str) -> None:
    keyword = keyword.strip()
    if not keyword:
        return
    if keyword in state["keywords"]:
        return
    state["keywords"].append(keyword)


def remove_keyword(state: Dict[str, Any], keyword: str) -> bool:
    before = len(state["keywords"])
    state["keywords"] = [k for k in state["keywords"] if k != keyword]
    return len(state["keywords"]) < before


def get_last_seen_bvids(state: Dict[str, Any], mid: str) -> List[str]:
    return list(state.get("last_seen", {}).get("up_videos", {}).get(str(mid), []))


def set_last_seen_bvids(state: Dict[str, Any], mid: str, bvids: List[str]) -> None:
    state.setdefault("last_seen", {}).setdefault("up_videos", {})[str(mid)] = bvids


def get_last_daily_date(state: Dict[str, Any]) -> str:
    return state.get("last_seen", {}).get("daily", {}).get("date")


def set_last_daily_date(state: Dict[str, Any], date_str: str) -> None:
    state.setdefault("last_seen", {}).setdefault("daily", {})["date"] = date_str
