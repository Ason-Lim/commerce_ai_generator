"""해외 직구 (2026-11-26) — GET /api/direct/home · /api/direct/search?q= . 저장·캐시하지 않음(Shopify 조건)."""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.direct_buy import savings, service

router = APIRouter(tags=["direct-buy"])
NO_STORE = {"Cache-Control": "no-store"}


@router.get("/api/direct/home")
def direct_home():
    return JSONResponse(service.home(), headers=NO_STORE)


@router.get("/api/direct/search")
def direct_search(q: str = Query("", max_length=100)):
    return JSONResponse(service.search(q), headers=NO_STORE)


@router.get("/api/direct/item/{key}")
def direct_item(key: str, ref: str | None = None, unit: str | None = None, n: str | None = None):
    """대화 결과 아래 '해외 직구' 칸 (2026-11-27) — 품목표의 품목만. ref·unit·n: 국내 후보 100g(ml)당 중간값(저장 안 함)."""
    return JSONResponse(service.search_item(key[:40], ref=savings.parse_ref(ref, unit, n)), headers=NO_STORE)


@router.get("/api/direct/recheck")
def direct_recheck(id: str = Query(..., max_length=120), price: int | None = Query(None, ge=0, le=10**10),
                   cur: str | None = Query(None, max_length=3)):
    """직구 도우미가 열릴 때 판매처 이동 전 재확인 (2026-11-27) — lookup_catalog, 저장 없음."""
    return JSONResponse(service.recheck(id, price, cur), headers=NO_STORE)
