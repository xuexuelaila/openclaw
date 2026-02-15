from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from .http import HttpClient


class BiliClient:
    def __init__(self) -> None:
        self.http = HttpClient()

    def _check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data.get("code") != 0:
            raise RuntimeError(f"Bili API error: {data}")
        return data

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.get_json(
            url,
            params,
            retry_on_statuses={412, 429},
            retry_on_codes={-799},
        )

    def search_user(self, keyword: str, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
        url = "https://api.bilibili.com/x/web-interface/search/type"
        params = {
            "search_type": "bili_user",
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
        }
        data = self._check(self._get(url, params))
        result = data.get("data", {}).get("result", []) or []
        users = []
        for item in result:
            users.append(
                {
                    "mid": item.get("mid"),
                    "uname": item.get("uname"),
                    "fans": item.get("fans"),
                }
            )
        return users

    def get_up_info(self, mid: str) -> Dict[str, Any]:
        url = "https://api.bilibili.com/x/space/acc/info"
        data = self._check(self._get(url, {"mid": mid}))
        d = data.get("data", {}) or {}
        info = {
            "mid": str(d.get("mid")),
            "name": d.get("name"),
            "sign": d.get("sign"),
            "level": d.get("level"),
            "face": d.get("face"),
        }
        try:
            stat = self.get_relation_stat(mid)
            info["follower"] = stat.get("follower", 0)
        except Exception:
            info["follower"] = d.get("follower", 0)
        return info

    def get_relation_stat(self, mid: str) -> Dict[str, Any]:
        url = "https://api.bilibili.com/x/relation/stat"
        data = self._check(self._get(url, {"vmid": mid}))
        return data.get("data", {}) or {}

    def list_up_videos(self, mid: str, page: int = 1, page_size: int = 30) -> List[Dict[str, Any]]:
        url = "https://api.bilibili.com/x/space/arc/search"
        params = {
            "mid": mid,
            "pn": page,
            "ps": page_size,
            "order": "pubdate",
        }
        data = self._check(self._get(url, params))
        vlist = data.get("data", {}).get("list", {}).get("vlist", []) or []
        videos: List[Dict[str, Any]] = []
        for v in vlist:
            videos.append(
                {
                    "bvid": v.get("bvid"),
                    "aid": v.get("aid"),
                    "title": v.get("title"),
                    "description": v.get("description"),
                    "pic": v.get("pic"),
                    "pubdate": v.get("created"),
                    "length": v.get("length"),
                    "play": v.get("play"),
                    "comment": v.get("comment"),
                    "mid": str(v.get("mid")),
                    "author": v.get("author"),
                    "url": f"https://www.bilibili.com/video/{v.get('bvid')}"
                    if v.get("bvid")
                    else None,
                }
            )
        return videos

    def get_video_detail(self, bvid: str) -> Dict[str, Any]:
        url = "https://api.bilibili.com/x/web-interface/view"
        data = self._check(self._get(url, {"bvid": bvid}))
        d = data.get("data", {}) or {}
        return {
            "bvid": d.get("bvid"),
            "title": d.get("title"),
            "desc": d.get("desc"),
            "pic": d.get("pic"),
            "pubdate": d.get("pubdate"),
            "owner": d.get("owner", {}),
            "stat": d.get("stat", {}),
            "duration": d.get("duration"),
            "url": f"https://www.bilibili.com/video/{d.get('bvid')}"
            if d.get("bvid")
            else None,
        }

    def search_videos_by_keyword(
        self, keyword: str, page: int = 1, page_size: int = 20
    ) -> List[Dict[str, Any]]:
        url = "https://api.bilibili.com/x/web-interface/search/type"
        params = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
        }
        data = self._check(self._get(url, params))
        result = data.get("data", {}).get("result", []) or []
        videos: List[Dict[str, Any]] = []
        for item in result:
            bvid = item.get("bvid")
            videos.append(
                {
                    "bvid": bvid,
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "pic": item.get("pic"),
                    "pubdate": item.get("pubdate"),
                    "author": item.get("author"),
                    "mid": str(item.get("mid")),
                    "play": item.get("play"),
                    "comment": item.get("comment"),
                    "url": f"https://www.bilibili.com/video/{bvid}" if bvid else None,
                }
            )
        return videos


def within_days(pub_ts: int | None, days: int) -> bool:
    if not pub_ts:
        return False
    pub = dt.datetime.utcfromtimestamp(pub_ts)
    now = dt.datetime.utcnow()
    return (now - pub).days <= days
