"""
홈 '지금 순위' — 쿠팡 식품 랭킹 · 카테고리 (+ 지금 뜨는 식품 화면의 급상승) (2026-11-23 개편 — 처음: 급상승 · 카테고리 · 트렌드 상품, 창 3-C ②, 설계 claude/home_rankings_design_2026-11-20.md §2·§3)
=====================================================================================================

`build(view)` 하나가 `GET /api/home/rankings?view=home|full` 응답을 만든다.

* 저장된 자료를 읽는다 — 급상승 리포트 파일, 하루 단위 식품 순위 CSV, 승인된 트렌드 글. 예외: 쿠팡 식품 랭킹은 메모리 10분(10분에 최대 1번 호출, 파일 저장 없음 — 약관 제5조 ③). 네이버 호출 0.
* 2026-11-23: 홈 탭 = 쿠팡 식품 랭킹 · 카테고리 · 함께 보면 좋은 상품(together.py, POST /api/home/together). picks 는 응답에 남김.
* 세 영역이 각자 status · 기준일 · items 를 가진다 (부분 실패 — 한 영역이 없어도 나머지는 나옴).
* home 과 full 은 **같은 선정 규칙**, 개수만 다름. 상품은 묶음(recent/steady)별 앞부분이 일치.
* 공개 응답 허용 목록: 키워드·순위·배수·시작일·태그·ask·승인 글 제목/링크·상품 카드 칸.
  검색 질의문·API 이름·호출 기록·파일 경로·미승인 글·운영자 메모는 넣지 않는다.

키워드 상태 (카테고리):
  steady       늘 인기 = 최근 90일 창 관측일 ≥ 60, 그중 100위 안 ≥ 80%
  other        관측일 ≥ 60, 조건 미충족
  insufficient 관측일 < 60 (판단 자료 부족)
  관측일 = **정상 파일**(존재 + 완전성: 행 ≥ 500 · 키워드 중복 없음 · date 칸이 파일 날짜와 같음)이 있는 날.
변화 (상태와 별개): 7일 전 정상 파일과 비교 — change_kind compared / entered(상위 500위 진입) / no_compare.
'오르는 중' = (state ∈ {other, insufficient}) AND (change_7d > 0 OR change_kind == entered). steady 는 절대 안 들어감.
"""
from __future__ import annotations

import csv
import datetime as dt
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.services.trends import period, tags as tagmod

KST = dt.timezone(dt.timedelta(hours=9))
TOP_BAND = 100
FULL_ROWS = 500                 # 정상 파일 행 수 (하루 상위 500)
STEADY_WINDOW, STEADY_MIN_OBS, STEADY_SHARE = 90, 60, 0.8
PICK_WINDOW, PICK_MIN_OBS = 30, 20          # 상품 배지 '관련 키워드 꾸준한 관심'
COMPARE_DAYS = 7
STALE_RANK_DAYS = 3             # 순위 파일이 이보다 오래되면 stale
STALE_SURGE_DAYS = 3
# 2026-11-23 사용자 요청: 홈 쿠팡 식품 랭킹 30개(화면은 6개 + 더보기)
LIMITS = {"home": {"surge": 6, "category": 6, "recent": 4, "steady": 2, "coupang": 30},
          "full": {"surge": 100, "category": TOP_BAND, "recent": 16, "steady": 4, "coupang": 100}}
COUPANG_NOTE = ("쿠팡 파트너스가 주는 식품 카테고리 베스트 순위 그대로예요 (우리 점수로 다시 줄 세우지 않아요). "
                "10분마다 새로 받고, 가격은 받은 시각의 가격이에요.")
PER_POST = 2                    # 글당 상품 1~2개
CACHE_SECONDS = 300
CATEGORY_NOTE = ("네이버 식품 검색어 순위 · 하루 한 번 · 늘 인기 = 최근 90일 창 관측일 60 이상·100위 안 80% 이상 · "
                 "오르는 중 = 7일 전보다 순위가 오름(또는 상위 500위 진입)")
PLACEMENT_NOTE = "최근 소개 {r}개 + 관련 키워드 꾸준한 관심 상품 최대 {s}개 — 두 묶음, 추천 순위가 아니에요"
BADGE_NOTES = {"keyword_steady": "관련 키워드가 최근 30일 창에서 관측된 날짜 중 80% 이상 100위 안",
               "multi_post": "같은 상품이 승인된 트렌드 글 2편 이상에 소개됨"}
DISCLOSURE = "이 영역의 상품 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. 수수료는 순위·순서에 영향을 주지 않아요."
IMAGE_HOSTS = ("coupangcdn.com",)

_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, dict]] = {}
_NORMAL: dict[tuple[str, float], bool] = {}


# ── 순위 파일 ───────────────────────────────────────────────────────────────
def is_normal(path: Path, day: str) -> bool:
    """정상 파일 = 읽힘 + 행 ≥ 500 + 키워드 중복 없음 + date 칸이 파일 날짜와 같음 (수정 시각으로 캐시)."""
    try:
        key = (str(path), path.stat().st_mtime)
    except OSError:
        return False
    with _LOCK:
        if key in _NORMAL:
            return _NORMAL[key]
    ok = False
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        kws = [(r.get("keyword") or "").strip() for r in rows]
        dates = {(r.get("date") or "").strip() for r in rows} - {""}
        ok = len(rows) >= FULL_ROWS and len(set(kws)) == len(kws) and all(kws) and dates <= {day}
    except (OSError, csv.Error, UnicodeDecodeError):
        ok = False
    with _LOCK:
        if len(_NORMAL) > 4000:
            _NORMAL.clear()
        _NORMAL[key] = ok
    return ok


def normal_days(files: dict[str, Path], end: str, window: int) -> dict[str, dict[str, int]]:
    """end 포함 window 일(달력) 안의 정상 파일 → {날짜: {키워드: 순위}}."""
    e = dt.date.fromisoformat(end)
    out = {}
    for i in range(window):
        day = (e - dt.timedelta(days=i)).isoformat()
        p = files.get(day)
        if p is not None and is_normal(p, day):
            got = period.read_ranks(p)
            if got:
                out[day] = got
    return out


def keyword_state(kw: str, hist: dict[str, dict[str, int]], *, min_obs: int = STEADY_MIN_OBS,
                  share: float = STEADY_SHARE) -> tuple[str, int, int]:
    observed = len(hist)
    top = sum(1 for r in hist.values() if (r.get(kw) or 10**6) <= TOP_BAND)
    if observed < min_obs:
        return "insufficient", observed, top
    return ("steady" if top >= share * observed else "other"), observed, top


def change_7d(kw: str, now_rank: int, before: dict[str, int] | None) -> tuple[int | None, str]:
    if before is None:
        return None, "no_compare"
    if kw not in before:
        return None, "entered"
    return before[kw] - now_rank, "compared"


def is_rising(item: dict) -> bool:
    return (item["state"] in ("other", "insufficient")) and (
        (item["change_7d"] or 0) > 0 or item["change_kind"] == "entered")


# ── 영역 셋 ────────────────────────────────────────────────────────────────
def _stale(day: str | None, today: dt.date, days: int) -> bool:
    try:
        return (today - dt.date.fromisoformat(day)).days > days
    except (TypeError, ValueError):
        return True


def surge_part(view: str, today: dt.date, env=None) -> dict:
    from app.services.trends import surge

    try:
        report = surge.load(env=env)
    except (OSError, ValueError):
        report = None
    pv = surge.public_view(report, limit=LIMITS[view]["surge"])
    if pv["status"] == "empty":
        return {"status": "empty", "data_until": None, "updated_at": None, "items": []}
    items = []
    for n, it in enumerate(pv["items"], 1):
        row = {"n": n, "keyword": it["keyword"], "status": it["status"], "times": it["times"],
               "rank": it["rank"], "onset": it["onset"], "ask": it["ask"]}
        if view == "full":
            row.update({"clues": it["clues"], "cause": it["cause"], "spark": it["spark"], "cross": it["cross"]})
        items.append(row)
    status = "stale" if _stale(pv["data_until"], today, STALE_SURGE_DAYS) else pv["status"]
    return {"status": status, "data_until": pv["data_until"], "updated_at": pv["generated_at"], "items": items}


def category_part(view: str, today: dt.date, env=None, rank_dir: Path | None = None) -> dict:
    if rank_dir is None:
        rank_dir, _kind = period.rank_dir_from_env(env)
    empty = {"status": "none", "rank_date": None, "tabs": [], "note": CATEGORY_NOTE}
    if rank_dir is None:
        return empty
    files = period.rank_files(rank_dir)
    latest = next((d for d in sorted(files, reverse=True) if is_normal(files[d], d)), None)
    if latest is None:
        return empty
    now = period.read_ranks(files[latest]) or {}
    hist = normal_days(files, latest, STEADY_WINDOW)
    before_day = (dt.date.fromisoformat(latest) - dt.timedelta(days=COMPARE_DAYS)).isoformat()
    before = hist.get(before_day)
    table = tagmod.load()
    try:
        events = tagmod.season_events(today)
    except Exception:  # noqa: BLE001 — 달력이 없으면 시즌 없이
        events = []
    rows = []
    for kw, rank in sorted(now.items(), key=lambda x: x[1]):
        if rank > TOP_BAND:
            break
        tg = tagmod.tags_for(kw, tags=table, events=events)
        if not tg:
            continue
        state, obs, top = keyword_state(kw, hist)
        ch, kind = change_7d(kw, rank, before)
        rows.append({"rank": rank, "keyword": kw, "ask": f"{kw} 추천해 줘", "tags": tg,
                     "season": tagmod.season_match(kw, events) if "season" in tg else [],
                     "state": state, "window_days": STEADY_WINDOW, "observed_days": obs, "top100_days": top,
                     "change_7d": ch, "change_kind": kind})
    for r in rows:
        r["rising"] = is_rising(r)
    limit = LIMITS[view]["category"]
    tabs = []
    for t in table:
        mine = [r for r in rows if t.tag in r["tags"]]
        if not mine:
            continue
        rising = [r for r in mine if r["rising"]]
        # 기본 보기 '오르는 중' — 비교 자료가 없어 하나도 없으면 '늘 인기'를 뺀 순위순, 그것도 없으면 전체
        others = [r for r in mine if r["state"] != "steady"]
        default, shown = ("rising", rising) if rising else (("not_steady", others) if others else ("all", mine))
        tabs.append({"tag": t.tag, "label": t.label, "icon": t.icon, "default_filter": default,
                     "counts": {"all": len(mine), "rising": len(rising),
                                "steady": sum(r["state"] == "steady" for r in mine),
                                "insufficient": sum(r["state"] == "insufficient" for r in mine)},
                     "items": (mine if view == "full" else shown)[:limit]})
    status = "stale" if _stale(latest, today, STALE_RANK_DAYS) else "ok"
    return {"status": status, "rank_date": latest, "compare_date": before_day if before is not None else None,
            "observed_days": len(hist), "window_days": STEADY_WINDOW, "tabs": tabs, "note": CATEGORY_NOTE,
            "season_events": [{"event": e["event"], "date": e["date"], "d_day": e["d_day"]} for e in events]}


def product_id(url: str) -> str:
    q = parse_qs(urlparse(url or "").query)
    return (q.get("pageKey") or q.get("productId") or [""])[0] or (url or "")


def _image(url: str | None) -> str | None:
    if not url:
        return None
    u = urlparse(url)
    return url if u.scheme == "https" and any(u.netloc.endswith(h) for h in IMAGE_HOSTS) else None


def picks_part(view: str, now: dt.datetime, *, posts=None, rank_dir: Path | None = None, env=None) -> dict:
    from app.services.trend_posts import policy, render
    from app.services.trend_posts.service import TrendPosts

    lim = LIMITS[view]
    try:
        published = (posts or TrendPosts()).published()          # 승인 글만, 승인 시각 내림차순
    except Exception:  # noqa: BLE001
        published = []
    # 키워드 꾸준한 관심 판단용 30일 창
    if rank_dir is None:
        rank_dir, _kind = period.rank_dir_from_env(env)
    hist: dict[str, dict[str, int]] = {}
    if rank_dir is not None:
        files = period.rank_files(rank_dir)
        latest = next((d for d in sorted(files, reverse=True) if is_normal(files[d], d)), None)
        if latest:
            hist = normal_days(files, latest, PICK_WINDOW)
    seen_count: dict[str, int] = {}
    for post in published:
        if post.conclusion == "hold":
            continue
        for p in post.products:
            pid = product_id(p.url)
            seen_count[pid] = seen_count.get(pid, 0) + 1
    cards: list[dict] = []
    used: set[str] = set()
    for post in published:                           # 최신 승인 글부터 — 같은 상품은 가장 최근 글 하나만
        if post.conclusion == "hold":
            continue
        taken = 0
        for n, p in enumerate(post.products, 1):
            pid = product_id(p.url)
            if pid in used or taken >= PER_POST:
                continue
            used.add(pid)
            taken += 1
            kw = p.keyword or post.topic
            state, _obs, _top = keyword_state(kw, hist, min_obs=PICK_MIN_OBS) if hist else ("insufficient", 0, 0)
            badges = (["keyword_steady"] if state == "steady" else []) + (
                ["multi_post"] if seen_count.get(pid, 0) >= 2 else [])
            hidden = p.price_krw is None or policy.is_stale(p.price_checked_at, now)
            cards.append({
                "product_id": pid, "title": p.title, "mall": p.platform,
                "price_krw": None if hidden else p.price_krw,
                "price_checked_at": None if hidden else p.price_checked_at, "price_hidden": hidden,
                "image": _image(p.image_url), "rocket": bool(p.rocket) and not hidden,
                "why": f"트렌드 글 기준 · {post.title}", "post_title": post.title,
                "post_url": render.post_url(post), "go_url": f"{render.post_url(post)}/go/{n}",
                "badges": badges, "post_count": seen_count.get(pid, 1),
                "_approved": post.approved_at or "",
            })
    if not cards:
        return {"status": "none", "disclosure": DISCLOSURE, "groups": {"recent": [], "steady": []},
                "source": "승인된 트렌드 글", "placement_note": "", "badge_notes": BADGE_NOTES}
    # 묶음 내부 정렬 고정: 승인 시각 내림차순 → productId 오름차순
    def order(xs):
        return sorted(sorted(xs, key=lambda c: c["product_id"]), key=lambda c: c["_approved"], reverse=True)

    steady_all = order([c for c in cards if "keyword_steady" in c["badges"]])
    recent_all = order([c for c in cards if "keyword_steady" not in c["badges"]])
    steady = steady_all[:lim["steady"]]
    fill = lim["steady"] - len(steady)                       # steady 가 모자라면 recent 로 채움 (반대는 없음)
    recent = recent_all[:lim["recent"] + fill]
    for c in steady + recent:
        c.pop("_approved", None)
    return {"status": "ok", "disclosure": DISCLOSURE, "groups": {"recent": recent, "steady": steady},
            "source": "승인된 트렌드 글", "filled": fill,
            "placement_note": PLACEMENT_NOTE.format(r=lim["recent"], s=lim["steady"]), "badge_notes": BADGE_NOTES}


def coupang_part(view: str, now: dt.datetime, env=None) -> dict:
    """쿠팡 식품 랭킹 (2026-11-23 — 홈 첫 탭). 메모리 10분(파일 저장 없음) — 10분에 최대 1번 쿠팡 호출."""
    from app.services.trends import coupang_best as cb

    out = cb.ranked(now.astimezone(KST).date(), now, LIMITS[view]["coupang"], env=env)
    return {**out, "disclosure": DISCLOSURE, "note": COUPANG_NOTE}


# ── 묶기 ──────────────────────────────────────────────────────────────────
def build(view: str = "home", *, now: dt.datetime | None = None, env=None, posts=None,
          rank_dir: Path | None = None, use_cache: bool = True) -> dict:
    view = "full" if view == "full" else "home"
    if use_cache and posts is None and rank_dir is None and env is None:
        with _LOCK:
            hit = _CACHE.get(view)
        if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
            return hit[1]
    now = now or dt.datetime.now(KST)
    today = now.astimezone(KST).date()
    out = {"generated_at": now.astimezone(KST).isoformat(timespec="minutes"), "view": view}
    for name, fn in (("coupang", lambda: coupang_part(view, now, env)),
                     ("surge", lambda: surge_part(view, today, env)),
                     ("categories", lambda: category_part(view, today, env, rank_dir)),
                     ("picks", lambda: picks_part(view, now, posts=posts, rank_dir=rank_dir, env=env))):
        try:
            out[name] = fn()
        except Exception:  # noqa: BLE001 — 영역 하나가 실패해도 나머지는 나온다
            import logging

            logging.getLogger(__name__).exception("home rankings %s failed", name)
            out[name] = {"status": "none", "items": [], "tabs": [], "groups": {"recent": [], "steady": []}}
    if use_cache and posts is None and rank_dir is None and env is None:
        with _LOCK:
            _CACHE[view] = (time.monotonic(), out)
    return out


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()
