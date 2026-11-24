"""'다음 4주 예보' — 관리자 화면용 후보 목록 (2026-11-24, 예측 창 ⑤ 1차)
=====================================================================

연구 문서 §5 ① '다음 4주 예보 화면'의 1차판. **백테스트에서 가장 나았던 두 기준선만** 쓴다(탐색기는 아직 쓰지 않음 — 결과 ③).
  - 전년 같은 주: 364일 전(요일 맞춤) 같은 주에 100위 안이던 키워드
  - 행사 상대일: 그 주 안의 행사마다, 작년 같은 행사까지 남은 일수가 같은 기간에 100위 안이던 키워드

* 대상은 Q1 과 같다 — 기준일(as_of)에 100위 밖인 키워드(이미 상위권인 것은 '유지' 라 뺌).
* 예측은 기준일까지의 파일만 읽는다(백테스트와 같은 함수).
* 주마다 '작년 그 주 자료가 몇 % 있었는지'를 함께 낸다 — 순위 파일 빈 곳이면 후보가 적게 나오므로 경고.
* **예보가 아니라 후보 목록**이다: 백테스트(2025 1~4월)에서 28일 상위 20 중 7일 이상 앞서 맞힌 비율이 약 11%.
  사람이 골라 링크·글을 준비하는 데 쓴다(연구 §5-1 운영 리듬: 월요일 제안 → 5~8개 확정).
* 고객 화면·추천 순위에는 쓰지 않는다.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from app.services.trends.forecast import backtest as bt
from app.services.trends.forecast import calendar as cal

TOP_N = 20
LOW_COVERAGE = 0.6


def _window_best(days: bt._Days, a: dt.date, b: dt.date, limit: dt.date) -> tuple[dict[str, tuple[int, dt.date]], int]:
    """[a, b] 동안 키워드별 (최고 순위, 그 날짜) + 관측일 수."""
    out: dict[str, tuple[int, dt.date]] = {}
    seen = 0
    d = a
    while d <= b:
        if d <= limit:
            day = days.get(d)
            if day:
                seen += 1
                for kw, r in day.items():
                    if r < out.get(kw, (10**6, d))[0]:
                        out[kw] = (r, d)
        d += dt.timedelta(days=1)
    return out, seen


def next_weeks(rank_dir: str | Path, as_of: dt.date, *, weeks: int = 4, top_n: int = TOP_N,
               rows: list[dict] | None = None) -> dict:  # fmt: skip
    rows = cal.load() if rows is None else rows
    days = bt._Days(rank_dir)
    got = bt.population(days, as_of)
    if got is None:
        return {"as_of": as_of.isoformat(), "status": "no_data", "weeks": [],
                "note": "기준일 최근 7일 순위 파일이 없어요 — 순위 수집·백필을 먼저 확인해 주세요"}  # fmt: skip
    top_now, _vocab = got
    occ: dict[str, dict[int, dt.date]] = {}
    for name, d in bt._event_dates(rows):
        occ.setdefault(name, {})[d.year] = d
    out_weeks = []
    for k in range(1, weeks + 1):
        a = as_of + dt.timedelta(days=7 * (k - 1) + 1)
        b = as_of + dt.timedelta(days=7 * k)
        cand: dict[str, dict] = {}
        ly, seen = _window_best(days, a - dt.timedelta(days=bt.YEAR_SHIFT), b - dt.timedelta(days=bt.YEAR_SHIFT), as_of)
        for kw, (r, when) in ly.items():
            if r <= bt.BAND and kw not in top_now:
                cand[kw] = {"keyword": kw, "score": r, "last_year_best": r, "last_year_date": when.isoformat(),
                            "sources": ["전년 같은 주"]}  # fmt: skip
        events = []
        for name, d in bt._event_dates(rows):
            if not a <= d <= b:
                continue
            prev = occ[name].get(d.year - 1)
            events.append({"event": name, "date": d.isoformat(), "d_day": (d - as_of).days,
                           "last_year": prev.isoformat() if prev else None})  # fmt: skip
            if prev is None:
                continue
            pa = prev - dt.timedelta(days=(d - a).days)
            pb = prev + dt.timedelta(days=(b - d).days)
            best, _ = _window_best(days, pa, pb, as_of)
            tag = f"{name} D-{(d - as_of).days}"
            for kw, (r, when) in best.items():
                if r > bt.BAND or kw in top_now:
                    continue
                c = cand.setdefault(kw, {"keyword": kw, "score": r, "last_year_best": r,
                                         "last_year_date": when.isoformat(), "sources": []})  # fmt: skip
                if tag not in c["sources"]:
                    c["sources"].append(tag)
                if r < c["score"]:
                    c.update(score=r, last_year_best=r, last_year_date=when.isoformat())
        items = sorted(cand.values(), key=lambda c: (c["score"], -len(c["sources"]), c["keyword"]))
        cov = seen / 7
        out_weeks.append({
            "start": a.isoformat(),
            "end": b.isoformat(),
            "events": events,
            "candidates": len(items),
            "items": items[:top_n],
            "last_year_coverage": round(cov, 2),
            "warning": (f"작년 같은 주 순위 자료가 {seen}/7일뿐이에요 — 후보가 적게 나올 수 있어요"
                        if cov < LOW_COVERAGE else None),
        })  # fmt: skip
    return {
        "as_of": as_of.isoformat(),
        "status": "ok",
        "weeks": out_weeks,
        "excluded_top_now": len(top_now),
        "note": ("후보 목록이에요(예보 확정 아님) — 기준일에 100위 밖이고, 작년 같은 주 또는 작년 같은 행사 시점에 100위 안이던 키워드. "
                 "백테스트(2025 1~4월)에서 28일·상위 20 중 7일 이상 앞서 맞힌 비율 약 11%. 고객 화면·추천 순위에는 쓰지 않아요."),
    }  # fmt: skip


__all__ = ["next_weeks", "TOP_N"]
