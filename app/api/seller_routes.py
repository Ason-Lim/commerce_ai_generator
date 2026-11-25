"""셀러 센터 화면과 셀러 쪽 API (창 5 ①, 2026-11-25). 설계 claude/stage5_seller_design_2026-11-25.md.

  GET  /seller                 셀러 센터 (#k=초대 코드, 검색 노출 막음)
  POST /seller/api/me          {key} → 내 셀러 정보(연락처는 가림)
  POST /seller/api/contact     {key, contact} → 내 담당자 연락처 바꾸기
  POST /seller/api/products         {key} → 내 상품 목록 (판매자 표기 / 확인됨 구분)
  POST /seller/api/products/save    {key, product_id?, fields} → 새 상품·고치기 (→ 검수 대기)
  POST /seller/api/products/csv     {key, csv} → 한꺼번에 등록 (한 줄이라도 틀리면 저장 안 함)
  POST /seller/api/products/withdraw {key, product_id} → 판매 끄기 (옛 이름)
  POST /seller/api/products/listing {key, product_id?, on} → 판매 켜기·끄기 (검수 없음, product_id 없으면 모두)
  POST /seller/api/health           {key} → '상품 정보 그대로예요' 확인 요청 여부
  POST /seller/api/confirm          {key} → '상품 정보 그대로예요'
  POST /seller/api/billing          {key} → ④ 내 요금제·청구 내역 (보기만, 실제 청구 없음)
  POST /seller/api/ask              {key, text, handoff?} → ⑤ 문의 — 안내문 바로 + 필요하면 CS 티켓 (규칙만, 외부 AI 없음)
  POST /seller/api/asks             {key} → 내 문의와 운영팀 답
  ── ③ SCM (2026-11-25) ──
  POST /seller/api/stock            {key, product_id, stock?, sold_out, restock_on?} → 재고·품절
  POST /seller/api/suppliers        {key} → 내 공급사 · 상품별 공급사 연결 · 재고
  POST /seller/api/suppliers/save   {key, supplier_id?, name, contact?, memo?}
  POST /seller/api/supply           {key, product_id, supplier_id?, sku?} → 상품에 공급사 붙이기 (비우면 직접 출고)
  POST /seller/api/orders           {key} → 주문·발주 묶음·알림 (받는 분은 가림)
  POST /seller/api/orders/csv       {key, csv, entrust_ok} → 판매처 주문 올리기
  POST /seller/api/po               {key} → 새 주문으로 발주 묶음
  POST /seller/api/po/file          {key, batch_id} → 발주서 엑셀 (서버에 남기지 않음)
  POST /seller/api/tracking         form: key, file → 송장 넣기

셀러 쪽 API 는 셀러 번호를 받지 않는다 — 코드로만 셀러를 정한다(셀러 간 격리).
운영자 API 는 app/admin/routes.py (/admin/api/seller/...).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from urllib.parse import quote

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.corpmall_routes import NOINDEX, _client
from app.services.seller import billing, health, products, scm, store
from app.services.seller import chat as seller_chat

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
        got = products.list_mine(scm.engine(), body.key, _client(request))
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
        got = products.withdraw(scm.engine(), body.key, _client(request), body.product_id)
        return JSONResponse({"ok": True, "product": got}, headers=NOINDEX)
    except store.SellerError as e:
        return _err(e)


# ── ③ SCM ──
class StockIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    product_id: str = Field(..., max_length=12)
    stock: int | str | None = None
    sold_out: bool = False
    restock_on: str | None = Field(None, max_length=10)


class SupplierIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    supplier_id: str | None = Field(None, max_length=12)
    name: str = Field(..., max_length=40)
    contact: ContactIn | None = None
    memo: str = Field("", max_length=200)


class SupplyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    product_id: str = Field(..., max_length=12)
    supplier_id: str | None = Field(None, max_length=12)
    sku: str = Field("", max_length=40)


class OrdersCsvIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    csv: str = Field(..., max_length=300_000)
    entrust_ok: bool = False


class BatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    batch_id: str = Field(..., max_length=12)


def _ok(**kw) -> JSONResponse:
    return JSONResponse({"ok": True, **kw}, headers=NOINDEX)


@router.post("/seller/api/stock")
def seller_stock(body: StockIn, request: Request):
    try:
        got = scm.set_stock(scm.engine(), body.key, _client(request), body.product_id, stock=body.stock,
                            sold_out=body.sold_out, restock_on=body.restock_on)  # fmt: skip
        return _ok(stock=got)
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/suppliers")
def seller_suppliers(body: KeyIn, request: Request):
    try:
        eng, cl = scm.engine(), _client(request)
        s = store.resolve(eng, body.key, cl)
        return _ok(suppliers=scm.list_suppliers(eng, body.key, cl), supply=scm.supply_of(eng, s["seller_id"]),
                   stock=scm.stock_of(eng, s["seller_id"]))  # fmt: skip
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/suppliers/save")
def seller_supplier_save(body: SupplierIn, request: Request):
    try:
        got = scm.save_supplier(scm.engine(), body.key, _client(request), name=body.name, memo=body.memo,
                                contact=body.contact.model_dump() if body.contact else None, supplier_id=body.supplier_id)  # fmt: skip
        return _ok(supplier=got)
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/supply")
def seller_supply(body: SupplyIn, request: Request):
    try:
        return _ok(supply=scm.set_supply(scm.engine(), body.key, _client(request), body.product_id,
                                         supplier_id=body.supplier_id, sku=body.sku))  # fmt: skip
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/orders")
def seller_orders(body: KeyIn, request: Request):
    try:
        eng, cl = scm.engine(), _client(request)
        return _ok(orders=scm.list_orders(eng, body.key, cl), batches=scm.list_batches(eng, body.key, cl),
                   alerts=scm.my_alerts(eng, body.key, cl), csv_template=scm.order_csv_template())  # fmt: skip
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/orders/csv")
def seller_orders_csv(body: OrdersCsvIn, request: Request):
    try:
        got = scm.import_orders(scm.engine(), body.key, _client(request), body.csv, entrust_ok=body.entrust_ok)
        return JSONResponse(got, status_code=200 if got["ok"] else 400, headers=NOINDEX)
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/po")
def seller_po(body: KeyIn, request: Request):
    try:
        return _ok(batch=scm.create_batch(scm.engine(), body.key, _client(request)))
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/po/file")
def seller_po_file(body: BatchIn, request: Request):
    try:
        data, name = scm.render_batch(scm.engine(), body.key, _client(request), body.batch_id)
    except store.SellerError as e:
        return _err(e)
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={**NOINDEX, "Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})  # fmt: skip


@router.post("/seller/api/tracking")
async def seller_tracking(
    request: Request, key: Annotated[str, Form(max_length=40)], file: Annotated[UploadFile, File()]
):
    data = await file.read(2_000_001)
    if len(data) > 2_000_000:
        return _err(store.SellerError("파일은 2MB 까지 올릴 수 있어요"))
    try:
        return _ok(**scm.upload_tracking(scm.engine(), key, _client(request), file.filename or "", data))
    except store.SellerError as e:
        return _err(e)


# ── 판매 켜기·끄기 · 죽은 몰 확인 (2026-11-25) ──
class ListingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    product_id: str | None = Field(None, max_length=12)
    on: bool


@router.post("/seller/api/products/listing")
def seller_listing(body: ListingIn, request: Request):
    try:
        n = products.set_listing(scm.engine(), body.key, _client(request), body.product_id, body.on)
        return _ok(changed=n)
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/health")
def seller_health(body: KeyIn, request: Request):
    try:
        return _ok(health=health.my_health(scm.engine(), body.key, _client(request)))
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/confirm")
def seller_confirm(body: KeyIn, request: Request):
    try:
        return _ok(health=health.confirm_unchanged(scm.engine(), body.key, _client(request)))
    except store.SellerError as e:
        return _err(e)


# ── ④ 월 이용료 (보기만) ──
@router.post("/seller/api/billing")
def seller_billing(body: KeyIn, request: Request):
    try:
        return _ok(billing=billing.my_billing(billing.engine(), body.key, _client(request)))
    except store.SellerError as e:
        return _err(e)


# ── ⑤ 셀러 문의 ──
class AskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., max_length=40)
    text: str = Field(..., max_length=600)
    handoff: bool = False


@router.post("/seller/api/ask")
def seller_ask(body: AskIn, request: Request):
    try:
        return _ok(**seller_chat.ask(store.engine(), body.key, _client(request), body.text, handoff=body.handoff))
    except store.SellerError as e:
        return _err(e)


@router.post("/seller/api/asks")
def seller_asks(body: KeyIn, request: Request):
    try:
        return _ok(asks=seller_chat.my_asks(store.engine(), body.key, _client(request)))
    except store.SellerError as e:
        return _err(e)
