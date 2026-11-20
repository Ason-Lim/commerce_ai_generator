"""
급상승 키워드 — 기간 조회 (2026-11-19 설계 1절 · 2절, GPT 검토 반영)
=====================================================================

입력 (파일만, 외부 호출 없음):
  - 식품 키워드 **하루 단위** 순위 CSV  NAVER_DAILY_RANK_DIR (food_YYYY-MM-DD.csv, date·rank·keyword, 하루 상위 500)
      없으면 NAVER_DAILY_DIR 로 대신 — 단 그 폴더는 2026-07-09 부터 '최근 30일 묶음' 순위가 섞여 있어 결과에 주의 표시
  - 급상승 결과  TREND_SURGE_DIR/surge_YYYY-MM-DD.json  (surge.load 와 같은 파일)
  - 등록부 '링크 있음'  (호출자가 함수로 넘김, 기본 없음)

이 화면이 보여 주는 것은 **기간별 식품 키워드 순위 변화**다. 순위가 올랐다고 검색량이 늘었다고 단정할 수 없고
(순위는 상대값), 급상승 감지 이력은 별도 칸이다. 급상승 파일에 없는 날은 '상승하지 않음'이 아니라
'하루 상위 20개에 들지 않음'일 뿐이다.

날짜 상태 셋 (GPT 검토): 정상 관측(파일 있고 순위 있음) / 파일 있는데 500위 밖 / 파일 누락·오류.
  - 누락일은 집계에서 뺀다 (0 이나 501 로 채우지 않음).
  - 500위 밖은 '순위 없음(None)' 이며, 첫날에 없으면 '새로'가 아니라 **상위 500위 진입**으로 부른다.

키워드 한 줄 (period_table):
  start_rank / end_rank      기간 안 첫 관측일 · 마지막 관측일의 순위 (없으면 None = 500위 밖)
  change                     start_rank - end_rank (둘 다 있을 때만; +면 올라감)
  max_gain                   기간 중 최대 개선폭 = 최고 순위 전 가장 나쁜 관측 순위 - 최고 순위 (500위 밖은 501 로 보되 from_outside 표시)
  best_rank / best_date      기간 중 최고 순위
  days_top100 / days_listed  100위 안 관측 일수 / 500위 안 관측 일수
  recent_direction           최근 7 관측일 평균 순위 vs 그 앞 7 관측일 (up·down·flat·short)
  surge.days / first / peak_ratio / status_at_end
                             급상승 목록 포함 일수(종료일 이하 파일만) · 기간 내 첫 기록일 · 최고 배수 · 종료일 기준 감지 상태
  group                      ranked(양끝 순위 있음) · entered(상위 500 진입) · exited(500위 밖으로) · transient(기간 중에만 잠깐)
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import statistics
import threading
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
TOP = 500
TOP_BAND = 100                 # '상위권' 기준
DIRECTION_WINDOW = 7           # 최근 방향: 7 관측일 vs 그 앞 7 관측일
DIRECTION_MIN_MOVE = 20        # 평균 순위 차이가 이보다 작으면 'flat'
PRESETS = {"1w": 7, "1m": 30, "3m": 91}
MIXED_WINDOW_FROM = "2026-07-09"   # NAVER_DAILY_DIR 의 '30일 묶음' 순위가 시작된 날 (단일 날 파일: 08-08·09-02·10-10)


# ── rank files (cached by path+mtime) ────────────────────────────────────────
_CACHE: dict[tuple[str, float], dict[str, int]] = {}
_LOCK = threading.Lock()


def rank_dir_from_env(env=None) -> tuple[Path | None, str]:
    """(폴더, 종류) — 'daily' = 하루 단위(NAVER_DAILY_RANK_DIR), 'mixed' = 예전 폴더(NAVER_DAILY_DIR), 'none'."""
    source = os.environ if env is None else env
    daily = (source.get("NAVER_DAILY_RANK_DIR") or "").strip()
    if daily and Path(daily).expanduser().exists():
        return Path(daily).expanduser(), "daily"
    old = (source.get("NAVER_DAILY_DIR") or "").strip()
    if old and Path(old).expanduser().exists():
        return Path(old).expanduser(), "mixed"
    return None, "none"


def rank_files(rank_dir: str | Path) -> dict[str, Path]:
    """{date: path} — 파일 이름의 날짜만 믿는다 (안의 date 칸은 검사용)."""
    return {p.stem[5:]: p for p in sorted(Path(rank_dir).glob("food_????-??-??.csv"))}


def read_ranks(path: Path) -> dict[str, int] | None:
    """{keyword: rank}. 읽기 실패·빈 파일은 None (= 누락으로 취급). 같은 키워드가 두 번이면 더 좋은(앞) 순위."""
    try:
        key = (str(path), path.stat().st_mtime)
    except OSError:
        return None
    with _LOCK:
        hit = _CACHE.get(key)
    if hit is not None:
        return hit
    out: dict[str, int] = {}
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                kw, rank = (row.get("keyword") or "").strip(), (row.get("rank") or "").strip()
                if kw and rank.isdigit() and kw not in out:
                    out[kw] = int(rank)
    except (OSError, csv.Error, UnicodeDecodeError):
        return None
    if not out:
        return None
    with _LOCK:
        if len(_CACHE) > 4000:
            _CACHE.clear()
        _CACHE[key] = out
    return out


def load_range(rank_dir: str | Path, start: str, end: str) -> tuple[dict[str, dict[str, int]], list[str], list[str]]:
    """(날짜별 순위, 관측일 목록, 누락일 목록) — start~end 달력 날짜 기준. 읽기 실패 파일은 누락."""
    files = rank_files(rank_dir)
    ranks: dict[str, dict[str, int]] = {}
    observed, missing = [], []
    d, e = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while d <= e:
        day = d.isoformat()
        got = read_ranks(files[day]) if day in files else None
        if got:
            ranks[day] = got
            observed.append(day)
        else:
            missing.append(day)
        d += dt.timedelta(days=1)
    return ranks, observed, missing


def coverage(rank_dir: str | Path | None, surge_dir: str | Path | None) -> dict:
    """자료 있는 기간 — 화면 머리말 ('식품 순위 2024-01-01~ · 급상승 감지 2026-10-31~')."""
    out: dict = {"rank": None, "surge": None}
    if rank_dir and Path(rank_dir).exists():
        days = sorted(rank_files(rank_dir))
        if days:
            d0, d1 = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
            out["rank"] = {"first": days[0], "last": days[-1], "files": len(days),
                           "calendar_days": (d1 - d0).days + 1, "missing": (d1 - d0).days + 1 - len(days)}
    if surge_dir and Path(surge_dir).exists():
        days = sorted(p.stem[6:] for p in Path(surge_dir).glob("surge_????-??-??.json"))
        if days:
            out["surge"] = {"first": days[0], "last": days[-1], "files": len(days)}
    return out


# ── surge files (종료일 이하만) ───────────────────────────────────────────────
def surge_index(surge_dir: str | Path | None, start: str, end: str) -> tuple[dict[str, dict], list[str]]:
    """({keyword: {'days': n, 'first': 날짜, 'peak_ratio': x, 'status_at_end': 상태, 'last_file': 날짜}}, 읽은 파일 날짜들)
    — surge_YYYY-MM-DD.json 중 start ≤ 날짜 ≤ end 만 읽는다 (과거 조회에 미래 자료가 섞이지 않게)."""
    out: dict[str, dict] = {}
    files: list[str] = []
    if not surge_dir or not Path(surge_dir).exists():
        return out, files
    for p in sorted(Path(surge_dir).glob("surge_????-??-??.json")):
        day = p.stem[6:]
        if day < start or day > end:
            continue
        try:
            rep = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        files.append(day)
        for it in rep.get("items") or []:
            kw = it.get("keyword")
            if not kw:
                continue
            e = out.setdefault(kw, {"days": 0, "first": day, "peak_ratio": 0.0, "status_at_end": None, "last_file": None})
            e["days"] += 1
            e["peak_ratio"] = max(e["peak_ratio"], float(it.get("ratio_peak") or 0))
            e["status_at_end"], e["last_file"] = it.get("status"), day
    return out, files


# ── per-keyword metrics ──────────────────────────────────────────────────────
def keyword_metrics(keyword: str, ranks: dict[str, dict[str, int]], observed: list[str]) -> dict | None:
    """관측일만 본다. 기간 안에 한 번도 500위 안에 없었으면 None."""
    series = [(d, ranks[d].get(keyword)) for d in observed]
    known = [(d, r) for d, r in series if r is not None]
    if not known:
        return None
    start_rank, end_rank = series[0][1], series[-1][1]
    best_date, best_rank = min(known, key=lambda x: (x[1], x[0]))
    # 최대 개선폭: 최고 순위 '이전' 관측일 중 가장 나쁜 순위(500위 밖 = 501) 대비
    before = [r if r is not None else TOP + 1 for d, r in series if d < best_date]
    worst_before = max(before) if before else None
    max_gain = (worst_before - best_rank) if worst_before is not None else 0
    from_outside = bool(before) and worst_before == TOP + 1
    if start_rank is not None and end_rank is not None:
        group, change = "ranked", start_rank - end_rank
    elif start_rank is None and end_rank is not None:
        group, change = "entered", None
    elif start_rank is not None:
        group, change = "exited", None
    else:
        group, change = "transient", None
    return {
        "keyword": keyword, "group": group,
        "start": {"date": series[0][0], "rank": start_rank}, "end": {"date": series[-1][0], "rank": end_rank},
        "change": change, "max_gain": max_gain, "from_outside": from_outside,
        "best": {"date": best_date, "rank": best_rank},
        "days_listed": len(known), "days_top100": sum(1 for _, r in known if r <= TOP_BAND),
        "recent_direction": direction([r for _, r in series]),
        "series": [[d, r] for d, r in series],
    }


def direction(values: list[int | None], window: int = DIRECTION_WINDOW) -> str:
    """최근 window 관측일 평균 순위 vs 그 앞 window 관측일 (500위 밖 = 501). 자료가 2*window 미만이면 'short'."""
    v = [x if x is not None else TOP + 1 for x in values]
    if len(v) < 2 * window:
        return "short"
    recent, before = statistics.fmean(v[-window:]), statistics.fmean(v[-2 * window:-window])
    if before - recent >= DIRECTION_MIN_MOVE:
        return "up"
    if recent - before >= DIRECTION_MIN_MOVE:
        return "down"
    return "flat"


SORT_KEYS = {
    "change": lambda m: (m["change"] if m["change"] is not None else -10_000, -m["end"]["rank"] if m["end"]["rank"] else 0),
    "max_gain": lambda m: (m["max_gain"], -(m["best"]["rank"] or 0)),
    "days_top100": lambda m: (m["days_top100"], m["days_listed"]),
    "surge_days": lambda m: (m["surge"]["days"], m["surge"]["peak_ratio"]),
    "best": lambda m: (-m["best"]["rank"], m["days_top100"]),
}


def period_table(rank_dir: str | Path, start: str, end: str, *, surge_dir: str | Path | None = None,
                 has_link: Callable[[str], bool] | None = None, sort: str = "change", limit: int | None = None,
                 min_days: int = 1, with_series: bool = True) -> dict:
    """기간 조회 결과 한 덩이 — 화면 표 + 머리말. limit 는 그룹마다 앞에서 자름 (None = 전부)."""
    if end < start:
        start, end = end, start
    ranks, observed, missing = load_range(rank_dir, start, end)
    surge, surge_files = surge_index(surge_dir, start, end)
    keywords = set()
    for day in observed:
        keywords.update(ranks[day])
    rows = []
    for kw in keywords:
        m = keyword_metrics(kw, ranks, observed)
        if not m or m["days_listed"] < min_days:
            continue
        s = surge.get(kw) or {"days": 0, "first": None, "peak_ratio": 0.0, "status_at_end": None, "last_file": None}
        m["surge"] = s
        if has_link is not None:
            try:
                m["has_link"] = bool(has_link(kw))
            except Exception:  # noqa: BLE001 — 등록부를 못 읽으면 '모름'
                m["has_link"] = None
        if not with_series:
            m.pop("series", None)
        rows.append(m)
    key = SORT_KEYS.get(sort, SORT_KEYS["change"])
    rows.sort(key=key, reverse=True)
    groups = {g: [r for r in rows if r["group"] == g] for g in ("ranked", "entered", "exited", "transient")}
    if sort == "change":          # 진입 그룹은 종료 순위가 좋은 순으로 (GPT 검토: 신규 진입은 별도 그룹)
        groups["entered"].sort(key=lambda m: m["end"]["rank"])
    out_groups = {g: (v[:limit] if limit else v) for g, v in groups.items()}
    return {
        "start": start, "end": end, "sort": sort,
        "days": {"calendar": len(observed) + len(missing), "observed": len(observed), "missing": missing},
        "surge_files": surge_files,
        "keywords": len(rows),
        "counts": {g: len(v) for g, v in groups.items()},
        "groups": out_groups,
        "notes": [
            "순위 변화는 상대 순위의 변화예요. 순위가 올라도 검색량이 늘었다고 단정할 수 없어요.",
            "급상승 목록 포함 일수는 그날 상위 20개에 든 날 수예요. 빠진 날이 '상승하지 않음'은 아니에요.",
            "파일이 없는 날은 집계에서 빠져요 (0이나 501로 채우지 않음).",
        ],
    }


def keyword_history(keyword: str, rank_dir: str | Path, *, end: str | None = None, surge_dir: str | Path | None = None,
                    start: str | None = None) -> dict:
    """키워드 하나의 관심 이력 (설계 2절) — 순위 전체 기간 + 급상승 감지일 + 종료일 이하 가장 최근 급상승 파일의 60일 지수."""
    files = rank_files(rank_dir)
    have = sorted(files)
    if end:
        have = [d for d in have if d <= end]
    if start:
        have = [d for d in have if d >= start]
    days: list[str] = []
    if have:                                       # 첫 파일~마지막 파일 사이의 달력 날짜 (누락일 포함)
        d, e = dt.date.fromisoformat(have[0]), dt.date.fromisoformat(have[-1])
        while d <= e:
            days.append(d.isoformat())
            d += dt.timedelta(days=1)
    series, listed_days = [], []
    for d in days:
        got = read_ranks(files[d]) if d in files else None
        if got is None:
            series.append([d, None, "missing"])
            continue
        r = got.get(keyword)
        series.append([d, r, "ok" if r is not None else "out"])
        if r is not None:
            listed_days.append(d)
    # 급상승 파일 (종료일 이하)
    surge_days, latest = [], None
    if surge_dir and Path(surge_dir).exists():
        for p in sorted(Path(surge_dir).glob("surge_????-??-??.json")):
            day = p.stem[6:]
            if end and day > end:
                continue
            try:
                rep = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for it in rep.get("items") or []:
                if it.get("keyword") == keyword:
                    surge_days.append({"date": day, "ratio_peak": it.get("ratio_peak"), "status": it.get("status"),
                                       "onset": it.get("onset")})
                    latest = {"date": day, "series": it.get("series"), "status": it.get("status"),
                              "ratio_recent": it.get("ratio_recent"), "ratio_peak": it.get("ratio_peak"),
                              "onset": it.get("onset"), "blog": _clues(it.get("blog")),
                              "cause": _public_cause(it.get("cause")), "cross": (it.get("cross") or {}).get("n")}
    known = [(d, r) for d, r, s in series if r is not None]
    stage = stages(series)
    return {
        "keyword": keyword, "end": end, "series": series, "days_listed": len(listed_days),
        "best": ({"date": min(known, key=lambda x: (x[1], x[0]))[0], "rank": min(r for _, r in known)} if known else None),
        "surge_days": surge_days, "latest_surge": latest, "stages": stage,
        "companions": [],   # 호출자가 period_table 결과로 채움 (같은 기간 함께 오른 키워드)
    }


def stages(series: list[list]) -> list[dict]:
    """흐름 단계 (규칙 기반): 등장 → 상승 → 정점 → 하락/정착.  관측일 기준, 500위 밖은 501.
    주 단위 평균 순위로 본다 (하루 흔들림 무시)."""
    pts = [(d, r if r is not None else TOP + 1) for d, r, s in series if s != "missing"]
    if len(pts) < 3:
        return []
    weeks: list[tuple[str, float]] = []
    for i in range(0, len(pts), 7):
        chunk = pts[i:i + 7]
        weeks.append((chunk[0][0], statistics.fmean(r for _, r in chunk)))
    out: list[dict] = []
    first_in = next((d for d, r in pts if r <= TOP), None)
    if first_in:
        out.append({"stage": "등장", "date": first_in})
    best_i = min(range(len(weeks)), key=lambda i: weeks[i][1])
    if best_i > 0 and weeks[0][1] - weeks[best_i][1] >= DIRECTION_MIN_MOVE:
        rise = next((weeks[i][0] for i in range(1, best_i + 1) if weeks[i - 1][1] - weeks[i][1] >= DIRECTION_MIN_MOVE), weeks[best_i][0])
        if first_in and rise < first_in:            # 주 묶음이 등장일보다 앞서 시작하면 등장일부터
            rise = first_in
        out.append({"stage": "상승", "date": rise})
    out.append({"stage": "정점", "date": weeks[best_i][0], "rank": round(weeks[best_i][1])})
    if best_i < len(weeks) - 1:
        tail = weeks[-1][1] - weeks[best_i][1]
        if tail >= DIRECTION_MIN_MOVE:
            out.append({"stage": "하락", "date": weeks[best_i + 1][0], "rank": round(weeks[-1][1])})
        else:
            out.append({"stage": "정착", "date": weeks[best_i + 1][0], "rank": round(weeks[-1][1])})
    return out


def companions(keyword: str, table: dict, top: int = 6) -> list[dict]:
    """같은 기간에 함께 오른 키워드 — 글자가 겹치거나(빼빼로↔빼빼로만들기) 순위 개선폭이 큰 순."""
    me = keyword.replace(" ", "")
    rows = [r for g in table["groups"].values() for r in g if r["keyword"] != keyword]
    related = [r for r in rows if me in r["keyword"].replace(" ", "") or r["keyword"].replace(" ", "") in me]
    others = sorted((r for r in rows if r not in related and (r["change"] or 0) > 0), key=lambda r: -(r["change"] or 0))
    return [{"keyword": r["keyword"], "change": r["change"], "group": r["group"], "related": r in related}
            for r in (related + others)[:top]]


def _clues(blog: dict | None) -> dict | None:
    if not blog or blog.get("status") != "ok":
        return None
    return {"last7": blog.get("last7"), "posts": blog.get("posts"), "clues": dict(list((blog.get("clues") or {}).items())[:5])}


def _public_cause(cause: dict | None) -> dict | None:
    if not cause or not cause.get("public", True):
        return None
    return {"text": cause.get("cause") or cause.get("summary") or cause.get("text"), "kind": cause.get("kind"),
            "confidence": cause.get("confidence"), "label": cause.get("label")}


# ── env glue ─────────────────────────────────────────────────────────────────
def resolve_period(preset: str | None, start: str | None, end: str | None, last_day: str | None) -> tuple[str, str]:
    """1w·1m·3m 또는 직접 입력. end 가 없으면 자료의 마지막 날."""
    e = dt.date.fromisoformat(end) if end else (dt.date.fromisoformat(last_day) if last_day else dt.date.today())
    if start:
        s = dt.date.fromisoformat(start)
    else:
        s = e - dt.timedelta(days=PRESETS.get(preset or "1m", 30) - 1)
    return s.isoformat(), e.isoformat()


def source_note(kind: str, rank_dir: Path | None) -> str | None:
    if kind == "daily":
        return None
    if kind == "mixed":
        return (f"하루 단위 순위 폴더(NAVER_DAILY_RANK_DIR)가 없어 예전 폴더를 읽어요. 이 폴더는 {MIXED_WINDOW_FROM}부터 "
                "'최근 30일 묶음' 순위가 섞여 있어 그 뒤 날짜의 변화 폭은 작게 보여요.")
    return "식품 순위 폴더(NAVER_DAILY_RANK_DIR 또는 NAVER_DAILY_DIR)가 설정되지 않았어요."
