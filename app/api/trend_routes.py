"""공개 트렌드 글 (2단계, 2026-11-16) — 서버가 그리는 페이지.  승인된 글만 나간다.

  GET /trends                    게시된 글 목록
  GET /trends/{글}               글 한 편 (승인되지 않았거나 내린 글은 404)
  GET /api/trends/posts          앱 화면용 게시 글 요약 (첫 화면 '오늘의 트렌드', 지금 뜨는 식품) — 2026-11-18
  GET /sitemap.xml · /robots.txt 검색엔진용 (2026-11-18)
  POST /api/trends/posts/{글}/feedback  글 끝 피드백 (2026-11-21) — 좋음·보통·나쁨 + 이유 칩, 집계는 돌려주지 않음
  GET /trends/{글}/go/{번호}     상품 링크 — 고객이 누를 때만 판매처로 보내고 클릭을 남긴다
                                 (관리자 로그인 브라우저는 'trend_internal' 로 따로 — 1단계 chat_internal 과 같은 이유)
"""
from __future__ import annotations

import logging
from typing import Annotated

import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict, Field

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


@router.get("/api/home/rankings")
def home_rankings(view: str = Query("home", pattern="^(home|full)$")):
    """홈 '지금 순위' (창 3-C, 2026-11-22 · 11-23 개편) — 쿠팡 식품 랭킹 · 카테고리 · 급상승(지금 뜨는 식품 화면). 저장된 자료만 읽는다(외부 호출 0), 5분 캐시.
    view=home 은 요약(6·6·4+2), view=full 은 탭 '지금 뜨는 식품' 전체 화면 — 같은 선정 규칙."""
    from app.services.trends import home_rankings as hr

    return JSONResponse(hr.build(view), headers={"Cache-Control": "public, max-age=60"})


class _TogetherIn(BaseModel):
    """이 브라우저가 최근 누른 품목 낱말 (2026-11-23) — 본문으로만 받고 저장·기록하지 않는다."""
    model_config = ConfigDict(extra="forbid")
    seeds: list[str] = Field(default_factory=list, max_length=10)
    view: str = Field("home", pattern="^(home|full)$")


@router.post("/api/home/together")
def home_together(body: _TogetherIn):
    """홈 '함께 보면 좋은 상품' — 레시피 짝 · 같은 태그 · 새로 둘러보기. 쿠팡 랭킹(메모리 1시간) + 트렌드 글 상품 + 레시피 서비스.
    seeds 가 비면 쿠팡 식품 랭킹 1위 품목 기준(personal=false). seeds 는 로그·파일에 남기지 않는다."""
    from app.services.trends import together

    try:
        out = together.build(together.clean_seeds(body.seeds), body.view)
    except Exception:  # noqa: BLE001
        log.warning("home together failed")
        out = {"status": "none", "personal": False, "items": [], "disclosure": together.DISCLOSURE, "note": ""}
    return JSONResponse(out, headers={"Cache-Control": "no-store"})


@router.get("/api/home/highlight")
def home_highlight(kw: str = Query(..., min_length=1, max_length=40)):
    """홈 카테고리 '이번 주 주목' 대표 상품 (2026-11-23 저녁). 지금 홈 응답의 주목 키워드만 받는다 — 아무 검색어나 쿠팡에 보내지 않음.
    쿠팡 검색 1번(메모리 10분 캐시), 저장 없음."""
    from app.services.trends import highlight as hl
    from app.services.trends import home_rankings as hr

    allowed = {(t.get("highlight") or {}).get("keyword") for t in (hr.build("home").get("categories") or {}).get("tabs") or []}
    if kw not in allowed:
        return JSONResponse({"status": "unknown"}, status_code=404)
    try:
        item = hl.pick(kw)
    except Exception:  # noqa: BLE001 — 사진 하나 못 받아도 카드는 보인다
        log.warning("home highlight failed")
        item = None
    body = {"status": "ok" if item else "none", "item": item, "disclosure": hr.DISCLOSURE}
    return JSONResponse(body, headers={"Cache-Control": "no-store"})


@router.get("/home/hgo/{key}")
def go_highlight(key: str, request: Request):
    """'이번 주 주목' 상품 클릭 — 메모리 표의 제휴 링크로(10분), 지나면 쿠팡 검색 화면. 클릭 기록에 상품명은 남기지 않음."""
    import re as _re

    from app.services.trends import highlight as hl

    if not _re.fullmatch(r"[0-9a-f]{12}", key or ""):
        return RedirectResponse("/", status_code=303)
    url, affiliate = hl.target(key)
    if affiliate:
        try:
            from app.admin.auth import request_ok
            from app.services.analytics_logger import log_product_click

            log_product_click(session_id="home", query="home_internal" if request_ok(request) else "home", product={
                "product_url": url, "product_name": url, "mall_name": "쿠팡", "rank": 0,
                "selected_section": "category_highlight", "recommendation_mode": "ranking"})
        except Exception:  # noqa: BLE001
            log.warning("highlight click log failed")
    return RedirectResponse(url, status_code=302 if url.startswith("http") else 303)


@router.get("/home/go/{product_id}")   # /go/{sid}/{rank}(대화)와 겹치지 않게 /home/go
def go_coupang_best(product_id: str, request: Request):
    """쿠팡 식품 랭킹·함께 보면 좋은 상품 클릭 (2026-11-23) — 지금 메모리 랭킹에 있는 상품만, 클릭 기록 뒤 쿠팡 링크로."""
    from app.services.trends import coupang_best as cb

    if not product_id.isdigit() or len(product_id) > 20:
        return RedirectResponse("/", status_code=303)
    item = cb.find(product_id)
    if item is None:
        # 2026-11-23 '최근 본 상품'(브라우저에 7일)에서 누를 때 — 지금 랭킹에서 빠진 상품은 쿠팡 상품 페이지로 바로 보낸다
        # (우리 서버에 그 상품 정보를 남기지 않으므로 제휴 링크를 만들 수 없음 — 수수료 없는 일반 링크).
        return RedirectResponse(f"https://www.coupang.com/vp/products/{product_id}", status_code=302)
    try:
        from app.admin.auth import request_ok
        from app.services.analytics_logger import log_product_click

        internal = request_ok(request)
        section = "together" if request.query_params.get("from") == "together" else "coupang_best"
        log_product_click(session_id="home", query="home_internal" if internal else "home", product={
            "product_url": item["url"], "product_name": item["url"], "mall_name": "쿠팡",   # 11-23: 상품명은 남기지 않음(#82 와 같음)
            "rank": item["rank"], "selected_section": section, "recommendation_mode": "ranking"})
    except Exception:  # noqa: BLE001 — 기록이 이동을 막지 않는다
        log.warning("coupang best click log failed")
    return RedirectResponse(item["url"], status_code=302)


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


class _FeedbackIn(BaseModel):
    """자유 입력 칸 없음 — 평가와 칩 코드만 (그 밖의 키는 거부)."""
    model_config = ConfigDict(extra="forbid")
    rating: str = Field(..., max_length=8)
    reasons: list[str] = Field(default_factory=list, max_length=6)


@router.post("/api/trends/posts/{post_id}/feedback")
def trends_feedback(post_id: str, body: _FeedbackIn, request: Request, posts: Posts):
    """글 끝 피드백 저장 (2026-11-21). 판·규칙 판은 서버가 게시본에서 정한다. 관리자 로그인 브라우저는 운영자 평가로 따로.
    IP 는 저장하지 않는다 — 무작위 브라우저 식별자(쿠키 tg_fb)와 평가만. 집계는 돌려주지 않는다."""

    from app.admin.auth import request_ok
    from app.services.trend_posts import feedback as fb

    post = posts.public(post_id)
    if post is None:
        raise HTTPException(404, "게시된 글이 아니에요.")
    bid = request.cookies.get(fb.COOKIE) or ""
    fresh = not fb.BROWSER_ID.match(bid)
    if fresh:
        bid = fb.new_browser_id()
    if not fb.LIMITER.hit(bid):
        raise HTTPException(429, "잠시 뒤에 다시 눌러 주세요.")
    try:
        out = fb.FeedbackStore(clock=posts.clock).record(post, body.rating, body.reasons, bid,
                                                        operator=request_ok(request))
    except fb.FeedbackError as exc:
        raise HTTPException(404 if exc.code == "not_found" else 400, str(exc)) from exc
    r = JSONResponse(out, headers={"Cache-Control": "no-store"})
    if fresh:
        r.set_cookie(fb.COOKIE, bid, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax", path="/",
                     secure="https" in (request.url.scheme, request.headers.get("x-forwarded-proto", "")))
    return r
