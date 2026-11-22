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


site_hidden: list[str] = []


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
    # 2026-11-22 (3-A): 공개되면 안 되는 글 — 검토 대기·반려·내린 글 (주소로 직접 들어가도 안 보여야 함)
    from tests.services.trend_posts.helpers import item, report, search_result

    hidden = []
    for topic, step in (("방어회", "pending"), ("과메기", "rejected"), ("굴", "withdrawn")):
        draft, _ = svc.create_from_surge(report(item(topic)), topic, find_products=lambda k: search_result())
        svc.submit(draft.id)
        if step == "rejected":
            svc.reject(draft.id, "시험")
        if step == "withdrawn":
            svc.approve(draft.id)
            svc.withdraw(draft.id, "시험")
        hidden.append(draft.id)
    site_hidden.extend(hidden)
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


# ── 2026-11-22 창 3-A 넘어가는 기준: 이름 없는 버튼·링크 0 · 미승인 글 차단 · 사이트맵 승인 글만 ──────────

NAMELESS_JS = """() => [...document.querySelectorAll('button, a[href], [role=button], input:not([type=hidden]), textarea, select')]
  .filter(el => el.offsetParent !== null || el.getClientRects().length)
  .filter(el => {
    const name = (el.getAttribute('aria-label') || el.getAttribute('title') || el.innerText || el.value ||
                  el.getAttribute('placeholder') || (el.labels && el.labels[0] && el.labels[0].innerText) ||
                  (el.getAttribute('aria-labelledby') && document.getElementById(el.getAttribute('aria-labelledby'))?.innerText) ||
                  [...el.querySelectorAll('img[alt]')].map(i => i.alt).join('') || '').trim();
    return !name;
  })
  .map(el => el.outerHTML.slice(0, 120))"""


def test_no_nameless_buttons_or_links(site, page):
    base, post = site
    for path in ("/", "/#/hot", "/trends", f"/trends/{post.id}"):
        page.goto(base + path)
        page.wait_for_load_state("networkidle")
        nameless = page.evaluate(NAMELESS_JS)
        assert nameless == [], f"{path}: 이름 없는 버튼·링크 {nameless}"


def test_unapproved_posts_are_not_reachable(site, page):
    base, post = site
    assert len(site_hidden) == 3
    for pid in site_hidden:
        resp = page.goto(f"{base}/trends/{pid}")
        assert resp.status == 404, pid
    page.goto(base + "/trends")
    links = page.locator("a[href^='/trends/']").evaluate_all("els => els.map(e => e.getAttribute('href'))")
    assert not any(pid in (h or "") for pid in site_hidden for h in links)


def test_sitemap_lists_only_approved_posts(site, page):
    base, post = site
    xml = page.request.get(base + "/sitemap.xml").text()
    assert post.id in xml or quote(post.id) in xml
    assert not any(pid in xml or quote(pid) in xml for pid in site_hidden)
