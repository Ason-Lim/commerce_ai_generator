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
* (2026-11-24 밤) 한 주에 행사가 여럿이면 근거에 행사가 다 붙어 구별이 안 된다 → `main_event` = 작년 같은 행사 날짜가
  그 키워드의 작년 최고 순위 날짜와 가장 가까운 행사 태그(같으면 D-day 가 작은 것). `sources` 는 그대로 전부 낸다.
* (2026-11-25) 비교 기준 확정 — '전년 기준': 평소엔 전년 같은 주, 설·추석 D-35~D+7 은 전년 같은 명절 날짜에 맞춤
  (backtest.year_back). 근거 이름은 맞춘 명절이 있으면 '전년 설날 맞춤' 처럼 바뀐다.
* (2026-11-25) 탐색기(반복만)는 **근거 열로만** 붙인다 — 목록에 넣거나 순서를 바꾸지 않는다. 그 주에 진입이 예상되는데
  목록에 없는 반복 키워드는 주마다 `explorer_only` 로 따로 낸다. 2026 백테스트 28일·상위20·7일+ 20.5%
  (규칙을 만들 때 본 자료라 참고값 — 실제 성적은 forecast.ledger).
* (2026-11-24 밤) 거리가 같으면 절기(type=solar_term, 입하 등)를 쇼핑 행사·공휴일보다 뒤로 민다 — 절기는 날짜가
  다른 행사와 자주 겹치고(입하=어린이날 5-05), 실제 수요를 끄는 쪽은 대개 쇼핑 행사라서. 순서: 거리 → 절기 여부 → D-day → 달력 순서.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from app.services.trends.forecast import backtest as bt
from app.services.trends.forecast import calendar as cal
from app.services.trends.forecast import events as ev

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


def _year_back_best(days: bt._Days, a: dt.date, b: dt.date, limit: dt.date, shifts) -> tuple[dict, int, set[str]]:
    """[a, b] 의 날마다 '전년 기준' 날(year_back)을 보고 키워드별 (최고 순위, 그 날짜) + 관측일 수 + 맞춘 명절."""
    out: dict[str, tuple[int, dt.date]] = {}
    seen, aligned = 0, set()
    d = a
    while d <= b:
        src, name = bt.year_back(d, shifts)
        if name:
            aligned.add(name)
        day = days.get(src) if src <= limit else None
        if day:
            seen += 1
            for kw, r in day.items():
                if r < out.get(kw, (10**6, src))[0]:
                    out[kw] = (r, src)
        d += dt.timedelta(days=1)
    return out, seen, aligned


def explorer_repeat(days: bt._Days, as_of: dt.date, horizon: int, top_now: set[str], rows: list[dict],
                    rank_dir) -> dict[str, dict]:  # fmt: skip
    """탐색기(반복만) — {키워드: {event, expected_enter, best_rank_past}}. 기준일까지의 파일만 (backtest.m_explorer 와 같은 조건)."""
    out: dict[str, dict] = {}
    names = {name for name, _ in bt._event_dates(rows)} | set(ev.GROUPS)
    for name in sorted(names):
        occ = ev.group_occurrences(name, rows)
        for y, (start, _end) in occ.items():
            if not 1 <= (start - as_of).days <= horizon - ev.ENTER_FROM:
                continue
            years = sorted(yy for yy in occ if yy < y)
            if len(years) < 2:
                continue
            rep = ev.event_report(name, rank_dir, years, rows=rows, as_of=as_of, limit=200)
            for f in ev.forecast_from_report(rep, start):
                if f["grade"] != "반복" or f["keyword"] in top_now:
                    continue
                enter = dt.date.fromisoformat(f["expected_enter"])
                if not as_of < enter <= as_of + dt.timedelta(days=horizon):
                    continue
                cur = out.get(f["keyword"])
                score = f["best_rank_past"] or 999
                if cur is None or score < cur["best_rank_past"]:
                    out[f["keyword"]] = {"event": name, "expected_enter": enter.isoformat(), "best_rank_past": score}
    return out


def next_weeks(rank_dir: str | Path, as_of: dt.date, *, weeks: int = 4, top_n: int = TOP_N,
               rows: list[dict] | None = None, with_explorer: bool = True) -> dict:  # fmt: skip
    rows = cal.load() if rows is None else rows
    shifts = bt.lunar_shifts(rows)
    days = bt._Days(rank_dir)
    got = bt.population(days, as_of)
    if got is None:
        return {"as_of": as_of.isoformat(), "status": "no_data", "weeks": [],
                "note": "기준일 최근 7일 순위 파일이 없어요 — 순위 수집·백필을 먼저 확인해 주세요"}  # fmt: skip
    top_now, _vocab = got
    occ: dict[str, dict[int, dt.date]] = {}
    for name, d in bt._event_dates(rows):
        occ.setdefault(name, {})[d.year] = d
    exr = explorer_repeat(days, as_of, 7 * weeks, top_now, rows, rank_dir) if with_explorer else {}
    solar = {r["event"] for r in rows if r.get("type") == "solar_term"}  # 거리 동점이면 절기는 뒤로
    out_weeks = []
    for k in range(1, weeks + 1):
        a = as_of + dt.timedelta(days=7 * (k - 1) + 1)
        b = as_of + dt.timedelta(days=7 * k)
        cand: dict[str, dict] = {}
        ly, seen, aligned = _year_back_best(days, a, b, as_of, shifts)
        ly_tag = "전년 " + "·".join(sorted(aligned)) + " 맞춤" if aligned else "전년 같은 주"
        for kw, (r, when) in ly.items():
            if r <= bt.BAND and kw not in top_now:
                cand[kw] = {"keyword": kw, "score": r, "last_year_best": r, "last_year_date": when.isoformat(),
                            "sources": [ly_tag]}  # fmt: skip
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
                    c.setdefault("_ev", []).append((tag, prev, (d - as_of).days, name in solar))
                if r < c["score"]:
                    c.update(score=r, last_year_best=r, last_year_date=when.isoformat())
        for c in cand.values():
            evs = c.pop("_ev", [])
            best_day = dt.date.fromisoformat(c["last_year_date"])
            c["main_event"] = min(evs, key=lambda e: (abs((e[1] - best_day).days), e[3], e[2]))[0] if evs else None
        items = sorted(cand.values(), key=lambda c: (c["score"], -len(c["sources"]), c["keyword"]))
        week_ex = {kw: x for kw, x in exr.items() if a.isoformat() <= x["expected_enter"] <= b.isoformat()}
        for c in items:
            c["explorer_repeat"] = week_ex.get(c["keyword"])
        shown = {c["keyword"] for c in items[:top_n]}
        ex_only = sorted(({"keyword": kw} | x for kw, x in week_ex.items() if kw not in shown),
                         key=lambda x: (x["best_rank_past"], x["keyword"]))  # fmt: skip
        cov = seen / 7
        out_weeks.append({
            "start": a.isoformat(),
            "end": b.isoformat(),
            "events": events,
            "candidates": len(items),
            "items": items[:top_n],
            "explorer_only": ex_only[:10],
            "baseline_tag": ly_tag,
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
                 "'전년' 근거는 평소 전년 같은 주, 설·추석 시즌은 전년 같은 명절 날짜 기준. 탐색기(반복만)는 근거 열로만 표시하고 순서에 쓰지 않아요. "
                 "백테스트 28일·상위 20·7일 이상 앞서 맞힌 비율: 2025 약 10% · 2026 약 16%(전년 기준·행사 상대일). 고객 화면·추천 순위에는 쓰지 않아요."),
    }  # fmt: skip


__all__ = ["next_weeks", "TOP_N"]
