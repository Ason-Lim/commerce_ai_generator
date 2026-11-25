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

지표 (§4, 기간마다 · 예측일 전체 합산 — **모든 기간을 판정할 수 있는 같은 예측일만**)
  n_true · n_pred · hits · precision · recall · recall_known(과거에 본 키워드만 분모) · first_seen_true(처음 등장한 정답 수)
  · top20_precision(점수 순 상위 20) · **top20_lead7**(제출한 상위 20 중 첫 진입이 예측 후 7일 이상인 적중 ÷ 실제 제출 수 — 준비형 성능)
  · lead_median(그 방법이 맞힌 사례의 첫 관측 진입까지 일수 — 방법끼리 견주는 값 아님)
  · major_missed(50위 안까지 오른 정답 중 그 방법이 놓친 비율) · false_pos · extra_hits(탐색기가 기준선 셋이 모두 놓친 적중)
  union.major_missed_all = 모든 방법의 합집합으로도 놓친 주요 상승 비율 · major_first_seen = 그중 처음 등장 키워드 수
질문: q1(기본) · q1p(Q1′ — 최근 28일 안에 100위 안이던 키워드 제외, 보조 실험)

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
METHODS = ("recent", "last_year", "last_year_lunar", "event_rel", "explorer", "explorer_repeat")
QUESTIONS = ("q1", "q1p")  # q1p = 최근 Q1P_DAYS 일 내내 100위 밖이던 키워드만 (최근 재진입 제외 — 보조 실험)
Q1P_DAYS = 28
LEAD_MIN = 7  # '준비형' 적중: 첫 진입이 예측 후 7일 이상
BASELINES = ("recent", "last_year", "last_year_lunar", "event_rel")


class _Days:
    """날짜 → 순위표(없으면 None). as_of 를 넘는 날은 '예측 쪽'에서 읽지 못하게 따로 막는다."""

    def __init__(self, rank_dir: str | Path):
        self.files = period.rank_files(rank_dir)
        self._memo: dict[str, dict[str, int] | None] = {}

    def get(self, d: dt.date) -> dict[str, int] | None:
        # 2026-11-25: 같은 날 파일을 여러 번 읽지 않게(트렌드 변화 탭 8주 계산이 운영 맥에서 30초 걸렸음)
        k = d.isoformat()
        if k not in self._memo:
            p = self.files.get(k)
            self._memo[k] = period.read_ranks(p) if p else None
        return self._memo[k]


_DAYS_CACHE: dict = {}


def days_for(rank_dir: str | Path) -> _Days:
    """같은 순위 폴더·같은 파일 목록이면 읽어 둔 _Days 를 다시 쓴다(파일이 늘면 새로). 하나만 보관."""
    files = period.rank_files(rank_dir)
    key = (str(rank_dir), len(files), max(files) if files else "")
    if _DAYS_CACHE.get("key") != key:
        _DAYS_CACHE.clear()
        _DAYS_CACHE.update(key=key, days=_Days(rank_dir))
    return _DAYS_CACHE["days"]


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


def truth(days: _Days, as_of: dt.date, h: int, top_now: set[str], *, min_share: float = FUTURE_MIN_SHARE
          ) -> tuple[dict[str, dict], int] | None:  # fmt: skip
    """{키워드: {first: **처음 관측된** 진입까지 일수, best}} 정답 + 관측일 수. 관측일이 모자라면 None.
    정답은 '관측된 진입'이다 — 누락된 날의 잠깐 진입은 못 본다. min_share 를 높여 결과가 유지되는지 견준다."""
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
    if seen < math.ceil(h * min_share):
        return None
    return hits, seen


# ── 제출 예측의 결과 4분류 (2026-11-25, GPT 검토 반영) ──
# 제출한 상위 20 을 넷으로 나눈다(분모 = 제출 수, 합 100%):
#   선행 적중(첫 진입 7~28일) · 선행 부족 적중(1~6일) · 시점 어긋남(기간 앞 14일 또는 뒤 14일 안 100위 진입) · 관측창 내 미진입.
# '관측창 내 미진입'은 관측 결과일 뿐 원인 확정이 아니다 — 트렌드 변화는 **검토 가설**(trend_shift 탭), 후보 선정 오류일 수도 있다.
# 그래서 성능 평가에서 빼지 않는다: 주 지표는 늘 제출 상위 20 전체의 선행 적중률, 4분류는 개선 방향을 찾는 보조 지표.
# 실제 상승 쪽의 '과거 400일 Top500 관측 이력 없음' 비율은 분모(실제 주요 상승)가 달라 따로 낸다.
TIMING_DAYS = 14
REASONS = ("lead", "late", "timing", "gone")
REASON_NAMES = {"lead": "선행 적중(7~28일)", "late": "선행 부족 적중(1~6일)", "timing": "시점 어긋남(앞뒤 14일 안 진입)",
                "gone": "관측창 내 미진입"}  # fmt: skip
NO_HISTORY_NAME = "과거 400일 Top500 관측 이력 없음"
HISTORY_MIN = 0.9  # 과거 400일 중 순위 파일이 이 비율 미만이면 '이력 없음'을 판정하지 않음(자료 부족)


def history_coverage(days: _Days, as_of: dt.date) -> float:
    """기준일 전 VOCAB_DAYS 일(기준일 포함) 중 순위 파일이 있는 날 비율 — '이력 없음' 판정이 믿을 만한지."""
    n = VOCAB_DAYS + 1
    have = sum(1 for k in range(n) if (as_of - dt.timedelta(days=k)).isoformat() in days.files)
    return have / n


def near_window(days: _Days, as_of: dt.date, h: int) -> set[str]:
    """기간 바로 앞(as_of−14~as_of−1)·바로 뒤(as_of+h+1~+h+14)에 100위 안이던 키워드 — '시점 어긋남' 판정용(채점에서만 씀)."""
    out: set[str] = set()
    for a, b in ((as_of - dt.timedelta(days=TIMING_DAYS), as_of - dt.timedelta(days=1)),
                 (as_of + dt.timedelta(days=h + 1), as_of + dt.timedelta(days=h + TIMING_DAYS))):  # fmt: skip
        d = a
        while d <= b:
            for kw, r in (days.get(d) or {}).items():
                if r <= BAND:
                    out.add(kw)
            d += dt.timedelta(days=1)
    return out


def classify_top(top: list[str], hits_true: dict[str, dict], near: set[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {r: [] for r in REASONS}
    for k in top:
        if k in hits_true:
            out["lead" if hits_true[k]["first"] >= LEAD_MIN else "late"].append(k)
        elif k in near:
            out["timing"].append(k)
        else:
            out["gone"].append(k)
    return out


# ── 방법들: {키워드: 점수(작을수록 확신 — 근거 순위)} ──
def m_recent(days: _Days, as_of: dt.date, h: int, top_now: set[str], **_) -> dict[str, float]:
    best = _best(days, as_of - dt.timedelta(days=RECENT_DAYS - 1), as_of, limit=as_of)
    return {kw: r for kw, r in best.items() if r <= BAND and kw not in top_now}


def m_last_year(days: _Days, as_of: dt.date, h: int, top_now: set[str], **_) -> dict[str, float]:
    a = as_of + dt.timedelta(days=1 - YEAR_SHIFT)
    b = as_of + dt.timedelta(days=h - YEAR_SHIFT)
    best = _best(days, a, b, limit=as_of)
    return {kw: r for kw, r in best.items() if r <= BAND and kw not in top_now}


# 2026-11-25 사용자 결정: 비교 기준 = '전년 기준' — 평소엔 전년 같은 주(364일), 설·추석(음력) 시즌엔 전년 같은 명절 날짜에 맞춤.
LUNAR_HOLIDAYS = ("설날", "추석")
LUNAR_BEFORE, LUNAR_AFTER = 35, 7  # 명절 D-35 ~ D+7 은 명절 기준으로 옮긴다 (선물 준비 기간 + 연휴 뒤)


def lunar_shifts(rows: list[dict]) -> list[tuple[dt.date, dt.date, int, str]]:
    """(구간 시작, 구간 끝, 뒤로 옮길 일수, 명절 이름) — 올해 명절 D-35~D+7 안의 날은 (올해 명절 − 작년 명절) 만큼 뒤로."""
    occ: dict[str, dict[int, dt.date]] = {}
    for r in rows:
        if r.get("event") in LUNAR_HOLIDAYS:
            d = dt.date.fromisoformat(r["date"])
            occ.setdefault(r["event"], {})[d.year] = d
    out = []
    for name, by_year in occ.items():
        for y, d in by_year.items():
            prev = by_year.get(y - 1)
            if prev:
                out.append((d - dt.timedelta(days=LUNAR_BEFORE), d + dt.timedelta(days=LUNAR_AFTER), (d - prev).days, name))
    return out


def year_back(t: dt.date, shifts) -> tuple[dt.date, str | None]:
    """t 의 '작년 같은 날' (명절 구간이면 명절 맞춤, 아니면 364일 전) + 맞춘 명절 이름."""
    for a, b, n, name in shifts:
        if a <= t <= b:
            return t - dt.timedelta(days=n), name
    return t - dt.timedelta(days=YEAR_SHIFT), None


def m_last_year_lunar(days: _Days, as_of: dt.date, h: int, top_now: set[str], *, rows: list[dict], **_) -> dict[str, float]:
    """전년 기준 — 전년 같은 주, 단 설·추석 시즌은 전년 같은 명절 날짜 기준."""
    shifts = lunar_shifts(rows)
    out: dict[str, float] = {}
    for k in range(1, h + 1):
        src, _ = year_back(as_of + dt.timedelta(days=k), shifts)
        if src > as_of:
            continue
        day = days.get(src)
        for kw, r in (day or {}).items():
            if r <= BAND and kw not in top_now and r < out.get(kw, 10**6):
                out[kw] = r
    return out


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
               repeat_only: bool = False, **_) -> dict[str, float]:  # fmt: skip
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
                if repeat_only and f["grade"] != "반복":
                    continue
                if enter <= as_of + dt.timedelta(days=h) and start > as_of and f["keyword"] not in top_now:
                    score = (0 if f["grade"] == "반복" else 1000) + (f["best_rank_past"] or 999)
                    if score < out.get(f["keyword"], 10**6):
                        out[f["keyword"]] = score
    return out


def m_explorer_repeat(*a, **k) -> dict[str, float]:
    """탐색기 — '반복'(판정 가능한 해 2개 이상 모두 만족)만."""
    return m_explorer(*a, **k, repeat_only=True)


# ── 실험 (2026-11-25, 기본 방법 아님) — 리포트카드에서 '놓친 주요 상승의 절반은 후보 목록엔 있었으나 상위 20 경계에서 잘림'
# → 후보는 전년 기준 그대로 두고 **순서만** 바꿔 본다. 탐색기(반복만)의 +2.2%p 가 날짜별로 엇갈려 좁히는 방향을 찾는다.
def m_ly_repeat_first(days: _Days, as_of: dt.date, h: int, top_now: set[str], **k) -> dict[str, float]:
    """전년 기준 후보 + 탐색기(반복만)에도 있으면 앞으로(같은 묶음 안에서는 작년 순위)."""
    base = m_last_year_lunar(days, as_of, h, top_now, **k)
    rep = m_explorer(days, as_of, h, top_now, repeat_only=True, **k)
    return {kw: (0 if kw in rep else 1000) + r for kw, r in base.items()}


def m_ly_two_years(days: _Days, as_of: dt.date, h: int, top_now: set[str], *, rows: list[dict], **_) -> dict[str, float]:
    """전년 기준 후보 + 2년 전 같은 시기(같은 맞춤 규칙)에도 100위 안이었으면 앞으로."""
    shifts = lunar_shifts(rows)
    base = m_last_year_lunar(days, as_of, h, top_now, rows=rows)
    two: set[str] = set()
    for k in range(1, h + 1):
        src, _ = year_back(as_of + dt.timedelta(days=k), shifts)
        src2, _ = year_back(src, shifts)
        for kw, r in (days.get(src2) or {}).items():
            if r <= BAND:
                two.add(kw)
    return {kw: (0 if kw in two else 1000) + r for kw, r in base.items()}


def m_repeat_then_ly(days: _Days, as_of: dt.date, h: int, top_now: set[str], **k) -> dict[str, float]:
    """탐색기(반복만) 후보를 먼저(과거 최고 순위 순), 자리가 남으면 전년 기준 후보로 채움."""
    rep = m_explorer(days, as_of, h, top_now, repeat_only=True, **k)
    base = m_last_year_lunar(days, as_of, h, top_now, **k)
    out = {kw: float(r) for kw, r in rep.items()}
    for kw, r in base.items():
        out.setdefault(kw, 10_000 + r)
    return out


EXPERIMENTS = ("ly_repeat_first", "ly_two_years", "repeat_then_ly")
EXPERIMENT_NAMES = {"ly_repeat_first": "실험: 전년 기준 + 반복 우선", "ly_two_years": "실험: 전년 기준 + 2년 연속 우선",
                    "repeat_then_ly": "실험: 반복 먼저, 전년 기준으로 채움"}  # fmt: skip

FUNCS = {"recent": m_recent, "last_year": m_last_year, "last_year_lunar": m_last_year_lunar, "event_rel": m_event_rel, "explorer": m_explorer,
         "ly_repeat_first": m_ly_repeat_first, "ly_two_years": m_ly_two_years, "repeat_then_ly": m_repeat_then_ly,
         "explorer_repeat": m_explorer_repeat}  # fmt: skip


def _empty() -> dict:
    return {"n_true": 0, "n_true_known": 0, "n_pred": 0, "hits": 0, "hits_known": 0, "top_pred": 0, "top_hits": 0,
            "top_lead": 0, "leads": [], "major": 0, "major_hit": 0, "extra_hits": 0,
            "br_late": 0, "br_timing": 0, "br_gone": 0}  # fmt: skip


def run(rank_dir: str | Path, start: dt.date, end: dt.date, *, step: int = 7, horizons=HORIZONS,
        methods=METHODS, rows: list[dict] | None = None, question: str = "q1",
        min_share: float = FUTURE_MIN_SHARE) -> dict:  # fmt: skip
    """start~end 사이 step 일 간격의 예측일마다 Q1(또는 Q1′)을 풀고 합산.

    **모든 기간을 판정할 수 있는 예측일만** 쓴다 — 기간마다 평가일이 달라 같은 방법의 예측 수가 기간마다 달라지는 일을 막는다.
    """
    rows = cal.load() if rows is None else rows
    days = _Days(rank_dir)
    acc = {m: {h: _empty() for h in horizons} for m in methods}
    union = {h: {"major": 0, "major_hit": 0, "new_major": 0, "major_hist_ok": 0} for h in horizons}
    paired = {m: {h: [] for h in horizons} for m in methods}  # 날짜별 (선행 적중, 제출) — 비교 기준과 짝 비교
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
        excl = set(top_now)
        if question == "q1p":  # 최근 28일 안에 한 번이라도 100위 안이던 키워드는 뺀다
            excl |= {kw for kw, r in _best(days, d - dt.timedelta(days=Q1P_DAYS - 1), d, limit=d).items() if r <= BAND}
        truths = {h: truth(days, d, h, excl, min_share=min_share) for h in horizons}
        lacking = [h for h, t in truths.items() if t is None]
        if lacking:
            skipped.append({"as_of": d.isoformat(), "why": f"미래 관측일 부족({', '.join(f'{h}일' for h in lacking)})"})
            d += dt.timedelta(days=step)
            continue
        hist_ok = history_coverage(days, d) >= HISTORY_MIN
        row = {"as_of": d.isoformat(), "excluded": len(excl), "vocab": len(vocab), "history_ok": hist_ok, "h": {}}
        for h in horizons:
            hits_true, seen = truths[h]
            known_true = {k for k in hits_true if k in vocab}
            major = {k for k, v in hits_true.items() if v["best"] <= MAJOR_BAND}
            near = near_window(days, d, h)
            base_hit: set[str] = set()
            all_hit: set[str] = set()
            res = {}
            for m in methods:
                pred = FUNCS[m](days, d, h, excl, rows=rows, rank_dir=rank_dir, cache=cache)
                hit = {kw for kw in pred if kw in hits_true}
                top = sorted(pred, key=lambda k: (pred[k], k))[:TOP_N]
                a = acc[m][h]
                a["n_true"] += len(hits_true)
                a["n_true_known"] += len(known_true)
                a["n_pred"] += len(pred)
                a["hits"] += len(hit)
                a["hits_known"] += len(hit & known_true)
                a["top_pred"] += len(top)
                a["top_hits"] += sum(1 for k in top if k in hits_true)
                a["top_lead"] += sum(1 for k in top if k in hits_true and hits_true[k]["first"] >= LEAD_MIN)
                br = classify_top(top, hits_true, near)
                a["br_late"] += len(br["late"])
                a["br_timing"] += len(br["timing"])
                a["br_gone"] += len(br["gone"])
                paired[m][h].append((len(br["lead"]), len(top)))
                a["leads"] += [hits_true[k]["first"] for k in hit]
                a["major"] += len(major)
                a["major_hit"] += len(major & hit)
                res[m] = hit
                all_hit |= hit
                if m in BASELINES:
                    base_hit |= hit
            for m in ("explorer", "explorer_repeat"):
                if m in res:
                    acc[m][h]["extra_hits"] += len(res[m] - base_hit)
            union[h]["major"] += len(major)
            union[h]["major_hit"] += len(major & all_hit)
            if hist_ok:  # 과거 자료가 모자란 날은 '이력 없음'을 세지 않는다
                union[h]["new_major"] += len(major - vocab)
                union[h]["major_hist_ok"] += len(major)
            row["h"][h] = {"true": len(hits_true), "seen_days": seen, **{m: len(v) for m, v in res.items()}}
        dates.append(d.isoformat())
        per_date.append(row)
        d += dt.timedelta(days=step)
    by_month: dict[str, int] = {}
    for x in skipped:
        by_month[x["as_of"][:7]] = by_month.get(x["as_of"][:7], 0) + 1
    return {
        "question": question,
        "range": [start.isoformat(), end.isoformat()],
        "step": step,
        "dates": len(dates),
        "evaluated": dates,
        "skipped": skipped,
        "skipped_by_month": by_month,
        "metrics": {m: {h: _summary(acc[m][h], m) for h in horizons} for m in methods},
        "paired": _paired(paired, horizons),
        "union": {
            h: {
                "major": u["major"],
                "major_missed_all": round(1 - u["major_hit"] / u["major"], 4) if u["major"] else None,
                "major_first_seen": u["new_major"],  # = 과거 400일 Top500 관측 이력 없음 (자료 충분한 날만)
                "first_seen_share": round(u["new_major"] / u["major_hist_ok"], 4) if u["major_hist_ok"] else None,
                "history_short_dates": sum(1 for r in per_date if not r["history_ok"]),
            }
            for h, u in union.items()
        },
        "per_date": per_date,
        "rules": {
            "band": BAND,
            "major_band": MAJOR_BAND,
            "vocab_days": VOCAB_DAYS,
            "recent_days": RECENT_DAYS,
            "year_shift": YEAR_SHIFT,
            "future_min_share": min_share,
            "top_n": TOP_N,
            "lead_min": LEAD_MIN,
            "q1p_days": Q1P_DAYS,
        },
        "notes": [
            "Q1 = 예측일에 100위 밖인 키워드가 기간 안에 한 번이라도 100위 안에 들어오는가"
            + (f" — Q1′: 최근 {Q1P_DAYS}일 안에 100위 안이던 키워드는 뺌" if question == "q1p" else ""),
            "정답은 '관측된 진입' — 누락된 날의 잠깐 진입은 못 봄. 선행 일수는 처음 관측된 진입까지",
            "모든 기간을 판정할 수 있는 예측일만 씀(같은 평가일로 비교)",
            "예측은 예측일까지의 파일만 읽음(정보 누출 통제) — 정답만 그 뒤를 읽음",
            "2024·2025 는 규칙을 보고 만든 탐색·개발 자료 — 최종 성적은 앞으로 쌓이는 실제 예보로",
        ],
    }


PAIR_BASE = "last_year_lunar"


def _paired(paired: dict, horizons) -> dict:
    """비교 기준(전년 기준)과 같은 평가일끼리 짝 비교 — 날짜별 선행 적중률 차이의 나음/같음/못함 일수·평균."""
    if PAIR_BASE not in paired:
        return {}
    out: dict = {}
    for m, byh in paired.items():
        if m == PAIR_BASE:
            continue
        out[m] = {}
        for h in horizons:
            diffs = []
            for (lm, sm), (lb, sb) in zip(byh[h], paired[PAIR_BASE][h]):
                if sm and sb:
                    diffs.append(lm / sm - lb / sb)
            out[m][h] = {
                "dates": len(diffs),
                "better": sum(1 for x in diffs if x > 0),
                "same": sum(1 for x in diffs if x == 0),
                "worse": sum(1 for x in diffs if x < 0),
                "mean_diff_pp": round(statistics.mean(diffs) * 100, 1) if diffs else None,
                "submitted": sum(s for _, s in byh[h]),
                "lead_hits": sum(x for x, _ in byh[h]),
            }
    return out


def _summary(a: dict, m: str) -> dict:
    p = a["hits"] / a["n_pred"] if a["n_pred"] else None
    r = a["hits"] / a["n_true"] if a["n_true"] else None
    out = {
        "n_true": a["n_true"],
        "n_pred": a["n_pred"],
        "hits": a["hits"],
        "precision": round(p, 4) if p is not None else None,
        "recall": round(r, 4) if r is not None else None,
        "recall_known": round(a["hits_known"] / a["n_true_known"], 4) if a["n_true_known"] else None,
        "first_seen_true": a["n_true"] - a["n_true_known"],
        "top20_precision": round(a["top_hits"] / a["top_pred"], 4) if a["top_pred"] else None,
        "top20_lead7": round(a["top_lead"] / a["top_pred"], 4) if a["top_pred"] else None,
        "top_submitted": a["top_pred"],
        "lead_median": statistics.median(a["leads"]) if a["leads"] else None,
        "major_missed": round(1 - a["major_hit"] / a["major"], 4) if a["major"] else None,
        "false_pos": a["n_pred"] - a["hits"],
        "miss_breakdown": {  # 제출 상위 20 기준 비율 (합 = 1)
            "lead": round(a["top_lead"] / a["top_pred"], 4) if a["top_pred"] else None,
            "late": round(a["br_late"] / a["top_pred"], 4) if a["top_pred"] else None,
            "timing": round(a["br_timing"] / a["top_pred"], 4) if a["top_pred"] else None,
            "gone": round(a["br_gone"] / a["top_pred"], 4) if a["top_pred"] else None,
        },
    }
    if m.startswith("explorer"):
        out["extra_hits"] = a["extra_hits"]
    return out


__all__ = ["HORIZONS", "METHODS", "BASELINES", "QUESTIONS", "population", "truth", "run", "FUNCS", "lunar_shifts", "year_back",
           "classify_top", "near_window", "REASONS", "REASON_NAMES",
           "NO_HISTORY_NAME", "HISTORY_MIN", "history_coverage"]
