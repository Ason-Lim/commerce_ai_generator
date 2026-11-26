"""⑩ 입점 신청 (창 5, 2026-11-25) — 공개 신청 페이지 · 접수 · 신청 확인.

  GET  /join              입점 신청 페이지 (검색 노출 막음)
  POST /join/api/send     신청 + 서류(base64) → 1차 분석 → 결과·신청 확인 코드
  POST /join/api/look     신청 확인 코드로 진행 상황 (자동 체험 코드는 처음 한 번만)
  POST /join/api/withdraw 신청 철회

운영자 화면·API 는 app/admin/routes.py (/admin/api/seller-joins …).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.corpmall_routes import NOINDEX, _client
from app.services.seller import join

router = APIRouter(tags=["seller-join"], include_in_schema=False)
PAGE = Path(__file__).resolve().parents[1] / "services" / "seller" / "web" / "join.html"
TERMS_PAGE = PAGE.with_name("seller_terms.html")  # 2026-11-26 셀러 입점 이용약관(초안)


class FileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field("", max_length=120)
    type: str = Field(..., max_length=40)
    data: str = Field(..., max_length=7_200_000)


class JoinIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trade_name: str = Field(..., max_length=60)
    biz_no: str = Field(..., max_length=20)
    contact_name: str = Field(..., max_length=30)
    email: str = Field("", max_length=120)
    phone: str = Field("", max_length=20)
    store_url: str = Field("", max_length=300)
    products: str = Field(..., max_length=500)
    files: dict[str, FileIn] = Field(default_factory=dict)
    consent: bool = False
    website: str = Field("", max_length=50)  # 숨은 칸 (봇)


class TokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(..., max_length=40)


def _err(e: Exception) -> JSONResponse:
    return JSONResponse({"ok": False, "error": str(e)}, status_code=400, headers=NOINDEX)


@router.get("/join")
def join_page():
    return FileResponse(PAGE, headers=NOINDEX)


@router.get("/seller/terms")
def seller_terms_page():
    return FileResponse(TERMS_PAGE, headers=NOINDEX)


@router.post("/join/api/send")
def join_send(body: JoinIn, request: Request):
    raw = body.model_dump()
    raw["files"] = {k: v for k, v in raw["files"].items() if k in join.FILE_KINDS}
    try:
        got = join.submit(join.engine(), raw, _client(request))
    except join.store.SellerError as e:
        return _err(e)
    return JSONResponse({"ok": True, **got}, headers=NOINDEX)


@router.post("/join/api/look")
def join_look(body: TokenIn):
    try:
        return JSONResponse({"ok": True, **join.check(join.engine(), body.token)}, headers=NOINDEX)
    except join.store.SellerError as e:
        return _err(e)


@router.post("/join/api/withdraw")
def join_withdraw(body: TokenIn):
    try:
        return JSONResponse({"ok": True, **join.withdraw(join.engine(), body.token)}, headers=NOINDEX)
    except join.store.SellerError as e:
        return _err(e)
