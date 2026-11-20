"""관리자 백엔드 (/admin) — 로그인 1곳, 탭 2개.

  운영 탭   /admin                 판매처 API 점검 · 대화·추천 기록 · 장바구니·결제 뼈대
            (integrated_system 의 소비자 백엔드 consumer/app.py 에서 옮김, 2026-10-29)
  트렌드 탭 /admin/trends          검색량 급상승 리포트 (데이터랩 급상승 → 블로그 탐지 → 구글 트렌드 → 교차 확인)
                                   · 블로그 초안(applesodda 임시저장용 텍스트) — 2026-10-31
                                   · 쇼핑커넥트 발급 요청 목록(발급 완료·건너뛰기) — 2026-11-02
  AI 탭     /admin/ai              AI 비용 (작업별·모델별, 저장본 재사용으로 아낀 호출) · 확인된 사실 — 2026-11-11
  B2B 탭    /admin/b2b             B2B 콘솔 (자연어 지시 → 공고 분석 · 후보 · 원가 · 견적요청서 · 제안서)
            /admin/b2b/monitor     선물 입찰 모니터 · 트렌드 · 평가표 · 엑셀
            /admin/b2b/evidence    공급사 근거 (commerce 의 /b2b/suppliers · /b2b/products)
            /admin/b2b/templates   제안서 디자인 템플릿 (기본 4종 + 등록 · HTML 슬라이드/PPTX/PDF 에 적용)
            (integrated_system b2b/app.py 에서 옮김 — 같은 동작, 경로만 /admin/b2b 아래로)

외부로 메일·메시지를 보내거나 결제를 하는 기능은 없다 (견적요청서 · 제안서는 초안 파일만 만든다).
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, Field

from app.admin.auth import COOKIE, guest_trends_on, request_ok, require_admin, token_ok

WEB = Path(__file__).parent / "web"
B2B_WEB = Path(__file__).parent / "b2b" / "web"

router = APIRouter(tags=["admin"], include_in_schema=False)
api = Depends(require_admin)


def _page(request: Request, path: Path):
    if not request_ok(request):
        return RedirectResponse("/admin/login?next=" + quote(request.url.path), status_code=303)
    return FileResponse(path, headers={"Cache-Control": "no-store"})


# ── 로그인 ────────────────────────────────────────────────
LOGIN_HTML = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>관리자 로그인 | AI 식품 추천</title><style>body{font-family:system-ui,sans-serif;background:#f4f5f2;color:#1d211d;display:grid;place-items:center;min-height:100vh;margin:0}
form{background:#fff;padding:28px;border-radius:16px;width:min(360px,90vw);border:1px solid #e3e5df}h1{font-size:18px;margin:0 0 4px}p{margin:0 0 16px;color:#6b706a;font-size:13px}
input,button{width:100%;padding:12px;border-radius:10px;border:1px solid #d9dcd5;font-size:15px;box-sizing:border-box}
input:focus{outline:none;border-color:#9aa196}button{margin-top:10px;background:#1d211d;color:#fff;font-weight:700;cursor:pointer;border:0}
.err{color:#b4442f;font-size:13px;margin-top:8px}</style>
<form method=post action=/admin/login><h1>관리자</h1><p>운영 · B2B 내부 화면</p>
<input type=hidden name=next value="__NEXT__"><input name=token type=password placeholder="접근 토큰" autofocus autocomplete=current-password>
<button>들어가기</button>__ERR__</form>"""


def _safe_next(nxt: str | None) -> str:
    return nxt if nxt and nxt.startswith("/admin") and "//" not in nxt else "/admin"


@router.get("/admin/login", response_class=HTMLResponse)
def login_page(next: str | None = None, error: int = 0):
    from html import escape

    return LOGIN_HTML.replace("__NEXT__", escape(_safe_next(next))).replace(
        "__ERR__", "<div class=err>토큰이 맞지 않아요.</div>" if error else "")


@router.post("/admin/login")
def login(request: Request, token: str = Form(...), next: str = Form("/admin")):
    target = _safe_next(next)
    if not token_ok(token):
        return RedirectResponse(f"/admin/login?error=1&next={quote(target)}", status_code=303)
    r = RedirectResponse(target, status_code=303)
    r.set_cookie(COOKIE, token, httponly=True, samesite="strict", max_age=60 * 60 * 12, path="/",
                 secure=request.url.scheme == "https")
    return r


@router.post("/admin/logout")
def logout():
    r = RedirectResponse("/admin/login", status_code=303)
    r.delete_cookie(COOKIE, path="/")
    return r


# ── 운영 탭 ───────────────────────────────────────────────
@router.get("/admin")
def admin_home(request: Request):
    return _page(request, WEB / "admin.html")


# ── 트렌드 탭 (2026-10-31) ─────────────────────────────────
import threading as _threading

_TREND_JOB: dict = {"running": False, "error": None, "finished": None}
_TREND_LOCK = _threading.Lock()


@router.get("/admin/trends")
def admin_trends(request: Request):
    if not request_ok(request) and guest_trends_on():      # read-only guest view (ADMIN_GUEST_TRENDS=1)
        return FileResponse(WEB / "trends.html", headers={"Cache-Control": "no-store"})
    return _page(request, WEB / "trends.html")


@router.get("/admin/api/trends")
def trends_report(request: Request, date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$")):
    from app.services.trends import surge

    admin = request_ok(request)
    if not admin and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    return {"report": surge.load(date), "dates": surge.history_dates()[-30:], "job": dict(_TREND_JOB),
            "guest": not admin}


# ── 급상승 키워드 기간 조회 · 키워드 관심 이력 (2026-11-19 설계 1·2절) — 파일만 읽음, 외부 호출 없음 ─────────
def _period_dirs():
    from app.services.trends import period, surge

    rank_dir, kind = period.rank_dir_from_env()
    return rank_dir, kind, surge.report_dir()


def _period_has_link():
    """표에 보이는 줄에만 등록부 '링크 있음'을 붙인다 (화면과 같은 기준 chat.service.registry_links)."""
    try:
        from app.services.chat.service import registry_links
    except Exception:  # noqa: BLE001
        return None
    cache: dict[str, bool] = {}

    def has(kw: str) -> bool:
        if kw not in cache:
            try:
                cache[kw] = bool(registry_links([kw]))
            except Exception:  # noqa: BLE001
                cache[kw] = False
        return cache[kw]
    return has


@router.get("/admin/api/trends/period")
def trends_period(request: Request, preset: str | None = Query(None, pattern=r"^(1w|1m|3m)$"),
                  start: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                  end: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                  sort: str = Query("change", pattern=r"^(change|max_gain|days_top100|surge_days|best)$"),
                  limit: int = Query(60, ge=1, le=500), min_days: int = Query(1, ge=1, le=400)):
    """기간별 식품 키워드 순위 변화 + 급상승 감지 이력 (종료일 이하 자료만). 1w·1m·3m 또는 start~end."""
    from app.services.trends import period

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, surge_dir = _period_dirs()
    cov = period.coverage(rank_dir, surge_dir)
    if not rank_dir or not cov["rank"]:
        return {"ok": False, "coverage": cov, "source": {"kind": kind, "note": period.source_note(kind, rank_dir)}}
    s, e = period.resolve_period(preset, start, end, cov["rank"]["last"])
    if (date.fromisoformat(e) - date.fromisoformat(s)).days > 400:
        raise HTTPException(400, "기간은 400일 이내로 골라 주세요")
    table = period.period_table(rank_dir, s, e, surge_dir=surge_dir, sort=sort, min_days=min_days, with_series=True)
    has = _period_has_link()
    for g, rows in table["groups"].items():
        rows[:] = rows[:limit]
        for r in rows:
            r["series"] = r["series"][-90:]                    # 작은 선 그래프용 (최대 90점)
            r["has_link"] = has(r["keyword"]) if has else None
    table.update(ok=True, coverage=cov, source={"kind": kind, "note": period.source_note(kind, rank_dir)},
                 guest=not request_ok(request))
    return table


@router.get("/admin/api/trends/keyword")
def trends_keyword(request: Request, keyword: str = Query(..., min_length=1, max_length=60),
                   start: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                   end: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$")):
    """키워드 하나의 관심 이력 — 순위 전체 기간(누락·500위 밖 표시), 급상승 감지일, 종료일 이하 최근 급상승 파일의 60일 지수, 함께 움직인 키워드."""
    from app.services.trends import period

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, surge_dir = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    kw = keyword.strip()
    h = period.keyword_history(kw, rank_dir, end=end, surge_dir=surge_dir)
    if start or end:                                           # 같은 기간에 함께 오른 키워드
        s, e = period.resolve_period("1m", start, end, h["series"][-1][0] if h["series"] else None)
        table = period.period_table(rank_dir, s, e, surge_dir=None, with_series=False)
        h["companions"] = period.companions(kw, table)
        h["period"] = {"start": s, "end": e}
    has = _period_has_link()
    h["has_link"] = has(kw) if has else None
    h["source"] = {"kind": kind, "note": period.source_note(kind, rank_dir)}
    return h


@router.get("/admin/api/trends/forecast/events")
def trends_forecast_events(request: Request, days: int = Query(35, ge=7, le=120)):
    """행사 달력(data/event_calendar.csv) — 행사 목록(연속 행사군 포함)과 앞으로 days 일 안의 행사(D-day). 자료가 있는 연도도 함께."""
    from app.services.trends import period
    from app.services.trends.forecast import calendar as cal
    from app.services.trends.forecast import events as ev

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, _ = _period_dirs()
    cov = period.coverage(rank_dir, None)
    years = []
    if cov["rank"]:
        years = sorted({int(d[:4]) for d in period.rank_files(rank_dir)})
    rows = cal.load()
    events = cal.events(rows, types=("fixed", "lunar", "computed", "solar_term"))
    for name, (a, b) in ev.GROUPS.items():                       # 연속 행사군 (복날 등) — 시작 행사 날짜로 보임
        occ = ev.group_occurrences(name, rows)
        if occ:
            events.append({"event": name, "type": "group", "category": "행사군", "note": f"{a}~{b}",
                           "dates": {y: d[0].isoformat() for y, d in occ.items()}})
    events.sort(key=lambda e: min(d[5:] for d in e["dates"].values()))
    return {"ok": bool(rows), "events": events, "upcoming": cal.upcoming(date.today(), days, rows),
            "data_years": years, "coverage": cov, "source": {"kind": kind, "note": period.source_note(kind, rank_dir)}}


@router.get("/admin/api/trends/forecast/event")
def trends_forecast_event(request: Request, event: str = Query(..., min_length=1, max_length=40),
                          years: str | None = Query(None, pattern=r"^\d{4}(,\d{4})*$"),
                          as_of: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                          seeds: str | None = Query(None, max_length=400), limit: int = Query(60, ge=1, le=300),
                          coupang: int = Query(0, ge=0, le=1)):
    """행사 선행 곡선 — 행사 전에 100위 안으로 들어오고 행사 뒤 나가는 '반복 패턴' 키워드와 상대일 곡선(−35…+14).
    as_of(기준일, 기본 오늘) 뒤 자료는 읽지 않고, 이탈 구간이 기준일 전에 끝난 해만 판정(정보 누출 방지).
    coupang=1 이면 반복·후보 키워드의 쿠팡 파트너스 상품 후보 수를 함께 (쿠팡 호출 — 느림)."""
    from app.services.trends import period
    from app.services.trends.forecast import calendar as cal
    from app.services.trends.forecast import events as ev

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    rows = cal.load()
    occ = ev.group_occurrences(event.strip(), rows)
    if not occ:
        raise HTTPException(404, "달력에 없는 행사예요")
    today = date.fromisoformat(as_of) if as_of else date.today()
    ys = [int(y) for y in years.split(",")] if years else sorted(occ)
    seed_list = [s.strip() for s in (seeds or "").split(",") if s.strip()]
    rep = ev.event_report(event.strip(), rank_dir, sorted(ys), rows=rows, seeds=seed_list, limit=limit, as_of=today)
    nxt = min((d for d, _ in occ.values() if d > today), default=None)
    rep["next"] = {"date": nxt.isoformat(), "d_day": (nxt - today).days,
                   "forecast": ev.forecast_from_report(rep, nxt)} if nxt else None
    has = _period_has_link()
    cp = _coupang_links([r["keyword"] for r in rep["keywords"] if r["grade"] != "씨앗"]) if coupang else None
    for r in rep["keywords"]:
        r["has_link"] = has(r["keyword"]) if has else None            # 네이버 쇼핑커넥트 등록부
        r["coupang"] = None if cp is None else len(cp.get(r["keyword"]) or [])   # 쿠팡 파트너스 상품 후보 수
    rep["source"] = {"kind": kind, "note": period.source_note(kind, rank_dir)}
    rep["guest"] = not request_ok(request)
    return rep


# ── 가격 레이어 (2026-11-19 밤, 연구 §9) ─────────────────────────────────────────────
OVERSEAS_QUERY = {"올리브유": "extra virgin olive oil", "커피 원두": "coffee beans", "카카오·초콜릿": "dark chocolate",
                  "견과류": "almonds", "밀가루·파스타": "pasta"}


def _fx(fx_usd: float | None, fx_eur: float | None) -> dict:
    """환율 — 질의값 > 환경 변수(FX_USD_KRW·FX_EUR_KRW). 자동 조회는 다음 단계(출처·날짜를 함께 보관해야 해서)."""
    import os

    usd = fx_usd or _float(os.getenv("FX_USD_KRW"))
    eur = fx_eur or _float(os.getenv("FX_EUR_KRW"))
    src = "질의값" if fx_usd else ("환경 변수 FX_USD_KRW" if usd else None)
    return {k: v for k, v in (("USD", usd), ("EUR", eur)) if v} | {"source": src, "date": date.today().isoformat()}


def _float(v) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _domestic_products(keywords: list[str], limit: int = 8) -> list[dict]:
    """국내 상품(쿠팡 파트너스 공통 검색 picks) — {title, price, weight_g, per100g, url}. 실패하면 빈 목록."""
    from app.services.trend_posts import wiring

    out = []
    for kw in keywords:
        try:
            res = wiring.find_products(kw)
        except Exception:  # noqa: BLE001
            continue
        for it in (res or {}).get("items") or []:
            if it.get("section") != "picks":
                continue
            offer, prod = it.get("offer") or {}, it.get("product") or {}
            if not offer.get("product_url") or not offer.get("price_krw"):
                continue
            out.append({"title": prod.get("title") or "", "price": offer["price_krw"], "weight_g": prod.get("weight_g"),
                        "per100g": offer.get("per100g_krw"), "url": offer["product_url"], "keyword": kw,
                        "seen_at": offer.get("seen_at")})
        if len(out) >= limit:
            break
    return out[:limit]


def _ucp_foreign(query: str, limit: int = 8) -> dict:
    """등록부(사용·시험) 판매자에게 검색해 **외화 옵션**만 모은다 — 직구 견적 입력. 판매자별 실패는 격리."""
    try:
        import requests

        from app.services.ucp import client, discovery, registry
        from app.services.trends.forecast import overseas
    except Exception as e:  # noqa: BLE001
        return {"variants": [], "errors": [f"UCP 모듈 없음 ({e})"]}
    variants, errors = [], []
    for m in registry.load(states=("사용", "시험")):
        try:
            merchant = discovery.discover(m["host"], http=requests)
            res = client.search(merchant, query, http=requests, limit=limit)
            if not res.ok or not isinstance(res.response, dict):
                errors.append(f"{m['host']}: {res.error or res.code}")
                continue
            variants.extend(overseas.foreign_variants(res.response, m["host"]))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{m['host']}: {type(e).__name__}")
    return {"variants": variants[:limit], "errors": errors}


@router.get("/admin/api/trends/forecast/prices")
def trends_forecast_prices(request: Request, as_of: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$")):
    """감시 품목 전체 — 현재 위치(52주 백분위·1개월·1년 대비)·4주 전망(전년 같은 시기)·매수 시점 판정·켜진 동인.
    공공 시세(KAMIS 소매)만으로 판정. 백필(scripts/backfill_kamis_history.py) 전에는 일별 파일의 네 점만 써서 대부분 '보류'."""
    from app.services.trends.forecast import prices as pr

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    today = date.fromisoformat(as_of) if as_of else date.today()
    rows, src = pr.rows_for_analysis()
    days = sorted({r["date"] for r in rows})
    return {"ok": bool(rows), "as_of": today.isoformat(), "source": src,
            "history": {"backfilled": pr.HISTORY.exists(), "rows": len(rows), "days": len(days),
                        "first": days[0].isoformat() if days else None, "last": days[-1].isoformat() if days else None},
            "items": pr.summary(today, rows=rows, source=src), "signals": pr.signals()[-20:],
            "thresholds": {"low_pct": pr.LOW_PCT, "high_pct": pr.HIGH_PCT, "up": pr.UP, "down": pr.DOWN,
                           "min_years": pr.MIN_YEARS, "min_obs_52w": pr.MIN_OBS_52W},
            "guest": not request_ok(request)}


@router.get("/admin/api/trends/forecast/price")
def trends_forecast_price(request: Request, item: str = Query(..., min_length=1, max_length=40),
                          as_of: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                          coupang: int = Query(0, ge=0, le=1), ucp: int = Query(0, ge=0, le=1),
                          fx_usd: float | None = Query(None, gt=0), fx_eur: float | None = Query(None, gt=0),
                          origin: str = Query("US", pattern=r"^[A-Z]{2}$")):
    """감시 품목 하나 — 1년 시세·행사(김장·추석) 상대일 곡선(해마다)·전망·판정·동인.
    coupang=1: 국내 상품(쿠팡 파트너스) 가격 · ucp=1: UCP 판매자(Shopify 등) 외화 상품 → 직구 도착 추정가 → 100g당 비교.
    환율은 fx_usd/fx_eur 또는 FX_USD_KRW 환경 변수 — 없으면 견적을 내지 않는다. 직구 견적은 참고용(식품 구매대행 영업등록 전)."""
    from app.services.trends.forecast import calendar as cal
    from app.services.trends.forecast import overseas as ov
    from app.services.trends.forecast import prices as pr

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    row = next((r for r in pr.watchlist() if r["item"] == item.strip()), None)
    if not row:
        raise HTTPException(404, "감시 품목에 없어요 (data/price_watchlist.csv)")
    today = date.fromisoformat(as_of) if as_of else date.today()
    rows, src = pr.rows_for_analysis()
    rep = pr.item_report(row, rows, today, cal_rows=cal.load(), source=src)
    rep["domestic"] = _domestic_products(rep["keywords"][:2]) if (coupang or ucp) else None   # 직구 견적은 국내와 견줘야 뜻이 있음
    rep["overseas_quotes"] = None
    rep["compare"] = None
    if ucp:
        if row.get("overseas") != "quote":
            rep["overseas_quotes"] = {"variants": [], "errors": [], "blocked": row.get("overseas_note") or "직구 대상 아님"}
        else:
            fx = _fx(fx_usd, fx_eur)
            found = _ucp_foreign(OVERSEAS_QUERY.get(row["item"], rep["keywords"][0] if rep["keywords"] else row["item"]))
            quotes = [ov.quote(v, group=row.get("group", ""), item=row["item"], fx=fx, origin=origin)
                      for v in found["variants"]]
            rep["overseas_quotes"] = {"fx": fx, "quotes": quotes, "errors": found["errors"],
                                      "note": ov.ESTIMATE_NOTE if quotes else ("환율 없음 — fx_usd 또는 FX_USD_KRW" if "USD" not in fx else None)}
            rep["compare"] = ov.compare(quotes, rep["domestic"] or [])
    rep["guest"] = not request_ok(request)
    return rep


@router.post("/admin/api/trends/run", dependencies=[api])
def trends_run():
    """Makes today's report in the background (DataLab · blog search · DeepSeek) — about 1~3 minutes."""
    from app.services.trends import surge

    with _TREND_LOCK:
        if _TREND_JOB["running"]:
            return {"started": False, "job": dict(_TREND_JOB)}
        _TREND_JOB.update(running=True, error=None)

    def work():
        try:
            surge.run_from_env(db=_db())
            _TREND_JOB["error"] = None
        except Exception as exc:  # noqa: BLE001
            _TREND_JOB["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        finally:
            _TREND_JOB.update(running=False, finished=date.today().isoformat())

    _threading.Thread(target=work, daemon=True, name="trend-surge").start()
    return {"started": True, "job": dict(_TREND_JOB)}


class _DraftIn(BaseModel):
    date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    keywords: list[str] | None = Field(None, max_length=5)
    with_coupang: bool = True        # 2026-11-17: 키워드마다 쿠팡 파트너스 링크를 쇼핑커넥트 자리 앞에
    template: str | None = Field(None, pattern=r"^\d{2}$")    # 2026-11-20 쿠팡용 글 틀 번호 (없으면 주제별 기본)
    hold: bool = False               # 2026-11-20 구매 보류 결론 — 쿠팡용에 링크·고지를 넣지 않는다


@router.post("/admin/api/trends/blog-draft", dependencies=[api])
def trends_blog_draft(body: _DraftIn):
    """Text drafts for the applesodda blog (temporary save is done by a person / on request — never published here).

    2026-11-17: 두 판을 함께 만든다 — 'naver'(네이버 블로그용: 쇼핑커넥트 삽입 자리·고지, 쿠팡 없음)와
    'coupang'(쿠팡용: 쿠팡 링크·고지만, 쇼핑커넥트 없음).  위쪽 필드는 예전처럼 네이버 블로그용."""
    from app.services.trends import surge

    report = surge.load(body.date)
    if not report:
        raise HTTPException(404, "리포트가 없어요. 먼저 리포트를 만들어 주세요.")
    try:
        first = surge.blog_draft(report, body.keywords)
        coupang = _coupang_links(first["keywords"]) if body.with_coupang else None
        recipes = _blog_recipes(report, first["keywords"], coupang or {}, body.template)
        drafts = {"naver": surge.blog_draft(report, body.keywords, variant="naver",
                                            connect_ok=blog_connect_approved()),
                  "coupang": surge.blog_draft(report, body.keywords, coupang=coupang or {}, variant="coupang",
                                              recipes=recipes, template=body.template, hold=body.hold)}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    keywords = drafts["naver"]["keywords"]
    # 2026-11-02: 초안 키워드 중 쇼핑커넥트 링크 발급이 필요한 것 — 파일 맨 위 운영 메모 + 화면 표시 (본문에는 넣지 않음)
    needs = _link_needs(keywords)
    missing = [k for k in keywords if coupang is not None and not coupang.get(k)]
    folder = surge.ROOT / "var" / "blog_drafts"
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"trend_{report['data_until']}_{'_'.join(keywords)[:40]}"
    for variant, d in drafts.items():
        memo = _operator_memo(needs) if variant == "naver" else ""
        extra = []
        if missing and variant == "coupang":                  # 운영 메모 안(구분선 위)에 — 블로그에 붙일 본문에는 넣지 않는다
            extra.append("쿠팡 링크를 찾지 못한 키워드(주류는 넣지 않음): " + ", ".join(missing))
        if variant == "coupang" and d.get("templates"):       # 2026-11-20 글 틀
            extra.append("글 틀: " + " · ".join(f"{k} {t['id']} {t['name']}({t['kind_label']})"
                                               + (f" — {t['note']}" if t["note"] else "")
                                               for k, t in d["templates"].items()))
        for line in extra:
            head, _, last = memo.rpartition("\n")          # 마지막 줄 = 구분선
            memo = f"{head}\n{line}\n{last}" if memo else f"{MEMO_HEAD}\n{line}\n{MEMO_RULE}"
        path = folder / (f"{stem}.txt" if variant == "naver" else f"{stem}_쿠팡용.txt")
        path.write_text(_draft_text(memo, d["title"], d["tags"], d["body"]), encoding="utf-8")
        d["file"] = str(path.relative_to(surge.ROOT))
    out = drafts["naver"]
    return {**out, "link_needs": needs, "drafts": drafts,
            "coupang": None if coupang is None else {k: len(coupang.get(k) or []) for k in keywords}}


def blog_connect_approved(env=None) -> bool:
    """네이버 쇼핑커넥트 블로그 사용 승인 뒤 운영자가 켠다 (.env SC_BLOG_APPROVED=1) — 켜야 네이버용 초안에 쇼핑커넥트 고지."""
    import os

    source = os.environ if env is None else env
    return (source.get("SC_BLOG_APPROVED") or "0").strip() == "1"


MEMO_HEAD = "[운영 메모 — 블로그에 붙여 넣지 마세요]"
MEMO_RULE = "─" * 30
_DRAFT_FILE = re.compile(r"^var/blog_drafts/trend_[^/\\]{1,160}\.txt$")


def _draft_text(memo: str, title: str, tags: list[str], body: str) -> str:
    return (memo + "\n\n" if memo else "") + f"{title}\n\n태그: {', '.join(tags)}\n\n{body}\n"


class _DraftSaveIn(BaseModel):
    file: str = Field(..., max_length=200)
    title: str = Field(..., min_length=1, max_length=200)
    tags: list[str] = Field(default_factory=list, max_length=30)
    body: str = Field(..., min_length=1, max_length=50_000)


@router.post("/admin/api/trends/blog-draft/save", dependencies=[api])
def trends_blog_draft_save(body: _DraftSaveIn):
    """고친 초안 저장 (2026-11-17) — 같은 파일에 덮어쓰고 맨 위 운영 메모는 그대로 둔다.  발행하지 않는다.
    광고 고지가 빠졌는지 등은 막지 않고 경고로 알린다 (고치는 중에도 저장할 수 있게)."""
    from app.services.trends import surge

    folder = (surge.ROOT / "var" / "blog_drafts").resolve()
    path = (surge.ROOT / body.file).resolve()
    if not _DRAFT_FILE.match(body.file) or path.parent != folder or not path.is_file():
        raise HTTPException(404, "초안 파일을 찾을 수 없어요.")
    old = path.read_text(encoding="utf-8")
    memo = old.split("\n\n", 1)[0] if old.startswith(MEMO_HEAD) else ""
    tags = [t.strip().lstrip("#") for t in body.tags if t.strip()][:30]
    path.write_text(_draft_text(memo, body.title.strip(), tags, body.body.rstrip()), encoding="utf-8")
    return {"file": body.file, "saved": True, "warnings": _draft_warnings(body.file, body.body)}


def _parse_draft(text: str) -> dict:
    """초안 파일 → {title, tags, body} (맨 위 운영 메모는 빼고)."""
    if text.startswith(MEMO_HEAD):
        text = text.split("\n\n", 1)[1] if "\n\n" in text else ""
    title, _, rest = text.partition("\n\n")
    tags_line, _, body = rest.partition("\n\n")
    tags = [t.strip() for t in tags_line.removeprefix("태그:").split(",") if t.strip()] if tags_line.startswith("태그:") \
        else []
    if not tags_line.startswith("태그:"):
        body = rest
    return {"title": title.strip(), "tags": tags, "body": body.rstrip("\n")}


@router.get("/admin/api/trends/blog-drafts", dependencies=[api])
def trends_blog_drafts():
    """저장된 초안 목록 (2026-11-17) — 같은 날짜·키워드로 만든 네이버 블로그용·쿠팡용을 한 줄(짝)로, 최근에 고친 짝이 위."""
    from app.services.trends import surge

    folder = surge.ROOT / "var" / "blog_drafts"
    pairs: dict[str, dict] = {}
    for p in (folder.glob("trend_*.txt") if folder.is_dir() else []):
        rel = str(p.relative_to(surge.ROOT))
        if not _DRAFT_FILE.match(rel):
            continue
        variant = "coupang" if p.name.endswith(COUPANG_SUFFIX) else "naver"
        stem = rel[:-len(COUPANG_SUFFIX)] if variant == "coupang" else rel[:-len(".txt")]
        pair = pairs.setdefault(stem, {"stem": stem, "name": Path(stem).name.removeprefix("trend_"), "files": {},
                                       "mtime": 0.0})
        pair["files"][variant] = rel
        pair["mtime"] = max(pair["mtime"], p.stat().st_mtime)
    items = sorted(pairs.values(), key=lambda x: x["mtime"], reverse=True)[:60]
    for it in items:
        it["modified"] = date.fromtimestamp(it.pop("mtime")).isoformat()
    return {"items": items}


@router.get("/admin/api/trends/blog-draft/file", dependencies=[api])
def trends_blog_draft_file(file: str = Query(..., max_length=200)):
    """초안 한 벌 열기 — 짝(네이버 블로그용·쿠팡용)이 있으면 둘 다 돌려준다 ('drafts')."""
    from app.services.trends import surge

    folder = (surge.ROOT / "var" / "blog_drafts").resolve()

    def load(rel: str) -> dict | None:
        path = (surge.ROOT / rel).resolve()
        if not _DRAFT_FILE.match(rel) or path.parent != folder or not path.is_file():
            return None
        variant = "coupang" if path.name.endswith(COUPANG_SUFFIX) else "naver"
        return {**_parse_draft(path.read_text(encoding="utf-8")), "file": rel, "variant": variant}

    one = load(file)
    if one is None:
        raise HTTPException(404, "초안 파일을 찾을 수 없어요.")
    stem = file[:-len(COUPANG_SUFFIX)] if one["variant"] == "coupang" else file[:-len(".txt")]
    drafts = {"naver": load(stem + ".txt"), "coupang": load(stem + COUPANG_SUFFIX)}
    return {**one, "drafts": {k: v for k, v in drafts.items() if v}}


COUPANG_SUFFIX = "_쿠팡용.txt"


# ── 블로그 초안 승인 → 네이버 임시저장 (2026-11-20) ────────────────────────────
class _DraftApproveIn(BaseModel):
    file: str = Field(..., max_length=200)
    with_image: bool = False          # gpt-image 보조 그림 1장 (유료, 캡션 앞에 'AI로 만든 그림')


def _draft_path_or_404(rel: str) -> Path:
    from app.services.trends import surge

    folder = (surge.ROOT / "var" / "blog_drafts").resolve()
    path = (surge.ROOT / rel).resolve()
    if not _DRAFT_FILE.match(rel) or path.parent != folder or not path.is_file():
        raise HTTPException(404, "초안 파일을 찾을 수 없어요.")
    return path


@router.post("/admin/api/trends/blog-draft/approve", dependencies=[api])
def trends_blog_draft_approve(body: _DraftApproveIn):
    """관리자 확인 완료 → 네이버 블로그 임시저장 (발행 안 함). 저장된 내용 그대로 쓴다 — 고친 뒤에는 먼저 '저장'.
    .env BLOG_AUTODRAFT=1 일 때만. 검사(광고 표시·고지 위치·남은 안내·사용 후기 표현)에 걸리면 시작하지 않는다."""
    from app.services.trends import blog_autosave as bas, surge

    if not bas.enabled():
        raise HTTPException(400, "자동 임시저장이 꺼져 있어요 (.env BLOG_AUTODRAFT=1).")
    if not bas.mcp_python().is_file():
        raise HTTPException(400, f"네이버 블로그 도구를 찾지 못했어요: {bas.mcp_dir()} (.env NAVER_BLOG_MCP_DIR)")
    path = _draft_path_or_404(body.file)
    d = _parse_draft(path.read_text(encoding="utf-8"))
    variant = "coupang" if path.name.endswith(COUPANG_SUFFIX) else "naver"
    issues = bas.check(variant, d["title"], d["body"], _draft_warnings(body.file, d["body"]), surge.COUPANG_DISCLOSURE)
    if issues:
        raise HTTPException(400, {"message": "확인이 필요한 곳이 있어 임시저장을 시작하지 않았어요.", "issues": issues})
    keywords = [t for t in d["tags"] if t not in ("트렌드리포트", "요즘뜨는식품", "쿠팡파트너스", "쇼핑커넥트")] or [d["title"]]
    rec = bas.start(path, variant=variant, title=d["title"], tags=d["tags"], body=d["body"], keywords=keywords,
                    with_image=body.with_image)
    return {"file": body.file, "approval": rec}


@router.get("/admin/api/trends/blog-draft/approval", dependencies=[api])
def trends_blog_draft_approval(file: str = Query(..., max_length=200)):
    from app.services.trends import blog_autosave as bas

    path = _draft_path_or_404(file)
    return {"file": file, "approval": bas.read_approval(path), "enabled": bas.enabled()}


def _draft_warnings(file: str, text: str) -> list[str]:
    from app.services.trends import surge

    out = []
    if ("coupang.com" in text or "coupa.ng" in text) and surge.COUPANG_DISCLOSURE not in text:
        out.append("쿠팡 링크가 있는데 쿠팡 파트너스 대가성 문구가 없어요. 맨 위에 넣어 주세요.")
    if (file.endswith("_쿠팡용.txt") or not blog_connect_approved()) and "쇼핑 커넥트 활동" in text:
        out.append("쇼핑커넥트 고지 문구가 있어요. 쿠팡용 초안이거나 승인 전(SC_BLOG_APPROVED 꺼짐)이면 빼 주세요.")
    if "▶ [여기에" in text:
        out.append("'▶ [여기에 …]' 삽입 자리 안내가 남아 있어요. 올리기 전에 상품을 넣거나 지워 주세요.")
    return out


def _coupang_links(keywords: list[str]) -> dict[str, list[dict]]:
    """키워드마다 쿠팡 파트너스 상품 링크 (공통 검색 picks 순서 그대로, 제휴 링크만, 주류 제외). 실패하면 빈 목록."""
    from app.services.trend_posts import draft as post_draft, policy, wiring
    from app.services.trends import surge

    out: dict[str, list[dict]] = {}
    for kw in keywords:
        if policy.is_alcohol(kw):
            out[kw] = []
            continue
        try:
            found = post_draft.products_from_result(wiring.find_products(kw), keyword=kw)
        except Exception:  # noqa: BLE001 — 쿠팡을 못 불러도 초안은 만든다
            found = []
        out[kw] = [{"title": p.title, "url": p.url, "rocket": p.rocket} for p in found
                   if p.link_type == "affiliate"][:surge.COUPANG_PER_KEYWORD]
    return out


def _blog_recipes(report: dict, keywords: list[str], coupang: dict, override: str | None) -> dict:
    """레시피 틀(26)을 쓸 수 있는 키워드만 공공 레시피를 찾는다 (실패해도 초안은 만든다 — 그러면 다른 틀로)."""
    from app.services.trend_posts import draft as post_draft, templates, wiring

    status = {it["keyword"]: it.get("status") for it in report.get("items") or []}
    out = {}
    for kw in keywords:
        kind = templates.frame.keyword_type(kw, status=status.get(kw))
        if override != "26" and "26" not in templates.candidates(kw, kind)[:1]:
            continue
        try:
            out[kw] = post_draft.recipe_from_result(wiring.find_recipe(kw), kw)
        except Exception:  # noqa: BLE001
            out[kw] = None
    return out


def _link_needs(keywords: list[str]) -> dict | None:
    try:
        from app.services.affiliate import naver_shopping_connect as sc

        return sc.link_needs(keywords)
    except Exception:  # noqa: BLE001 — 확인을 못 해도 초안은 만든다
        return None


def _operator_memo(needs: dict | None) -> str:
    if not needs:
        return ""
    from app.services.affiliate import naver_shopping_connect as sc

    return sc.operator_memo(needs)


# ── 쇼핑커넥트 발급 요청 (2026-11-02) — 등록 링크가 없는 검색어·급상승 식품 ─────────────
class _ConnectStatusIn(BaseModel):
    status: str = Field(..., pattern=r"^(open|issued|skipped)$")


@router.get("/admin/api/connect/requests", dependencies=[api])
def connect_requests(status: str = Query("open", pattern=r"^(open|issued|skipped)$"),
                     limit: int = Query(50, ge=1, le=200)):
    import os

    from app.services.affiliate import naver_shopping_connect as sc

    items = sc.with_db(sc.list_requests, status, limit)
    return {"items": items, "status": status, "queue_on": os.getenv("SC_REQUEST_QUEUE", "0") == "1"}


@router.post("/admin/api/connect/requests/{req_id}", dependencies=[api])
def connect_request_status(req_id: int, body: _ConnectStatusIn):
    from app.services.affiliate import naver_shopping_connect as sc

    if not sc.with_db(sc.set_request_status, req_id, body.status):
        raise HTTPException(409, "바꾸지 못했어요. 이미 정리됐거나 같은 키워드의 열린 요청이 있어요.")
    return {"ok": True}


# ── 쇼핑커넥트 링크 등록부 (2026-11-17) — 관리자 화면에서 입력·삭제하면 naver_connect_links.csv 에 바로 쓴다 ──
class _LinkIn(BaseModel):
    keyword: str = Field("", max_length=60)
    product_name: str = Field("", max_length=200)
    store_name: str = Field("", max_length=80)
    price: str | int | None = None              # 브랜드커넥트 화면의 '판매가' (할인 전)
    discount_price: str | int | None = None     # 브랜드커넥트 화면의 '할인가' (2026-11-17)
    commission_rate: str | float | None = None
    link: str = Field("", max_length=300)
    memo: str = Field("", max_length=200)


class _LinksIn(BaseModel):
    rows: list[_LinkIn] = Field(..., min_length=1, max_length=30)
    request_id: int | None = None          # 발급 요청 줄에서 열었으면 저장 뒤 '발급 완료'로 정리


@router.get("/admin/api/connect/links", dependencies=[api])
def connect_links_list():
    from app.services.affiliate import connect_registry as reg

    from app.services.affiliate import brandconnect_finder as bf

    rows = reg.rows()
    items = []
    for r in reversed(rows):                 # 브랜드커넥트 수집분이 이 링크를 다른 상품 것으로 알면 표시 (2026-11-18)
        owner = bf.link_owner(r.get("쇼핑커넥트 링크") or "")
        mismatch = bool(owner) and not bf.same_product(owner["title"] or "", r.get("상품명") or "")
        items.append({**r, "_owner": owner if mismatch else None})
    return {"items": items, "count": len(rows), "file": str(reg.path().name)}


@router.post("/admin/api/connect/links", dependencies=[api])
def connect_links_add(body: _LinksIn):
    from app.services.affiliate import connect_registry as reg
    from app.services.affiliate import naver_shopping_connect as sc

    from app.services.affiliate import brandconnect_finder as bf

    res = reg.add([r.model_dump() for r in body.rows], owner_of=bf.link_owner)
    issued = False
    if res["added"]:
        if body.request_id is not None:
            issued = bool(sc.with_db(sc.set_request_status, body.request_id, "issued"))
        # 등록된 키워드의 열린 발급 요청도 정리 (CSV 가져오기와 같은 방식)
        for kw in {r["키워드"] for r in res["added"] if r["키워드"]}:
            sc.with_db(_close_open_request, kw)
    return {"added": len(res["added"]), "rejected": res["rejected"], "request_issued": issued}


def _close_open_request(conn, keyword: str) -> None:
    from app.services.affiliate import naver_shopping_connect as sc

    conn.execute("UPDATE sc_link_requests SET status='issued', updated_at=? WHERE keyword=? AND status='open'",
                 (sc._now(), keyword))
    conn.commit()


class _LinkDeleteIn(BaseModel):
    link: str = Field(..., min_length=8, max_length=300)


@router.post("/admin/api/connect/links/delete", dependencies=[api])
def connect_links_delete(body: _LinkDeleteIn):
    from app.services.affiliate import connect_registry as reg

    if not reg.delete(body.link):
        raise HTTPException(404, "등록부에 없는 링크예요.")
    return {"ok": True}


@router.get("/admin/api/brandconnect/issued", dependencies=[api])
def brandconnect_issued(keyword: str | None = Query(None, max_length=40)):
    """발급했지만 등록부에 없는 쇼핑커넥트 링크 — 수집분(shortenUrl)에서 읽기만 한다 (2026-11-18)."""
    from app.services.affiliate import brandconnect_finder as bf
    from app.services.affiliate import connect_registry as reg

    have = {(r.get("쇼핑커넥트 링크") or "").strip() for r in reg.rows()}
    return bf.issued_links(have, keyword)


class _RefreshIn(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=40)


@router.post("/admin/api/brandconnect/issued/refresh", dependencies=[api])
def brandconnect_issued_refresh(body: _RefreshIn):
    """키워드 하나를 브랜드커넥트에서 바로 다시 읽은 뒤(읽기 전용) 등록부에 없는 발급 링크를 돌려준다 (2026-11-18 2부)."""
    from app.services.affiliate import brandconnect_finder as bf
    from app.services.affiliate import connect_registry as reg

    res = bf.refresh_keyword(body.keyword)
    have = {(r.get("쇼핑커넥트 링크") or "").strip() for r in reg.rows()}
    return {"refresh": res, **bf.issued_links(have, body.keyword)}


@router.get("/admin/api/brandconnect/find", dependencies=[api])
def brandconnect_find(keyword: str = Query(..., min_length=1, max_length=40), n: int = Query(5, ge=1, le=10),
                      exclude_health: bool = True):
    """브랜드커넥트 상품 후보 — 키워드 관련성 → 리뷰 수 → 평점 → 수수료율 순 (판매량 자료 없음)."""
    from app.services.affiliate import brandconnect_finder as bf

    return bf.find(keyword, n, exclude_health=exclude_health)


@router.post("/admin/api/connect/queue-trends", dependencies=[api])
def connect_requests_from_trends(body: _DraftIn):
    """선택한 날짜(없으면 최신) 급상승 리포트에서 등록 링크가 없는 식품을 대기열에 올린다."""
    from app.services.affiliate import naver_shopping_connect as sc
    from app.services.trends import surge

    report = surge.load(body.date)
    if not report:
        raise HTTPException(404, "리포트가 없어요. 먼저 리포트를 만들어 주세요.")
    return {"queued": sc.with_db(sc.queue_trends, report)}


@router.get("/admin/api/markets", dependencies=[api])
def markets(q: str = Query(..., min_length=1, max_length=60)):
    from app.admin.ops.markets_check import check

    return check(q.strip())


def _db():
    from app.services.chat.service import engine_db

    return engine_db()


# ── AI 비용 (2026-11-11) — 작업별·모델별 비용, 저장본 재사용으로 아낀 호출, 확인된 사실 ──
@router.get("/admin/ai")
def admin_ai(request: Request):
    return _page(request, WEB / "ai.html")


@router.get("/admin/api/ai/cost", dependencies=[api])
def ai_cost(days: int = Query(30, ge=1, le=365)):
    from app.services.ai import usage

    return usage.report(days)


@router.get("/admin/api/ai/knowledge", dependencies=[api])
def ai_knowledge():
    from app.services.ai import cache as ai_cache
    from app.services.ai import facts
    from app.services.ai import pricing

    return {"cache": [dict(x, label=pricing.TASK_LABELS.get(x["task"].split(":")[0], x["task"])) for x in ai_cache.stats()],
            "cache_on": ai_cache.enabled(), "facts": [dict(f, current=facts.current(f)) for f in facts.all_facts()],
            "prices": pricing._table(), "prices_checked": pricing.CHECKED}


# ── 추천 근거 (1단계, 2026-11-10) — 고객 화면과 같은 선택을 읽기만 하고 근거를 나눠 보여 준다 ──
@router.get("/admin/evidence")
def admin_evidence(request: Request):
    return _page(request, WEB / "evidence.html")


@router.get("/admin/api/evidence", dependencies=[api])
def evidence_report(q: str = Query(..., min_length=1, max_length=200),
                    path: str = Query("db", pattern="^(db|auto)$"),
                    priority: str | None = Query(None, pattern="^[a-z_]{1,30}$")):
    """path=db: DB 예비 경로만 (외부 API 호출 없음) · path=auto: 고객과 같은 경로 (쿠팡 API 실시간 호출)."""
    from app.admin.ops import evidence

    if path == "db":
        shopping, extractor = evidence.forced_db_shopping(), None
    else:
        from app.api.chat_routes import get_chat_service

        svc = get_chat_service()
        shopping, extractor = svc.shopping, svc.keyword_extractor
    return evidence.build_report(q, shopping=shopping, keyword_extractor=extractor, priority=priority)


@router.get("/admin/api/conversations", dependencies=[api])
def conversations(limit: int = Query(50, ge=1, le=200)):
    from app.admin.ops.conversations import list_sessions

    return list_sessions(_db(), limit=limit)


@router.get("/admin/api/clicks", dependencies=[api])
def clicks(days: int = Query(30, ge=1, le=365)):
    from app.admin.ops.conversations import click_summary

    return click_summary(_db(), days=days)


@router.get("/admin/api/conversations/{session_id}", dependencies=[api])
def conversation(session_id: str):
    from app.admin.ops.conversations import session_detail

    if len(session_id) > 64:
        raise HTTPException(400, "세션 ID가 너무 길어요")

    return session_detail(_db(), session_id)


@router.get("/admin/api/payments", dependencies=[api])
def payment_providers():
    from app.admin.ops.payments import providers

    return {"providers": providers()}


class CartItemIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    price: int = Field(..., ge=0, le=100_000_000)
    shipping_fee: int | None = Field(None, ge=0, le=1_000_000)
    quantity: int = Field(1, ge=1, le=999)
    mall: str | None = Field(None, max_length=40)


class CartIn(BaseModel):
    items: list[CartItemIn] = Field(..., min_length=1, max_length=50)


@router.post("/admin/api/cart/preview", dependencies=[api])
def cart_preview(body: CartIn):
    from app.admin.ops.payments import preview

    return preview([i.model_dump() for i in body.items])


# ── B2B 탭 ────────────────────────────────────────────────
_console = None


def console():
    global _console
    if _console is None:
        from app.admin.b2b.console import Console

        _console = Console()
    return _console


@router.get("/admin/b2b")
def b2b_console_page(request: Request):
    return _page(request, B2B_WEB / "console.html")


@router.get("/admin/b2b/monitor")
def b2b_monitor_page(request: Request):
    return _page(request, B2B_WEB / "monitor.html")


@router.get("/admin/b2b/evidence")
def b2b_evidence_page(request: Request):
    return _page(request, B2B_WEB / "evidence.html")


class RunIn(BaseModel):
    workspace_id: str | None = None
    prompt: str = Field(..., min_length=1, max_length=8000)
    today: date | None = None
    template_id: str | None = Field(None, max_length=40)


@router.post("/admin/b2b/api/run", dependencies=[api])
def b2b_run(body: RunIn):
    return console().run(body.workspace_id, body.prompt, body.today, body.template_id)


@router.get("/admin/b2b/api/bids", dependencies=[api])
def b2b_bids():
    from app.admin.b2b import bids as bidstore

    return [b.model_dump(mode="json") for b in bidstore.list_bids()]


@router.post("/admin/b2b/api/bids/upload", dependencies=[api])
async def b2b_upload(file: UploadFile = File(...)):
    from app.admin.b2b import bids as bidstore

    content = await file.read()
    if len(content) > 5_000_000:
        raise HTTPException(413, "파일이 너무 큽니다")
    try:
        n = bidstore.import_file(file.filename or "upload.json", content)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"가져오기 실패: {e}")
    return {"imported": n}


@router.get("/admin/b2b/files/{name}", dependencies=[api])
def b2b_files(name: str, dl: bool = False):
    from app.admin.b2b.console import DOCS

    p = (DOCS / name).resolve()
    if DOCS.resolve() not in p.parents or not p.exists():
        raise HTTPException(404)
    media = {".hwpx": "application/hwp+zip", ".pdf": "application/pdf"}.get(p.suffix)
    return FileResponse(p, media_type=media, headers={"Cache-Control": "no-store"},
                        filename=name if dl or p.suffix in (".docx", ".pptx", ".hwpx") else None)


@router.get("/admin/b2b/assets/{pack}/{name}", dependencies=[api])
def b2b_asset_thumb(pack: str, name: str, w: int = 160):
    """학습한 제안서 그림의 썸네일 (그림 바꾸기 화면용 · 관리자만)."""
    from app.admin.b2b import design_assets

    root = design_assets.root().resolve()
    p = (root / pack / name).resolve()
    if root not in p.parents or not p.is_file() or p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        raise HTTPException(404)
    data, media = _thumb(str(p), p.stat().st_mtime, max(48, min(w, 480)))
    return Response(data, media_type=media, headers={"Cache-Control": "private, max-age=3600"})


@lru_cache(maxsize=512)
def _thumb(path: str, mtime: float, w: int) -> tuple[bytes, str]:
    import io

    from PIL import Image

    with Image.open(path) as im:
        im.thumbnail((w, w))
        buf = io.BytesIO()
        im.convert("RGBA").save(buf, "PNG", optimize=True)
    return buf.getvalue(), "image/png"


# ── 제안서 디자인 템플릿 ───────────────────────────────────────
@router.get("/admin/b2b/templates")
def b2b_templates_page(request: Request):
    return _page(request, B2B_WEB / "templates.html")


@router.get("/admin/b2b/api/templates", dependencies=[api])
def b2b_templates():
    from app.admin.b2b import proposal_templates as T

    return {"default": T.DEFAULT_ID, "items": [T.public(t) for t in T.list_all()]}


async def _upload(f: UploadFile | None, limit_mb: int) -> tuple[str, bytes] | None:
    if f is None or not f.filename:
        return None
    data = await f.read()
    if len(data) > limit_mb * 1024 * 1024:
        raise HTTPException(400, f"{f.filename}: {limit_mb}MB 이하 파일만 올릴 수 있어요")
    return (f.filename, data) if data else None


@router.post("/admin/b2b/api/templates", dependencies=[api])
async def b2b_template_create(name: str = Form(...), description: str = Form(""), base: str = Form(""),
                              primary: str = Form(""), accent: str = Form(""), ink: str = Form(""),
                              surface: str = Form(""), font_office: str = Form(""), font_css: str = Form(""),
                              cover: str = Form("split"), motion: bool = Form(True),
                              logo: UploadFile | None = File(None), reference: UploadFile | None = File(None),
                              pptx_base: UploadFile | None = File(None)):
    from app.admin.b2b import proposal_templates as T

    try:
        t = T.create(name, description=description, base=base or None, cover=cover, motion=motion,
                     colors={"primary": primary, "accent": accent, "ink": ink, "surface": surface},
                     font_office=font_office or None, font_css=font_css or None,
                     logo=await _upload(logo, 5), reference=await _upload(reference, 10),
                     pptx_base=await _upload(pptx_base, 30))
    except ValueError as e:
        raise HTTPException(400, str(e)) from None
    return T.public(t)


@router.post("/admin/b2b/api/templates/palette", dependencies=[api])
async def b2b_template_palette(image: UploadFile = File(...)):
    from app.admin.b2b import proposal_templates as T

    up = await _upload(image, 10)
    try:
        return T.extract_palette(up[1]) if up else {}
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "이미지를 읽을 수 없어요") from None


@router.delete("/admin/b2b/api/templates/{tid}", dependencies=[api])
def b2b_template_delete(tid: str):
    from app.admin.b2b import proposal_templates as T

    try:
        T.delete(tid)
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from None
    return {"deleted": tid}


@router.get("/admin/b2b/api/templates/{tid}/preview", dependencies=[api], response_class=HTMLResponse)
def b2b_template_preview(tid: str, fmt: str = "slides"):
    """예시 제안서(가상 기관)에 템플릿을 입혀 미리보기. fmt=pptx 면 PPTX 를 내려받는다."""
    import tempfile

    from app.admin.b2b import proposal_deck as D
    from app.admin.b2b import proposal_export as X
    from app.admin.b2b import proposal_templates as T

    t = T.get(tid)
    if t.id != tid:
        raise HTTPException(404)
    if fmt == "pptx":
        out = Path(tempfile.mkdtemp()) / f"template_{t.id}_sample.pptx"
        X.to_pptx(D.sample(), out, t, D.SAMPLE_MARKET)
        return FileResponse(out, filename=out.name)
    return HTMLResponse(D.render(D.sample(), t, D.SAMPLE_MARKET), headers={"Cache-Control": "no-store"})


def _filtered(status: str, institution_type: str, bid_type: str, keyword: str, scope: str, today: date | None = None):
    from app.admin.b2b import bids as bidstore

    out = []
    for b in bidstore.list_bids():
        v = b.view(today)
        if scope == "trusted" and not v["trusted"]:
            continue
        if scope == "default" and b.verification == "legacy_unverified":
            continue
        if status != "전체" and v["status"] != status:
            continue
        if institution_type != "전체" and b.institution_type != institution_type:
            continue
        if bid_type != "전체" and v["bid_type"] != bid_type:
            continue
        if keyword and keyword not in f"{b.title} {b.agency or ''} {b.summary}":
            continue
        out.append(v)
    order = {"마감임박": 0, "입찰중": 1, "마감일 미확인": 2, "입찰마감": 3}
    out.sort(key=lambda r: (order.get(r["status"], 9), r.get("deadline") or ""))
    return out


@router.get("/admin/b2b/api/monitor/bids", dependencies=[api])
def monitor_bids(status: str = "전체", institution_type: str = "전체", bid_type: str = "전체",
                 keyword: str = "", scope: str = "default"):
    from app.admin.b2b import bids as bidstore

    rows = _filtered(status, institution_type, bid_type, keyword.strip(), scope)
    allv = [b.view() for b in bidstore.list_bids()]
    counts = {k: sum(1 for r in allv if r["verification"] == k) for k in bidstore.VERIFICATION_LABEL}
    return {"rows": rows, "verification_counts": counts}


@router.get("/admin/b2b/api/monitor/bids/{bid_id}", dependencies=[api])
def monitor_bid(bid_id: str):
    from app.admin.b2b import bids as bidstore
    from app.admin.b2b.gift_monitor import checkpoints

    b = bidstore.get(bid_id)
    if not b:
        raise HTTPException(404, "공고 없음")
    v = b.view()
    v["checkpoints"] = checkpoints.checkpoints(b.title, b.summary)
    v["requirement"] = b.requirement.model_dump(mode="json") if b.requirement else None
    return v


class ManualBid(BaseModel):
    title: str = Field(..., min_length=2, max_length=300)
    agency: str | None = None
    deadline: str | None = None
    url: str | None = None
    budget: str | None = None
    text: str = Field("", max_length=60000)


@router.post("/admin/b2b/api/monitor/bids", dependencies=[api])
def monitor_add(body: ManualBid):
    from app.admin.b2b.gift_monitor import collectors

    n = collectors.add_manual(body.title, body.agency, body.deadline, body.url, body.text, body.budget)
    return n.view()


@router.post("/admin/b2b/api/monitor/bids/{bid_id}/attachments", dependencies=[api])
async def monitor_attach(bid_id: str, file: UploadFile = File(...)):
    from app.admin.b2b.gift_monitor import collectors

    content = await file.read()
    if len(content) > 20_000_000:
        raise HTTPException(413, "파일이 너무 큽니다 (20MB 이하)")
    try:
        n = collectors.attach(bid_id, file.filename or "첨부", content)
    except KeyError:
        raise HTTPException(404, "공고 없음")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, str(e))
    return n.view()


@router.post("/admin/b2b/api/monitor/bids/{bid_id}/verify", dependencies=[api])
def monitor_verify(bid_id: str, note: str = Form("")):
    from app.admin.b2b import bids as bidstore

    try:
        return bidstore.mark_verified(bid_id, note).view()
    except KeyError:
        raise HTTPException(404, "공고 없음")
    except ValueError as e:
        raise HTTPException(400, str(e))


class CollectIn(BaseModel):
    days: int = Field(14, ge=1, le=90)
    keywords: list[str] | None = None


@router.post("/admin/b2b/api/monitor/collect", dependencies=[api])
def monitor_collect(body: CollectIn):
    from app.admin.b2b.gift_monitor import collectors

    return collectors.collect_all(body.days, body.keywords)


@router.get("/admin/b2b/api/monitor/trends", dependencies=[api])
def monitor_trends(include_legacy: bool = False, include_unverified: bool = True):
    from app.admin.b2b.gift_monitor import trends

    return trends.analyze(include_unverified=include_unverified, include_legacy=include_legacy)


@router.get("/admin/b2b/api/monitor/evaluator", dependencies=[api])
def evaluator_form():
    from app.admin.b2b.gift_monitor import checkpoints

    return checkpoints.eval_form()


class EvalIn(BaseModel):
    answers: dict[str, str]
    weights: dict[str, float] | None = None


@router.post("/admin/b2b/api/monitor/evaluator", dependencies=[api])
def evaluator_run(body: EvalIn):
    from app.admin.b2b.gift_monitor import checkpoints

    return checkpoints.evaluate(body.answers, body.weights)


@router.get("/admin/b2b/api/monitor/export.xlsx", dependencies=[api])
def monitor_export(status: str = "전체", institution_type: str = "전체", bid_type: str = "전체",
                   keyword: str = "", scope: str = "default"):
    import io as _io

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    rows = _filtered(status, institution_type, bid_type, keyword.strip(), scope)
    wb = Workbook()
    ws = wb.active
    ws.title = "선물입찰"
    head = ["상태", "신뢰 등급", "기관명", "기관 유형", "공고명", "유형(규칙 분류)", "예산(원)", "예산 원문",
            "공고일", "마감일", "담당부서", "담당자", "연락처", "출처", "원문 링크"]
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="EEF1F4")
    for r in rows:
        ws.append([r["status"], r["verification_label"], r.get("agency"), r.get("institution_type"), r["title"],
                   r["bid_type"], r.get("budget"), r.get("budget_text"), r.get("posted"), r.get("deadline"),
                   r.get("department"), r.get("manager"), r.get("contact"), r.get("source"), r.get("url")])
    for col, w in zip("ABCDEFGHIJKLMNO", (10, 14, 18, 12, 50, 20, 14, 18, 12, 18, 14, 10, 14, 22, 40)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    buf = _io.BytesIO()
    wb.save(buf)
    return Response(buf.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote("B2B_선물입찰_모니터.xlsx")})


# ── 트렌드 글 검토 대기열 (2단계, 2026-11-16) ──────────────────────────
# 급상승 리포트 → 초안 → 검토 요청 → 승인(정책 검사 통과 시) → /trends 게시.  자동 게시 없음.
def _trend_posts():
    from app.services.trend_posts.service import TrendPosts

    return TrendPosts()


def _post_out(svc, post) -> dict:
    from app.services.trend_posts.model import STATUS_LABEL
    from app.services.trend_posts.render import post_url

    return {**post.model_dump(mode="json"), "status_label": STATUS_LABEL[post.status],
            "issues": svc.check(post), "public_url": post_url(post) if post.status == "approved" else None}


def _post_call(fn, *args):
    from app.services.trend_posts.service import PostError

    try:
        return fn(*args)
    except PostError as exc:
        status = 404 if exc.code == "not_found" else 409 if exc.code in ("bad_status", "exists", "not_editable",
                                                                         "policy") else 400
        raise HTTPException(status, {"message": str(exc), "code": exc.code, "issues": exc.issues}) from exc


@router.get("/admin/trend-posts")
def admin_trend_posts(request: Request):
    return _page(request, WEB / "trend_posts.html")


@router.get("/admin/api/trend-posts", dependencies=[api])
def trend_posts_list(status: str | None = Query(None, pattern=r"^(draft|pending|approved|rejected|withdrawn)$")):
    svc = _trend_posts()
    posts = svc.store.by_status(status) if status else svc.store.all()
    counts: dict[str, int] = {}
    for p in svc.store.all():
        counts[p.status] = counts.get(p.status, 0) + 1
    return {"items": [_post_out(svc, p) for p in posts], "counts": counts}


@router.get("/admin/api/trend-posts/{post_id}", dependencies=[api])
def trend_posts_get(post_id: str):
    svc = _trend_posts()
    return _post_out(svc, _post_call(svc.get, post_id))


class _PostDraftIn(BaseModel):
    date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    keyword: str = Field(..., min_length=1, max_length=40)
    with_products: bool = True
    template: str | None = Field(None, pattern=r"^\d{2}$")    # 2026-11-20 글 틀 번호 (없으면 주제별 기본)


@router.post("/admin/api/trend-posts/draft", dependencies=[api])
def trend_posts_draft(body: _PostDraftIn):
    from app.services.trend_posts import wiring
    from app.services.trends import surge

    report = surge.load(body.date)
    if not report:
        raise HTTPException(404, "리포트가 없어요. 먼저 리포트를 만들어 주세요.")
    svc = _trend_posts()
    post, created = _post_call(lambda: svc.create_from_surge(
        report, body.keyword, find_products=wiring.find_products if body.with_products else None,
        find_recipe=wiring.find_recipe, template=body.template))
    return {**_post_out(svc, post), "created": created}


class _PostEditIn(BaseModel):
    fields: dict


class _PostNoteIn(BaseModel):
    note: str | None = Field(None, max_length=500)


@router.post("/admin/api/trend-posts/{post_id}/update", dependencies=[api])
def trend_posts_update(post_id: str, body: _PostEditIn):
    svc = _trend_posts()
    try:
        post = _post_call(svc.update, post_id, body.fields)
    except ValueError as exc:                    # 칸 모양이 틀림 (pydantic)
        raise HTTPException(400, {"message": "칸 모양이 맞지 않아요.", "detail": str(exc)[:300]}) from exc
    return _post_out(svc, post)


@router.post("/admin/api/trend-posts/{post_id}/refresh", dependencies=[api])
def trend_posts_refresh(post_id: str):
    from app.services.trend_posts import wiring

    svc = _trend_posts()
    return _post_out(svc, _post_call(svc.refresh_products, post_id, wiring.find_products))


@router.post("/admin/api/trend-posts/{post_id}/{action}", dependencies=[api])
def trend_posts_action(post_id: str, action: str, body: _PostNoteIn | None = None):
    svc = _trend_posts()
    note = body.note if body else None
    calls = {"submit": lambda: svc.submit(post_id), "approve": lambda: svc.approve(post_id, note),
             "reject": lambda: svc.reject(post_id, note or ""), "withdraw": lambda: svc.withdraw(post_id, note),
             "reopen": lambda: svc.reopen(post_id)}
    if action not in calls:
        raise HTTPException(404, "없는 동작이에요.")
    return _post_out(svc, _post_call(calls[action]))


@router.get("/admin/trend-posts/{post_id}/preview")
def trend_posts_preview(post_id: str, request: Request):
    """승인 전 미리 보기 (관리자만, 검색 노출 차단).  공개 페이지와 같은 그리기 — 상품 링크는 눌러도 공개 쪽에서 막힌다."""
    if not request_ok(request):
        return RedirectResponse("/admin/login?next=" + quote(request.url.path), status_code=303)
    from app.services.trend_posts import render

    svc = _trend_posts()
    post = _post_call(svc.get, post_id)
    html = render.post_page(post, svc.clock()).replace(
        "<main>", '<main><p class=ad>미리 보기 — 아직 공개되지 않은 글이에요 (' + post.status + ")</p>", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"})
