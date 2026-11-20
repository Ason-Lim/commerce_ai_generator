"""우리 사이트 화면을 실제 브라우저로 확인 (2단계 마무리, 2026-11-18) — Playwright + Chromium.

무엇을 보나
* /trends 목록 → 글: 공통 메뉴, 로고가 본문 왼쪽 끝과 맞는지, 구조화 데이터(Article)
* 지금 뜨는 식품(/#/hot): 트렌드 글 줄·카드의 '트렌드 글 읽기'가 없다 (2026-11-20 — 트렌드 글은 '트렌드 글' 메뉴에서)
* 첫 화면: '오늘의 트렌드' 줄이 없다, 로고가 제목 '식'자와 세로로 맞는지, 메뉴는 오른쪽, 지운 중복 문구가 없는지
* 모바일 폭: 아래 탭이 보이고 머리줄 메뉴는 숨는지

서버는 테스트 안에서 띄운다 (트렌드 글 라우터 + 빌드된 화면 frontend/dist + 가짜 급상승 목록). DB·외부 API 를 부르지 않는다.
실행 (맥):  uv run playwright install chromium   # 처음 한 번
           npm --prefix frontend run build       # 화면을 바꿨으면
           uv run pytest tests/e2e -q
브라우저나 화면 빌드가 없으면 건너뛴다 (skip).
"""
from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from urllib.parse import quote

import pytest

pw = pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "frontend" / "dist"

SURGE = {"status": "ok", "data_until": "2026-11-15", "items": [
    {"keyword": "대방어", "status": "surging", "times": 2.7, "onset": "2026-11-03", "rank": 82, "spark": [1, 2, 3, 5],
     "cross": {"n": 2, "of": 2, "parts": {"블로그": True}}, "clues": [], "cause": None, "ask": "대방어 추천해줘",
     "youtube": None},
    {"keyword": "유자", "status": "new", "times": None, "onset": "2026-11-10", "rank": None, "spark": [0, 1, 2],
     "cross": {"n": 1, "of": 2, "parts": {}}, "clues": [], "cause": None, "ask": "유자 추천해줘", "youtube": None}]}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    if not (DIST / "index.html").is_file():
        pytest.skip("화면 빌드(frontend/dist)가 없어요 — npm --prefix frontend run build")
    import uvicorn
    from fastapi import FastAPI

    from app.api import trend_routes
    from app.web_frontend import mount_frontend
    from tests.services.trend_posts.helpers import approved, service

    svc = service(tmp_path_factory.mktemp("posts"))
    post = approved(svc, "대방어")
    app = FastAPI()

    @app.get("/api/trends/surge")
    def _surge():
        return SURGE

    @app.get("/api/trend-examples")
    def _examples():
        return {"items": []}

    app.include_router(trend_routes.router)
    app.dependency_overrides[trend_routes.get_trend_posts] = lambda: svc
    mount_frontend(app, DIST)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}", post
    server.should_exit = True
    th.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # noqa: BLE001 — 브라우저가 설치되지 않은 환경
            pytest.skip(f"Chromium 을 띄우지 못했어요 ({type(e).__name__}) — uv run playwright install chromium")
        yield b
        b.close()


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    pg = ctx.new_page()
    yield pg
    ctx.close()


def _left(locator) -> float:
    return locator.bounding_box()["x"]


def test_trend_post_pages(site, page):
    base, post = site
    page.goto(base + "/trends")
    assert page.locator(".menu a[aria-current=page]").inner_text() == "트렌드 글"
    assert abs(_left(page.locator("header .logo")) - _left(page.locator("main h1"))) <= 2      # 로고 = 본문 왼쪽 끝
    page.get_by_role("link", name=post.title).click()
    page.wait_for_url(f"**/trends/{quote(post.id)}")   # 주소의 한글은 %EB… 로 바뀌어 있다
    assert page.locator("h1").inner_text() == post.title
    assert page.locator('script[type="application/ld+json"]').count() == 1
    assert page.get_by_role("link", name="이 주제 더 물어보기").is_visible()


def test_hot_page_has_no_trend_posts(site, page):
    """2026-11-20 사용자 결정: 지금 뜨는 식품에서는 트렌드 글(위쪽 줄·카드 버튼)을 빼고 '트렌드 글' 메뉴로만 본다."""
    base, post = site
    page.goto(base + "/#/hot")
    cards = page.locator("li.card")
    cards.first.wait_for()
    assert page.get_by_role("region", name="최신 트렌드 글").count() == 0
    assert page.get_by_text(post.title).count() == 0
    assert page.get_by_role("link", name="트렌드 글 읽기").count() == 0
    page.get_by_role("link", name="트렌드 글").first.click()               # 메뉴에서는 그대로 갈 수 있다
    page.wait_for_url("**/trends")


def test_home_header_and_todays_trends(site, page):
    base, post = site
    page.goto(base + "/")
    h1 = page.locator("main h1").first
    h1.wait_for()
    assert page.get_by_role("region", name="오늘의 트렌드").count() == 0   # 2026-11-20: 첫 화면 트렌드 글 줄 없음
    assert page.get_by_text(post.title).count() == 0
    logo = page.locator("header a").first
    assert abs(_left(logo) - _left(h1)) <= 2                                          # 로고 = 제목 '식'자 세로선
    chat_menu = page.locator("header nav[aria-label='주요 메뉴'] a", has_text="대화")
    assert _left(chat_menu) > 640                                                     # 메뉴는 오른쪽
    text = page.locator("body").inner_text()
    assert "조건 확인 → 후보 비교" not in text                                         # 지운 중복 문구
    assert "광고 · 제휴 링크 안내" in text and "일정액의 수수료를 제공받습니다. 수수료는 본 사이트 운영에 도움이 됩니다" not in text
    assert page.get_by_label("진행 단계", exact=False).count() == 0                   # 진행 단계는 대화 중에만


def test_mobile_uses_the_bottom_tabs(site, browser):
    base, _post = site
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, locale="ko-KR")
    pg = ctx.new_page()
    try:
        pg.goto(base + "/trends")
        assert pg.locator("nav.tabbar").is_visible() and not pg.locator("nav.menu").is_visible()
        pg.goto(base + "/#/hot")
        tabs = pg.locator("nav[aria-label='주요 메뉴']").filter(has_text="지금 뜨는 식품").last
        assert tabs.is_visible() and tabs.locator("a[aria-current=page]").inner_text().strip() == "지금 뜨는 식품"
    finally:
        ctx.close()
