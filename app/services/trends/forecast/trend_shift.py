"""트렌드 변화 리포트 — '작년엔 떴는데 올해는 안 뜬 키워드' · '처음 뜬 키워드' (2026-11-25)
=========================================================================

예보가 못 맞힌 것 중 **트렌드 변화로 볼 몫**만 따로 보여 준다(사용자 결정 11-25 10:17).
  - 식은 키워드(작년 키워드가 안 옴): 전년 기준(평소 전년 같은 주, 설·추석은 전년 같은 명절 날짜)으로 작년 이 기간에
    **50위 안**이던 키워드가, 올해 같은 28일 동안 100위 안에 한 번도 못 들고 기간 앞뒤 14일에도 없던 것.
    (앞뒤 14일 안에 들었으면 '시점 어긋남'이라 여기서 뺀다.)
  - 새로 뜬 키워드(처음 등장): 28일 안에 **50위 안**까지 올라왔는데, 기준일 전 400일 동안 상위 500에 한 번도 없던 것.
* 기준일 뒤 28일(+14일)의 실제 순위가 있어야 판정한다 — 기본 기준일 = 마지막 순위 파일 − 42일.
* 늦게 적중·시점 어긋남은 방법으로 줄일 몫이라 여기 넣지 않는다(백테스트·예보 성적판의 '못 맞힌 이유').
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
    this_year = bt._best(
        days, as_of + dt.timedelta(days=1), as_of + dt.timedelta(days=H), limit=as_of + dt.timedelta(days=H)
    )
    came = [k for k in ly_major if k in hits]
    timing = [k for k in ly_major if k not in hits and k in near]
    cooled = sorted((k for k in ly_major if k not in hits and k not in near), key=lambda k: (ly_major[k], k))
    majors = {k: v for k, v in hits.items() if v["best"] <= BAND_SHOWN}
    new = sorted((k for k in majors if k not in vocab), key=lambda k: (majors[k]["best"], k))
    return {
        "as_of": as_of.isoformat(),
        "window": [(as_of + dt.timedelta(days=1)).isoformat(), (as_of + dt.timedelta(days=H)).isoformat()],
        "status": "ok",
        "last_year_major": len(ly_major),
        "came_back": len(came),
        "timing_off": len(timing),
        "cooled": len(cooled),
        "cooled_share": round(len(cooled) / len(ly_major), 4) if ly_major else None,
        "major_rise": len(majors),
        "new": len(new),
        "new_share": round(len(new) / len(majors), 4) if majors else None,
        "cooled_items": [{"keyword": k, "last_year_best": ly_major[k], "this_year_best": this_year.get(k)} for k in cooled[:limit]],
        "new_items": [{"keyword": k, "best": majors[k]["best"],
                       "first_date": (as_of + dt.timedelta(days=majors[k]["first"])).isoformat()} for k in new[:limit]],  # fmt: skip
        "note": ("식은 키워드 = 작년 이 기간(전년 기준) 50위 안 → 올해 28일 동안 100위 밖, 앞뒤 14일에도 없음. "
                 "새로 뜬 키워드 = 28일 안 50위 안까지 올랐는데 지난 400일 동안 상위 500에 없던 것. 참고 자료 — 추천 순위에 쓰지 않아요."),
    }  # fmt: skip


def weekly(rank_dir: str | Path, end: dt.date, *, weeks: int = 8, rows: list[dict] | None = None) -> list[dict]:
    """end 부터 1주씩 거슬러 올라가며 숫자만 (목록 없이)."""
    rows = cal.load() if rows is None else rows
    out = []
    for i in range(weeks):
        r = report(rank_dir, end - dt.timedelta(days=7 * i), rows=rows, limit=0)
        out.append({k: r.get(k) for k in ("as_of", "status", "last_year_major", "came_back", "timing_off", "cooled",
                                          "cooled_share", "major_rise", "new", "new_share")})  # fmt: skip
    return out


__all__ = ["report", "weekly", "default_as_of"]
