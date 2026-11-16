"""공개 트렌드 글 (2단계, 2026-11-16) — 서버가 그리는 페이지.  승인된 글만 나간다.

  GET /trends                    게시된 글 목록
  GET /trends/{글}               글 한 편 (승인되지 않았거나 내린 글은 404)
  GET /trends/{글}/go/{번호}     상품 링크 — 고객이 누를 때만 판매처로 보내고 클릭을 남긴다
                                 (관리자 로그인 브라우저는 'trend_internal' 로 따로 — 1단계 chat_internal 과 같은 이유)
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.trend_posts import render
from app.services.trend_posts.service import TrendPosts

log = logging.getLogger(__name__)
router = APIRouter(tags=["trends"], include_in_schema=False)

NOT_FOUND = render._page("글을 찾을 수 없어요", '<nav><a href="/trends">트렌드 글</a></nav>'
                         "<h1>글을 찾을 수 없어요</h1><p>게시되지 않았거나 내린 글이에요.</p>")


def get_trend_posts() -> TrendPosts:
    return TrendPosts()


Posts = Annotated[TrendPosts, Depends(get_trend_posts)]


def _html(text: str, status: int = 200) -> HTMLResponse:
    return HTMLResponse(text, status_code=status, headers={"Cache-Control": "no-cache"})


@router.get("/trends")
def trends_index(posts: Posts):
    return _html(render.index_page(posts.published()))


@router.get("/trends/{post_id}")
def trends_post(post_id: str, posts: Posts):
    post = posts.public(post_id)
    if post is None:
        return _html(NOT_FOUND, 404)
    return _html(render.post_page(post, posts.clock()))


@router.get("/trends/{post_id}/go/{n}")
def trends_go(post_id: str, n: int, request: Request, posts: Posts):
    post = posts.public(post_id)
    if post is None or not 1 <= n <= len(post.products):
        return RedirectResponse("/trends", status_code=303)
    product = post.products[n - 1]
    try:
        from app.admin.auth import request_ok
        from app.services.analytics_logger import log_product_click

        internal = request_ok(request)
        log_product_click(session_id=f"trend:{post.id}", query="trend_internal" if internal else "trend", product={
            "product_url": product.url, "product_name": product.title or product.url, "mall_name": product.platform,
            "rank": n, "selected_section": "trend", "recommendation_mode": "ranking"})
    except Exception:  # noqa: BLE001 — 기록이 이동을 막지 않는다
        log.warning("trend click log failed")
    return RedirectResponse(product.url, status_code=302)
