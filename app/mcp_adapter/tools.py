"""MCP 도구 2개의 몸체 — 프로토콜(mcp 패키지)을 모른다.  server.py 가 이 함수들을 도구로 등록한다.

food_search_products(text, limit)        → 공통 서비스 search_products 결과(commerce.v1)를 그대로 투영
food_get_recipe(recipe_id | dish_name)   → 공통 서비스 get_recipe 결과(commerce.v1)를 그대로 투영

제휴 링크 원칙 (2026-11-02)
* 쿠팡 파트너스·네이버 쇼핑커넥트 링크를 AI 에이전트를 거쳐 보여 줘도 되는지 아직 확인하지 않았다.
  → MCP_AFFILIATE_LINKS=1 이 아니면 제휴 상품의 링크(product_url)를 비우고, 쇼핑커넥트 등록 목록은 빼고,
    그 사실을 warnings 에 적는다.  상품·가격·순위·사유는 웹과 같다.
* 순위는 바꾸지 않는다 (링크를 빼도 rank 는 그대로).
"""
from __future__ import annotations

import os
import uuid
from collections.abc import Callable

from app.domain.commerce.requests import RecipeRequest, SearchRequest

AFFILIATE_HELD = ("제휴(수수료) 링크와 제휴 이미지 주소는 AI 에이전트 경유 표시 허용 여부를 확인 중이라 비워 두었어요. "
                  "상품 이름으로 판매처에서 찾아보시거나 웹 화면에서 이용해 주세요.")
# 2026-11-03 p35: 업체 '미리 보기' 예시 데이터는 외부 에이전트에 보내지 않는다 (실제 상품·가격이 아님)
PREVIEW_BLOCKED = ("업체 미리 보기(예시 데이터)가 섞인 결과라 보내지 않았어요. "
                   "실제 상품·가격이 아니라 외부 에이전트에는 보내지 않아요.")


def affiliate_links_allowed(env=None) -> bool:
    source = os.environ if env is None else env
    return (source.get("MCP_AFFILIATE_LINKS") or "0").strip() == "1"


def _hold_affiliate(data: dict) -> dict:
    items, held = [], False
    for it in data.get("items") or []:
        offer = it.get("offer") or {}
        if it.get("section") == "connect":            # 등록부 목록은 전부 제휴 링크
            held = True
            continue
        if offer.get("link_type") == "affiliate" and (offer.get("product_url") or (it.get("product") or {}).get("image_url")):
            # p35: 제휴 이미지 주소(쿠팡 파트너스 이미지 서버)도 링크와 같은 기준으로 비운다
            it = dict(it, offer=dict(offer, product_url=None), product=dict(it.get("product") or {}, image_url=None))
            held = True
        items.append(it)
    if held:
        data = dict(data, items=items, warnings=list(data.get("warnings") or []) + [AFFILIATE_HELD])
    return data


def food_search_products(text: str, limit: int = 10, *, shopping: Callable,
                         keyword_extractor: Callable | None = None, nlu_parse: Callable | None = None,
                         env=None) -> dict:
    from app.services.commerce.search import search_products

    from app.domain.commerce.models import CommerceError, CommerceResult

    clean = (text or "").strip()[:500]
    if not clean:                       # p35: 빈 검색어로 판매처 API 를 부르지 않는다
        return CommerceResult(request_id=str(uuid.uuid4()), status="error", errors=[CommerceError(
            code="bad_request", message="검색할 상품이나 문장을 적어 주세요.")]).model_dump(mode="json")
    req = SearchRequest(text=clean, limit=max(1, min(int(limit or 10), 10)))
    # p37: 이 호출의 정책으로 '미리 보기 상품 제외'를 명시 (프로세스 환경 변수를 바꾸지 않음)
    data = search_products(req, shopping=shopping, keyword_extractor=keyword_extractor,
                           nlu_parse=nlu_parse, allow_preview=False).model_dump(mode="json")
    if (data.get("provenance") or {}).get("preview_data"):
        # p35·p37: 그래도 예시가 섞였다면(명시 값으로 판단) 일부만 빼지 않고 통째로 보류
        return CommerceResult(request_id=data["request_id"], status="held", errors=[CommerceError(
            code="preview_data_blocked", message=PREVIEW_BLOCKED)]).model_dump(mode="json")
    data = data if affiliate_links_allowed(env) else _hold_affiliate(data)
    return dict(data, naver_search=_naver_search(data, clean))


def _naver_search(data: dict, text: str) -> list[dict]:
    """2026-11-04: 웹 대화와 같은 네이버쇼핑 '검색' 링크 (고객 편의용 · 제휴 아님 · 수수료 없음).
    상품을 가리키지 않고 검색 화면만 연다 — 제휴 링크 보류(MCP_AFFILIATE_LINKS)와 상관없이 넣는다."""
    from urllib.parse import quote

    from app.services.chat.service import NAVER_SEARCH_URL, _label, naver_search_links, naver_search_on

    if not naver_search_on():
        return []
    query = (data.get("provenance") or {}).get("query") or ""
    picks = [{"role": (i.get("score") or {}).get("role"), "weight_g": (i.get("product") or {}).get("weight_g")}
             for i in data.get("items") or [] if i.get("section") == "picks"]
    return [{"query": q, "url": NAVER_SEARCH_URL + quote(q), "check": note, "link_type": "search", "affiliate": False}
            for q, note in naver_search_links(_label(query), text, picks)]


def food_get_recipe(recipe_id: str | None = None, dish_name: str | None = None, *, resolver) -> dict:
    from app.services.commerce.recipes import get_recipe

    req = RecipeRequest(recipe_id=(recipe_id or None), dish_name=(dish_name or None))
    return get_recipe(req, resolver=resolver).model_dump(mode="json")
