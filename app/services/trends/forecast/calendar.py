"""
행사 달력 읽기 — data/event_calendar.csv (scripts/build_event_calendar.py 가 만듦)
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEFAULT = ROOT / "data" / "event_calendar.csv"
INCIDENTS = ROOT / "data" / "past_incidents.csv"


def load(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else DEFAULT
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.DictReader(fh) if r.get("date")]


def events(rows: list[dict] | None = None, *, types: tuple[str, ...] | None = None) -> list[dict]:
    """행사 이름별 요약 — [{event, type, category, note, dates:{year: date}}], 날짜 순 (연중 위치 기준)."""
    rows = load() if rows is None else rows
    by: dict[str, dict] = {}
    for r in rows:
        if types and r["type"] not in types:
            continue
        if r["event"].endswith(("연휴 시작", "연휴 끝")):
            continue
        e = by.setdefault(r["event"], {"event": r["event"], "type": r["type"], "category": r["category"],
                                       "note": r.get("note", ""), "dates": {}})
        e["dates"][int(r["date"][:4])] = r["date"]
    out = list(by.values())
    out.sort(key=lambda e: min(d[5:] for d in e["dates"].values()))
    return out


def occurrences(name: str, rows: list[dict] | None = None) -> dict[int, dt.date]:
    """{연도: 행사 날짜}"""
    rows = load() if rows is None else rows
    return {int(r["date"][:4]): dt.date.fromisoformat(r["date"]) for r in rows if r["event"] == name}


def upcoming(today: dt.date, days: int = 35, rows: list[dict] | None = None) -> list[dict]:
    """오늘부터 days 일 안의 행사 (D-day 포함) — 4주 예보 머리말용."""
    rows = load() if rows is None else rows
    out = []
    for r in rows:
        d = dt.date.fromisoformat(r["date"])
        if 0 <= (d - today).days <= days and not r["event"].endswith(("연휴 시작", "연휴 끝")):
            out.append({**r, "d_day": (d - today).days})
    out.sort(key=lambda r: r["date"])
    return out


def incidents(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else INCIDENTS
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))
