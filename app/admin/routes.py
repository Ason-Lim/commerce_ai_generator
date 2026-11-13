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

from datetime import date
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


@router.post("/admin/api/trends/blog-draft", dependencies=[api])
def trends_blog_draft(body: _DraftIn):
    """Text draft for the applesodda blog (temporary save is done by a person / on request — never published here)."""
    from app.services.trends import surge

    report = surge.load(body.date)
    if not report:
        raise HTTPException(404, "리포트가 없어요. 먼저 리포트를 만들어 주세요.")
    try:
        draft = surge.blog_draft(report, body.keywords)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    # 2026-11-02: 초안 키워드 중 쇼핑커넥트 링크 발급이 필요한 것 — 파일 맨 위 운영 메모 + 화면 표시 (본문에는 넣지 않음)
    needs = _link_needs(draft["keywords"])
    folder = surge.ROOT / "var" / "blog_drafts"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"trend_{report['data_until']}_{'_'.join(draft['keywords'])[:40]}.txt"
    memo = _operator_memo(needs)
    path.write_text((memo + "\n\n" if memo else "")
                    + f"{draft['title']}\n\n태그: {', '.join(draft['tags'])}\n\n{draft['body']}\n", encoding="utf-8")
    return {**draft, "file": str(path.relative_to(surge.ROOT)), "link_needs": needs}


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
