"""셀러 센터 화면과 셀러 쪽 API (창 5 ①, 2026-11-25). 설계 claude/stage5_seller_design_2026-11-25.md.

  GET  /seller                 셀러 센터 (#k=초대 코드, 검색 노출 막음)
  POST /seller/api/me          {key} → 내 셀러 정보(연락처는 가림)
  POST /seller/api/contact     {key, contact} → 내 담당자 연락처 바꾸기
  POST /seller/api/products         {key} → 내 상품 목록 (판매자 표기 / 확인됨 구분)
  POST /seller/api/products/save    {key, product_id?, fields} → 새 상품·고치기 (→ 검수 대기)
  POST /seller/api/products/csv     {key, csv} → 한꺼번에 등록 (한 줄이라도 틀리면 저장 안 함)
  POST /seller/api/products/withdraw {key, product_id} → 판매 중지

셀러 쪽 API 는 셀러 번호를 받지 않는다 — 코드로만 셀러를 정한다(셀러 간 격리).
운영자 API 는 app/admin/routes.py (/admin/api/seller/...).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.corpmall_routes import NOINDEX, _client
from app.services.seller import products, store

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


class ProductFieldsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., max_length=80)
    volume: str = Field("", max_length=40)
    price: int | str = Field(...)
    ship_fee: int | str | None = None
    sale_url: str = Field("", max_length=300)
    origin: str = Field("", max_length=40)
    cert: str = Field("", max_length=60)
    brix: float | str | None = None


class ProductSaveIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    product_id: str | None = Field(None, max_length=12)
    fields: ProductFieldsIn


class ProductCsvIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    csv: str = Field(..., max_length=200_000)


class ProductIdIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    product_id: str = Field(..., max_length=12)


@router.post("/seller/api/products")
def seller_products(body: KeyIn, request: Request):
    try:
        got = products.list_mine(products.engine(), body.key, _client(request))
        return JSONResponse({"ok": True, "products": got, "csv_template": products.csv_template()}, headers=NOINDEX)
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/products/save")
def seller_product_save(body: ProductSaveIn, request: Request):
    try:
        got = products.save(products.engine(), body.key, _client(request), body.fields.model_dump(), body.product_id)
        return JSONResponse({"ok": True, "product": got}, headers=NOINDEX)
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/products/csv")
def seller_product_csv(body: ProductCsvIn, request: Request):
    try:
        got = products.import_csv(products.engine(), body.key, _client(request), body.csv)
        return JSONResponse(got, status_code=200 if got["ok"] else 400, headers=NOINDEX)
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/products/withdraw")
def seller_product_withdraw(body: ProductIdIn, request: Request):
    try:
        got = products.withdraw(products.engine(), body.key, _client(request), body.product_id)
        return JSONResponse({"ok": True, "product": got}, headers=NOINDEX)
    except store.SellerError as e:
        return _err(e)
