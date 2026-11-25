"""트렌드 변화(검토 가설) 리포트 — 관측창 내 미진입 · 과거 400일 Top500 관측 이력 없음 (2026-11-25)
=====================================================================================

사용자 결정(11-25 10:17): 예보가 벗어난 것 중 트렌드 변화일 수 있는 몫을 따로 보여 준다.
GPT 검토(11-25 10:29) 반영: 이 화면은 **관측 결과**이고 원인 확정이 아니다 — 트렌드 변화는 검토할 가설로만 표시한다.
  - 관측창 내 미진입(작년 50위 안): 전년 기준(평소 전년 같은 주, 설·추석은 전년 같은 명절 날짜)으로 작년 이 기간에 50위 안이던
    키워드가 올해 같은 28일 동안 100위 안에 한 번도 못 들고, 기간 앞뒤 14일에도 없던 것. 수요가 식었을 수도 있지만
    더 큰 시점 차이·후보 선정 오류(작년이 일회성)일 수도 있다.
  - 과거 400일 Top500 관측 이력 없음: 28일 안에 50위 안까지 올랐는데 기준일 전 400일 동안 상위 500에 한 번도 없던 것.
    과거 400일 순위 파일이 90% 미만이면 판정하지 않는다(자료 부족 — 기존 키워드가 '이력 없음'으로 잡힐 수 있어서).
* 관측창(기준일+1 ~ +42일) 안 결측일 수를 함께 낸다. 기본 기준일 = 마지막 순위 파일 − 42일(끝만 확보 — 중간 결측은 따로 확인).
* 성능 평가에서 '관측창 내 미진입'을 빼지 않는다 — 주 지표는 제출 전체 선행 적중률(backtest·ledger).
* 관리자 전용 참고 자료 — 고객 화면·추천 순위에는 쓰지 않는다.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from app.services.trends import period
from app.services.trends.forecast import backtest as bt
from app.services.trends.forecast import calendar as cal

H = 28
BAND_SHOWN = bt.MAJOR_BAND  # 50위 안만 '주요'


def default_as_of(rank_dir) -> dt.date | None:
    files = period.rank_files(rank_dir)
    if not files:
        return None
    return dt.date.fromisoformat(max(files)) - dt.timedelta(days=H + bt.TIMING_DAYS)


def report(rank_dir: str | Path, as_of: dt.date, *, rows: list[dict] | None = None, limit: int = 30) -> dict:
    rows = cal.load() if rows is None else rows
    days = bt._Days(rank_dir)
    got = bt.population(days, as_of)
    if got is None:
        return {"as_of": as_of.isoformat(), "status": "no_data", "note": "기준일 최근 7일 순위 파일이 없어요"}
    top_now, vocab = got
    tr = bt.truth(days, as_of, H, top_now)
    last = as_of + dt.timedelta(days=H + bt.TIMING_DAYS)
    if tr is None or max(days.files, default="") < last.isoformat():
        return {"as_of": as_of.isoformat(), "status": "pending",
                "note": f"기준일 뒤 {H + bt.TIMING_DAYS}일 순위가 아직 없어요 — {last.isoformat()} 뒤에 판정해요"}  # fmt: skip
    hits, _seen = tr
    near = bt.near_window(days, as_of, H)
    ly = bt.m_last_year_lunar(days, as_of, H, top_now, rows=rows)
    ly_major = {k: r for k, r in ly.items() if r <= BAND_SHOWN}
    end = as_of + dt.timedelta(days=H)
    this_year = bt._best(days, as_of + dt.timedelta(days=1), end, limit=end)
    came = [k for k in ly_major if k in hits]
    timing = [k for k in ly_major if k not in hits and k in near]
    not_in = sorted((k for k in ly_major if k not in hits and k not in near), key=lambda k: (ly_major[k], k))
    majors = {k: v for k, v in hits.items() if v["best"] <= BAND_SHOWN}
    hist_ok = bt.history_coverage(days, as_of) >= bt.HISTORY_MIN
    no_hist = sorted((k for k in majors if k not in vocab), key=lambda k: (majors[k]["best"], k)) if hist_ok else []
    missing = [
        (as_of + dt.timedelta(days=k)).isoformat()
        for k in range(1, H + bt.TIMING_DAYS + 1)
        if (as_of + dt.timedelta(days=k)).isoformat() not in days.files
    ]
    return {
        "as_of": as_of.isoformat(),
        "window": [(as_of + dt.timedelta(days=1)).isoformat(), end.isoformat()],
        "status": "ok",
        "missing_days": len(missing),
        "missing_sample": missing[:5],
        "history_ok": hist_ok,
        "history_coverage": round(bt.history_coverage(days, as_of), 3),
        "last_year_major": len(ly_major),
        "came_back": len(came),
        "timing_off": len(timing),
        "not_entered": len(not_in),
        "not_entered_share": round(len(not_in) / len(ly_major), 4) if ly_major else None,
        "major_rise": len(majors),
        "no_history": len(no_hist) if hist_ok else None,
        "no_history_share": round(len(no_hist) / len(majors), 4) if hist_ok and majors else None,
        "not_entered_items": [{"keyword": k, "last_year_best": ly_major[k], "this_year_best": this_year.get(k)} for k in not_in[:limit]],
        "no_history_items": [{"keyword": k, "best": majors[k]["best"],
                              "first_date": (as_of + dt.timedelta(days=majors[k]["first"])).isoformat()} for k in no_hist[:limit]],  # fmt: skip
        "note": ("관측 결과예요(원인 확정 아님). 관측창 내 미진입 = 작년 이 기간(전년 기준) 50위 안 → 올해 28일 동안 100위 밖, 앞뒤 14일에도 없음 "
                 "— 수요 변화일 수도, 더 큰 시점 차이나 작년 일회성(후보 선정 오류)일 수도 있어요. "
                 "과거 400일 Top500 관측 이력 없음 = 28일 안 50위 안까지 올랐는데 지난 400일 상위 500에 없던 것(과거 순위 파일 90% 미만이면 판정 안 함). "
                 "성능 평가에서는 빼지 않아요. 추천 순위에 쓰지 않아요."),
    }  # fmt: skip


def weekly(rank_dir: str | Path, end: dt.date, *, weeks: int = 8, rows: list[dict] | None = None) -> list[dict]:
    """end 부터 1주씩 거슬러 올라가며 숫자만 (목록 없이)."""
    rows = cal.load() if rows is None else rows
    out = []
    for i in range(weeks):
        r = report(rank_dir, end - dt.timedelta(days=7 * i), rows=rows, limit=0)
        keys = ("as_of", "status", "missing_days", "history_ok", "last_year_major", "came_back", "timing_off",
                "not_entered", "not_entered_share", "major_rise", "no_history", "no_history_share")  # fmt: skip
        out.append({k: r.get(k) for k in keys})
    return out


__all__ = ["report", "weekly", "default_as_of"]
