"""B2B 입찰 폐쇄몰 — 직원 화면과 API (2026-11-24). 설계 claude/b2b_closed_mall_auth_2026-11-24.md.

  GET  /corp/{slug}                 직원 선물 페이지 (검색 노출 막음)
  POST /corp/api/{slug}/enter       {code} → 몰·상품·지금 고른 것 (code = 짧은 코드 또는 초대 링크 토큰, 소진 없음)
  POST /corp/api/{slug}/ask         {code, topic, text} → 임직원 문의 (CS 티켓, 답은 같은 코드로 들어오면 보임)
  POST /corp/api/{slug}/choose      {code, item_id, shipping?, consent, verify?} → 선택 저장(마감 전 변경 가능)

운영자 API 는 app/admin/routes.py (/admin/api/corpmall/...).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.services.corpmall import store

router = APIRouter(tags=["corpmall"], include_in_schema=False)
PAGE = Path(__file__).resolve().parents[1] / "services" / "corpmall" / "web" / "mall.html"
NOINDEX = {"X-Robots-Tag": "noindex, nofollow", "Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


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
    topic: str = Field(..., max_length=12)
    text: str = Field(..., max_length=400)


@router.get("/corp/{slug}")
def corp_page(slug: str):
    if not store.SLUG_RE.fullmatch(slug):
        raise HTTPException(404)
    return FileResponse(PAGE, headers=NOINDEX)


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
        got = store.ask(_eng(), slug, body.code, body.topic, body.text, _client(request))
        return JSONResponse({"ok": True, **got}, headers=NOINDEX)
    except store.MallError as e:
        return _err(e)
