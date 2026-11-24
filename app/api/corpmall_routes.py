"""B2B 입찰 폐쇄몰 — 직원 화면과 API (2026-11-24). 설계 claude/b2b_closed_mall_auth_2026-11-24.md.

  GET  /corp/{slug}                 직원 선물 페이지 (검색 노출 막음)
  POST /corp/api/{slug}/enter       {code} → 몰·상품·지금 고른 것 (code = 짧은 코드 또는 초대 링크 토큰, 소진 없음)
  POST /corp/api/{slug}/ask         {code, text, handoff?} → 매뉴얼로 바로 답, 매뉴얼 밖·사람 필수·handoff 면 CS 티켓
  GET  /corp/{slug}/manager         발주처 담당자 화면 (#k=담당자 토큰, 배송 정보 없음)
  POST /corp/api/{slug}/manager/view     {key} → 진행 상황
  POST /corp/api/{slug}/manager/request  {key, kind, label?, date?, n?, text?} → 운영자에게 요청 (CS 티켓)
  GET  /corp/po/{po_no}             공급사 발주 확인 화면 (#k=확인 토큰, 배송 정보 없음)
  POST /corp/api/po/{po_no}/view    {key} → 발주서 내용
  POST /corp/api/po/{po_no}/file    {key} → 그 공급사 전달용 파일(발주서 + 배송 목록 — 정식 발주이고 배송 정보가 남아 있는 동안)
  POST /corp/api/po/{po_no}/ack     {key, name, ship_date?, memo?} → 수신 확인
  POST /corp/api/{slug}/choose      {code, item_id, shipping?, consent, verify?} → 선택 저장(마감 전 변경 가능)

운영자 API 는 app/admin/routes.py (/admin/api/corpmall/...).
"""

from __future__ import annotations

from typing import Literal

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.services.corpmall import store

router = APIRouter(tags=["corpmall"], include_in_schema=False)
PAGE = Path(__file__).resolve().parents[1] / "services" / "corpmall" / "web" / "mall.html"
MANAGER_PAGE = PAGE.with_name("manager.html")
PO_ACK_PAGE = PAGE.with_name("po_ack.html")
NOINDEX = {"X-Robots-Tag": "noindex, nofollow", "Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
# 직원 페이지: 우편번호 찾기(카카오)가 사이트 도메인만 알 수 있게 — 경로(몰 이름)·# 뒤 코드는 보내지 않는다
PAGE_HEADERS = {**NOINDEX, "Referrer-Policy": "strict-origin"}


def _client(request: Request) -> str:
    return (
        request.headers.get("cf-connecting-ip")
        or (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else "")
        or "-"
    )


def _eng():
    return store.engine()


class EnterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(..., max_length=40)


class ShipIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field("", max_length=30)
    phone: str = Field("", max_length=20)
    zipcode: str = Field("", max_length=10)
    address: str = Field("", max_length=200)
    memo: str = Field("", max_length=100)


class ChooseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(..., max_length=40)
    item_id: str = Field(..., max_length=40)
    shipping: ShipIn | None = None
    consent: bool = False
    verify: str | None = Field(None, max_length=8)  # 배송지 바꿀 때 — 처음 넣은 휴대폰 끝 4자리


class AskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(..., max_length=40)
    text: str = Field(..., max_length=400)
    handoff: bool = False  # '그래도 담당자에게 남기기'


_READER: list = []


def _reader():
    """규칙이 모르는 문의의 '종류'만 고르는 AI (corp_cs — 고객 문장 작업이라 OpenAI·장애 시 Claude). 키가 없으면 None → 사람."""
    if not _READER:
        fn = None
        try:
            from app.api.chat_routes import _deepseek_ready

            if _deepseek_ready():
                from app.services.corpmall import assist
                from app.services.nlu.llm_client import LLMClient

                client = LLMClient(
                    assist.AI_PROMPT,
                    provider="deepseek",
                    timeout=15.0,
                    cache="corp_cs",
                    cache_days=30,
                    task="corp_cs",
                    thinking=False,
                )
                fn = lambda text: client.chat_json(text, temperature=0)  # noqa: E731
        except Exception:  # noqa: BLE001
            fn = None
        _READER.append(fn)
    return _READER[0]


@router.get("/corp/{slug}")
def corp_page(slug: str):
    if not store.SLUG_RE.fullmatch(slug):
        raise HTTPException(404)
    return FileResponse(PAGE, headers=PAGE_HEADERS)


def _err(e: store.MallError) -> JSONResponse:
    return JSONResponse({"ok": False, "error": str(e)}, status_code=400, headers=NOINDEX)


@router.post("/corp/api/{slug}/enter")
def corp_enter(slug: str, body: EnterIn, request: Request):
    try:
        return JSONResponse({"ok": True, **store.enter(_eng(), slug, body.code, _client(request))}, headers=NOINDEX)
    except store.MallError as e:
        return _err(e)


@router.post("/corp/api/{slug}/choose")
def corp_choose(slug: str, body: ChooseIn, request: Request):
    try:
        got = store.choose(
            _eng(),
            slug,
            body.code,
            body.item_id,
            _client(request),
            shipping=body.shipping.model_dump() if body.shipping else None,
            consent=body.consent,
            verify=body.verify,
        )
        return JSONResponse({"ok": True, **got}, headers=NOINDEX)
    except store.MallError as e:
        return _err(e)


@router.post("/corp/api/{slug}/ask")
def corp_ask(slug: str, body: AskIn, request: Request):
    try:
        got = store.ask(
            _eng(),
            slug,
            body.code,
            body.text,
            _client(request),
            handoff=body.handoff,
            reader=None if body.handoff else _reader(),
        )
        return JSONResponse({"ok": True, **got}, headers=NOINDEX)
    except store.MallError as e:
        return _err(e)


# ── 발주처 담당자 화면 (2026-11-24) ──
class MgrViewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)


class MgrRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    kind: str = Field(..., max_length=12)
    label: int | None = Field(None, ge=1, le=100000)
    date: str | None = Field(None, max_length=10)
    n: int | None = Field(None, ge=1, le=5000)
    text: str = Field("", max_length=300)


@router.get("/corp/{slug}/manager")
def corp_manager_page(slug: str):
    return FileResponse(MANAGER_PAGE, headers=NOINDEX)


@router.post("/corp/api/{slug}/manager/view")
def corp_manager_view(slug: str, body: MgrViewIn, request: Request):
    from app.services.corpmall import manager

    try:
        return JSONResponse({"ok": True, **manager.view(_eng(), slug, body.key, _client(request))}, headers=NOINDEX)
    except store.MallError as e:
        return _err(e)


@router.post("/corp/api/{slug}/manager/request")
def corp_manager_request(slug: str, body: MgrRequestIn, request: Request):
    from app.services.corpmall import manager

    try:
        got = manager.request(
            _eng(),
            slug,
            body.key,
            _client(request),
            body.kind,
            label=body.label,
            date=body.date,
            n=body.n,
            text=body.text,
        )
        return JSONResponse({"ok": True, **got}, headers=NOINDEX)
    except store.MallError as e:
        return _err(e)


# ── 공급사 발주 확인 (2026-11-24) ──
class PoViewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)


class PoAckIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    name: str = Field(..., max_length=30)
    action: Literal["accept", "change", "cancel_ok"] = "accept"
    agree: bool = False  # '수량·단가·금액·출고 기한을 확인하고 수락합니다' 체크
    ship_date: str | None = Field(None, max_length=10)
    memo: str = Field("", max_length=300)


@router.get("/corp/po/{po_no}")
def corp_po_page(po_no: str):
    return FileResponse(PO_ACK_PAGE, headers=NOINDEX)


@router.post("/corp/api/po/{po_no}/view")
def corp_po_view(po_no: str, body: PoViewIn, request: Request):
    from app.services.corpmall import podoc

    try:
        return JSONResponse(
            {"ok": True, **podoc.public_view(_eng(), po_no, body.key, _client(request))}, headers=NOINDEX
        )
    except store.MallError as e:
        return _err(e)


@router.post("/corp/api/po/{po_no}/ack")
def corp_po_ack(po_no: str, body: PoAckIn, request: Request):
    from app.services.corpmall import podoc

    try:
        eng = _eng()
        p = podoc.respond(
            eng, po_no, body.key, _client(request), action=body.action, name=body.name, agree=body.agree,
            ship_date=body.ship_date, memo=body.memo,
        )  # fmt: skip
        if p["status"] == "cancelled":  # 취소 확인 뒤에는 링크가 닫힌다
            return JSONResponse(
                {"ok": True, "po": {"po_no": po_no, "status": "cancelled", "status_label": p["status_label"]}},
                headers=NOINDEX,
            )
        return JSONResponse({"ok": True, **podoc.public_view(eng, po_no, body.key, _client(request))}, headers=NOINDEX)
    except store.MallError as e:
        return _err(e)


@router.post("/corp/api/po/{po_no}/file")
def corp_po_file(po_no: str, body: PoViewIn, request: Request):
    from urllib.parse import quote

    from fastapi.responses import Response

    from app.services.corpmall import podoc

    try:
        data, name = podoc.supplier_file(_eng(), po_no, body.key, _client(request))
    except store.MallError as e:
        return _err(e)
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={**NOINDEX, "Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"},
    )
