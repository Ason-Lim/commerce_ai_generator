"""셀러 센터 화면과 셀러 쪽 API (창 5 ①, 2026-11-25). 설계 claude/stage5_seller_design_2026-11-25.md.

  GET  /seller                 셀러 센터 (#k=초대 코드, 검색 노출 막음)
  POST /seller/api/me          {key} → 내 셀러 정보(연락처는 가림)
  POST /seller/api/contact     {key, contact} → 내 담당자 연락처 바꾸기

셀러 쪽 API 는 셀러 번호를 받지 않는다 — 코드로만 셀러를 정한다(셀러 간 격리).
운영자 API 는 app/admin/routes.py (/admin/api/seller/...).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.corpmall_routes import NOINDEX, _client
from app.services.seller import store

router = APIRouter(tags=["seller"], include_in_schema=False)
PAGE = Path(__file__).resolve().parents[1] / "services" / "seller" / "web" / "seller.html"


class KeyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)


class ContactIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field("", max_length=30)
    email: str = Field("", max_length=120)
    phone: str = Field("", max_length=20)


class ContactUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    contact: ContactIn


def _err(e: Exception) -> JSONResponse:
    return JSONResponse({"ok": False, "error": str(e)}, status_code=400, headers=NOINDEX)


@router.get("/seller")
def seller_page():
    return FileResponse(PAGE, headers=NOINDEX)


@router.post("/seller/api/me")
def seller_me(body: KeyIn, request: Request):
    try:
        return JSONResponse(
            {"ok": True, "seller": store.me(store.engine(), body.key, _client(request))}, headers=NOINDEX
        )
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/contact")
def seller_contact(body: ContactUpdateIn, request: Request):
    try:
        got = store.update_contact(store.engine(), body.key, _client(request), body.contact.model_dump())
        return JSONResponse({"ok": True, "seller": got}, headers=NOINDEX)
    except store.SellerError as e:
        return _err(e)
