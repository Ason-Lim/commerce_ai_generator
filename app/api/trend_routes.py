"""공개 트렌드 글 (2단계, 2026-11-16) — 서버가 그리는 페이지.  승인된 글만 나간다.

  GET /trends                    게시된 글 목록
  GET /trends/{글}               글 한 편 (승인되지 않았거나 내린 글은 404)
  GET /api/trends/posts          앱 화면용 게시 글 요약 (첫 화면 '오늘의 트렌드', 지금 뜨는 식품) — 2026-11-18
  GET /sitemap.xml · /robots.txt 검색엔진용 (2026-11-18)
  GET /trends/{글}/go/{번호}     상품 링크 — 고객이 누를 때만 판매처로 보내고 클릭을 남긴다
                                 (관리자 로그인 브라우저는 'trend_internal' 로 따로 — 1단계 chat_internal 과 같은 이유)
"""
from __future__ import annotations

import logging
from typing import Annotated

import re

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

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


def _flat(s: str) -> str:
    return re.sub(r"\s+", "", s or "").lower()


@router.get("/api/trends/posts")
def trends_posts_json(posts: Posts, limit: int = Query(3, ge=1, le=20)):
    """게시된 글 요약 — 최신순 limit 개와, 지금 뜨는 식품 카드가 '트렌드 글 읽기'를 붙일 수 있게 주제별 최신 글 표."""
    published = posts.published()
    by_topic: dict[str, dict] = {}
    for p in published:                       # 최신순이므로 처음 본 것이 그 주제의 최신 글
        by_topic.setdefault(_flat(p.topic), render.card(p))
    return {"items": [render.card(p) for p in published[:limit]], "by_topic": by_topic, "count": len(published)}


@router.get("/sitemap.xml")
def sitemap(posts: Posts):
    return Response(render.sitemap_xml(posts.published()), media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.get("/robots.txt")
def robots():
    return PlainTextResponse(render.robots_txt(), headers={"Cache-Control": "public, max-age=86400"})


@router.get("/trends")
def trends_index(posts: Posts):
    return _html(render.index_page(posts.published()))


@router.get("/trends/img/{name}")
def trends_image(name: str):
    """보류 글의 AI 대표 그림 (2026-11-20). 이름 모양이 맞고 var/trend_images 안에 있는 png·webp 만 (webp 는 v1.1)."""
    from fastapi.responses import FileResponse

    from app.services.trend_posts.cover import image_dir
    from app.services.trend_posts.model import VALID_IMAGE

    path = image_dir() / name
    if not VALID_IMAGE.match(name or "") or not path.is_file():
        return Response(status_code=404)
    media = "image/webp" if name.endswith(".webp") else "image/png"
    return FileResponse(path, media_type=media, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/trends/{post_id}")
def trends_post(post_id: str, posts: Posts):
    post = posts.public(post_id)
    if post is None:
        return _html(NOT_FOUND, 404)
    return _html(render.post_page(post, posts.clock()))


@router.get("/trends/{post_id}/go/{n}")
def trends_go(post_id: str, n: int, request: Request, posts: Posts):
    post = posts.public(post_id)
    if post is None or post.conclusion == "hold" or not 1 <= n <= len(post.products):
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
