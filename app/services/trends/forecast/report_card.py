"""행사별 리포트카드 (2026-11-25) — 행사 4주 전에 예보했다면 무엇을 맞히고 무엇을 놓쳤나
=====================================================================

한 행사·한 해마다: 예보일 = 행사 시작 28일 전, 관측창 = 예보일 + 1 ~ 행사 시작일(28일).
  - 방법별(전년 기준·행사 상대일·탐색기(반복만)·최근 유지) 제출 상위 20 의 선행 적중률(첫 진입 7~28일)과 결과 4분류
  - 실제 주요 상승(50위 안까지) 목록 — 어느 방법이 맞혔는지, 처음 진입이 D-몇인지
  - 놓친 주요 상승은 '과거 400일 Top500 관측 이력 없음'(과거 자료 90% 이상일 때만 판정)과 '이력 있음'으로 나눔
* 예보는 예보일까지의 파일만 읽는다(backtest 와 같은 함수). 관측 결과이지 원인 확정이 아니다.
* 백테스트와 같은 이유로 참고값(규칙을 만들 때 본 자료). 관리자 전용 — 추천 순위에 쓰지 않는다.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from app.services.trends.forecast import backtest as bt
from app.services.trends.forecast import calendar as cal
from app.services.trends.forecast import events as ev

H = 28
METHODS = ("last_year_lunar", "event_rel", "explorer_repeat", "recent")
NAMES = {"last_year_lunar": "전년 기준(비교 기준)", "event_rel": "행사 상대일", "explorer_repeat": "탐색기(반복만)",
         "recent": "최근 유지"}  # fmt: skip


def report_card(
    rank_dir: str | Path, event: str, year: int, *, rows: list[dict] | None = None, limit: int = 30
) -> dict:
    rows = cal.load() if rows is None else rows
    occ = ev.group_occurrences(event, rows)
    if year not in occ:
        return {"event": event, "year": year, "status": "no_event", "note": f"{year}년 {event} 날짜가 달력에 없어요"}
    start = occ[year][0]
    as_of = start - dt.timedelta(days=H)
    days = bt._Days(rank_dir)
    got = bt.population(days, as_of)
    if got is None:
        return {"event": event, "year": year, "date": start.isoformat(), "status": "no_data",
                "note": f"예보일 {as_of} 최근 7일 순위 파일이 없어요"}  # fmt: skip
    top_now, vocab = got
    tr = bt.truth(days, as_of, H, top_now)
    if tr is None or max(days.files, default="") < (as_of + dt.timedelta(days=H + bt.TIMING_DAYS)).isoformat():
        return {"event": event, "year": year, "date": start.isoformat(), "status": "pending",
                "note": "행사 뒤 14일까지 순위가 있어야 판정해요"}  # fmt: skip
    hits, seen = tr
    near = bt.near_window(days, as_of, H)
    hist_ok = bt.history_coverage(days, as_of) >= bt.HISTORY_MIN
    cache: dict = {}
    methods, predicted, ranked = {}, {}, {}
    for m in METHODS:
        pred = bt.FUNCS[m](days, as_of, H, top_now, rows=rows, rank_dir=rank_dir, cache=cache)
        order = sorted(pred, key=lambda k: (pred[k], k))
        top = order[: bt.TOP_N]
        for i, k in enumerate(order, 1):  # 상위 20 밖이라도 후보 목록에 있었으면 몇 번째였는지 (상위 20 경계 확인용)
            ranked.setdefault(k, {})[NAMES[m]] = i
        br = bt.classify_top(top, hits, near)
        methods[m] = {"name": NAMES[m], "submitted": len(top), "lead": len(br["lead"]),
                      "lead_rate": round(len(br["lead"]) / len(top), 4) if top else None,
                      "reasons": {r: len(br[r]) for r in bt.REASONS}, "lead_keywords": br["lead"]}  # fmt: skip
        for k in top:
            predicted.setdefault(k, []).append(NAMES[m])
    majors = sorted(
        ((k, v) for k, v in hits.items() if v["best"] <= bt.MAJOR_BAND), key=lambda kv: (kv[1]["best"], kv[0])
    )
    rises = []
    for k, v in majors:
        first = as_of + dt.timedelta(days=v["first"])
        rises.append({"keyword": k, "best": v["best"], "first_date": first.isoformat(), "d_day": (start - first).days,
                      "predicted_by": predicted.get(k, []), "candidate_rank": ranked.get(k, {}),
                      "history": ("없음" if k not in vocab else "있음") if hist_ok else "자료 부족"})  # fmt: skip
    missed = [r for r in rises if not r["predicted_by"]]
    beyond = [r for r in missed if r["candidate_rank"]]
    return {
        "event": event,
        "year": year,
        "date": start.isoformat(),
        "as_of": as_of.isoformat(),
        "window": [(as_of + dt.timedelta(days=1)).isoformat(), (as_of + dt.timedelta(days=H)).isoformat()],
        "status": "ok",
        "observed_days": seen,
        "history_ok": hist_ok,
        "methods": methods,
        "major_rise": len(rises),
        "major_predicted": len(rises) - len(missed),
        "missed": len(missed),
        "missed_no_history": sum(1 for r in missed if r["history"] == "없음"),
        "missed_beyond_top20": len(beyond),
        "rises": rises[:limit],
        "note": ("예보일 = 행사 시작 28일 전, 그날까지의 순위만 읽음. 제출 상위 20 기준 선행 적중(7~28일)·4분류. "
                 "주요 상승은 50위 안까지 오른 키워드, '맞힌 방법'은 그 키워드를 상위 20 에 낸 방법, '후보 순위'는 상위 20 밖이어도 "
                 "후보 목록에 있던 자리(상위 20 경계에서 잘린 것). 관측 결과이고 참고값이에요."),
    }  # fmt: skip


def summary(rank_dir: str | Path, event: str, *, rows: list[dict] | None = None) -> list[dict]:
    """그 행사의 해마다 한 줄(숫자만)."""
    rows = cal.load() if rows is None else rows
    out = []
    for y in sorted(ev.group_occurrences(event, rows)):
        r = report_card(rank_dir, event, y, rows=rows, limit=0)
        keys = (
            "year",
            "date",
            "status",
            "major_rise",
            "major_predicted",
            "missed",
            "missed_no_history",
            "missed_beyond_top20",
        )
        line = {k: r.get(k) for k in keys}
        line["lead_rate"] = {m: x["lead_rate"] for m, x in (r.get("methods") or {}).items()}
        out.append(line)
    return out


__all__ = ["report_card", "summary", "METHODS"]
