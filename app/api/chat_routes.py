"""Conversation API used by the React ui_ux front end.

    POST /api/chat           {session_id, message | answers | chip} → {session_id, stage, blocks}
    GET  /api/trend-examples → 홈 화면 예시 질문 (최신 trend_examples_*.json)
    GET  /api/recipe/easy    ?recipe_id=&key=  → 쉽게 보기 / AI image when ready (read-only polling)
    GET  /api/recipe/image   ?recipe_id=&v=    → stored AI dish image (read-only)
    GET  /go/{sid}/{rank}    click log + redirect to a product shown in that session
    GET  /go/{sid}/k/{key}   same, by the card's key (cards of earlier questions keep their own product)
    GET  /go/s/{owner}/{key} same, for a product in the 관심 상품 보관함
    GET  /api/chat/saved     ?owner=&session_id= → 관심 상품 + 최근 본 상품
    POST /api/chat/saved     {owner, session_id, key, on} → ♡ 담기/빼기 (서버가 보여 준 후보에서만 복사)

No secret is sent to the browser: the DeepSeek key stays in the server
environment and is only read by app.services.nlu.LLMClient.
"""
from __future__ import annotations

import logging
import os
import threading

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, Field

from app.services.chat.service import ChatService, engine_db

log = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

_service: ChatService | None = None
_lock = threading.Lock()


class ChatIn(BaseModel):
    session_id: str | None = Field(None, max_length=64)
    message: str | None = Field(None, max_length=500)
    answers: dict[str, str] | None = None
    chip: str | None = Field(None, max_length=200)
    # 2026-11-01: 관심 상품 보관함 id (브라우저별, '새 대화'를 눌러도 유지)
    owner: str | None = Field(None, max_length=64)


class ClickIn(BaseModel):
    session_id: str = Field(..., max_length=64)
    rank: int = Field(..., ge=1, le=200)
    url: str = Field(..., max_length=2000)


class SavedIn(BaseModel):
    owner: str = Field(..., max_length=64)
    session_id: str | None = Field(None, max_length=64)
    key: str = Field(..., max_length=32)
    on: bool = True


def _deepseek_ready() -> bool:
    return bool((os.getenv("DEEPSEEK_API_KEY") or "").strip() and (os.getenv("DEEPSEEK_MODEL") or "").strip())


def build_default_service() -> ChatService:
    from app.services.nlu.food_nlu import load_food_nlu
    from app.services.recipe_chat.service import RecipeChat
    from app.services.recipe_session.direct_stock_chat import interpret

    from app.services.recipe_chat import ai_image, easy_view
    from app.services.recipe_chat.catalog_store import CatalogProvider

    from app.services.recipe_chat import servings as servings_mod
    from app.services.recipe_chat import ai_recipe, discover, supplement

    ready = _deepseek_ready()
    db = engine_db()
    recipe = RecipeChat(stock_interpreter=interpret if ready else None,
                        # unclear servings messages only; validated before the state changes
                        servings_interpreter=servings_mod.llm_interpreter() if ready else None,
                        catalog_provider=CatalogProvider.from_env(),
                        easy_views=easy_view.from_env(),
                        ai_images=ai_image.from_env(),
                        # missing core step (원문 아님 · AI) — same key rule, validated before it is shown
                        supplements=supplement.from_env(),
                        # trend / new dish / link: NAVER search (server keys) + DeepSeek reading, validated
                        discovery=discover.from_env(),
                        # 'AI 제안 레시피' for dishes outside the catalogue (labelled, validated, stored once per dish)
                        ai_recipes=ai_recipe.from_env(db=db, statement_factory=db.sql),
                        consultant=None)
    # 2026-11-01: recipe consultation ('참치 샐러드 식감을 살리는 재료') — DeepSeek candidates, catalogue + blog evidence
    from app.services.recipe_chat import consult
    from app.services.recipe_chat.catalog_store import requested_kind

    if ready:
        from app.services.nlu.llm_client import LLMClient

        reader = LLMClient(consult.PROMPT, provider="deepseek", timeout=60.0, cache="recipe_consult", cache_days=30)
        # 2026-11-06: '굴국밥 1인분에 굴 몇 g' — used only when no public recipe gives the amount (labelled AI 추정)
        from app.services.recipe_chat import dish_shopping

        amounts = LLMClient(dish_shopping.AMOUNT_PROMPT, provider="deepseek", timeout=40.0,
                            cache="dish_amounts", cache_days=90)
        recipe.amount_estimator = lambda text: amounts.chat_json(text, temperature=0)
        recipe.consultant = consult.Consultant(lambda text: reader.chat_json(text, temperature=0.2),
                                               recipe.resolver.catalog, search=getattr(recipe.discovery, "provider", None),
                                               kind_of=requested_kind)
    keyword_extractor = None
    if ready:      # long shopping sentences → their product word (validated: it must be in the sentence)
        from app.services.chat.service import SHOP_KEYWORD_PROMPT
        from app.services.nlu.llm_client import LLMClient

        client = LLMClient(SHOP_KEYWORD_PROMPT, provider="deepseek", cache="shop_keyword", cache_days=90)
        keyword_extractor = lambda text: client.chat_json(text, temperature=0)  # noqa: E731
    food_tips = None
    if ready:      # 2026-11-04: 보관·손질·먹는 법 질문 — 일반 정보 짧게 (AI 정리로 표시, 서비스에서 검증)
        from app.services.chat import food_tips as food_tips_mod
        from app.services.nlu.llm_client import LLMClient

        tips_client = LLMClient(food_tips_mod.PROMPT, provider="deepseek")
        food_tips = lambda text: tips_client.chat_json(text, temperature=0.2)  # noqa: E731
    # 2026-11-11: 고급 작업 교차 확인 — 식품 지식(저장해 다시 쓰는 답)은 Claude 가 한 번 더 검토 (ANTHROPIC_API_KEY · AI_CROSS_CHECK)
    from app.services.ai import cross_check

    food_review = cross_check.reviewer("food_knowledge") if food_tips is not None else None
    return ChatService(db, nlu_loader=load_food_nlu, recipe_chat=recipe, keyword_extractor=keyword_extractor,
                       food_tips=food_tips, food_review=food_review)


def get_chat_service() -> ChatService:
    global _service
    with _lock:
        if _service is None:
            _service = build_default_service()
        return _service


_DEV = {"mtime": None, "on": None}


def dev_trace_on() -> bool:
    """CHAT_DEV_TRACE read from the repository .env again whenever the file changes (load_dotenv copied the start-up
    value into the environment, so the file wins) — switching development mode off needs no restart (2026-10-30).
    Without the key in .env, the process environment decides."""
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / ".env"
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = None
    if mtime is not None and mtime != _DEV["mtime"]:
        from dotenv import dotenv_values

        _DEV.update(mtime=mtime, on=dotenv_values(path).get("CHAT_DEV_TRACE"))
    value = _DEV["on"] if mtime is not None and _DEV["on"] is not None else os.environ.get("CHAT_DEV_TRACE")
    return (value or "").strip() == "1"


def public(response: dict) -> dict:
    """Verification details (search terms, API addresses, call log) leave the server only in development mode
    (CHAT_DEV_TRACE=1).  Customer responses never carry them."""
    if dev_trace_on():
        return response
    blocks = [dict(b, data={k: v for k, v in b["data"].items() if k != "trace"})
              if isinstance(b.get("data"), dict) else b for b in response.get("blocks") or []]
    return {**response, "blocks": blocks}


@router.post("/api/chat")
def chat(body: ChatIn, service: ChatService = Depends(get_chat_service)):
    return public(service.handle(body.session_id, message=body.message, answers=body.answers, chip=body.chip,
                                 owner=body.owner))


@router.get("/api/chat/saved")
def saved_view(owner: str | None = Query(None, max_length=64), session_id: str | None = Query(None, max_length=64),
               service: ChatService = Depends(get_chat_service)):
    return service.saved_view(owner, session_id)


@router.post("/api/chat/saved")
def saved_set(body: SavedIn, service: ChatService = Depends(get_chat_service)):
    return service.set_saved(body.owner, body.session_id, body.key, body.on)


@router.get("/api/trends/surge")
def trends_surge():
    """'지금 뜨는 식품' (customer tab): today's surge report in short — no search terms, API names or call logs."""
    from app.services.trends import surge

    return surge.public_view(surge.load())


@router.get("/api/trend-examples")
def trend_examples():
    """홈 화면 예시 질문 4개 — 매일 10시 scripts/update_trend_examples.py 가 만든 최신 파일 (2026-11-04).
    화면이 빌드 때 넣은 파일에 머물지 않게 한다.  {date, items:[{category, icon, keyword, question}]}"""
    from app.services.trends import examples

    return examples.latest()


@router.get("/api/recipe/easy")
def recipe_easy(recipe_id: str = Query(..., max_length=64), key: str | None = Query(None, max_length=64),
                service: ChatService = Depends(get_chat_service)):
    return service.recipe_easy(recipe_id, key)


@router.get("/api/recipe/image")
def recipe_image(recipe_id: str = Query(..., max_length=64), v: str = Query(..., max_length=64),
                 service: ChatService = Depends(get_chat_service)):
    found = service.recipe_image(recipe_id, v)
    if found is None:
        return Response(status_code=404)
    mime, data = found
    # the URL carries the source version, so the bytes never change for it
    return Response(content=data, media_type=mime, headers={"Cache-Control": "public, max-age=31536000, immutable"})


def _click_query(request: Request | None) -> str:
    """클릭 기록의 query 값. 관리자로 로그인한 브라우저(운영자 본인 시험)는 'chat_internal' 로 따로 남긴다
    (2026-11-10 R0 — 행동 신호 재도입 조건 2: 우리 테스트 세션을 걸러 낸다)."""
    try:
        from app.admin.auth import request_ok

        return "chat_internal" if request is not None and request_ok(request) else "chat"
    except Exception:  # noqa: BLE001
        return "chat"


@router.post("/api/click", status_code=204)
def click(body: ClickIn, request: Request, service: ChatService = Depends(get_chat_service)):
    """바로 이동 링크(네이버 쇼핑커넥트)의 클릭 기록 (2026-11-02).

    링크는 브라우저가 발급 주소 그대로 연다 — 이 호출은 이동과 무관한 기록용(sendBeacon)이다.
    직전에 보여 준 상품의 링크와 같을 때만 기록하고, 응답은 항상 204 (기록 여부를 알려 주지 않음)."""
    item = service.shown_item(body.session_id, body.rank)
    if item and item.get("url") == body.url:
        try:
            from app.services.analytics_logger import log_product_click

            log_product_click(session_id=body.session_id, query=_click_query(request), product={
                "product_url": item["url"], "product_name": item.get("title"), "mall_name": item.get("mall"),
                "rank": body.rank, "selected_section": "chat_direct", "recommendation_mode": "ranking"})
        except Exception:  # noqa: BLE001 — 기록 실패가 화면에 영향을 주지 않는다
            log.warning("direct click log failed")
    return Response(status_code=204)


@router.get("/go/{sid}/k/{key}")
def go_key(sid: str, key: str, request: Request, service: ChatService = Depends(get_chat_service)):
    return _redirect(sid, service.resolve_go_key(sid, key), shown=service.seen_card(sid, key), request=request)


@router.get("/go/s/{owner}/{key}")
def go_saved(owner: str, key: str, request: Request, service: ChatService = Depends(get_chat_service)):
    return _redirect(owner, service.resolve_saved_go(owner, key), section="saved", request=request)


@router.get("/go/{sid}/{rank}")
def go(sid: str, rank: int, request: Request, service: ChatService = Depends(get_chat_service)):
    return _redirect(sid, service.resolve_go(sid, rank), shown=service.shown_item(sid, rank), request=request)


def _redirect(sid: str, url: str | None, section: str = "chat", shown: dict | None = None,
              request: Request | None = None):
    if url is None:
        return RedirectResponse("/")
    try:
        from app.services.analytics_logger import log_product_click

        # 2026-11-10 (R0): 상품명이 없으면 같은 트랜잭션의 user_product_preference(상품명 NOT NULL)가 실패해
        # 클릭 기록까지 되돌려졌다 — 채팅 /go 클릭이 하나도 남지 않은 원인. 보여 준 상품의 이름·판매처를 넘기고,
        # 모르면 URL 을 이름 자리에 둔다.
        shown = shown if shown and shown.get("url") == url else {}
        log_product_click(session_id=sid, query=_click_query(request), product={
            "product_url": url, "product_name": shown.get("title") or url, "mall_name": shown.get("mall"),
            "rank": shown.get("rank"), "selected_section": section, "recommendation_mode": "ranking"})
    except Exception:  # noqa: BLE001 — logging must not block the redirect
        log.warning("click log failed")
    return RedirectResponse(url)
