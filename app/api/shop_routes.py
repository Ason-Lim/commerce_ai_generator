"""미니숍 고객 공개 · UCP 공개 (창 5, 2026-11-25).

  GET  /shop                      공개 셀러 목록
  GET  /shop/{seller_id}          셀러 미니숍 (승인된 상세페이지만, 중개 고지·판매자 정보·운영사 표시)
  GET  /.well-known/ucp           UCP business 프로필 (catalog.search · catalog.lookup, 결제 없음)
  POST /ucp/v1/catalog/search     UCP 카탈로그 검색
  POST /ucp/v1/catalog/lookup     UCP 카탈로그 조회
  GET  /ucp/platform.json         우리 UCP 플랫폼 프로필 (판매자 카탈로그를 읽을 때 UCP-Agent 로 보내는 주소)

SHOP_PUBLIC 이 꺼져 있거나 정식 공개 조건이 모자라면 모두 404 (shop_public 참고). 플랫폼 프로필은 UCP_PLATFORM_PUBLIC=1 일 때만.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.services.seller import shop_public

router = APIRouter()

SHOP_CSP = "default-src 'none'; img-src https:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
NOT_FOUND = HTMLResponse(
    "<!doctype html><meta charset=utf-8><title>없는 화면</title><p>없는 화면이에요.</p>", status_code=404
)


def _base(request: Request) -> str:
    return (os.environ.get("SITE_URL") or str(request.base_url)).rstrip("/")


def _headers() -> dict:
    h = {"Cache-Control": "no-store", "Content-Security-Policy": SHOP_CSP, "Referrer-Policy": "no-referrer"}
    if shop_public.mode() != "formal":
        h["X-Robots-Tag"] = "noindex, nofollow"
    return h


def _html(fn):
    try:
        return HTMLResponse(fn(), headers=_headers())
    except shop_public.NotPublic:
        return NOT_FOUND
    except shop_public.store.SellerError:
        return NOT_FOUND


@router.get("/shop", include_in_schema=False)
def shop_index():
    return _html(lambda: shop_public.index_page(shop_public.engine()))


@router.get("/shop/{key}", include_in_schema=False)
def shop_seller(key: str):
    """주소 이름(/shop/renerpaint) 또는 셀러 번호."""
    import re

    from app.services.seller import catalog

    if not re.fullmatch(r"[A-Za-z0-9-]{3,40}", key):
        return NOT_FOUND
    sid = catalog.resolve_seller(catalog.engine(), key)
    if not sid:
        return NOT_FOUND
    return _html(lambda: shop_public.page_for(shop_public.engine(), sid))


def _ucp_json(data: dict, status: int = 200) -> JSONResponse:
    h = {"Cache-Control": "no-store"}
    if shop_public.mode() != "formal":
        h["X-Robots-Tag"] = "noindex"
    return JSONResponse(data, status_code=status, headers=h)


def _ucp_error(code: str, content: str, status: int) -> JSONResponse:
    return _ucp_json({"ucp": {"version": shop_public.UCP_VERSION, "status": "error"},
                      "messages": [{"type": "error", "code": code, "content": content, "severity": "unrecoverable"}]},
                     status)  # fmt: skip


@router.get("/.well-known/ucp", include_in_schema=False)
def ucp_business_profile(request: Request):
    eng = shop_public.engine()
    if shop_public.mode() == "off" or not shop_public.public_sellers(eng):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    return _ucp_json(shop_public.ucp_profile(_base(request)))


async def _body(request: Request) -> dict | None:
    try:
        data = await request.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


@router.post("/ucp/v1/catalog/search", include_in_schema=False)
async def ucp_catalog_search(request: Request):
    body = await _body(request)
    if body is None:
        return _ucp_error("invalid_request", "JSON 객체를 보내 주세요", 400)
    try:
        return _ucp_json(shop_public.ucp_search(shop_public.engine(), body, _base(request)))
    except shop_public.NotPublic:
        return JSONResponse({"detail": "Not Found"}, status_code=404)


@router.post("/ucp/v1/catalog/lookup", include_in_schema=False)
async def ucp_catalog_lookup(request: Request):
    body = await _body(request)
    if body is None or not isinstance(body.get("ids"), list) or not body["ids"]:
        return _ucp_error("invalid_request", "ids 목록이 필요해요", 400)
    try:
        return _ucp_json(shop_public.ucp_lookup(shop_public.engine(), body, _base(request)))
    except shop_public.NotPublic:
        return JSONResponse({"detail": "Not Found"}, status_code=404)


@router.get("/ucp/platform.json", include_in_schema=False)
def ucp_platform_profile():
    """판매자 카탈로그를 읽을 때 보내는 플랫폼 프로필 — 판매자가 이 주소를 직접 가져와 검증한다."""
    if (os.environ.get("UCP_PLATFORM_PUBLIC") or "").strip() != "1":
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    from app.services.ucp import platform

    return JSONResponse(platform.platform_profile(), headers={"Cache-Control": "public, max-age=3600"})
