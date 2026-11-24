"""
예측 백테스트 — 기준선 3종 + 선행 곡선 탐색기 (연구 문서 2026-11-19 §4, 예측 창 다음 단계 ③)
==========================================================================================

질문 Q1 (GPT 1차 고정): **예측일(as_of) 현재 100위 밖인 키워드 중, 7·14·28일 안에 한 번이라도 100위 안에 들어올 키워드.**
  - 상위권 '유지'는 따로 평가한다(여기서는 하지 않음).
  - 모집단: as_of 의 마지막 관측일(최근 7일 안)에 100위 안이 아닌 **모든** 키워드(처음 보는 키워드 포함 — 놓친 상승도 세려고).
    예측은 as_of 이전 VOCAB_DAYS 일 안에 본 키워드에서만 나올 수 있다.
  - 정답: (as_of, as_of+h] 의 관측일 중 하루라도 100위 안. 그 기간 관측일이 h×FUTURE_MIN_SHARE 보다 적으면 그 기간은 판정하지 않는다.

정보 누출 통제: 예측(후보 고르기·점수)은 **as_of 이하 파일만** 읽는다. 정답만 as_of 뒤를 읽는다.

방법 (모두 같은 모집단·같은 기간에서 비교)
  recent       최근 상태 유지 — 최근 7일(as_of 포함) 안에 100위 안이었던 키워드가 다시 들어온다
  last_year    전년 계절 반복 — 364일 전(요일 맞춤) 같은 기간에 100위 안이었던 키워드
  event_rel    행사 상대일 반복 — (as_of, as_of+h] 안 행사마다 작년 같은 행사까지 남은 일수가 같은 기간에 100위 안이었던 키워드
  explorer     선행 곡선 탐색기(events.event_report) — 반복/후보 키워드 중 예상 진입일(행사 시작 − 선행일)이 기간 안인 것
               (as_of 이전 해만 판정에 씀 — event_report 의 as_of 규칙)

지표 (§4, 기간마다 · 예측일 전체 합산)
  n_true · n_pred · hits · precision · recall · top20_precision(점수 순 상위 20) · lead_median(적중의 첫 진입까지 일수)
  · major_missed(50위 안까지 오른 정답 중 놓친 비율) · false_pos(불필요한 준비 작업 수) · extra_hits(explorer 가 기준선 셋이 모두 놓친 적중)

이 결과는 **2024·2025 = 탐색·개발 자료** 위의 규칙 비교용이다. 최종 성적은 앞으로 매주 쌓이는 '실제 예보 vs 실제'로 낸다.
목표(초안): 28일 기간 적중률 기준선 대비 +15%p — 첫 결과를 보고 다시 정한다.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
from pathlib import Path

from app.services.trends import period
from app.services.trends.forecast import calendar as cal
from app.services.trends.forecast import events as ev

BAND = period.TOP_BAND  # 100
MAJOR_BAND = 50
HORIZONS = (7, 14, 28)
VOCAB_DAYS = 400  # 모집단 어휘 — as_of 전 400일 안 상위 500 등장
RECENT_DAYS = 7
YEAR_SHIFT = 364  # 52주 — 요일을 맞춘다
FUTURE_MIN_SHARE = 0.6
TOP_N = 20
METHODS = ("recent", "last_year", "event_rel", "explorer")
BASELINES = ("recent", "last_year", "event_rel")


class _Days:
    """날짜 → 순위표(없으면 None). as_of 를 넘는 날은 '예측 쪽'에서 읽지 못하게 따로 막는다."""

    def __init__(self, rank_dir: str | Path):
        self.files = period.rank_files(rank_dir)

    def get(self, d: dt.date) -> dict[str, int] | None:
        p = self.files.get(d.isoformat())
        return period.read_ranks(p) if p else None


def _best(days: _Days, start: dt.date, end: dt.date, *, limit: dt.date) -> dict[str, int]:
    """[start, end] (limit 이하만) 동안 키워드별 최고 순위."""
    out: dict[str, int] = {}
    d = start
    while d <= end:
        if d <= limit:
            day = days.get(d)
            if day:
                for kw, r in day.items():
                    if r < out.get(kw, 10**6):
                        out[kw] = r
        d += dt.timedelta(days=1)
    return out


def population(days: _Days, as_of: dt.date) -> tuple[set[str], set[str]] | None:
    """(지금 100위 안 키워드 = 모집단에서 뺄 것, 어휘 = as_of 전 VOCAB_DAYS 일 안 상위 500 등장).
    as_of 의 마지막 관측일(최근 7일 안)이 없으면 None(그날은 건너뜀)."""
    last = None
    for k in range(RECENT_DAYS):
        day = days.get(as_of - dt.timedelta(days=k))
        if day:
            last = day
            break
    if last is None:
        return None
    vocab: set[str] = set()
    d = as_of - dt.timedelta(days=VOCAB_DAYS)
    while d <= as_of:
        day = days.get(d)
        if day:
            vocab.update(day)
        d += dt.timedelta(days=1)
    top_now = {kw for kw, r in last.items() if r <= BAND}
    return top_now, vocab


def truth(days: _Days, as_of: dt.date, h: int, top_now: set[str]) -> tuple[dict[str, dict], int] | None:
    """{키워드: {first: 첫 진입 날짜까지 일수, best}} 정답 + 관측일 수. 관측일이 모자라면 None."""
    hits: dict[str, dict] = {}
    seen = 0
    for k in range(1, h + 1):
        day = days.get(as_of + dt.timedelta(days=k))
        if not day:
            continue
        seen += 1
        for kw, r in day.items():
            if r <= BAND and kw not in top_now:
                cur = hits.get(kw)
                if cur is None:
                    hits[kw] = {"first": k, "best": r}
                elif r < cur["best"]:
                    cur["best"] = r
    if seen < math.ceil(h * FUTURE_MIN_SHARE):
        return None
    return hits, seen


# ── 방법들: {키워드: 점수(작을수록 확신 — 근거 순위)} ──
def m_recent(days: _Days, as_of: dt.date, h: int, top_now: set[str], **_) -> dict[str, float]:
    best = _best(days, as_of - dt.timedelta(days=RECENT_DAYS - 1), as_of, limit=as_of)
    return {kw: r for kw, r in best.items() if r <= BAND and kw not in top_now}


def m_last_year(days: _Days, as_of: dt.date, h: int, top_now: set[str], **_) -> dict[str, float]:
    a = as_of + dt.timedelta(days=1 - YEAR_SHIFT)
    b = as_of + dt.timedelta(days=h - YEAR_SHIFT)
    best = _best(days, a, b, limit=as_of)
    return {kw: r for kw, r in best.items() if r <= BAND and kw not in top_now}


def _event_dates(rows: list[dict]) -> list[tuple[str, dt.date]]:
    out = []
    for r in rows:
        if r.get("type") == "window" or r["event"].endswith(("연휴 끝",)):
            continue
        out.append((r["event"], dt.date.fromisoformat(r["date"])))
    return out


def m_event_rel(days: _Days, as_of: dt.date, h: int, top_now: set[str], *, rows: list[dict], **_) -> dict[str, float]:
    out: dict[str, float] = {}
    occ: dict[str, dict[int, dt.date]] = {}
    for name, d in _event_dates(rows):
        occ.setdefault(name, {})[d.year] = d
    for name, d in _event_dates(rows):
        off = (d - as_of).days
        if not 1 <= off <= h:
            continue
        prev = occ[name].get(d.year - 1)
        if prev is None:
            continue
        a = prev - dt.timedelta(days=off - 1)  # 작년: 행사까지 남은 일수가 같은 날부터
        b = prev + dt.timedelta(days=h - off)
        for kw, r in _best(days, a, b, limit=as_of).items():
            if r <= BAND and kw not in top_now and r < out.get(kw, 10**6):
                out[kw] = r
    return out


def m_explorer(days: _Days, as_of: dt.date, h: int, top_now: set[str], *, rows: list[dict], rank_dir, cache: dict,
               **_) -> dict[str, float]:  # fmt: skip
    """선행 곡선 탐색기 — 행사(군) 시작이 (as_of, as_of+h+28] 안이면, 작년까지의 반복/후보 키워드의 예상 진입일을 본다."""
    out: dict[str, float] = {}
    names = {name for name, _ in _event_dates(rows)} | set(ev.GROUPS)
    for name in sorted(names):
        occ = ev.group_occurrences(name, rows)
        for y, (start, _end) in occ.items():
            if not 1 <= (start - as_of).days <= h - ev.ENTER_FROM:
                continue
            years = sorted(yy for yy in occ if yy < y)
            if not years:
                continue
            key = (name, y, as_of)
            if key not in cache:
                cache[key] = ev.event_report(name, rank_dir, years, rows=rows, as_of=as_of, limit=200)
            for f in ev.forecast_from_report(cache[key], start):
                enter = dt.date.fromisoformat(f["expected_enter"])
                if enter <= as_of + dt.timedelta(days=h) and start > as_of and f["keyword"] not in top_now:
                    score = (0 if f["grade"] == "반복" else 1000) + (f["best_rank_past"] or 999)
                    if score < out.get(f["keyword"], 10**6):
                        out[f["keyword"]] = score
    return out


FUNCS = {"recent": m_recent, "last_year": m_last_year, "event_rel": m_event_rel, "explorer": m_explorer}


def _empty() -> dict:
    return {"n_true": 0, "n_pred": 0, "hits": 0, "top_pred": 0, "top_hits": 0, "leads": [], "major": 0,
            "major_hit": 0, "extra_hits": 0}  # fmt: skip


def run(rank_dir: str | Path, start: dt.date, end: dt.date, *, step: int = 7, horizons=HORIZONS,
        methods=METHODS, rows: list[dict] | None = None) -> dict:  # fmt: skip
    """start~end 사이 step 일 간격의 예측일마다 Q1 을 풀고 합산."""
    rows = cal.load() if rows is None else rows
    days = _Days(rank_dir)
    acc = {m: {h: _empty() for h in horizons} for m in methods}
    dates, skipped, per_date = [], [], []
    cache: dict = {}
    d = start
    while d <= end:
        got = population(days, d)
        if got is None:
            skipped.append({"as_of": d.isoformat(), "why": "최근 7일 순위 자료 없음"})
            d += dt.timedelta(days=step)
            continue
        top_now, vocab = got
        row = {"as_of": d.isoformat(), "top_now": len(top_now), "vocab": len(vocab), "h": {}}
        for h in horizons:
            t = truth(days, d, h, top_now)
            if t is None:
                row["h"][h] = None
                continue
            hits_true, _seen = t
            base_hit: set[str] = set()
            res = {}
            for m in methods:
                pred = FUNCS[m](days, d, h, top_now, rows=rows, rank_dir=rank_dir, cache=cache)
                hit = {kw for kw in pred if kw in hits_true}
                top = sorted(pred, key=lambda k: (pred[k], k))[:TOP_N]
                a = acc[m][h]
                a["n_true"] += len(hits_true)
                a["n_pred"] += len(pred)
                a["hits"] += len(hit)
                a["top_pred"] += len(top)
                a["top_hits"] += sum(1 for k in top if k in hits_true)
                a["leads"] += [hits_true[k]["first"] for k in hit]
                major = {k for k, v in hits_true.items() if v["best"] <= MAJOR_BAND}
                a["major"] += len(major)
                a["major_hit"] += len(major & hit)
                res[m] = hit
                if m in BASELINES:
                    base_hit |= hit
            if "explorer" in res:
                acc["explorer"][h]["extra_hits"] += len(res["explorer"] - base_hit)
            row["h"][h] = {"true": len(hits_true), **{m: len(v) for m, v in res.items()}}
        dates.append(d.isoformat())
        per_date.append(row)
        d += dt.timedelta(days=step)
    return {
        "range": [start.isoformat(), end.isoformat()],
        "step": step,
        "dates": len(dates),
        "skipped": skipped,
        "metrics": {m: {h: _summary(acc[m][h], m) for h in horizons} for m in methods},
        "per_date": per_date,
        "rules": {
            "band": BAND,
            "major_band": MAJOR_BAND,
            "vocab_days": VOCAB_DAYS,
            "recent_days": RECENT_DAYS,
            "year_shift": YEAR_SHIFT,
            "future_min_share": FUTURE_MIN_SHARE,
            "top_n": TOP_N,
        },  # fmt: skip
        "notes": [
            "Q1 = 예측일에 100위 밖인 키워드가 기간 안에 한 번이라도 100위 안에 들어오는가",
            "예측은 예측일까지의 파일만 읽음(정보 누출 통제) — 정답만 그 뒤를 읽음",
            "2024·2025 는 규칙을 보고 만든 탐색·개발 자료 — 최종 성적은 앞으로 쌓이는 실제 예보로",
        ],
    }


def _summary(a: dict, m: str) -> dict:
    p = a["hits"] / a["n_pred"] if a["n_pred"] else None
    r = a["hits"] / a["n_true"] if a["n_true"] else None
    out = {
        "n_true": a["n_true"],
        "n_pred": a["n_pred"],
        "hits": a["hits"],
        "precision": round(p, 4) if p is not None else None,
        "recall": round(r, 4) if r is not None else None,
        "top20_precision": round(a["top_hits"] / a["top_pred"], 4) if a["top_pred"] else None,
        "lead_median": statistics.median(a["leads"]) if a["leads"] else None,
        "major_missed": round(1 - a["major_hit"] / a["major"], 4) if a["major"] else None,
        "false_pos": a["n_pred"] - a["hits"],
    }
    if m == "explorer":
        out["extra_hits"] = a["extra_hits"]
    return out


__all__ = ["HORIZONS", "METHODS", "BASELINES", "population", "truth", "run", "FUNCS"]
