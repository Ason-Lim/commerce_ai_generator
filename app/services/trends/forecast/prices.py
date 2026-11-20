"""
가격 레이어 — 감시 품목의 공공 시세(KAMIS) 시계열 · 시즌 곡선 · 현재 위치 · 매수 시점 판정 (2026-11-19 밤, 연구 문서 §9)

자료
  data/kamis/history.csv          scripts/backfill_kamis_history.py 가 만든 일별 소매 시세 (2024-01-01~). 없으면
  data/kamis/daily_*.json          하루 한 번 받은 dailySalesList 의 당일·1일전·1개월전·1년전 네 점을 모아 '성긴 시계열'로 대신 쓴다
                                   (점이 적어 대부분 '보류'가 나온다 — 백필 뒤에 제대로 판정).
  data/price_watchlist.csv         감시 품목 ↔ KAMIS 품목·품종 ↔ 동인 ↔ 직구 가능 여부
  data/price_drivers.csv           원가 동인 가설표 (엘니뇨·곡물·사료·AI·김장·환율 …) — 모두 status=가설
  data/driver_signals.csv          동인 활성 상태 (사람이 넣음: date, driver, on/off, note). 자동 수집은 다음 단계.

원칙 (행사 선행 곡선과 같음)
  * 해마다 따로 본다(평균하지 않음). 전망은 '전년 같은 날짜 → +h일' 비율의 해별 값과 중앙값·범위를 함께 낸다.
  * as_of(기준일) 뒤 자료는 읽지 않는다 — 백테스트용.
  * 판정 임계값(LOW_PCT·HIGH_PCT·UP·DOWN·MIN_YEARS)은 **첫 값** — 백테스트로 다시 정한다.
  * 동인은 가설이다. 활성 상태(on)는 사람이 적은 것이고, 판정에는 '이유'로만 붙지 수치에 들어가지 않는다.
  * 이 모듈은 공공 시세(원물)만 다룬다. 쿠팡·UCP 상품 가격 비교는 routes 에서 붙인다(올리브유·양고기처럼 KAMIS 에 없는 품목).
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[4]
HISTORY = ROOT / "data" / "kamis" / "history.csv"
DAILY_DIR = ROOT / "data" / "kamis"
WATCHLIST = ROOT / "data" / "price_watchlist.csv"
DRIVERS = ROOT / "data" / "price_drivers.csv"
SIGNALS = ROOT / "data" / "driver_signals.csv"

# 판정 임계 — 첫 값 (연구 §9)
LOW_PCT, HIGH_PCT = 0.30, 0.70        # 52주 분포 위치: 하위 30% = 싼 구간, 상위 30% = 비싼 구간
UP, DOWN = 0.05, 0.05                 # 4주 전망 ±5% 를 '오름/내림' 으로
MIN_YEARS = 2                         # 전망에 쓸 수 있는 전년 수 (2024·2025 둘 다 있어야 '전망', 하나면 '참고')
MIN_OBS_52W = 20                      # 52주 창 최소 관측일
HORIZONS = (7, 14, 28)
TOL_DAYS = 3                          # 같은 날짜가 없으면 ±3일 안 가장 가까운 관측
CURVE_REL = (-42, 28)                 # 행사(김장·명절) 상대일 곡선 범위
BASE_REL = (-42, -29)                 # 곡선의 기준 구간 (비율 1.0 의 분모 = 이 구간 중앙값)


# ── 자료 읽기 ────────────────────────────────────────────────
def _csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.DictReader(fh)]


def watchlist(path: Path | None = None) -> list[dict]:
    return [r for r in _csv(path or WATCHLIST) if r.get("item")]


def drivers(path: Path | None = None) -> dict[str, dict]:
    return {r["id"]: r for r in _csv(path or DRIVERS) if r.get("id")}


def signals(path: Path | None = None) -> list[dict]:
    return [r for r in _csv(path or SIGNALS) if r.get("date") and r.get("driver")]


def load_history(path: Path | None = None, *, cls: str = "01") -> list[dict]:
    """history.csv → [{date, item, kind, rank, unit, price}] (소매만, 기본)."""
    out = []
    for r in _csv(path or HISTORY):
        if r.get("cls", "01") != cls:
            continue
        try:
            out.append({"date": dt.date.fromisoformat(r["date"]), "item": r["item_name"], "kind": r["kind_name"],
                        "rank": r.get("rank", ""), "unit": r["unit"], "price": int(r["price"]), "src": "history"})
        except (KeyError, ValueError):
            continue
    return out


def _shift_month(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    last = (dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)).day
    return dt.date(y, m, min(d.day, last))


def _int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def load_daily_points(daily_dir: Path | None = None, *, cls_code: str = "01") -> list[dict]:
    """daily_*.json(dailySalesList) 의 당일·1일전·1개월전·1년전 네 점 → 성긴 시계열. 백필 전 대체용."""
    out, seen = [], set()
    for p in sorted((daily_dir or DAILY_DIR).glob("daily_*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for it in doc.get("price") or []:
            if it.get("product_cls_code") != cls_code:
                continue
            name = it.get("productName") or it.get("item_name") or ""
            item, _, kind = name.partition("/")
            try:
                day = dt.date.fromisoformat(it.get("lastest_day") or "")
            except ValueError:
                continue
            points = ((day, it.get("dpr1")), (day - dt.timedelta(days=1), it.get("dpr2")),
                      (_shift_month(day, -1), it.get("dpr3")), (_shift_month(day, -12), it.get("dpr4")))
            for d, v in points:
                price = _int(v)
                key = (d, item.strip(), kind.strip())
                if price and key not in seen:
                    seen.add(key)
                    out.append({"date": d, "item": item.strip(), "kind": kind.strip(), "rank": "",
                                "unit": it.get("unit") or "", "price": price, "src": "daily"})
    return out


def rows_for_analysis(history: list[dict] | None = None, daily: list[dict] | None = None) -> tuple[list[dict], str]:
    """백필 자료가 있으면 그것, 없으면 일별 파일의 네 점. (행, 출처 설명)"""
    history = load_history() if history is None else history
    if history:
        return history, "KAMIS 백필(history.csv)"
    daily = load_daily_points() if daily is None else daily
    return daily, "KAMIS 일별 파일의 당일·1일전·1개월전·1년전 점만(백필 전 — 성김)"


# ── 시계열 ────────────────────────────────────────────────────
def _kind_ok(r: dict, kind_filter: str) -> bool:
    """품종 필터 — 괄호로 나눈 첫 토큰은 품종 이름(괄호 뺀 것)과 **똑같아야** 하고('갈비' ≠ '갈비살'), 나머지 토큰은
    품종·단위·등급 어디든 들어 있으면 된다. 'XL30구(일반란)' ↔ kind 'XL30구'·rank '일반란' / '등심(1등급)' ↔ '등심'·'1등급'.
    history.csv(품종·등급이 열로 나뉨)와 daily 파일('XL30구(일반란)' 한 덩어리) 둘 다 맞는다."""
    if not kind_filter:
        return True
    squash = lambda t: re.sub(r"\s+", "", t)              # noqa: E731
    toks = [squash(t) for t in re.split(r"[()]", kind_filter) if t.strip()]
    kind = r.get("kind") or ""
    base = squash(re.sub(r"\(.*?\)", "", kind))
    hay = squash(kind + (r.get("unit") or "") + (r.get("rank") or ""))
    if not toks:
        return True
    return toks[0] == base and all(t in hay for t in toks[1:])


def series(rows: list[dict], item: str, kind_filter: str = "", *, as_of: dt.date | None = None) -> dict[dt.date, int]:
    """{날짜: 가격} — 같은 날 여러 행(등급 등)은 중앙값. as_of 뒤는 뺀다."""
    by: dict[dt.date, list[int]] = {}
    for r in rows:
        if r["item"] != item or not _kind_ok(r, kind_filter):
            continue
        if as_of is not None and r["date"] > as_of:
            continue
        by.setdefault(r["date"], []).append(r["price"])
    return {d: int(median(v)) for d, v in sorted(by.items())}


def at(s: dict[dt.date, int], day: dt.date, tol: int = TOL_DAYS) -> tuple[dt.date, int] | None:
    """day 에 가장 가까운(±tol) 관측. 같은 거리면 앞 날짜."""
    best = None
    for k in range(0, tol + 1):
        for d in (day - dt.timedelta(days=k), day + dt.timedelta(days=k)):
            if d in s:
                return d, s[d]
    return best


def _same_day_years_ago(d: dt.date, years: int) -> dt.date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:                      # 2-29
        return d.replace(year=d.year - years, day=28)


def position(s: dict[dt.date, int], as_of: dt.date) -> dict | None:
    """현재 위치 — 최근 관측, 1개월·1년 전 대비, 52주 창 안의 백분위(같은 값은 절반으로 세는 중간 순위)·최저·최고."""
    dates = [d for d in s if d <= as_of]
    if not dates:
        return None
    last = max(dates)
    now = s[last]
    win = [s[d] for d in dates if (last - d).days < 364]
    pct = (sum(1 for v in win if v < now) + 0.5 * sum(1 for v in win if v == now)) / len(win) if win else None   # 중간 순위
    m1 = at(s, _shift_month(last, -1))
    y1 = at(s, _same_day_years_ago(last, 1))
    return {"date": last.isoformat(), "price": now, "n_52w": len(win),
            "pct_52w": round(pct, 2) if pct is not None else None,
            "min_52w": min(win) if win else None, "max_52w": max(win) if win else None,
            "vs_1m": round((now / m1[1] - 1) * 100) if m1 else None,
            "vs_1y": round((now / y1[1] - 1) * 100) if y1 else None,
            "stale_days": (as_of - last).days}


def outlook(s: dict[dt.date, int], as_of: dt.date, *, years: tuple[int, ...] = (1, 2),
            horizons: tuple[int, ...] = HORIZONS) -> dict:
    """전년 같은 날짜 → +h일 비율. 해마다 따로 + 중앙값·범위. {h: {years:{y: ratio}, median, lo, hi, n}}"""
    out = {}
    for h in horizons:
        per = {}
        for k in years:
            base_day = _same_day_years_ago(as_of, k)
            b, f = at(s, base_day), at(s, base_day + dt.timedelta(days=h))
            if b and f and b[1]:
                per[base_day.year] = round(f[1] / b[1], 3)
        vals = list(per.values())
        out[h] = {"years": per, "n": len(vals), "median": round(median(vals), 3) if vals else None,
                  "lo": min(vals) if vals else None, "hi": max(vals) if vals else None,
                  "agree": (all(v >= 1 for v in vals) or all(v <= 1 for v in vals)) if len(vals) >= 2 else None}
    return out


def relative_curve(s: dict[dt.date, int], anchors: dict[int, dt.date], rel: tuple[int, int] = CURVE_REL,
                   *, as_of: dt.date | None = None) -> dict[int, dict]:
    """행사 기준 상대일 곡선 — {연도: {points: [[rel, price, ratio]], base: 기준 구간 중앙값}}. ratio = price/base."""
    out = {}
    for y, a in sorted(anchors.items()):
        pts = []
        for k in range(rel[0], rel[1] + 1):
            d = a + dt.timedelta(days=k)
            if as_of is not None and d > as_of:
                break
            if d in s:
                pts.append([k, s[d]])
        base_vals = [p for k, p in pts if BASE_REL[0] <= k <= BASE_REL[1]]
        base = median(base_vals) if len(base_vals) >= 3 else None
        out[y] = {"anchor": a.isoformat(), "base": base,
                  "points": [[k, p, round(p / base, 3) if base else None] for k, p in pts]}
    return out


# ── 매수 시점 판정 ───────────────────────────────────────────
def buy_timing(pos: dict | None, ol: dict, *, horizon: int = 28) -> dict:
    """지금 / 기다리기 / 분할 / 보류 — 이유와 함께. 규칙(첫 값):
      보류      관측 부족(52주 창 < MIN_OBS_52W) 또는 전년 비교 가능 해 < MIN_YEARS
      기다리기  4주 전망 중앙값 ≤ −DOWN (가장 낮은 지평 h 를 '언제'로)
      지금      4주 전망 ≥ +UP 이고 지금이 비싼 구간(≥HIGH_PCT)이 아님 · 또는 싼 구간(≤LOW_PCT)이고 내림 전망 없음
      분할      그 밖(전망이 평평하거나 해마다 방향이 다름, 비싼 구간인데 더 오를 전망)"""
    reasons = []
    if not pos:
        return {"verdict": "보류", "reasons": ["시세 자료 없음"], "best_h": None}
    h = ol.get(horizon) or {}
    n_obs, pct, med = pos["n_52w"], pos["pct_52w"], h.get("median")
    if n_obs < MIN_OBS_52W:
        reasons.append(f"52주 관측 {n_obs}일 < {MIN_OBS_52W} (백필 필요)")
    if h.get("n", 0) < MIN_YEARS:
        reasons.append(f"전년 비교 가능 해 {h.get('n', 0)} < {MIN_YEARS}")
    if reasons:
        if med is not None:
            reasons.append(f"참고: 전년 같은 시기 {horizon}일 뒤 {(med - 1) * 100:+.0f}% (해 {h['n']}개)")
        return {"verdict": "보류", "reasons": reasons, "best_h": None}
    lows = sorted(((ol[k]["median"], k) for k in ol if ol[k]["median"] is not None), key=lambda t: (t[0], t[1]))
    best_h = lows[0][1] if lows and lows[0][0] < 1 - DOWN else 0
    exp_txt = f"전년 같은 시기 {horizon}일 뒤 {(med - 1) * 100:+.0f}% (해 {h['n']}개, 범위 {(h['lo'] - 1) * 100:+.0f}…{(h['hi'] - 1) * 100:+.0f}%)"
    pos_txt = f"지금 52주 분포의 {'하위' if pct <= 0.5 else '상위'} {round((pct if pct <= 0.5 else 1 - pct) * 100)}% 자리 ({pos['price']:,}원)"
    if h.get("agree") is False:
        reasons.append("해마다 방향이 달라요 — 전망 신뢰 낮음")
    if med <= 1 - DOWN:
        verdict = "기다리기"
        reasons.insert(0, f"{best_h}일 뒤가 가장 낮을 것으로 보여요 ({(lows[0][0] - 1) * 100:+.0f}%)")
    elif med >= 1 + UP and pct < HIGH_PCT:
        verdict = "지금"
    elif pct <= LOW_PCT and med > 1 - DOWN:
        verdict = "지금"
        reasons.insert(0, "싼 구간이고 더 내릴 전망이 없어요")
    elif pct >= HIGH_PCT:
        verdict = "분할"
        reasons.insert(0, "비싼 구간 — 필요한 만큼만 사고 나머지는 나눠서")
    else:
        verdict = "분할"
    reasons.extend([exp_txt, pos_txt])
    if verdict == "분할" and h.get("agree") is False:
        verdict = "분할"
    return {"verdict": verdict, "reasons": reasons, "best_h": best_h, "expected_28d": round((med - 1) * 100)}


def active_drivers(row: dict, drv: dict[str, dict], sig: list[dict], as_of: dt.date) -> list[dict]:
    """감시 품목의 동인 목록 — 최근 신호(as_of 이전)의 상태. 신호 없으면 unknown."""
    out = []
    for did in [x for x in (row.get("drivers") or "").split(";") if x]:
        d = drv.get(did)
        if not d:
            continue
        latest = None
        for s in sig:
            try:
                sd = dt.date.fromisoformat(s["date"])
            except ValueError:
                continue
            if s["driver"] == did and sd <= as_of and (latest is None or sd >= latest[0]):
                latest = (sd, s)
        out.append({"id": did, "driver": d["driver"], "direction": d["direction"], "status": d["status"],
                    "lag_days": [d["lag_days_min"], d["lag_days_max"]], "signal_source": d["signal_source"],
                    "state": latest[1]["state"] if latest else "unknown",
                    "signal_date": latest[0].isoformat() if latest else None,
                    "signal_note": latest[1].get("note") if latest else None, "note": d.get("note", "")})
    return out


# ── 리포트 ───────────────────────────────────────────────────
def _anchors(cal_rows: list[dict], event: str) -> dict[int, dt.date]:
    return {int(r["date"][:4]): dt.date.fromisoformat(r["date"]) for r in cal_rows if r.get("event") == event}


def item_report(row: dict, rows: list[dict], as_of: dt.date, *, drv: dict[str, dict] | None = None,
                sig: list[dict] | None = None, cal_rows: list[dict] | None = None, source: str = "") -> dict:
    drv = drivers() if drv is None else drv
    sig = signals() if sig is None else sig
    rep = {"item": row["item"], "group": row.get("group"), "kamis": None, "overseas": row.get("overseas"),
           "overseas_note": row.get("overseas_note"), "keywords": [k for k in (row.get("keywords") or "").split(";") if k],
           "note": row.get("note"), "as_of": as_of.isoformat(), "drivers": active_drivers(row, drv, sig, as_of),
           "source": source}
    if not row.get("kamis_item"):
        rep["position"] = None
        rep["outlook"] = {}
        rep["timing"] = {"verdict": "보류", "reasons": ["공공 시세(KAMIS) 품목이 없어요 — 상품 가격 비교로만"], "best_h": None}
        rep["curves"] = {}
        return rep
    s = series(rows, row["kamis_item"], row.get("kamis_kind", ""), as_of=as_of)
    rep["kamis"] = {"item": row["kamis_item"], "kind": row.get("kamis_kind", ""), "n": len(s),
                    "first": min(s).isoformat() if s else None, "last": max(s).isoformat() if s else None}
    pos = position(s, as_of)
    ol = outlook(s, as_of)
    rep["position"] = pos
    rep["outlook"] = {str(h): v for h, v in ol.items()}
    rep["timing"] = buy_timing(pos, ol)
    rep["series_1y"] = [[d.isoformat(), p] for d, p in s.items() if (as_of - d).days <= 400]
    rep["curves"] = {}
    ev = row.get("anchor_event")
    if ev and cal_rows:
        anc = _anchors(cal_rows, ev)
        if anc:
            rep["curves"] = {"event": ev, "years": relative_curve(s, anc, as_of=as_of)}
    return rep


def summary(as_of: dt.date, *, rows: list[dict] | None = None, wl: list[dict] | None = None, source: str = "") -> list[dict]:
    """감시 품목 전체 한 줄씩 — 판정·현재 위치·4주 전망 (화면 표)."""
    wl = watchlist() if wl is None else wl
    if rows is None:
        rows, source = rows_for_analysis()
    drv, sig = drivers(), signals()
    out = []
    for row in wl:
        if row.get("kamis_item"):
            s = series(rows, row["kamis_item"], row.get("kamis_kind", ""), as_of=as_of)
            pos = position(s, as_of)
            ol = outlook(s, as_of)
            t = buy_timing(pos, ol)
            o28 = ol.get(28) or {}
        else:
            pos, t, o28 = None, {"verdict": "보류", "reasons": ["공공 시세 없음 — 상품 비교로만"], "best_h": None}, {}
        act = [d for d in active_drivers(row, drv, sig, as_of) if d["state"] == "on"]
        out.append({"item": row["item"], "group": row.get("group"), "kamis_item": row.get("kamis_item") or None,
                    "overseas": row.get("overseas"), "position": pos, "verdict": t["verdict"], "reasons": t["reasons"],
                    "expected_28d": t.get("expected_28d"), "outlook_28_n": o28.get("n", 0),
                    "active_drivers": [d["driver"] for d in act]})
    order = {"지금": 0, "기다리기": 1, "분할": 2, "보류": 3}
    out.sort(key=lambda r: (order.get(r["verdict"], 9), r["item"]))
    return out
