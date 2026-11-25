"""관리자 백엔드 (/admin) — 로그인 1곳, 탭 2개.

  운영 탭   /admin                 판매처 API 점검 · 대화·추천 기록 · 장바구니·결제 뼈대
            (integrated_system 의 소비자 백엔드 consumer/app.py 에서 옮김, 2026-10-29)
  트렌드 탭 /admin/trends          검색량 급상승 리포트 (데이터랩 급상승 → 블로그 탐지 → 구글 트렌드 → 교차 확인)
                                   · 블로그 초안(applesodda 임시저장용 텍스트) — 2026-10-31
                                   · 쇼핑커넥트 발급 요청 목록(발급 완료·건너뛰기) — 2026-11-02
  개선 탭   /admin/improve         주간 지표 · 점검 후보 · 확인 결과 · 고침 기록 — 2026-11-23 (3-D ④)
  AI 탭     /admin/ai              AI 비용 (작업별·모델별, 저장본 재사용으로 아낀 호출) · 확인된 사실 — 2026-11-11
  B2B 탭    /admin/b2b             B2B 콘솔 (자연어 지시 → 공고 분석 · 후보 · 원가 · 견적요청서 · 제안서)
            /admin/b2b/monitor     선물 입찰 모니터 · 트렌드 · 평가표 · 엑셀
            /admin/b2b/evidence    공급사 근거 (commerce 의 /b2b/suppliers · /b2b/products)
            /admin/b2b/templates   제안서 디자인 템플릿 (기본 4종 + 등록 · HTML 슬라이드/PPTX/PDF 에 적용)
            (integrated_system b2b/app.py 에서 옮김 — 같은 동작, 경로만 /admin/b2b 아래로)

외부로 메일·메시지를 보내거나 결제를 하는 기능은 없다 (견적요청서 · 제안서는 초안 파일만 만든다).
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Annotated, Literal
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict, Field

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


_BACKTEST_CACHE: dict = {}


@router.get("/admin/api/trends/forecast/next4w")
def trends_forecast_next4w(request: Request, as_of: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                           weeks: int = Query(4, ge=1, le=6), top_n: int = Query(20, ge=5, le=50),
                           coupang: int = Query(0, ge=0, le=1)):
    """다음 4주 예보 (2026-11-24, 예측 창 ⑤ 1차) — 전년 기준(설·추석 명절 맞춤)·행사 상대일 후보 목록.
    탐색기(반복만)는 근거 열(explorer_repeat)·explorer_only 로만 붙이고 순서에 쓰지 않는다 (2026-11-25). 관리자 전용 — 고객 화면·추천 순위에 쓰지 않는다.
    coupang=1 이면 후보 키워드(주끼리 겹치면 한 번만)의 쿠팡 파트너스 상품 후보 수를 함께 (쿠팡 호출 — 느림).
    기본(0)은 쿠팡을 부르지 않고 coupang=None(미확인)."""
    from app.services.trends import period
    from app.services.trends.forecast import next_weeks as nw

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    day = date.fromisoformat(as_of) if as_of else date.today()
    out = nw.next_weeks(rank_dir, day, weeks=weeks, top_n=top_n)
    has = _period_has_link()
    kws = list(dict.fromkeys(it["keyword"] for w in out["weeks"] for it in w["items"]))
    cp = _coupang_links(kws) if coupang and kws else None
    for w in out["weeks"]:
        for it in w["items"]:
            it["has_link"] = has(it["keyword"]) if has else None
            it["coupang"] = None if cp is None else len(cp.get(it["keyword"]) or [])   # 쿠팡 파트너스 상품 후보 수
    out["coupang_checked"] = cp is not None
    out["source"] = {"kind": kind, "note": period.source_note(kind, rank_dir)}
    return out


@router.get("/admin/api/trends/forecast/ledger")
def trends_forecast_ledger(request: Request):
    """예보 성적판 (2026-11-25) — 저장해 둔 주간 예보를 28일 뒤 실제와 맞춘 결과. 주 지표 28일·상위 20·선행 적중률(7~28일, 제출 전체), 비교 기준 전년 기준. 4분류는 보조."""
    from app.services.trends import period
    from app.services.trends.forecast import ledger

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    return ledger.evaluate(rank_dir)


@router.post("/admin/api/trends/forecast/ledger/save", dependencies=[api])
def trends_forecast_ledger_save():
    """어제 기준 예보를 장부에 적는다 (이미 있으면 그대로 — 고치지 않음). 지난 날짜는 받지 않는다(뒤늦은 예보 방지)."""
    from datetime import timedelta

    from app.services.trends import period
    from app.services.trends.forecast import ledger

    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    day = date.today() - timedelta(days=1)
    return ledger.save(rank_dir, day) | {"as_of": day.isoformat()}


@router.get("/admin/api/trends/forecast/trend-shift")
def trends_forecast_trend_shift(request: Request, as_of: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                                weeks: int = Query(8, ge=1, le=26)):
    """트렌드 변화(검토 가설, 2026-11-25) — 관측창 내 미진입(작년 이 기간 50위 안 → 올해 28일 100위 밖·앞뒤 14일도 없음)
    · 과거 400일 Top500 관측 이력 없음(28일 안 50위 안). 관측 결과이지 원인 확정이 아니다. 기준일 뒤 42일 순위 필요,
    결측일 수 함께. 기본 기준일 = 마지막 순위 파일 − 42일. 참고 자료(추천 순위에 쓰지 않음)."""
    from app.services.trends import period
    from app.services.trends.forecast import trend_shift as ts

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    latest = ts.default_as_of(rank_dir)
    day = date.fromisoformat(as_of) if as_of else latest
    if day is None:
        raise HTTPException(404, "순위 파일이 없어요")
    out = ts.report(rank_dir, day)
    out["latest_as_of"] = latest.isoformat() if latest else None
    out["weekly"] = ts.weekly(rank_dir, day, weeks=weeks)
    return out


class _AskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=2, max_length=2000)
    provider: str = Field(pattern="^(anthropic|ollama)$")


class _RateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    at: str = Field(min_length=10, max_length=40)
    rating: str = Field(pattern="^(good|fix|bad)$")
    corrected: str | None = Field(default=None, max_length=4000)


@router.get("/admin/api/trends/forecast/knowledge", dependencies=[api])
def trends_forecast_knowledge():
    """예보 지식 묶음·데이터셋 상태 (2026-11-25) — 최신 묶음 시각·크기, 데이터셋 파일별 줄 수."""
    from app.services.trends.forecast import knowledge as kn

    snap = kn.latest()
    ds = kn.root() / "dataset"
    files = [{"name": p.name, "rows": sum(1 for _ in p.open(encoding="utf-8"))} for p in sorted(ds.glob("*.jsonl"))] if ds.exists() else []
    return {"built_at": snap.get("built_at") if snap else None, "chars": len(kn.context_text(snap)) if snap else 0,
            "dataset": files, "rules": kn.RULES, "backtests": [(b["file"], b.get("run_at"), b.get("dates")) for b in (snap or {}).get("backtests", [])],
            "backtests_skipped": (snap or {}).get("backtests_skipped", [])}  # fmt: skip


@router.post("/admin/api/trends/forecast/knowledge/build", dependencies=[api])
def trends_forecast_knowledge_build():
    """지식 묶음 새로 만들기 + 이번 주 템플릿 질문·답 데이터셋 저장. 매주 forecast_ledger.py 도 같은 일을 한다."""
    from app.services.trends import period
    from app.services.trends.forecast import knowledge as kn

    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    snap = kn.build(rank_dir)
    return {"built_at": snap["built_at"], "chars": len(kn.context_text(snap)), "dataset": kn.export_week(snap)}


@router.post("/admin/api/trends/forecast/ask", dependencies=[api])
def trends_forecast_ask(body: _AskIn):
    """AI에게 묻기 — 최신 지식 묶음을 함께 주고 Claude(anthropic) 또는 Ollama 에 묻는다. 관리자 질문만 기록."""
    from app.services.trends.forecast import knowledge as kn

    try:
        return kn.ask(body.question, body.provider)
    except LookupError as e:
        raise HTTPException(409, str(e)) from e
    except Exception as e:  # noqa: BLE001 — 키 없음·Ollama 꺼짐 등
        # 2026-11-25: 502 는 Cloudflare 가 자기 오류 화면으로 바꿔 이유가 안 보였다 → 424(의존 실패)로 JSON 그대로 전달
        import logging

        logging.getLogger("forecast.ask").warning("ask failed provider=%s: %r", body.provider, e)
        raise HTTPException(424, f"{'Claude' if body.provider == 'anthropic' else 'Ollama'} 호출 실패: {type(e).__name__}: {str(e)[:300]}") from e


@router.get("/admin/api/trends/forecast/ask/log", dependencies=[api])
def trends_forecast_ask_log(limit: int = Query(30, ge=1, le=200)):
    from app.services.trends.forecast import knowledge as kn

    return {"items": list(reversed(kn.ask_log(limit)))}


@router.post("/admin/api/trends/forecast/ask/rate", dependencies=[api])
def trends_forecast_ask_rate(body: _RateIn):
    """좋음(그대로)·고침(고친 답)·버림 — 좋음·고침은 데이터셋 forecast_ask_gold.jsonl 에 들어간다."""
    from app.services.trends.forecast import knowledge as kn

    try:
        return kn.rate(body.at, body.rating, body.corrected)
    except (LookupError, ValueError) as e:
        raise HTTPException(404, str(e)) from e


@router.get("/admin/api/trends/forecast/report-card")
def trends_forecast_report_card(request: Request, event: str = Query(..., min_length=1, max_length=40),
                                year: int | None = Query(None, ge=2024, le=2030)):
    """행사별 리포트카드 (2026-11-25) — 행사 28일 전에 예보했다면 방법별 선행 적중·4분류, 실제 주요 상승을 누가 맞혔나·놓쳤나.
    year 없으면 해마다 한 줄 요약만. 참고값(백테스트와 같은 자료)."""
    from app.services.trends import period
    from app.services.trends.forecast import report_card as rc

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    out = {"event": event, "summary": rc.summary(rank_dir, event)}
    if year:
        out["card"] = rc.report_card(rank_dir, event, year)
    return out


@router.get("/admin/api/trends/forecast/backtest")
def trends_forecast_backtest(request: Request, start: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
                             end: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"), step: int = Query(7, ge=1, le=28),
                             explorer: int = Query(1, ge=0, le=1), question: str = Query("q1", pattern="^(q1|q1p)$"),
                             min_share: float = Query(0.6, ge=0.3, le=1.0)):
    """예측 백테스트 (2026-11-24) — Q1(지금 100위 밖 → 7·14·28일 안 100위 진입) 기준선 3종 + 선행 곡선 탐색기.
    예측은 예측일까지의 파일만 읽는다. 결과는 같은 조건이면 메모리에 둔다(순위 파일이 늘면 다시 계산)."""
    from app.services.trends import period
    from app.services.trends.forecast import backtest as bt

    if not request_ok(request) and not guest_trends_on():
        raise HTTPException(401, "관리자 로그인이 필요해요")
    rank_dir, kind, _ = _period_dirs()
    if not rank_dir:
        raise HTTPException(404, period.source_note(kind, rank_dir) or "식품 순위 자료가 없어요")
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    if b < a or (b - a).days > 400:
        raise HTTPException(400, "기간은 400일 안으로 골라 주세요")
    files = period.rank_files(rank_dir)
    key = (str(rank_dir), start, end, step, explorer, question, min_share, len(files), max(files) if files else "")
    if key not in _BACKTEST_CACHE:
        methods = bt.METHODS if explorer else bt.BASELINES
        _BACKTEST_CACHE.clear()
        _BACKTEST_CACHE[key] = bt.run(rank_dir, a, b, step=step, methods=methods, question=question,
                                      min_share=min_share) | {
            "source": {"kind": kind, "note": period.source_note(kind, rank_dir)}}
    out = dict(_BACKTEST_CACHE[key])
    out.pop("per_date", None) if len(out.get("per_date") or []) > 60 else None
    return out


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


@router.get("/admin/api/trends/report-for-keywords", dependencies=[api])
def trends_report_for_keywords(keywords: str = Query(..., max_length=300)):
    """2026-11-21 등록된 링크로 초안을 시작할 때 — 그 키워드들이 들어 있는 가장 최근 급상승 리포트(30일 안) 날짜.
    가장 많이 들어 있는 리포트, 같으면 최근 것. 초안은 리포트 데이터로 쓰므로 리포트에 없는 키워드는 missing."""
    from app.services.trends import surge

    want = [k.strip() for k in keywords.split(",") if k.strip()][:5]
    best = None
    for day in reversed(surge.history_dates()[-30:]):
        rep = surge.load(day) or {}
        have = {it.get("keyword") for it in rep.get("items") or []}
        found = [k for k in want if k in have]
        if found and (best is None or len(found) > len(best["found"])):
            best = {"date": day, "found": found, "missing": [k for k in want if k not in have]}
        if best and not best["missing"]:
            break
    return best or {"date": None, "found": [], "missing": want}


class _DraftIn(BaseModel):
    date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    keywords: list[str] | None = Field(None, max_length=5)
    with_coupang: bool = True        # 2026-11-17: 키워드마다 쿠팡 파트너스 링크를 쇼핑커넥트 자리 앞에
    template: str | None = Field(None, pattern=r"^\d{2}$")    # 2026-11-20 쿠팡용 글 틀 번호 (없으면 주제별 기본)
    hold: bool = False               # 2026-11-20 구매 보류 결론 — 쿠팡용에 링크·고지를 넣지 않는다
    # 2026-11-21 관리자가 고른 세부 질문 {키워드: [면 id]} — 답 문장이 있는 면만 쿠팡용 본문 '자주 찾는 질문'으로
    questions: dict[str, list[str]] | None = Field(None, max_length=5)
    # 2026-11-21 화면 재설계: 만들 글(네이버 블로그용·쿠팡용 중 고른 것만)과 사람이 고른 쇼핑커넥트 링크 {키워드: [링크]}
    variants: list[str] = Field(default_factory=lambda: ["naver", "coupang"], min_length=1, max_length=2)
    connect: dict[str, list[str]] | None = Field(None, max_length=5)


@router.post("/admin/api/trends/blog-draft", dependencies=[api])
def trends_blog_draft(body: _DraftIn):
    """Text drafts for the applesodda blog (temporary save is done by a person / on request — never published here).

    2026-11-17: 두 판을 함께 만든다 — 'naver'(네이버 블로그용: 쇼핑커넥트 삽입 자리·고지, 쿠팡 없음)와
    'coupang'(쿠팡용: 쿠팡 링크·고지만, 쇼핑커넥트 없음).  위쪽 필드는 예전처럼 네이버 블로그용."""
    from app.services.trends import surge

    report = surge.load(body.date)
    # 2026-11-21 상품 소개형: 고른 키워드 중 리포트에 없는 것은 데이터 줄 없이 '상품 소개'로 쓴다 (예: 사과)
    in_report = {it.get("keyword") for it in (report or {}).get("items") or []}
    intro = [k for k in (body.keywords or []) if k not in in_report]
    if not report:
        if not intro:
            raise HTTPException(404, "리포트가 없어요. 먼저 리포트를 만들거나, 키워드를 직접 넣어 상품 소개형으로 만들어 주세요.")
        report = {"items": [], "data_until": date.today().isoformat()}
    want = [v for v in ("naver", "coupang") if v in body.variants]
    if not want:
        raise HTTPException(400, "만들 글(네이버 블로그용·쿠팡용)을 하나 이상 골라 주세요.")
    try:
        first = surge.blog_draft(report, body.keywords, intro=intro)
        # 2026-11-20 v1.3: 보류 결론이면 쿠팡 상품을 찾지 않는다 (링크를 넣지 않으므로). 쿠팡용을 안 만들면 찾지 않음
        coupang = _coupang_links(first["keywords"], channel="blog") \
            if body.with_coupang and not body.hold and "coupang" in want else None
        recipes = _blog_recipes(report, first["keywords"], coupang or {}, body.template)
        drafts = {"naver": surge.blog_draft(report, body.keywords, variant="naver",
                                            connect_ok=blog_connect_approved(), intro=intro),
                  "coupang": surge.blog_draft(report, body.keywords, coupang=coupang or {}, variant="coupang",
                                              recipes=recipes, template=body.template, hold=body.hold,
                                              faq=_faq(first["keywords"], body.questions), intro=intro)}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    drafts["coupang"]["faq"] = {} if body.hold else {k: [q for q, _ in v] for k, v in
                                                     _faq(first["keywords"], body.questions).items() if v}
    drafts = {v: drafts[v] for v in want}
    keywords = first["keywords"]
    # 2026-11-21 네이버 블로그용: 사람이 고른 쇼핑커넥트 링크(connect) 먼저, 그 밖 키워드는 등록부에서 키워드 칸이 같은 링크를
    # 자동으로 넣는다 (승인 켜짐일 때만)
    naver_auto: dict[str, int] = {}
    naver_picked: dict[str, int] = {}
    if "naver" in drafts and blog_connect_approved():
        from app.services.trends import blog_links as bl
        opts = _connect_options(keywords)
        by_url = {o["url"]: o for o in opts["all"]}
        by_url.update({o["url"]: o for v in opts["by_keyword"].values() for o in v})
        text = drafts["naver"]["body"]
        for kw, urls in (body.connect or {}).items():
            chosen = [by_url[u] for u in urls if u in by_url][:bl.MAX_LINKS]
            if kw in keywords and chosen:
                try:
                    text = bl.set_naver_links(text, kw, chosen, surge.DISCLOSURE)
                    naver_picked[kw] = len(chosen)
                except bl.LinkError:
                    pass
        rest = {"by_keyword": {k: v for k, v in opts["by_keyword"].items() if k not in naver_picked}}
        drafts["naver"]["body"], naver_auto = bl.auto_naver(text, rest, surge.DISCLOSURE)
    # 2026-11-20 세부 질문 후보 · 제목 유사도 (네이버 공식 검색 API 블로그 제목, 실패해도 초안은 만든다) — 운영 메모에만
    serp = _blog_serp(keywords)
    status_of = {it["keyword"]: it.get("status") for it in report.get("items") or []}
    subq = _subquestions(keywords, serp, status_of)
    sims = {v: _title_similarity(d["title"], keywords, serp) for v, d in drafts.items()}
    # 2026-11-02: 초안 키워드 중 쇼핑커넥트 링크 발급이 필요한 것 — 파일 맨 위 운영 메모 + 화면 표시 (본문에는 넣지 않음)
    needs = _link_needs(keywords)
    missing = [k for k in keywords if coupang is not None and not coupang.get(k)]
    folder = surge.ROOT / "var" / "blog_drafts"
    folder.mkdir(parents=True, exist_ok=True)
    stem = (f"trend_{date.today().isoformat()}_소개_{'_'.join(keywords)[:36]}" if set(first.get("intro") or []) == set(keywords)
            else f"trend_{report['data_until']}_{'_'.join(keywords)[:40]}")
    for variant, d in drafts.items():
        memo = _operator_memo(needs) if variant == "naver" else ""
        extra = [x.memo_line() for x in subq.values()] + [_ts().memo_line(sims[variant])]
        if variant == "naver" and naver_picked:
            extra.append("고른 쇼핑커넥트 링크를 넣음: " + ", ".join(f"{k} {n}개" for k, n in naver_picked.items()))
        if variant == "naver" and naver_auto:
            extra.append("쇼핑커넥트 링크 자동으로 넣음(등록부 키워드 같음): "
                         + ", ".join(f"{k} {n}개" for k, n in naver_auto.items()))
        if missing and variant == "coupang":                  # 운영 메모 안(구분선 위)에 — 블로그에 붙일 본문에는 넣지 않는다
            extra.append("쿠팡 링크를 찾지 못한 키워드(주류는 넣지 않음): " + ", ".join(missing))
        if variant == "coupang" and coupang is not None:   # 2026-11-21 블로그 쿠팡 링크 채널
            extra.append(_channel_memo())
        if variant == "coupang" and d.get("faq"):
            extra.append("본문 '자주 찾는 질문'에 넣은 질문: " + " · ".join(f"{k}: {', '.join(v)}" for k, v in d["faq"].items()))
        if variant == "coupang" and d.get("hold"):
            extra.append("구매 보류 결론 — 쿠팡 링크·광고 고지를 넣지 않아요. 대표 그림은 AI 그림(승인할 때 만들어요, 유료).")
        elif variant == "coupang" and d.get("cover"):
            extra.append("대표 그림: 쿠팡 상품 사진 1장 (승인할 때 글 위쪽에 넣어요)")
        if d.get("intro"):                                     # 2026-11-21 상품 소개형
            extra.append("상품 소개형(리포트에 없는 키워드 — 검색량 데이터 없이): " + ", ".join(d["intro"]))
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
        d["title_similarity"] = sims[variant]
        _save_cover(path, d.get("cover"))
    _save_serp(folder / f"{stem}.serp.json", keywords, serp, subq)
    out = drafts.get("naver") or next(iter(drafts.values()))
    if "naver" in drafts:
        drafts["naver"]["connect_auto"] = naver_auto
        drafts["naver"]["connect_picked"] = naver_picked
    return {**out, "link_needs": needs, "drafts": drafts, "intro": first.get("intro") or [],
            "subquestions": {k: v.as_dict() for k, v in subq.items()},
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
    confirm_similar: bool = False     # 2026-11-21 제목 유사도 '높음'이어도 진행 (관리자가 한 번 확인)
    confirm_again: bool = False       # 2026-11-21 이미 임시저장한 초안을 고쳐 하나 더 넣기 (관리자가 한 번 확인)


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
    # 2026-11-21 결정: 고친 제목으로 유사도 다시 (초안 때 받아 둔 상위 제목 — 승인 때는 검색을 다시 하지 않음).
    # '높음'이면 막지 않고 한 번 확인받는다 (confirm_similar). 확인한 것은 승인 기록에 남긴다 — 기준선 조정 자료.
    sim = _title_similarity_cached(path, d["title"], keywords)
    if sim.get("level") == "높음" and not body.confirm_similar:
        raise HTTPException(409, {"message": "제목이 검색 상위 글과 많이 비슷해요. 그래도 진행할까요?",
                                  "need_confirm": "title_similarity", "title_similarity": sim})
    extra = {"title_similarity": {k: sim.get(k) for k in ("percent", "level", "nearest", "compared")}} \
        if sim.get("status") == "ok" else {}
    if sim.get("level") == "높음":
        extra["similar_confirmed"] = True
    # 2026-11-21 '저장'이 곧 임시저장 — 같은 내용을 두 번 넣지 않고, 이미 넣은 글을 고쳐 다시 넣을 때는 한 번 확인
    #   (네이버 임시저장 글은 고쳐 쓰는 길이 없어 새 글로 하나 더 들어간다)
    digest = hashlib.sha256(json.dumps([variant, d["title"], d["tags"], d["body"], body.with_image],
                                       ensure_ascii=False).encode()).hexdigest()[:16]
    prev = bas.read_approval(path) or {}
    if prev.get("status") == "running":
        return {"file": body.file, "approval": prev, "title_similarity": sim, "skipped": "running"}
    if prev.get("status") == "done" and prev.get("content_hash") == digest:
        return {"file": body.file, "approval": prev, "title_similarity": sim, "skipped": "same_content"}
    if prev.get("status") == "done" and not body.confirm_again:
        raise HTTPException(409, {"message": "이 초안은 이미 네이버 임시저장함에 있어요. 고친 내용으로 하나 더 넣을까요?",
                                  "need_confirm": "again", "approved_at": prev.get("approved_at")})
    extra["content_hash"] = digest
    rec = bas.start(path, variant=variant, title=d["title"], tags=d["tags"], body=d["body"], keywords=keywords,
                    with_image=body.with_image, cover=_read_cover(path), extra=extra)
    return {"file": body.file, "approval": rec, "title_similarity": sim}


def _cover_path(draft_path: Path) -> Path:
    return draft_path.with_name(draft_path.name[:-len(".txt")] + ".cover.json")


def _save_cover(draft_path: Path, cover: dict | None) -> None:
    """2026-11-20 대표 그림 정보 — 초안 옆 .cover.json (쿠팡용만: 구매 = 쿠팡 상품 사진, 보류 = AI 그림)."""
    p = _cover_path(draft_path)
    try:
        if cover:
            p.write_text(json.dumps(cover, ensure_ascii=False), encoding="utf-8")
        elif p.exists():
            p.unlink()
    except OSError:
        pass


def _read_cover(draft_path: Path) -> dict | None:
    try:
        data = json.loads(_cover_path(draft_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("kind") in ("ai", "seller") else None


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


# ── 2026-11-21 초안의 상품 링크 고르기 (네이버 = 등록부 쇼핑커넥트, 쿠팡 = 쿠팡 파트너스 검색) ──────────────
def _connect_options(keywords: list[str]) -> dict:
    from app.services.affiliate import connect_registry as reg
    from app.services.trends import blog_links as bl

    try:
        rows = reg.rows()
    except Exception:  # noqa: BLE001 — 등록부를 못 읽어도 초안은 만든다
        rows = []
    return bl.connect_options(keywords, rows)


@router.get("/admin/api/trends/blog-draft/link-options", dependencies=[api])
def trends_blog_draft_link_options(file: str = Query(..., max_length=200)):
    """초안 키워드마다 넣을 수 있는 링크 후보. 네이버 블로그용 = 등록부 쇼핑커넥트 링크, 쿠팡용 = 쿠팡 파트너스 검색 후보
    (블로그 채널 아이디, 공통 검색 순서 그대로 최대 6개, 주류 제외). 고른 것은 apply-links 로 본문에 넣는다."""
    from app.services.trends import blog_links as bl

    path = _draft_path_or_404(file)
    d = _parse_draft(path.read_text(encoding="utf-8"))
    variant = "coupang" if path.name.endswith(COUPANG_SUFFIX) else "naver"
    keywords = bl.keywords_of(d["body"])
    if variant == "naver":
        opts = _connect_options(keywords)
        return {"variant": variant, "keywords": keywords, "connect_ok": blog_connect_approved(), **opts}
    found = _coupang_links(keywords, channel="blog", limit=6)
    return {"variant": variant, "keywords": keywords, "by_keyword": {k: [{**x, "match": "쿠팡 검색"} for x in v]
                                                                    for k, v in found.items()}, "all": []}


class _ApplyLinksIn(BaseModel):
    variant: str = Field(..., pattern="^(naver|coupang)$")
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=50_000)
    keyword: str = Field(..., min_length=1, max_length=60)
    links: list[dict] = Field(default_factory=list, max_length=3)


@router.post("/admin/api/trends/blog-draft/apply-links", dependencies=[api])
def trends_blog_draft_apply_links(body: _ApplyLinksIn):
    """화면의 제목·본문(저장 전 고친 것 포함)에 고른 링크를 넣어 돌려준다. 파일에는 쓰지 않는다 — '저장'을 눌러야 저장."""
    from app.services.trend_posts import templates
    from app.services.trends import blog_links as bl, surge

    links = [{"title": str(x.get("title") or "")[:200], "url": str(x.get("url") or "")[:500],
              "rocket": bool(x.get("rocket"))} for x in body.links]
    try:
        if body.variant == "naver":
            if links and not blog_connect_approved():
                raise bl.LinkError("쇼핑커넥트 블로그 사용 승인 전이에요 (.env SC_BLOG_APPROVED=1 일 때만 링크를 넣어요).")
            return {"title": body.title, "body": bl.set_naver_links(body.body, body.keyword, links, surge.DISCLOSURE)}
        title, text = bl.set_coupang_links(body.title, body.body, body.keyword, links,
                                           disclosure=surge.COUPANG_DISCLOSURE, site_ops=surge.SITE_OPS,
                                           ad_prefix=surge.AD_PREFIX, hold_line=templates.HOLD_LINE["blog"])
        return {"title": title, "body": text}
    except bl.LinkError as exc:
        raise HTTPException(400, str(exc)) from exc


def _coupang_links(keywords: list[str], channel: str | None = None, limit: int | None = None) -> dict[str, list[dict]]:
    """키워드마다 쿠팡 파트너스 상품 링크 (공통 검색 picks 순서 그대로, 제휴 링크만, 주류 제외). 실패하면 빈 목록.
    2026-11-21: channel='blog' 이면 .env COUPANG_BLOG_SUB_ID 채널로 링크를 받는다(없으면 기본 채널 그대로)."""
    import contextlib

    from app.services import coupang_api

    sub = coupang_api.coupang_blog_sub_id() if channel == "blog" else None
    with coupang_api.sub_id_channel(sub) if sub else contextlib.nullcontext():
        return _coupang_links_now(keywords, limit) if limit else _coupang_links_now(keywords)


def _channel_memo() -> str:
    from app.services import coupang_api

    blog = coupang_api.coupang_blog_sub_id()
    if blog:
        return f"쿠팡 채널: 블로그 전용 '{blog}' (사이트와 따로 집계)"
    return ("쿠팡 채널: 블로그 전용 채널이 없어 사이트와 같은 채널"
            + (f" '{coupang_api.coupang_sub_id()}'" if coupang_api.coupang_sub_id() else "")
            + "로 집계돼요 — 파트너스 '채널 아이디 관리'에서 만든 뒤 .env COUPANG_BLOG_SUB_ID")


def _faq(keywords: list[str], picked: dict[str, list[str]] | None) -> dict[str, list[tuple[str, list[str]]]]:
    from app.services.trends import subquestions

    return {kw: subquestions.faq(kw, (picked or {}).get(kw) or []) for kw in keywords if (picked or {}).get(kw)}


def _coupang_links_now(keywords: list[str], limit: int | None = None) -> dict[str, list[dict]]:
    from app.services.trend_posts import draft as post_draft, policy, wiring
    from app.services.trends import surge

    out: dict[str, list[dict]] = {}
    for kw in keywords:
        if policy.is_alcohol(kw):
            out[kw] = []
            continue
        try:
            found = post_draft.products_from_result(wiring.find_products(kw), keyword=kw,
                                                    limit=limit or post_draft.MAX_PRODUCTS)
        except Exception:  # noqa: BLE001 — 쿠팡을 못 불러도 초안은 만든다
            found = []
        out[kw] = [{"title": p.title, "url": p.url, "rocket": p.rocket, "image_url": p.image_url} for p in found
                   if p.link_type == "affiliate"][:limit or surge.COUPANG_PER_KEYWORD]
    return out


# ── 2026-11-20 세부 질문 후보 · 제목 유사도 ─────────────────────────────────────────────
def _ts():
    from app.services.trends import title_similarity

    return title_similarity


def _blog_serp(keywords: list[str]) -> dict[str, list[str]]:
    """키워드마다 블로그 제목(정확도순 최대 100, 공식 검색 API). 꺼짐(BLOG_SERP=0)·키 없음·실패면 빈 목록."""
    from app.services.trends import subquestions

    search = subquestions.title_search_from_env()
    out: dict[str, list[str]] = {}
    for kw in keywords:
        try:
            out[kw] = search(kw) if search else []
        except Exception:  # noqa: BLE001 — 검색을 못 해도 초안은 만든다
            out[kw] = []
    return out


def _subquestions(keywords: list[str], serp: dict[str, list[str]], status_of: dict) -> dict:
    from app.services.trends import subquestions

    return {kw: subquestions.suggest(kw, serp.get(kw) or [], status=status_of.get(kw)) for kw in keywords}


def _title_similarity(title: str, keywords: list[str], serp: dict[str, list[str]]) -> dict:
    """첫 키워드의 상위 제목과 비교 (제목이 첫 키워드를 앞세우므로). 첫 키워드 자료가 없으면 다음 키워드."""
    pool = next((serp[k] for k in keywords if serp.get(k)), [])
    return _ts().compare(title, pool, keywords)


def _save_serp(path, keywords: list[str], serp: dict, subq: dict) -> None:
    import json as _json
    from datetime import datetime as _dt, timezone as _tz

    data = {"fetched_at": _dt.now(_tz.utc).isoformat(timespec="seconds"), "keywords": keywords,
            "titles": {k: (serp.get(k) or [])[:30] for k in keywords},
            "subquestions": {k: v.as_dict() for k, v in subq.items()}}
    try:
        path.write_text(_json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def _serp_path(draft_path):
    name = draft_path.name
    if name.endswith(COUPANG_SUFFIX):
        name = name[:-len(COUPANG_SUFFIX)] + ".txt"
    return draft_path.with_name(name[:-len(".txt")] + ".serp.json")


def _title_similarity_cached(draft_path, title: str, keywords: list[str]) -> dict:
    import json as _json

    try:
        data = _json.loads(_serp_path(draft_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "none", "compared": 0}
    return _title_similarity(title, data.get("keywords") or keywords, data.get("titles") or {})


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


# ── 로컬 모델 학습 데이터셋 (2026-11-21) — 짧은 정리 작업의 문장·정답, 사람이 확인(gold/고침/버림) ──
class _DatasetReviewIn(BaseModel):
    verdict: str = Field(..., pattern="^(ok|fix|drop)$")
    output: dict | None = None
    note: str | None = Field(None, max_length=200)


@router.get("/admin/api/ai/dataset", dependencies=[api])
def ai_dataset(task: str | None = Query(None, max_length=40)):
    from app.services.ai import dataset

    st = dataset.DatasetStore()
    # 2026-11-22: 학습 안 함 — 화면에 '사용 안 함'을 띄우고 남은 칸 숫자만 보여 준다 (확인 대기 목록은 비움)
    return {"status": "off", "off_since": dataset.TRAINING_OFF_SINCE, "capture_setting_on": dataset.requested(),
            "note": "고객 문장으로 학습하지 않기로 했어요 (2026-11-22). 수집·내보내기는 꺼져 있어요.",
            "stats": st.stats(), "queue": [], "tasks": sorted(dataset.tasks())}


@router.post("/admin/api/ai/dataset/{eid}/review", dependencies=[api])
def ai_dataset_review(eid: int, body: _DatasetReviewIn):
    from app.services.ai import dataset

    try:
        return dataset.DatasetStore().review(eid, body.verdict, output=body.output, note=body.note)
    except dataset.DatasetError as exc:
        raise HTTPException(400, str(exc)) from exc


# ── 개선 목록 (2026-11-23, 3-D ④) — 주간 지표 · 점검 후보 · 확인 결과 · 고침 기록 (자동 수정 없음) ──
class _ReviewIn(BaseModel):
    verdict: str = Field(..., pattern="^(confirmed|not_error|hold)$")
    note: str | None = Field(None, max_length=300)


class _FixIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    pr: str | None = Field(None, max_length=40)
    candidate_ids: list[str] = Field(default_factory=list, max_length=20)
    affected: str | None = Field(None, max_length=300)
    check_on: str | None = Field(None, pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    result: str = Field("pending", pattern="^(pending|better|same|worse|reverted)$")
    result_note: str | None = Field(None, max_length=300)


@router.get("/admin/improve")
def admin_improve(request: Request):
    return _page(request, WEB / "improve.html")


@router.get("/admin/api/improve/weekly", dependencies=[api])
def improve_weekly(week: str | None = Query(None, pattern=r"^\d{4}-W\d{2}$")):
    from app.admin.ops import improve

    return improve.weekly(week)


@router.post("/admin/api/improve/weekly/run", dependencies=[api])
def improve_weekly_run():
    from app.admin.ops import improve

    try:
        return improve.run_weekly()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"주간 지표를 만들지 못했어요 ({type(exc).__name__})") from exc


@router.get("/admin/api/improve/candidates", dependencies=[api])
def improve_candidates(days: int = Query(7, ge=1, le=90)):
    from app.admin.ops import improve

    return improve.candidates(days) | {"reviewed": improve.reviewed_list()}


@router.post("/admin/api/improve/candidates/{cid}/review", dependencies=[api])
def improve_review(cid: str, body: _ReviewIn):
    from app.admin.ops import improve

    try:
        return improve.review(cid, body.verdict, body.note)
    except KeyError as exc:
        raise HTTPException(404, "그 점검 후보를 찾지 못했어요 (신호 기록 보존 기간이 지났을 수 있어요)") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/admin/api/improve/fixes", dependencies=[api])
def improve_fixes():
    from app.admin.ops import improve

    return {"fixes": improve.fixes_view(), "results": improve.RESULTS}


@router.post("/admin/api/improve/fixes", dependencies=[api])
def improve_fix_add(body: _FixIn):
    from app.admin.ops import improve

    try:
        return improve.save_fix(body.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/admin/api/improve/fixes/{fid}", dependencies=[api])
def improve_fix_update(fid: int, body: _FixIn):
    from app.admin.ops import improve

    try:
        return improve.save_fix(body.model_dump(), fid)
    except KeyError as exc:
        raise HTTPException(404, "그 고침 기록이 없어요") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# 합성 재현 사례 초안 (2026-11-23, 3-D ⑥) — '오류 확인' 후보 → 역할 넷 자리 → 사람이 합성 문장·기대 검색어 → 내보내기
class _CaseIn(BaseModel):
    turns: list[str] = Field(default_factory=list, max_length=6)
    search: str | None = Field(None, max_length=60)
    search_has: list[str] = Field(default_factory=list, max_length=6)
    search_not: list[str] = Field(default_factory=list, max_length=6)
    searches: list[str] = Field(default_factory=list, max_length=6)
    fix: str | None = Field(None, max_length=20)
    status: str = Field("draft", pattern="^(draft|ready|dropped)$")


class _PreviewIn(BaseModel):
    turns: list[str] = Field(..., min_length=1, max_length=6)


@router.get("/admin/api/improve/cases", dependencies=[api])
def improve_cases():
    from app.admin.ops import improve

    return {"cases": improve.cases_view(), "roles": improve.CASE_ROLES, "statuses": improve.CASE_STATUS}


@router.post("/admin/api/improve/cases/start/{review_id}", dependencies=[api])
def improve_cases_start(review_id: str):
    from app.admin.ops import improve

    try:
        return {"cases": improve.start_cases(review_id)}
    except KeyError as exc:
        raise HTTPException(404, "'오류 확인'한 점검 후보만 재현 사례를 만들 수 있어요") from exc


@router.post("/admin/api/improve/cases/preview", dependencies=[api])
def improve_cases_preview(body: _PreviewIn):
    from app.admin.ops import improve

    return {"searches": improve.preview([t[:80] for t in body.turns])}


@router.post("/admin/api/improve/cases/{n}", dependencies=[api])
def improve_case_save(n: int, body: _CaseIn):
    from app.admin.ops import improve

    try:
        return improve.save_case(n, body.model_dump())
    except KeyError as exc:
        raise HTTPException(404, "그 사례가 없어요") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/admin/api/improve/cases/export", dependencies=[api])
def improve_cases_export():
    from app.admin.ops import improve

    return Response(improve.export_cases(), media_type="text/plain; charset=utf-8")


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


# ── B2B 입찰 폐쇄몰 운영 (2026-11-24) — 설계 claude/b2b_closed_mall_auth_2026-11-24.md ──
@router.get("/admin/b2b/mall")
def admin_b2b_mall(request: Request):
    return _page(request, B2B_WEB / "mall.html")


@router.get("/admin/b2b/suppliers")
def admin_b2b_suppliers(request: Request):
    return _page(request, B2B_WEB / "suppliers.html")


@router.get("/admin/b2b/settle")
def admin_b2b_settle(request: Request):
    return _page(request, B2B_WEB / "settle.html")


@router.get("/admin/b2b/inquiries")
def admin_b2b_inquiries(request: Request):
    return _page(request, B2B_WEB / "inquiries.html")


# ── B2B 문의 창구 (2026-11-24) — 설계 claude/b2b_inquiry_desk_2026-11-24.md ──
class _InqStatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(..., max_length=12)
    note: str = Field("", max_length=200)
    human_checked: bool = False


class _InqNoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., min_length=1, max_length=500)


def _inq():
    from app.services.b2b_inquiry import store

    return store, store.engine()


def _inq_call(fn):
    from app.services.b2b_inquiry import store

    try:
        return fn()
    except store.InquiryError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/admin/api/b2b-inquiry", dependencies=[api])
def b2b_inquiry_list(status: str | None = None):
    """목록 — 연락처 없음."""
    store, eng = _inq()
    return {"inquiries": store.list_inquiries(eng, status), "counts": store.counts(eng),
            "labels": store.STATUS_LABEL}


@router.get("/admin/api/b2b-inquiry/{iid}", dependencies=[api])
def b2b_inquiry_detail(iid: str):
    """상세 — 회신하려면 연락처가 필요하므로 여기서만 복호화해 보여 준다."""
    store, eng = _inq()
    d = store.get(eng, iid, with_contact=True)
    if d is None:
        raise HTTPException(404, "inquiry not found")
    return {"inquiry": d}


@router.post("/admin/api/b2b-inquiry/{iid}/status", dependencies=[api])
def b2b_inquiry_status(iid: str, body: _InqStatusIn):
    store, eng = _inq()
    return {"ok": True, "inquiry": _inq_call(lambda: store.set_status(eng, iid, body.status, by="operator", note=body.note,
                                                                       human_checked=body.human_checked))}


@router.post("/admin/api/b2b-inquiry/{iid}/note", dependencies=[api])
def b2b_inquiry_note(iid: str, body: _InqNoteIn):
    store, eng = _inq()
    return {"ok": True, "inquiry": _inq_call(lambda: store.note(eng, iid, body.text, by="operator"))}


@router.post("/admin/api/b2b-inquiry/{iid}/to-bid", dependencies=[api])
def b2b_inquiry_to_bid(iid: str):
    """조건만(연락처 없이) 콘솔 공고로 등록 → 콘솔에서 바로 분석하도록 주소를 돌려준다."""
    store, eng = _inq()
    bid_id = _inq_call(lambda: store.to_bid(eng, iid, by="operator"))
    return {"ok": True, "bid_id": bid_id, "console": "/admin/b2b?q=" + quote(f"{bid_id} 분석해줘")}


class _MallIn(BaseModel):
    spec: dict


class _MallCodesIn(BaseModel):
    n: int = Field(..., ge=1, le=5000)


class _MallMarkIn(BaseModel):
    order_ids: list[str] = Field(..., max_length=5000)
    status: str = Field(..., pattern="^(shipped|delivered)$")


def _corp():
    from app.services.corpmall import store

    return store, store.engine()


def _mall_or_404(store, eng, mall_id):
    m = store.get_mall(eng, mall_id=mall_id)
    if m is None:
        raise HTTPException(404, "mall not found")
    return m


@router.get("/admin/api/corpmall", dependencies=[api])
def corpmall_list():
    store, eng = _corp()
    return {"malls": [dict(m, stats=store.stats(eng, m["mall_id"])) for m in store.list_malls(eng)]}


@router.post("/admin/api/corpmall", dependencies=[api])
def corpmall_create(body: _MallIn):
    store, eng = _corp()
    try:
        return {"ok": True, "mall": store.create_mall(eng, body.spec)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/admin/api/corpmall/{mall_id}", dependencies=[api])
def corpmall_detail(mall_id: str):
    store, eng = _corp()
    m = _mall_or_404(store, eng, mall_id)
    return {"mall": m, "stats": store.stats(eng, mall_id), "orders": store.orders(eng, mall_id),
            "events": store.events(eng, mall_id)}


@router.post("/admin/api/corpmall/{mall_id}/status/{status}", dependencies=[api])
def corpmall_status(mall_id: str, status: str):
    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    try:
        if status == "closed":
            return {"ok": True, **store.close_mall(eng, mall_id)}
        store.set_status(eng, mall_id, status)
        return {"ok": True}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/codes", dependencies=[api])
def corpmall_codes(mall_id: str, body: _MallCodesIn):
    """코드 원문은 이 응답에만 — 화면이 바로 CSV 로 내려받게 한다 (서버에는 해시만)."""
    store, eng = _corp()
    m = _mall_or_404(store, eng, mall_id)
    try:
        got = store.issue_codes(eng, mall_id, body.n)
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True, "codes": [{"label": n, "code": c, "link": f"/corp/{m['slug']}#t={t}"} for n, c, t in got]}


@router.post("/admin/api/corpmall/{mall_id}/codes/{label}/reissue", dependencies=[api])
def corpmall_reissue(mall_id: str, label: int):
    store, eng = _corp()
    m = _mall_or_404(store, eng, mall_id)
    try:
        n, c, t = store.void_and_reissue(eng, mall_id, label)
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True, "label": n, "code": c, "link": f"/corp/{m['slug']}#t={t}"}


@router.get("/admin/api/corpmall/{mall_id}/no-address", dependencies=[api])
def corpmall_no_address(mall_id: str):
    """마감 뒤 주소 없이 기본 상품이 된 코드 번호 — 발주처에 넘겨 일괄 수령 등으로 처리."""
    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"labels": store.no_address_labels(eng, mall_id)}


@router.post("/admin/api/corpmall/{mall_id}/export", dependencies=[api])
def corpmall_export(mall_id: str):
    """발송 요청 주문(배송 정보 포함)을 공급사 전달용으로 — 한 번 내보낸 것은 '발송 준비'로 바뀌고 다시 나오지 않는다."""
    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"ok": True, "orders": store.export_orders(eng, mall_id, by="operator")}


class _SuppliersIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suppliers: dict[str, dict] = Field(..., max_length=200)


@router.post("/admin/api/corpmall/{mall_id}/suppliers", dependencies=[api])
def corpmall_suppliers(mall_id: str, body: _SuppliersIn):
    """몰 상품마다 공급사·품번 (직원·발주처 화면에는 안 보임)."""
    from app.services.corpmall import po

    store, eng = _corp()
    try:
        return {"ok": True, "items": po.set_suppliers(eng, mall_id, body.suppliers)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/po", dependencies=[api])
def corpmall_po_create(mall_id: str):
    """발주 묶음 만들기 — 넣은 주문은 '발송 준비'. 파일은 묶음에서 따로 받는다(실패해도 다시 받기)."""
    from app.services.corpmall import po

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    try:
        return {"ok": True, **po.create_batch(eng, mall_id, by="operator")}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/admin/api/corpmall/{mall_id}/po", dependencies=[api])
def corpmall_po_list(mall_id: str):
    from app.services.corpmall import po

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"batches": po.list_batches(eng, mall_id)}


@router.get("/admin/api/corpmall/{mall_id}/po/{batch_id}/file", dependencies=[api])
def corpmall_po_file(mall_id: str, batch_id: str, supplier: str | None = Query(None, max_length=40)):
    """발주 묶음 파일 — supplier 없으면 운영자용 통합본, 있으면 그 공급사 전달용(다른 공급사 정보 없음). 서버에 남기지 않는다."""
    from fastapi.responses import Response

    from app.services.corpmall import po

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    from app.services.corpmall import podoc

    try:
        target = next(
            (p for p in podoc.list_pos(eng, mall_id, batch_id) if p["supplier"] == supplier and p["status"] != "cancelled"),
            None,
        ) if supplier else None  # fmt: skip
        if target is not None:  # 공급사 전달용 — 정식 발주서만, 받으면 '전달됨'
            data, name = podoc.operator_supplier_file(eng, mall_id, target["po_no"], by="operator")
        else:
            data, name = po.render(eng, mall_id, batch_id, supplier=supplier, by="operator")
    except store.MallError as e:
        raise HTTPException(400 if supplier else 404, str(e)) from e
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}", "Cache-Control": "no-store"},
    )


@router.post("/admin/api/corpmall/{mall_id}/tracking-file", dependencies=[api])
async def corpmall_tracking_file(
    mall_id: str, file: Annotated[UploadFile, File()], shipped: Annotated[bool, Form()] = False
):
    """공급사가 송장을 채워 돌려준 발주서(엑셀·CSV) → 주문 번호로 송장 넣기. 파일은 읽고 버린다."""
    from app.services.corpmall import po

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    data = await file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "파일이 너무 커요 (5MB 까지)")
    try:
        rows, problems = po.read_tracking(file.filename or "", data)
    except Exception as e:  # noqa: BLE001 — 깨진 파일
        raise HTTPException(400, "엑셀·CSV 파일을 읽지 못했어요") from e
    if not rows and not problems:
        raise HTTPException(400, "'주문 번호'와 '송장' 칸이 있는 줄을 찾지 못했어요")
    got = store.set_tracking(eng, mall_id, rows, shipped=shipped) if rows else {"n": 0, "skipped": 0, "same": 0, "conflicts": []}
    return {"ok": True, "read": len(rows), "problems": problems, **got}


# ── 공급 거래처 · 정식 발주서 (2026-11-24) — 설계 claude/b2b_supplier_po_2026-11-24.md ──
class _SupplierIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., max_length=40)
    biz_no: str = Field("", max_length=14)
    contact: dict = Field(default_factory=dict)
    order_method: str = Field("email", max_length=8)
    payment_terms: str = Field("", max_length=120)
    lead_days: int | None = Field(None, ge=0, le=60)
    vat_mode: str = Field("excluded", max_length=10)
    memo: str = Field("", max_length=300)
    active: bool = True


@router.get("/admin/api/b2b-suppliers", dependencies=[api])
def b2b_suppliers_list():
    from app.services.corpmall import store as cstore
    from app.services.corpmall import suppliers as sup

    return {"suppliers": sup.list_all(cstore.engine()), "methods": sup.ORDER_METHODS, "vat_modes": sup.VAT_MODES}


@router.get("/admin/api/b2b-suppliers/{supplier_id}", dependencies=[api])
def b2b_supplier_get(supplier_id: str):
    from app.services.corpmall import store as cstore
    from app.services.corpmall import suppliers as sup

    d = sup.get(cstore.engine(), supplier_id, full=True)
    if d is None:
        raise HTTPException(404, "supplier not found")
    return {"supplier": d}


@router.post("/admin/api/b2b-suppliers", dependencies=[api])
def b2b_supplier_create(body: _SupplierIn):
    from app.services.corpmall import store as cstore
    from app.services.corpmall import suppliers as sup

    try:
        return {"ok": True, "supplier": sup.save(cstore.engine(), body.model_dump())}
    except cstore.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/b2b-suppliers/{supplier_id}", dependencies=[api])
def b2b_supplier_update(supplier_id: str, body: _SupplierIn):
    from app.services.corpmall import store as cstore
    from app.services.corpmall import suppliers as sup

    try:
        return {"ok": True, "supplier": sup.save(cstore.engine(), body.model_dump(), supplier_id)}
    except cstore.MallError as e:
        raise HTTPException(400, str(e)) from e


class _PoAckIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = Field(..., min_length=1, max_length=300)
    ship_date: str | None = Field(None, max_length=10)


class _PoCancelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(..., min_length=1, max_length=200)


@router.get("/admin/api/corpmall/{mall_id}/pos", dependencies=[api])
def corpmall_pos(mall_id: str):
    from app.services.corpmall import podoc

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"pos": podoc.list_pos(eng, mall_id)}


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/ack-link", dependencies=[api])
def corpmall_po_ack_link(mall_id: str, po_no: str, reissue: bool = Query(False)):
    """공급사 확인 링크 — 같은 판이면 같은 링크. reissue=true('링크 재발급')일 때만 새로 만들고 옛 링크를 막는다."""
    from app.services.corpmall import podoc

    store, eng = _corp()
    try:
        return {"ok": True, "link": podoc.ack_link(eng, mall_id, po_no, reissue=reissue)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/ack", dependencies=[api])
def corpmall_po_mark_ack(mall_id: str, po_no: str, body: _PoAckIn):
    from app.services.corpmall import podoc

    store, eng = _corp()
    try:
        return {"ok": True, "po": podoc.mark_ack(eng, mall_id, po_no, by="operator", note=body.note, ship_date=body.ship_date)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/cancel", dependencies=[api])
def corpmall_po_cancel(mall_id: str, po_no: str, body: _PoCancelIn):
    """취소 — 공급사에 전달 전이면 바로, 전달 뒤면 '취소 요청'(공급사 취소 확인 뒤 취소)."""
    from app.services.corpmall import podoc

    store, eng = _corp()
    try:
        return {"ok": True, "po": podoc.cancel(eng, mall_id, po_no, by="operator", reason=body.reason)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


class _PoNoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = Field(..., min_length=1, max_length=200)


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/cancel-confirm", dependencies=[api])
def corpmall_po_cancel_confirm(mall_id: str, po_no: str, body: _PoNoteIn):
    """공급사가 메일·전화로 취소를 확인했을 때 운영자 표시 — 근거 메모 필수. 그때 주문이 되돌아간다."""
    from app.services.corpmall import podoc

    store, eng = _corp()
    try:
        return {"ok": True, "po": podoc.confirm_cancel(eng, mall_id, po_no, by="operator", note=body.note)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/cancel-withdraw", dependencies=[api])
def corpmall_po_cancel_withdraw(mall_id: str, po_no: str):
    from app.services.corpmall import podoc

    store, eng = _corp()
    try:
        return {"ok": True, "po": podoc.withdraw_cancel(eng, mall_id, po_no, by="operator")}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/finalize", dependencies=[api])
def corpmall_po_finalize(mall_id: str, po_no: str):
    """미확정 발주서 확정 — 거래처·단가·발주사 정보를 채운 뒤 다시 계산해 정식 발주로."""
    from app.services.corpmall import podoc

    store, eng = _corp()
    try:
        return {"ok": True, "po": podoc.finalize(eng, mall_id, po_no, by="operator")}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


# ── 2단계: 수주 문의 → 폐쇄몰 초안 · 매출·매입 정산 (2026-11-24) — 설계 claude/b2b_stage2_settle_2026-11-24.md ──
class _MallDraftIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str = Field(..., max_length=40)
    opens_at: str = Field(..., max_length=25)
    closes_at: str = Field(..., max_length=25)
    candidate_ids: list[str] = Field(..., min_length=1, max_length=40)
    title: str | None = Field(None, max_length=80)
    delivery_mode: str | None = Field(None, max_length=12)
    default_item: str | None = Field(None, max_length=80)


class _ContractIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    unit_price: int | None = Field(None, ge=0, le=10_000_000)
    headcount: int | None = Field(None, ge=1, le=1_000_000)
    vat_mode: str = Field("included", max_length=10)
    tax_type: str = Field("taxable", max_length=10)  # 매출 과세·면세 (세무 검토 뒤 확정)
    basis: str = Field("headcount", max_length=10)
    invoice_issued_on: str | None = Field(None, max_length=10)
    invoice_memo: str = Field("", max_length=200)


class _PoInvoiceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    received_on: str | None = Field(None, max_length=10)
    memo: str = Field("", max_length=200)


@router.get("/admin/api/b2b-inquiry/{iid}/candidates", dependencies=[api])
def b2b_inquiry_candidates(iid: str, q: str = Query("", max_length=60)):
    from app.services.corpmall import draft

    return {"candidates": draft.candidates(q)}


@router.post("/admin/api/b2b-inquiry/{iid}/mall-draft", dependencies=[api])
def b2b_inquiry_mall_draft(iid: str, body: _MallDraftIn):
    """수주 문의 → 폐쇄몰 초안(직원은 못 들어옴). 상품은 공급사 근거 후보에서, 매입 단가는 견적 단가만."""
    from app.services.corpmall import draft

    store, eng = _corp()
    try:
        m = draft.from_inquiry(eng, iid, slug=body.slug, opens_at=body.opens_at, closes_at=body.closes_at,
                               candidate_ids=body.candidate_ids, title=body.title, delivery_mode=body.delivery_mode,
                               default_item=body.default_item)
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True, "mall": m}


@router.get("/admin/api/corpmall/{mall_id}/settle", dependencies=[api])
def corpmall_settle(mall_id: str):
    from app.services.corpmall import settle

    store, eng = _corp()
    try:
        return settle.summary(eng, mall_id)
    except store.MallError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/contract", dependencies=[api])
def corpmall_contract(mall_id: str, body: _ContractIn):
    from app.services.corpmall import settle

    store, eng = _corp()
    try:
        return {"ok": True, "contract": settle.set_contract(eng, mall_id, body.model_dump())}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/invoice", dependencies=[api])
def corpmall_po_invoice(mall_id: str, po_no: str, body: _PoInvoiceIn):
    from app.services.corpmall import settle

    store, eng = _corp()
    try:
        settle.set_po_invoice(eng, mall_id, po_no, received_on=body.received_on, memo=body.memo)
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


@router.get("/admin/api/b2b-settle", dependencies=[api])
def b2b_settle_overview():
    from app.services.corpmall import settle

    store, eng = _corp()
    return {"malls": settle.overview(eng)}


# ── 3단계: 발주서 메일 (2026-11-24) — 설계 claude/b2b_po_mail_2026-11-24.md ──
class _MailEditIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(..., max_length=200)
    body: str = Field(..., max_length=6000)
    attach: bool = False


def _site() -> str:
    from app.services.trend_posts.render import site_url

    return site_url()


@router.get("/admin/api/corpmall/{mall_id}/mails", dependencies=[api])
def corpmall_mails(mall_id: str):
    from app.services.corpmall import mailer

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"mails": mailer.list_mails(eng, mall_id), "smtp": mailer.smtp_config() is not None}


@router.post("/admin/api/corpmall/{mall_id}/pos/{po_no}/mail", dependencies=[api])
def corpmall_mail_prepare(mall_id: str, po_no: str):
    from app.services.corpmall import mailer

    store, eng = _corp()
    try:
        return {"ok": True, "mail": mailer.prepare(eng, mall_id, po_no)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/mails/{mail_id}", dependencies=[api])
def corpmall_mail_edit(mall_id: str, mail_id: str, body: _MailEditIn):
    from app.services.corpmall import mailer

    store, eng = _corp()
    try:
        return {"ok": True, "mail": mailer.edit(eng, mall_id, mail_id, subject=body.subject, body=body.body, attach=body.attach)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/mails/{mail_id}/send", dependencies=[api])
def corpmall_mail_send(mall_id: str, mail_id: str):
    """운영자가 확인한 메일 보내기 — 발신 메일(SMTP)이 연결됐을 때만."""
    from app.services.corpmall import mailer

    store, eng = _corp()
    try:
        return {"ok": True, "mail": mailer.send(eng, mall_id, mail_id, base_url=_site())}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/admin/api/corpmall/{mall_id}/mails/{mail_id}/eml", dependencies=[api])
def corpmall_mail_eml(mall_id: str, mail_id: str):
    """발신 메일 연결 전: .eml 로 내려받아 메일 프로그램에서 직접 보내기(같은 판이면 확인 링크도 같음)."""
    from fastapi.responses import Response

    from app.services.corpmall import mailer

    store, eng = _corp()
    try:
        data, name = mailer.eml(eng, mall_id, mail_id, base_url=_site())
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e
    return Response(data, media_type="message/rfc822",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}", "Cache-Control": "no-store"})


@router.post("/admin/api/corpmall/{mall_id}/mails/{mail_id}/mark-sent", dependencies=[api])
def corpmall_mail_mark(mall_id: str, mail_id: str):
    from app.services.corpmall import mailer

    store, eng = _corp()
    try:
        return {"ok": True, "mail": mailer.mark_sent(eng, mall_id, mail_id)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/mails/{mail_id}/mark-not-sent", dependencies=[api])
def corpmall_mail_mark_not_sent(mall_id: str, mail_id: str, body: _PoNoteIn):
    """결과 불명 메일을 '안 감'으로 정리(공급사 확인 근거 메모) — 그 뒤 다시 보낼 수 있다."""
    from app.services.corpmall import mailer

    store, eng = _corp()
    try:
        return {"ok": True, "mail": mailer.mark_not_sent(eng, mall_id, mail_id, by="operator", note=body.note)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


class _MallManualIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manual: dict


class _MallTrackingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: list[dict] = Field(..., max_length=5000)
    shipped: bool = False  # 택배사 인수·출고 확인된 주문만 올릴 때 True → '발송함'


@router.post("/admin/api/corpmall/{mall_id}/manual", dependencies=[api])
def corpmall_manual(mall_id: str, body: _MallManualIn):
    """몰 답변 매뉴얼(출고 예정일·택배사·교환 조건 등) — 직원 질문 자동 답이 이 값만 쓴다."""
    store, eng = _corp()
    try:
        return {"ok": True, "manual": store.update_manual(eng, mall_id, body.manual)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/tracking", dependencies=[api])
def corpmall_tracking(mall_id: str, body: _MallTrackingIn):
    """송장 번호 [{order_id, tracking}]. 송장 발급 ≠ 출고 — shipped=True 일 때만 '발송함'. 이 몰의 주문만 바뀐다."""
    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"ok": True, **store.set_tracking(eng, mall_id, body.rows, shipped=body.shipped)}


class _MgrIssueIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field("담당자", max_length=40)
    role: Literal["view", "request", "settle"] = "request"  # 보기만 · 보기+요청 · +정산 금액 확인


class _MgrRoleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["view", "request", "settle"]


class _ExtendIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    closes_at: str = Field(..., max_length=25)


@router.post("/admin/api/corpmall/{mall_id}/extend", dependencies=[api])
def corpmall_extend(mall_id: str, body: _ExtendIn):
    store, eng = _corp()
    try:
        return {"ok": True, "closes_at": store.extend_close(eng, mall_id, body.closes_at)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/admin/api/corpmall/{mall_id}/managers", dependencies=[api])
def corpmall_managers(mall_id: str):
    from app.services.corpmall import manager

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"managers": manager.list_managers(eng, mall_id)}


@router.post("/admin/api/corpmall/{mall_id}/managers", dependencies=[api])
def corpmall_manager_issue(mall_id: str, body: _MgrIssueIn):
    """발주처 담당자 링크 — 원문 링크는 이 응답에만 (서버는 해시만)."""
    from app.services.corpmall import manager

    store, eng = _corp()
    try:
        return {"ok": True, **manager.issue(eng, mall_id, body.label, body.role)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/managers/{manager_id}/role", dependencies=[api])
def corpmall_manager_role(mall_id: str, manager_id: str, body: _MgrRoleIn):
    """담당자 권한 바꾸기 — 링크는 그대로."""
    from app.services.corpmall import manager

    store, eng = _corp()
    try:
        return {"ok": True, **manager.set_role(eng, mall_id, manager_id, body.role)}
    except store.MallError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/admin/api/corpmall/{mall_id}/managers/{manager_id}/revoke", dependencies=[api])
def corpmall_manager_revoke(mall_id: str, manager_id: str):
    from app.services.corpmall import manager

    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    if not manager.revoke(eng, mall_id, manager_id):
        raise HTTPException(404, "manager not found or already revoked")
    return {"ok": True}


@router.get("/admin/api/corpmall-manual", dependencies=[api])
def corpmall_manual_fields():
    from app.services.corpmall import manual

    return {"fields": [{"key": k, "label": lb, "max": n} for k, lb, n in manual.MALL_FIELDS], "common": manual.COMMON}


@router.post("/admin/api/corpmall/{mall_id}/mark", dependencies=[api])
def corpmall_mark(mall_id: str, body: _MallMarkIn):
    store, eng = _corp()
    _mall_or_404(store, eng, mall_id)
    return {"ok": True, "n": store.mark(eng, mall_id, body.order_ids, body.status)}


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

    from app.services.trend_posts import cover as _cover
    from app.services.trend_posts.render import cover as hero

    return {**post.model_dump(mode="json"), "status_label": STATUS_LABEL[post.status],
            "issues": svc.check(post), "public_url": post_url(post) if post.status == "approved" else None,
            "hero": hero(post), "cover_running": _cover.running(post.id)}


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
    if post.conclusion == "hold" and post.cover is None:   # 2026-11-20 보류 글 대표 그림 (AI, 한 번)
        from app.services.trend_posts import cover

        cover.start(svc, post.id)
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
    if action == "cover":                        # 2026-11-20 보류 글 AI 대표 그림 다시 만들기
        from app.services.trend_posts import cover

        post = _post_call(svc.get, post_id)
        if post.conclusion != "hold":
            raise HTTPException(400, "AI 그림은 보류 글에만 만들어요 (구매 글은 상품 사진을 써요).")
        if not cover.start(svc, post_id):
            raise HTTPException(400, "그림을 만들 수 없어요 (이미 만드는 중이거나 그림 도구가 꺼져 있어요).")
        return {**_post_out(svc, post), "cover_running": True}
    if action == "delete":                       # 2026-11-21 v1.1 초안·반려·내린 글 지우기 (대표 그림 파일도)
        from app.services.trend_posts import cover

        post = _post_call(svc.delete, post_id)
        if post.cover:
            for f in cover.image_dir().glob(post.id + "*"):
                if f.suffix in (".png", ".webp"):
                    f.unlink(missing_ok=True)
        return {"deleted": True, "id": post.id}
    calls = {"submit": lambda: svc.submit(post_id), "approve": lambda: svc.approve(post_id, note),
             "reject": lambda: svc.reject(post_id, note or ""), "withdraw": lambda: svc.withdraw(post_id, note),
             "reopen": lambda: svc.reopen(post_id)}
    if action not in calls:
        raise HTTPException(404, "없는 동작이에요.")
    return _post_out(svc, _post_call(calls[action]))


# ── 트렌드 글 피드백 (2026-11-21 첫 버전, 설계 §6-8): 확인 필요 목록 · 글 판별 집계 · 개선 기록. 자동 수정·내림 없음 ──
def _feedback_call(fn, *args):
    from app.services.trend_posts.feedback import FeedbackError

    try:
        return fn(*args)
    except FeedbackError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/admin/api/trend-feedback", dependencies=[api])
def trend_feedback_overview():
    from app.services.trend_posts import feedback as fb

    st = fb.FeedbackStore()
    return {"needs_check": st.needs_check(), "by_version": st.by_version("customer"),
            "operator": st.by_version("operator"), "improvements": st.improvements(),
            "labels": {"ratings": fb.RATINGS, "neg": fb.NEG_REASONS, "pos": fb.POS_REASONS}}


@router.get("/admin/api/chat-feedback", dependencies=[api])
def chat_feedback_overview():
    """2026-11-21 대화 답 피드백 — 신호 종류별 물은 수·응답·도움 평가·칩 비율, 최근 나쁨(사람 검수 샘플).
    결정 신호가 있을 때만 묻기 때문에 '대화 전체 만족도'가 아니다."""
    from app.services.chat import answer_feedback as afb

    st = afb.AnswerFeedbackStore()
    return {"customer": st.overview("customer"), "operator": st.overview("operator"),
            "labels": {"ratings": afb.RATINGS, "neg": afb.NEG_REASONS, "signals": afb.SIGNALS},
            "bias_note": "상품을 거의 골랐다는 신호가 있을 때만 물어요 — 못 찾고 떠난 대화는 여기 없어요."}


@router.get("/admin/api/coupang-gaps", dependencies=[api])
def coupang_gaps_overview(days: int = 28):
    """2026-11-22 '쿠팡 빈칸' — 쿠팡이 0건을 주거나 받은 것이 모두 걸러진 검색어, 바꿔 쓸 말로 다시 찾아 나온 것.
    검색어·날짜·횟수만(세션·손님 문장 없음). 운영자가 바꿔 쓸 말 표·트렌드 글 주제·셀러 입점 후보로 판단."""
    from app.services.commerce import coupang_gaps as cg

    days = max(1, min(int(days or 28), 365))
    return {"days": days, "enabled": cg.enabled(), "items": cg.GapStore().overview(days),
            "synonyms": [{k: r[k] for k in ("from", "to", "kind", "when")} for r in cg.synonym_rows()],
            "note": "쿠팡 파트너스 검색 API 기준 — 쿠팡 사이트에 상품이 없다는 뜻은 아니에요."}


@router.get("/admin/api/coupang-gaps/leads", dependencies=[api])
def coupang_gaps_leads(days: int = 28, format: str = Query("json", pattern="^(json|csv)$")):  # noqa: A002
    """2026-11-25 창 5 준비 — 셀러 영업 후보: 쿠팡 빈칸 검색어 × 네이버 식품 순위, 우선순위. format=csv 는 엑셀용 내려받기."""
    from fastapi.responses import Response

    from app.services.commerce import coupang_gaps as cg

    days = max(1, min(int(days or 28), 365))
    rows = cg.seller_leads(days)
    if format == "csv":
        return Response(cg.seller_leads_csv(rows), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="seller_leads_{days}d.csv"'})  # fmt: skip
    return {"days": days, "items": rows, "note": cg.LEAD_NOTE}


class _CheckedIn(BaseModel):
    note: str | None = Field(None, max_length=200)


@router.post("/admin/api/trend-feedback/{fid}/checked", dependencies=[api])
def trend_feedback_checked(fid: int, body: _CheckedIn | None = None):
    from app.services.trend_posts import feedback as fb

    if not fb.FeedbackStore().mark_checked(fid, body.note if body else None):
        raise HTTPException(404, "없거나 이미 확인한 평가예요.")
    return {"ok": True}


class _ImprovementIn(BaseModel):
    day: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    basis: str = Field(..., min_length=1, max_length=500)
    change: str = Field(..., min_length=1, max_length=500)
    scope: str = Field(..., pattern="^(post|rule)$")
    post_id: str | None = Field(None, max_length=120)
    rules_from: str | None = Field(None, max_length=40)
    rules_to: str | None = Field(None, max_length=40)
    approver: str = Field(..., min_length=1, max_length=60)
    check_due: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


@router.post("/admin/api/trend-feedback/improvements", dependencies=[api])
def trend_feedback_add_improvement(body: _ImprovementIn):
    from app.services.trend_posts import feedback as fb

    return _feedback_call(fb.FeedbackStore().add_improvement, body.model_dump())


class _ResultIn(BaseModel):
    result: str = Field(..., max_length=10)


@router.post("/admin/api/trend-feedback/improvements/{iid}/result", dependencies=[api])
def trend_feedback_result(iid: int, body: _ResultIn):
    from app.services.trend_posts import feedback as fb

    if not _feedback_call(fb.FeedbackStore().set_result, iid, body.result):
        raise HTTPException(404, "없는 개선 기록이에요.")
    return {"ok": True}


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


# ── 고객 문의(CS) — 2026-11-23 창 4 ③: 사람 필수 대기열. 종결·회신은 여기(관리자 토큰)에서만 ──
class _CsAnswerIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


@router.get("/admin/api/cs/tickets", dependencies=[api])
def cs_tickets_list(status: str | None = Query(None, pattern="^(open|answered|closed)$")):
    from app.services.cs import tickets

    return {"tickets": tickets.queue(status)}


@router.post("/admin/api/cs/tickets/{ticket_id}/answer", dependencies=[api])
def cs_ticket_answer(ticket_id: str, body: _CsAnswerIn):
    from app.services.cs import tickets

    t = tickets.answer(ticket_id, body.text, by="operator")
    if t is None:
        raise HTTPException(404, "ticket not found")
    return {"ok": True, "ticket": t}


@router.post("/admin/api/cs/tickets/{ticket_id}/close", dependencies=[api])
def cs_ticket_close(ticket_id: str):
    from app.services.cs import tickets

    t = tickets.close(ticket_id, by="operator")
    if t is None:
        raise HTTPException(404, "ticket not found")
    return {"ok": True, "ticket": t}


# ── 클릭·구매 연결 (2026-11-24, 병행 창): 노출 → 클릭 → 쿠팡 클릭·주문 주간 보고 — 측정용, 순위에 안 씀 ──
@router.get("/admin/measure")
def admin_measure(request: Request):
    return _page(request, WEB / "measure.html")


@router.get("/admin/api/measure/report", dependencies=[api])
def admin_measure_report(start: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
                         end: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
                         unit: str = Query("week", pattern="^(day|week|month|total)$")):
    """기간 보고 — 시작일~끝일(400일 안)을 일·주·월·합계로. 금액 포함(관리자 화면 전용)."""
    from app.services.measure import coupang_report

    try:
        return coupang_report.report(start=date.fromisoformat(start), end=date.fromisoformat(end), unit=unit,
                                     with_money=True)  # fmt: skip
    except ValueError as e:
        raise HTTPException(400, "기간은 끝일이 시작일 뒤이고 400일 안이어야 해요") from e


@router.get("/admin/api/measure/weekly", dependencies=[api])
def admin_measure_weekly(weeks: int = Query(4, ge=1, le=26)):
    from app.services.measure import coupang_report

    return coupang_report.weekly(weeks=weeks, with_money=True)


# ── CS 탭 (2026-11-23 창 4 ④): 사람 필수 대기열 · 노출 중지 상품 · 분야 판단 검수 ──
@router.get("/admin/cs")
def admin_cs(request: Request):
    return _page(request, WEB / "cs.html")


class _CsJudgeIn(BaseModel):
    verdict: str = Field(..., pattern="^(right|wrong|unsure)$")
    should: str | None = Field(None, max_length=20)


@router.get("/admin/api/cs/review", dependencies=[api])
def cs_review_samples(days: int = Query(7, ge=1, le=90)):
    from app.services.cs import review

    return review.samples(days)


@router.post("/admin/api/cs/review/{sample_id}", dependencies=[api])
def cs_review_judge(sample_id: str, body: _CsJudgeIn):
    """판정만 남는다 (문장 없음). 샘플 번호는 최근 90일 샘플에 있어야 한다."""
    from app.services.cs import review

    if not re.fullmatch(r"[0-9a-f]{12}", sample_id or ""):
        raise HTTPException(404, "sample not found")
    hit = next((it for g in review.samples(90, per_domain=10**6)["groups"] for it in g["items"] if it["id"] == sample_id), None)
    if hit is None:
        raise HTTPException(404, "sample not found")
    try:
        return {"ok": True, "verdict": review.judge(sample_id, body.verdict, body.should, domain=hit["domain"])}
    except ValueError as e:
        raise HTTPException(400, f"bad {e}") from e


# ── 식품 안전 신고 상품 노출 임시 중지 — 2026-11-23 창 4 ③-2. 풀기는 여기(관리자 토큰)에서만 ──
class _CsBlockIn(BaseModel):
    product_id: str = Field(..., pattern=r"^\d{1,20}$")
    ticket_id: str | None = Field(None, max_length=40)


@router.get("/admin/api/cs/blocked", dependencies=[api])
def cs_blocked_list():
    from app.services.cs import blocked

    return {"products": blocked.listing()}


@router.post("/admin/api/cs/blocked", dependencies=[api])
def cs_block(body: _CsBlockIn):
    """신고 티켓의 후보 상품 중 운영자가 고른 것을 막는다 (후보에 없는 번호는 받지 않음)."""
    from app.services.cs import blocked, tickets

    title = ""
    if body.ticket_id:
        t = next((x for x in tickets.queue() if x["id"] == body.ticket_id), None)
        if t is None:
            raise HTTPException(404, "ticket not found")
        hit = next((p for p in t.get("products") or [] if p["product_id"] == body.product_id), None)
        if hit is None:
            raise HTTPException(400, "product is not a candidate of this ticket")
        title = hit.get("title") or ""
    return {"ok": True, "product": blocked.block(body.product_id, title=title, ticket_id=body.ticket_id, by="operator")}


@router.post("/admin/api/cs/blocked/{product_id}/unblock", dependencies=[api])
def cs_unblock(product_id: str):
    from app.services.cs import blocked

    got = blocked.unblock(product_id, by="operator")
    if got is None:
        raise HTTPException(404, "not blocked")
    return {"ok": True, "product": got}


# ── 셀러 센터 ① (창 5, 2026-11-25) — 셀러 만들기·초대 코드·입점 승인/정지/종료(운영자만). 고객 화면 노출 없음 ──
class _SellerContactIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field("", max_length=30)
    email: str = Field("", max_length=120)
    phone: str = Field("", max_length=20)


class _SellerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., max_length=60)
    kind: Literal["direct", "consign"]
    contact: _SellerContactIn
    memo: str = Field("", max_length=200)


class _SellerStatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["active", "suspended", "ended"]
    reason: str = Field(..., min_length=1, max_length=200)


def _seller():
    from app.services.seller import store

    return store, store.engine()


def _seller_call(store, fn):
    try:
        return fn()
    except store.SellerError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/admin/api/seller", dependencies=[api])
def seller_list():
    store, eng = _seller()
    from app.services.seller import catalog

    links = catalog.store_urls(catalog.engine())
    slugs = catalog.slugs(catalog.engine())
    return {"sellers": [dict(x, store_url=links.get(x["seller_id"], ""), slug=slugs.get(x["seller_id"], ""),
                             shop_preview=f"/admin/seller/{slugs.get(x['seller_id']) or x['seller_id']}/shop")
                        for x in store.list_sellers(eng)]}  # fmt: skip


class _SlugIn(BaseModel):
    slug: str = Field("", max_length=40)


@router.post("/admin/api/seller/{seller_id}/slug", dependencies=[api])
def seller_slug(seller_id: str, body: _SlugIn):
    """셀러 주소 이름 (/shop/renerpaint) — 같은 이름의 다른 회사면 막고 후보를 알려 준다 (2026-11-25)."""
    store, _eng = _seller()
    from app.services.seller import catalog

    return {"ok": True, **_seller_call(store, lambda: catalog.set_slug(catalog.engine(), seller_id, body.slug, by="operator"))}


class _StoreUrlIn(BaseModel):
    url: str = Field("", max_length=300)


@router.post("/admin/api/seller/{seller_id}/store", dependencies=[api])
def seller_store_url(seller_id: str, body: _StoreUrlIn):
    """셀러 몰(판매처) 주소 — 스마트스토어면 연동 상품의 빈 판매처 링크도 채운다 (2026-11-25)."""
    store, _eng = _seller()
    from app.services.seller import catalog

    return {"ok": True, **_seller_call(store, lambda: catalog.set_store_url(catalog.engine(), seller_id, body.url, by="operator"))}


@router.post("/admin/api/seller", dependencies=[api])
def seller_create(body: _SellerIn):
    store, eng = _seller()
    got = _seller_call(store, lambda: store.create_seller(eng, name=body.name, kind=body.kind,
                                                          contact=body.contact.model_dump(), memo=body.memo, by="operator"))  # fmt: skip
    return {"ok": True, "seller": got}


@router.get("/admin/api/seller/{seller_id}", dependencies=[api])
def seller_detail(seller_id: str):
    store, eng = _seller()
    got = store.detail(eng, seller_id)
    if got is None:
        raise HTTPException(404, "seller not found")
    return {"seller": got}


@router.post("/admin/api/seller/{seller_id}/key", dependencies=[api])
def seller_issue_key(seller_id: str):
    """초대 코드 — 원문은 이 응답에만. 옛 코드는 막힌다."""
    store, eng = _seller()
    return {"ok": True, **_seller_call(store, lambda: store.issue_key(eng, seller_id, by="operator"))}


@router.post("/admin/api/seller/{seller_id}/key/revoke", dependencies=[api])
def seller_revoke_keys(seller_id: str):
    store, eng = _seller()
    return {"ok": True, "revoked": _seller_call(store, lambda: store.revoke_keys(eng, seller_id, by="operator"))}


@router.post("/admin/api/seller/{seller_id}/status", dependencies=[api])
def seller_status(seller_id: str, body: _SellerStatusIn):
    store, eng = _seller()
    got = _seller_call(store, lambda: store.set_status(eng, seller_id, body.status, by="operator", reason=body.reason))
    return {"ok": True, "seller": got}



# ── 셀러 상품 검수 ② (창 5, 2026-11-25) — 판매자 표기 / 확인됨 분리, 승인·반려·확인은 운영자만. 고객 화면 노출 없음 ──
class _SellerVerifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Literal["origin", "cert", "brix"]
    value: str | float | None = None
    note: str = Field("", max_length=200)


class _SellerReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approved", "rejected"]
    note: str = Field("", max_length=200)


@router.get("/admin/seller")
def admin_seller_page(request: Request):
    return _page(request, WEB / "seller.html")


@router.get("/admin/api/seller-products", dependencies=[api])
def seller_products_queue(status: str = Query("pending", pattern="^(pending|approved|rejected|withdrawn|all)$"),
                          seller_id: str | None = Query(None, max_length=12)):  # fmt: skip
    from app.services.seller import products

    return {"products": products.queue(products.engine(), status, seller_id), "statuses": products.STATUSES}


@router.post("/admin/api/seller-products/{product_id}/verify", dependencies=[api])
def seller_product_verify(product_id: str, body: _SellerVerifyIn):
    from app.services.seller import products, store

    return {"ok": True, "product": _seller_call(store, lambda: products.verify(products.engine(), product_id, body.key,
                                                                               body.value, by="operator", note=body.note))}  # fmt: skip


@router.post("/admin/api/seller-products/{product_id}/review", dependencies=[api])
def seller_product_review(product_id: str, body: _SellerReviewIn):
    from app.services.seller import products, store

    return {"ok": True, "product": _seller_call(store, lambda: products.review(products.engine(), product_id, body.decision,
                                                                               by="operator", note=body.note))}  # fmt: skip



# ── 셀러 AI 상세페이지 ⑦ (창 5, 2026-11-25) — 검수 요청 목록 · 미리보기 · 승인/반려 (고객 노출 없음) ──
class _DetailReviewIn(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str = Field("", max_length=200)


@router.get("/admin/api/seller-details", dependencies=[api])
def seller_details_queue(status: str = Query("submitted", pattern="^(draft|submitted|approved|rejected|all)$")):
    from app.services.seller import detail_page

    return {"details": detail_page.queue(detail_page.engine(), status), "statuses": detail_page.STATUSES}


@router.post("/admin/api/seller-details/{detail_id}/review", dependencies=[api])
def seller_detail_review(detail_id: str, body: _DetailReviewIn):
    from app.services.seller import detail_page, store

    return {"ok": True, **_seller_call(store, lambda: detail_page.review(detail_page.engine(), detail_id, body.decision,
                                                                         by="operator", note=body.note))}  # fmt: skip


@router.get("/admin/seller-details/{detail_id}/preview", dependencies=[api])
def seller_detail_preview(detail_id: str):
    from app.services.seller import detail_page, store

    page = _seller_call(store, lambda: detail_page.operator_preview(detail_page.engine(), detail_id))
    return HTMLResponse(page, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex",
                                       "Content-Security-Policy": DETAIL_CSP})  # fmt: skip


@router.get("/admin/seller-products/{product_id}/preview", dependencies=[api])
def seller_product_preview(product_id: str):
    """상품 검수 옆 '손님 화면 미리보기' — 상세페이지가 없으면 상품 정보만으로 (2026-11-25)."""
    from app.services.seller import detail_page, store

    page = _seller_call(store, lambda: detail_page.product_preview(detail_page.engine(), product_id))
    return HTMLResponse(page, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex",
                                       "Content-Security-Policy": DETAIL_CSP})  # fmt: skip


@router.get("/admin/seller/{seller_id}/sample", dependencies=[api])
def seller_shop_sample(seller_id: str):
    """미니숍 샘플 보기 (2026-11-25 시험용) — 승인 전 상품까지, 상세페이지가 없으면 상품 정보로 만든 규칙 초안.
    운영자만 · 손님에게 보이지 않음. 고칠 곳을 찾을 때."""
    from app.services.seller import detail_page, store

    try:
        from app.services.seller import catalog

        seller_id = getattr(catalog, "resolve_seller", lambda e, k: None)(catalog.engine(), seller_id) or seller_id
    except Exception:  # noqa: BLE001
        pass
    page = _seller_call(store, lambda: detail_page.shop_page(detail_page.engine(), seller_id, sample=True,
                                                             banner="미니숍 샘플 — 승인 전 상품 포함 · 손님에게 보이지 않아요"))  # fmt: skip
    return HTMLResponse(page, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex",
                                       "Content-Security-Policy": DETAIL_CSP})  # fmt: skip


@router.get("/admin/seller/{key}/preview/{product_id}", dependencies=[api])
def seller_product_preview_named(key: str, product_id: str):
    """회사 이름이 보이는 상품 미리보기 주소 (/admin/seller/renerpaint/preview/P…) — 그 셀러 상품만."""
    from app.services.seller import catalog, detail_page, products, store

    sid = catalog.resolve_seller(catalog.engine(), key)
    with detail_page.engine().connect() as c:
        owner = c.execute(products.t_product.select().where(products.t_product.c.product_id == product_id)).mappings().first()
    if not sid or owner is None or owner["seller_id"] != sid:
        raise HTTPException(404, "없는 상품이에요")
    return seller_product_preview(product_id)


@router.get("/admin/seller/{seller_id}/shop", dependencies=[api])
def seller_shop_preview(seller_id: str):
    """⑧ 미니숍 미리보기 — 승인된 상세페이지만. 주소 이름(/admin/seller/renerpaint/shop)이나 셀러 번호로."""
    from app.services.seller import catalog, detail_page, store

    seller_id = catalog.resolve_seller(catalog.engine(), seller_id) or seller_id
    page = _seller_call(store, lambda: detail_page.shop_page(detail_page.engine(), seller_id,
                                                             banner="운영자 미니숍 미리보기 — 손님에게 보이지 않아요"))  # fmt: skip
    return HTMLResponse(page, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex",
                                       "Content-Security-Policy": DETAIL_CSP})  # fmt: skip


class _BizVerifyIn(BaseModel):
    ok: bool


@router.get("/admin/api/seller-biz", dependencies=[api])
def seller_biz_list():
    """⑧ 미니숍 공개 — 셀러 사업자 정보 · 확인 · 공개 동의 · 공개 여부, 그리고 운영사 쪽 정식 공개에 빠진 것."""
    from app.services.seller import shop_public

    return {"sellers": shop_public.biz_list(shop_public.engine()), "mode": shop_public.mode(),
            "formal_missing": shop_public.formal_missing()}  # fmt: skip


class _BizInfoIn(BaseModel):
    info: dict


@router.post("/admin/api/seller-biz/{seller_id}/save", dependencies=[api])
def seller_biz_save(seller_id: str, body: _BizInfoIn):
    """운영자가 입점 서류를 보고 판매자 정보를 대신 적는다 — 저장하면 확인이 풀리고, '확인'은 따로."""
    from app.services.seller import shop_public, store

    return {"ok": True, "biz": _seller_call(store, lambda: shop_public.biz_save_operator(shop_public.engine(), seller_id,
                                                                                        body.info, by="operator"))}  # fmt: skip


@router.post("/admin/api/seller-biz/{seller_id}/verify", dependencies=[api])
def seller_biz_verify(seller_id: str, body: _BizVerifyIn):
    from app.services.seller import shop_public, store

    return {"ok": True, "biz": _seller_call(store, lambda: shop_public.biz_verify(shop_public.engine(), seller_id,
                                                                                ok=body.ok, by="operator"))}  # fmt: skip


class _JoinDecideIn(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject|trial)$")
    note: str = Field("", max_length=300)


@router.get("/admin/api/seller-joins", dependencies=[api])
def seller_joins(status: str = Query("open", pattern="^(open|all|received|check|trial|rejected|approved|withdrawn)$")):
    """⑩ 입점 신청 — AI 1차 분석 결과와 함께 (연락처는 가려서)."""
    from app.services.seller import join

    return {"joins": join.queue(join.engine(), status), "statuses": join.STATUSES}


@router.get("/admin/api/seller-joins/{join_id}", dependencies=[api])
def seller_join_detail(join_id: str):
    from app.services.seller import join, store

    return {"join": _seller_call(store, lambda: join.detail(join.engine(), join_id))}


@router.get("/admin/seller-joins/{join_id}/file/{kind}", dependencies=[api])
def seller_join_file(join_id: str, kind: str):
    """제출 서류 — 운영자만, 저장 없이 보기."""
    from fastapi.responses import Response

    from app.services.seller import join, store

    data, typ = _seller_call(store, lambda: join.file_bytes(join.engine(), join_id, kind))
    return Response(data, media_type=typ, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex",
                                                   "Content-Disposition": "inline", "X-Content-Type-Options": "nosniff"})  # fmt: skip


@router.post("/admin/api/seller-joins/{join_id}/decide", dependencies=[api])
def seller_join_decide(join_id: str, body: _JoinDecideIn):
    """입점 승인·반려·수동 체험 코드 — 운영자만 (AI 는 승인·반려하지 않는다)."""
    from app.services.seller import join, store

    return {"ok": True, **_seller_call(store, lambda: join.decide(join.engine(), join_id, body.decision, by="operator",
                                                                  note=body.note))}  # fmt: skip


DETAIL_CSP = "default-src 'none'; img-src https:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"


# ── 셀러 SCM ③ (창 5, 2026-11-25) — 품절·출고 지연·송장 미등록 숫자만 (받는 분 정보 없음) ──
@router.get("/admin/api/seller-alerts", dependencies=[api])
def seller_alerts():
    from app.services.seller import scm

    return {"alerts": scm.all_alerts(scm.engine()), "delay_biz_days": scm.DELAY_BIZ_DAYS}



# ── 죽은 셀러몰 찾기 (2026-11-25) — 판매 없음·클릭 없음(측정 전)·변화 없음. 목록·알림까지만, 정지는 운영자 ──
@router.get("/admin/api/seller-health", dependencies=[api])
def seller_health_report():
    from app.services.seller import health, scm

    return health.report(scm.engine())



# ── 셀러 월 이용료 ④ (2026-11-25) — 표시·기록만, 실제 청구 없음. 금액·조정·발행·입금·면제는 운영자만 ──
class _SellerPlanIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_name: str = Field(..., max_length=40)
    monthly_fee: int = Field(..., ge=0, le=10_000_000)
    vat_mode: Literal["excluded", "included"]
    starts_on: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    memo: str = Field("", max_length=200)


class _InvAdjustIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: int = Field(..., ge=0, le=10_000_000)
    reason: str = Field(..., min_length=1, max_length=200)


class _InvMarkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to: Literal["issued", "paid", "waived"]
    note: str = Field("", max_length=200)
    tax_invoice_no: str = Field("", max_length=40)


@router.get("/admin/api/seller-billing", dependencies=[api])
def seller_billing_summary():
    from app.services.seller import billing

    return {"sellers": billing.summary(billing.engine()), "vat_modes": billing.VAT_MODES, "statuses": billing.INV_STATUS}


@router.get("/admin/api/seller-billing/{seller_id}", dependencies=[api])
def seller_billing_detail(seller_id: str):
    from app.services.seller import billing

    eng = billing.engine()
    billing.ensure_invoices(eng)
    return {"plan": billing.plan_of(eng, seller_id), "invoices": billing.invoices(eng, seller_id)}


@router.post("/admin/api/seller-billing/{seller_id}/plan", dependencies=[api])
def seller_billing_plan(seller_id: str, body: _SellerPlanIn):
    from app.services.seller import billing, store

    eng = billing.engine()
    got = _seller_call(store, lambda: billing.set_plan(eng, seller_id, **body.model_dump(), by="operator"))
    billing.ensure_invoices(eng)
    return {"ok": True, "plan": got}


@router.post("/admin/api/seller-invoices/{invoice_id}/adjust", dependencies=[api])
def seller_invoice_adjust(invoice_id: str, body: _InvAdjustIn):
    from app.services.seller import billing, store

    return {"ok": True, "invoice": _seller_call(store, lambda: billing.adjust(billing.engine(), invoice_id, body.amount,
                                                                              by="operator", reason=body.reason))}  # fmt: skip


@router.post("/admin/api/seller-invoices/{invoice_id}/mark", dependencies=[api])
def seller_invoice_mark(invoice_id: str, body: _InvMarkIn):
    from app.services.seller import billing, store

    return {"ok": True, "invoice": _seller_call(store, lambda: billing.mark(billing.engine(), invoice_id, body.to, by="operator",
                                                                            note=body.note, tax_invoice_no=body.tax_invoice_no))}  # fmt: skip
