"""commerce_ai MCP 서버 — 로컬 stdio 전용 (내부 검증 1단계).

    pip install "mcp>=1.2"
    python -m app.mcp_adapter.server            # Claude Desktop 등에서 stdio 로 실행

원격(HTTP) 공개는 하지 않는다: 요청 제한·키 검증·제휴 링크 정책 확인이 먼저다.
웹(/api/chat)과 같은 서비스 설정(build_default_service)을 쓰므로 판매처 키·DB 는 서버 .env 그대로다.
"""
from __future__ import annotations

import functools
import os

from app.mcp_adapter import tools

NAME = "commerce-ai-food"
INSTRUCTIONS = ("식품 쇼핑 후보와 공공 레시피를 찾는 도구예요. 결과의 순위·사유·고지(disclosure)·경고(warnings)를 "
                "바꾸지 말고 함께 보여 주세요. 배송비가 null 이면 0원이 아니라 '미확인'이에요. "
                "AI 제안 레시피(source_level=ai_suggestion)는 원문이 아니라고 밝혀 주세요. "
                "naver_search 는 네이버쇼핑 검색 화면 링크(제휴 아님·수수료 없음)예요 — 상품 추천이 아니라 "
                "'조건으로 찾아보기'로, 확인할 점(check)과 함께 보여 주세요.")


@functools.lru_cache(maxsize=1)
def _service():
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    except ImportError:
        pass
    # p35 의 환경 변수 강제(PARTNER_PREVIEW=0)는 p37 에서 뺐다 — 미리 보기 제외는 도구 호출마다 명시(tools.allow_preview=False)
    _bind_engine()
    from app.api.chat_routes import build_default_service

    return build_default_service()


_LIFECYCLE = None


def _bind_engine():
    """DB 연결 등록 (2026-11-03 p36).  웹(main.py lifespan)·Streamlit 은 시작할 때 bind_engine 을 하지만 MCP 서버는
    하지 않아, 레시피 카탈로그(DB recipe_catalog)를 읽지 못하고 빈 목록이 됐다 (EngineProviderUnboundError).
    이미 등록돼 있으면 그대로 둔다.  DB 에 닿지 못해도 도구는 계속 동작한다 (카탈로그만 빈 목록)."""
    global _LIFECYCLE
    from app.db.engine_provider import bind_engine, is_bound
    from app.db.lifecycle import EngineLifecycle

    if is_bound():
        return
    try:
        lifecycle = EngineLifecycle()
        lifecycle.initialize()
        bind_engine(lifecycle.engine)
        _LIFECYCLE = lifecycle
    except Exception as e:  # noqa: BLE001
        import sys

        print(f"[commerce-ai-food] DB 연결 등록 실패 — 레시피 카탈로그 없이 동작: {type(e).__name__}", file=sys.stderr)


def _nlu_parse(text: str):
    nlu = _service()._nlu()
    return nlu.parse(text) if nlu is not None else None


def search_products(text: str, limit: int = 10) -> dict:
    """식품 상품 후보 검색. text 는 고객 문장 그대로 (예: '5만원 이하 한우 등심'). limit 1~10."""
    svc = _service()
    return tools.food_search_products(text, limit, shopping=svc.shopping, keyword_extractor=svc.keyword_extractor,
                                      nlu_parse=_nlu_parse)


def get_recipe(recipe_id: str | None = None, dish_name: str | None = None) -> dict:
    """공공 레시피 조회. recipe_id(예: 'EPIS:467') 또는 dish_name(예: '크림파스타') 중 하나.
    이름이 여러 레시피에 맞으면 status=needs_followup 과 후보(followup.options)를 돌려준다."""
    return tools.food_get_recipe(recipe_id, dish_name, resolver=_service().recipe.resolver)


def build():
    try:                                            # mcp 2.x
        from mcp.server import MCPServer as Server
    except ImportError:                             # mcp 1.x
        from mcp.server.fastmcp import FastMCP as Server
    server = Server(NAME, instructions=INSTRUCTIONS)
    ro = _read_only()
    server.tool(name="food_search_products", annotations=ro)(search_products)
    server.tool(name="food_get_recipe", annotations=ro)(get_recipe)
    return server


def _read_only():
    """두 도구 모두 읽기 전용 — 결제·주문·저장 도구는 의도적으로 없다."""
    from mcp.types import ToolAnnotations

    try:
        return ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=True)   # 2.x
    except Exception:  # noqa: BLE001
        return ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True)       # 1.x


def main() -> None:
    build().run()          # stdio


if __name__ == "__main__":
    main()
