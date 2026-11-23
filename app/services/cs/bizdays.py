"""영업일 계산 — 주말·공휴일·설날·추석 연휴 제외 (자료: data/event_calendar.csv, 2026-11-23 창 4 ③)."""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

CAL = Path(__file__).resolve().parents[3] / "data" / "event_calendar.csv"


@lru_cache(maxsize=1)
def holidays() -> frozenset[date]:
    out: set[date] = set()
    try:
        with CAL.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name, cat = row.get("event") or "", row.get("category") or ""
                if cat == "공휴일" or (cat == "명절" and ("설날" in name or "추석" in name)):
                    try:
                        out.add(date.fromisoformat(row["date"]))
                    except (KeyError, ValueError):
                        continue
    except OSError:
        pass
    return frozenset(out)


def is_bizday(d: date) -> bool:
    return d.weekday() < 5 and d not in holidays()


def add_bizdays(start: datetime, n: int) -> datetime:
    """start 다음 영업일부터 n 번째 영업일의 같은 시각 (n=0 이면 start 그대로)."""
    d = start
    left = n
    while left > 0:
        d += timedelta(days=1)
        if is_bizday(d.date()):
            left -= 1
    return d


def bizdays_between(start: datetime, end: datetime) -> int:
    n, d = 0, start.date()
    while d < end.date():
        d += timedelta(days=1)
        if is_bizday(d):
            n += 1
    return n
