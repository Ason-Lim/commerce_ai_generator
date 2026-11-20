"""
선행 곡선 탐색기 — 행사 전후 반복 패턴 키워드 자동 추출 (연구 문서 2026-11-19 §3 B-1, GPT 1·2차 검토 반영)
================================================================================================

입력: 하루 단위 식품 순위 폴더 (period.rank_files / read_ranks) + 행사 달력 (forecast.calendar)
출력: 행사마다 "행사 전에 100위 안으로 **들어오고** 행사 뒤 **나가는**" 키워드와 그 상대일 곡선.

상대일 상태 셋 (GPT 2차 ①):
  int(1~500)  정상 파일에서 관측된 순위          → 순위 계산·100위 판정 둘 다 사용
  "out"       정상 파일(500건)에 없음 = 500위 밖  → 정확한 순위는 모름, **100위 밖으로는 사용**
  None        파일 누락·불완전                   → 판단 불가, 집계에서 뺌 (501 대입 없음)

판정 (연도마다):
  기준 구간 BASE  −35…−29  대체로 100위 밖 (유지형 제외)       관측일(int 또는 out) ≥ BASE_MIN_OBS
  진입 구간 ENTER −28…0    100위 안에 한 번 이상                관측일 ≥ ENTER_MIN_OBS
  이탈 구간 EXIT  +3…+14   대체로 100위 밖 (지속형 제외)       관측일 ≥ EXIT_MIN_OBS
  어느 구간이든 관측일이 모자라면 그 해는 '자료 부족' — 판정에 넣지 않는다.
  '대체로' = 100위 안 관측일 비율 ≤ BAND_SHARE_MAX (하루 튄 값은 봐줌).

등급 (GPT 2차 ②): 판정 가능한 해가 **2개 이상**이고 모두 만족 → "반복"(행사 전후 반복 패턴) ·
  한 해만 만족(판정 가능한 해가 하나뿐이거나 일부만 만족) → "후보" · 씨앗 키워드는 판정 이유와 함께 "씨앗".
  '결속'이라는 말은 인과처럼 읽혀 쓰지 않는다.

정보 누출 (GPT 2차 ③): `as_of`(예측 기준일) 뒤의 파일은 읽지 않는다(None 처리) — 이탈 구간이 as_of 전에 끝난 해만 판정.
정점 (GPT 2차 ④): '최고 순위의 25% 안' 대신 두 구간 — peak_best(최고 순위가 **연속**된 날), peak_top(PEAK_BAND 위 안을 **연속** 충족한 가장 긴 구간 중 최고 순위를 품은 것).
연속 행사군 (GPT 2차 ⑤): 복날처럼 이어지는 행사는 GROUPS 로 묶어 시작(초복) 기준 상대일에 끝(말복) 뒤 이탈을 본다.
"""
from __future__ import annotations

import datetime as dt
import statistics
from pathlib import Path

from app.services.trends import period
from app.services.trends.forecast import calendar as cal

REL_FROM, REL_TO = -35, 14          # 표시·판정 창 같음 (GPT 2차 ⑤)
BASE_FROM, BASE_TO = -35, -29
ENTER_FROM = -28                    # ENTER_TO = 행사 끝(단일 행사 0, 행사군은 끝 행사 상대일)
EXIT_AFTER_FROM, EXIT_AFTER_TO = 3, 14   # 행사(군) 끝 뒤 +3…+14
TOP_BAND = period.TOP_BAND          # 100
PEAK_BAND = 20                      # '상위권 유지 구간' 기준 순위
BAND_SHARE_MAX = 1 / 3
BASE_MIN_OBS, ENTER_MIN_OBS, EXIT_MIN_OBS = 4, 20, 8   # 구간별 최소 관측일 (7·29·12일 중)
MIN_YEARS_REPEAT = 2

# 연속 행사군: 이름 → (시작 행사, 끝 행사). 상대일 0 = 시작 행사.
GROUPS = {"복날(초복~말복)": ("초복", "말복"), "설 연휴": ("설날 연휴 시작", "설날 연휴 끝"),
          "추석 연휴": ("추석 연휴 시작", "추석 연휴 끝")}


def group_occurrences(event: str, rows: list[dict] | None = None) -> dict[int, tuple[dt.date, dt.date]]:
    """{연도: (시작일, 끝일)} — 단일 행사는 시작=끝."""
    if event in GROUPS:
        a, b = GROUPS[event]
        oa, ob = cal.occurrences(a, rows), cal.occurrences(b, rows)
        return {y: (oa[y], ob[y]) for y in oa if y in ob}
    return {y: (d, d) for y, d in cal.occurrences(event, rows).items()}


def _state(day_ranks: dict[str, int] | None, kw: str):
    if day_ranks is None:
        return None
    return day_ranks.get(kw, "out")


def load_window(rank_dir: str | Path, start: dt.date, span: int, *, as_of: dt.date | None = None,
                rel_from: int = REL_FROM, rel_to_after: int = REL_TO) -> dict[int, dict[str, int] | None]:
    """{상대일: 순위표 | None}. 상대일 0 = start, 끝 상대일 = span + rel_to_after. as_of 뒤 날짜는 읽지 않는다."""
    files = period.rank_files(rank_dir)
    out = {}
    for k in range(rel_from, span + rel_to_after + 1):
        day = start + dt.timedelta(days=k)
        if as_of is not None and day > as_of:
            out[k] = None
            continue
        iso = day.isoformat()
        out[k] = period.read_ranks(files[iso]) if iso in files else None
    return out


def keyword_curve(window: dict[int, dict[str, int] | None], kw: str) -> list[list]:
    return [[k, _state(window[k], kw)] for k in sorted(window)]


def _in_band(v, band: int = TOP_BAND) -> bool | None:
    """band 위 안인가 — 'out' 은 False(순위 밖으로 사용), None(누락)은 None."""
    if v is None:
        return None
    return isinstance(v, int) and v <= band


def _runs(curve: list[list], pred) -> list[tuple[int, int]]:
    """pred(v) 가 참인 **연속** 상대일 구간들 [(시작, 끝)]. None·거짓은 끊음."""
    runs, start, prev = [], None, None
    for k, v in curve:
        ok = bool(pred(v))
        if ok and start is None:
            start = k
        if ok:
            prev = k
        if not ok and start is not None:
            runs.append((start, prev))
            start = None
    if start is not None:
        runs.append((start, prev))
    return runs


def analyze_curve(curve: list[list], span: int = 0) -> dict | None:
    """곡선 하나의 진입·정점·이탈 판정. 자료가 모자라면 usable=False 와 이유."""
    by = {k: v for k, v in curve}
    enter_to = span
    exit_from, exit_to = span + EXIT_AFTER_FROM, span + EXIT_AFTER_TO

    def band_flags(a, b):
        fl = [_in_band(by.get(k)) for k in range(a, b + 1)]
        return [f for f in fl if f is not None]

    base, enter, exit_ = band_flags(BASE_FROM, BASE_TO), band_flags(ENTER_FROM, enter_to), band_flags(exit_from, exit_to)
    ranks = [(k, v) for k, v in curve if isinstance(v, int)]
    reasons, lack = [], []
    if len(base) < BASE_MIN_OBS:
        lack.append(f"기준 구간 관측 {len(base)}일<{BASE_MIN_OBS}")
    if len(enter) < ENTER_MIN_OBS:
        lack.append(f"진입 구간 관측 {len(enter)}일<{ENTER_MIN_OBS}")
    if len(exit_) < EXIT_MIN_OBS:
        lack.append(f"이탈 구간 관측 {len(exit_)}일<{EXIT_MIN_OBS}")
    usable = not lack

    best_rank = min((v for _, v in ranks), default=None)
    first_in = next((k for k in range(ENTER_FROM, enter_to + 1) if _in_band(by.get(k))), None)
    peak_best = peak_top = None
    if best_rank is not None:
        best_runs = _runs(curve, lambda v: isinstance(v, int) and v == best_rank)
        peak_best = list(max(best_runs, key=lambda r: (r[1] - r[0], -r[0])))     # 가장 긴 최고 순위 연속 구간
        top_runs = [r for r in _runs(curve, lambda v: isinstance(v, int) and v <= PEAK_BAND)
                    if r[0] <= peak_best[0] <= r[1]]
        peak_top = list(top_runs[0]) if top_runs else None

    bound = False
    if usable:
        base_out = sum(base) / len(base) <= BAND_SHARE_MAX
        exits = sum(exit_) / len(exit_) <= BAND_SHARE_MAX
        if not base_out:
            reasons.append("기준 구간에 이미 100위 안(유지형)")
        if first_in is None:
            reasons.append("진입 구간에 100위 안 없음")
        if not exits:
            reasons.append("행사 뒤에도 100위 안(지속형)")
        bound = base_out and first_in is not None and exits
    return {"usable": usable, "lack": lack, "bound": bound, "reasons": reasons, "best_rank": best_rank,
            "peak_best": peak_best, "peak_top": peak_top, "enter_rel": first_in,
            "lead_days": -first_in if first_in is not None else None,
            "observed_days": sum(1 for _, v in curve if v is not None),
            "out_days": sum(1 for _, v in curve if v == "out"),
            "missing_days": sum(1 for _, v in curve if v is None)}


def candidates(window: dict[int, dict[str, int] | None], span: int = 0) -> set[str]:
    out: set[str] = set()
    for k in range(ENTER_FROM, span + 1):
        day = window.get(k)
        if day:
            out.update(kw for kw, r in day.items() if r <= TOP_BAND)
    return out


def event_report(event: str, rank_dir: str | Path, years: list[int], *, rows: list[dict] | None = None,
                 seeds: list[str] | None = None, limit: int = 60, as_of: dt.date | None = None) -> dict:
    """행사(또는 행사군) 하나 — 연도별 반복 패턴 키워드와 곡선.

    years: 분석에 쓸 연도. as_of 가 있으면 이탈 구간이 as_of 전에 끝난 해만 쓰고, as_of 뒤 파일은 읽지 않는다.
    """
    occ = group_occurrences(event, rows)
    per_year: dict[int, dict] = {}
    skipped = []
    for y in years:
        if y not in occ:
            skipped.append({"year": y, "why": "달력에 없음"})
            continue
        start, end = occ[y]
        span = (end - start).days
        if as_of is not None and end + dt.timedelta(days=EXIT_AFTER_TO) > as_of:
            skipped.append({"year": y, "why": f"이탈 구간이 기준일({as_of.isoformat()}) 뒤에 끝남"})
            continue
        window = load_window(rank_dir, start, span, as_of=as_of)
        if not any(window.values()):
            skipped.append({"year": y, "why": "순위 자료 없음"})
            continue
        per_year[y] = {"start": start.isoformat(), "end": end.isoformat(), "span": span, "window": window,
                       "coverage": {"observed": sum(1 for v in window.values() if v), "total": len(window)}}

    kws: dict[str, dict] = {}
    for y, info in per_year.items():
        for kw in candidates(info["window"], info["span"]) | set(seeds or []):
            curve = keyword_curve(info["window"], kw)
            a = analyze_curve(curve, info["span"])
            if a is None:
                continue
            kws.setdefault(kw, {"keyword": kw, "years": {}})["years"][y] = {**a, "curve": curve}

    out_rows = []
    for kw, d in kws.items():
        ys = d["years"]
        judged = [y for y, a in ys.items() if a["usable"]]
        bound_years = [y for y in judged if ys[y]["bound"]]
        if len(judged) >= MIN_YEARS_REPEAT and bound_years and len(bound_years) == len(judged):
            grade = "반복"
        elif bound_years:
            grade = "후보"
        elif kw in (seeds or []):
            grade = "씨앗"
        else:
            continue
        basis = bound_years or judged or list(ys)
        leads = [ys[y]["lead_days"] for y in basis if ys[y]["lead_days"] is not None]
        peaks = [ys[y]["peak_best"] for y in basis if ys[y]["peak_best"]]
        bests = [a["best_rank"] for a in ys.values() if a["best_rank"] is not None]
        out_rows.append({
            "keyword": kw, "grade": grade, "bound_years": bound_years, "judged_years": judged, "years": ys,
            "lead_days": statistics.median(leads) if leads else None,
            "peak_rel": [statistics.median(p[0] for p in peaks), statistics.median(p[1] for p in peaks)] if peaks else None,
            "best_rank": min(bests) if bests else None,
        })
    order = {"반복": 0, "후보": 1, "씨앗": 2}
    out_rows.sort(key=lambda r: (order[r["grade"]], r["best_rank"] if r["best_rank"] is not None else 999, -(r["lead_days"] or 0)))
    return {"event": event, "group": GROUPS.get(event),
            "years": {y: {k: v for k, v in i.items() if k != "window"} for y, i in per_year.items()},
            "skipped": skipped, "as_of": as_of.isoformat() if as_of else None, "rel_range": [REL_FROM, REL_TO],
            "rules": {"base": [BASE_FROM, BASE_TO], "enter_from": ENTER_FROM, "exit_after": [EXIT_AFTER_FROM, EXIT_AFTER_TO],
                      "band": TOP_BAND, "peak_band": PEAK_BAND, "min_obs": [BASE_MIN_OBS, ENTER_MIN_OBS, EXIT_MIN_OBS],
                      "min_years_repeat": MIN_YEARS_REPEAT, "band_share_max": round(BAND_SHARE_MAX, 3)},
            "keywords": out_rows[:limit], "total": len(out_rows)}


def forecast_from_report(report: dict, target_start: dt.date) -> list[dict]:
    """다음 행사(군) 시작일에 반복/후보 키워드의 상대일을 얹은 '예보 재료' (전년 패턴 기준 — 성과는 백테스트로)."""
    out = []
    for r in report["keywords"]:
        if r["grade"] not in ("반복", "후보") or r["lead_days"] is None:
            continue
        pk = r["peak_rel"]
        out.append({"keyword": r["keyword"], "grade": r["grade"],
                    "expected_enter": (target_start - dt.timedelta(days=int(r["lead_days"]))).isoformat(),
                    "expected_peak": [(target_start + dt.timedelta(days=int(pk[0]))).isoformat(),
                                      (target_start + dt.timedelta(days=int(pk[1]))).isoformat()] if pk else None,
                    "best_rank_past": r["best_rank"], "basis_years": r["bound_years"] or r["judged_years"]})
    return out
