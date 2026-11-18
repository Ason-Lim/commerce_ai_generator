"""서버 설정으로 상품·레시피 찾기 (웹 대화·MCP 와 같은 공통 서비스).  키는 .env 그대로, 실패해도 초안은 만든다."""
from __future__ import annotations

import functools
import logging

log = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def _service():
    from app.api.chat_routes import build_default_service

    return build_default_service()


def find_products(keyword: str) -> dict:
    from app.domain.commerce.requests import SearchRequest
    from app.services.commerce.search import search_products

    try:
        svc = _service()
        nlu = svc._nlu()
        return search_products(SearchRequest(text=keyword, limit=10), shopping=svc.shopping,
                               keyword_extractor=svc.keyword_extractor,
                               nlu_parse=(nlu.parse if nlu is not None else None),
                               allow_preview=False).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        log.warning("trend post product search failed: %s", type(exc).__name__)
        return {"items": [], "warnings": ["상품을 불러오지 못했어요"]}


def find_recipe(keyword: str) -> dict:
    from app.domain.commerce.requests import RecipeRequest
    from app.services.commerce.recipes import get_recipe

    try:
        return get_recipe(RecipeRequest(dish_name=keyword), resolver=_service().recipe.resolver).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        log.warning("trend post recipe lookup failed: %s", type(exc).__name__)
        return {"items": []}
