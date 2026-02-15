from __future__ import annotations


def parse_count(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip().replace(",", "")
    if not s:
        return 0
    try:
        return int(s)
    except Exception:
        pass
    # handle Chinese units
    if s.endswith("万"):
        try:
            return int(float(s[:-1]) * 10000)
        except Exception:
            return 0
    if s.endswith("亿"):
        try:
            return int(float(s[:-1]) * 100000000)
        except Exception:
            return 0
    return 0
