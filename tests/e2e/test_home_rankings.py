"""화면 시험 '지금 순위' (창 3-C, 2026-11-22 — 설계 §4 시나리오 · 2026-11-23 개편: 홈 = 쿠팡 식품 랭킹 · 카테고리 · 함께 보면 좋은 상품).

홈 → 지금 순위 → 탭 셋 전환 → 카테고리 칩 → 키워드 누르면 대화 시작(한 번만) → 상품 고지가 첫 링크보다 앞 →
링크는 /trends/…/go/… → 전체 보기(지금 뜨는 식품) 전체 화면 · 보기 칩. '장바구니'·'주문' 문구 0, 이름 없는 버튼·링크 0.
서버 응답은 고정값(hr.build 대신) — 규칙은 tests/services/trends/test_home_rankings_2026_11_22.py 가 본다.
"""
from __future__ import annotations

import threading
import time

import pytest

pw = pytest.importorskip("playwright.sync_api")

from tests.e2e.test_site_browser import DIST, NAMELESS_JS, SURGE, _free_port  # noqa: E402


def kw(rank, k, tags, state="insufficient", kind="compared", ch=5, rising=True):
    return {"rank": rank, "keyword": k, "ask": f"{k} 추천해 줘", "tags": tags, "season": [], "state": state,
            "window_days": 90, "observed_days": 70, "top100_days": 60, "change_7d": ch if kind == "compared" else None,
            "change_kind": kind, "rising": rising}


APPLE, GAM, RICE = kw(7, "사과", ["fruit"]), kw(18, "대봉감", ["fruit"], kind="entered"), kw(12, "쌀20kg", ["cook"], "steady", ch=0, rising=False)
CARD = {"product_id": "111", "title": "부사 사과 3kg 가정용", "mall": "쿠팡", "price_krw": 19900,
        "price_checked_at": "2026-11-21T00:00:00+00:00", "price_hidden": False, "image": None, "rocket": True,
        "why": "트렌드 글 기준 · 사과 고르는 법", "post_title": "사과 고르는 법", "post_url": "/trends/2026-11-21-a",
        "go_url": "/trends/2026-11-21-a/go/1", "badges": ["multi_post"], "post_count": 2}


CP = [{"rank": 1, "product_id": "7230779632", "title": "신선한 대란", "image": None, "price_krw": 7880, "price_hidden": False,
       "rocket": True, "change_kind": "compared", "change": 2, "seed": "대란", "go_url": "/home/go/7230779632"},
      {"rank": 3, "product_id": "218520566", "title": "돌 스위티오 바나나", "image": None, "price_krw": 4230, "price_hidden": False,
       "rocket": True, "change_kind": "new", "change": None, "seed": "바나나", "go_url": "/home/go/218520566"}]
TOGETHER_SEEN: list[str] = []
EXTRA_FRUIT: list[dict] = []
HIGHLIGHT: list[dict] = []        # 11-23 저녁 B: '이번 주 주목' 시험에서만 채움      # 11-23 저녁: 카테고리 6개 + 더보기 시험에서만 채움


def together(seeds):
    personal = bool(seeds)
    return {"status": "ok", "personal": personal, "disclosure": "쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.",
            "note": "맞춤 추천 · 이 브라우저에서 최근 누른 품목 기준" if personal else "일반 추천 · 쿠팡 식품 랭킹 1위 '대란' 기준",
            "fetched_at": "2026-11-23T10:05+09:00", "items": [{
                "product_id": "1275124832", "title": "곰곰 아삭한 콩나물", "image": None, "price_krw": 1090, "price_hidden": False,
                "rocket": True, "go_url": "/home/go/1275124832?from=together", "seed": "콩나물", "source": "coupang_best",
                "kind": "explore", "why": "새로 둘러보기 · 요리/식재료"}]}


def data(view):
    full = view == "full"
    fruit = [APPLE, GAM] + EXTRA_FRUIT + ([kw(40, "귤", ["fruit"], "steady", ch=0, rising=False)] if full else [])
    return {
        "generated_at": "2026-11-22T10:05+09:00", "view": view,
        "coupang": {"status": "ok", "fetched_at": "2026-11-23T10:05+09:00", "compare": True, "compare_ready": True,
                    "items": CP, "disclosure": "쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.", "note": "쿠팡 기준"},
        "surge": {"status": "ok", "data_until": "2026-11-21", "updated_at": "x",
                  "items": [{"n": 1, "keyword": "대방어", "status": "surging", "times": 2.7, "rank": 82, "onset": "2026-11-03", "ask": "대방어 추천해 줘"}]},
        "categories": {"status": "ok", "rank_date": "2026-11-21", "note": "네이버 식품 검색어 순위", "tabs": [
            {"tag": "fruit", "label": "과일", "icon": "Apple", "default_filter": "rising",
             "counts": {"all": len(fruit), "rising": 2, "steady": int(full), "insufficient": 2}, "items": fruit,
             "highlight": HIGHLIGHT[0] if HIGHLIGHT else None},
            {"tag": "cook", "label": "요리/식재료", "icon": "Utensils", "default_filter": "all",
             "counts": {"all": 1, "rising": 0, "steady": 1, "insufficient": 0}, "items": [RICE]}]},
        "picks": {"status": "ok", "disclosure": "쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.",
                  "groups": {"recent": [CARD], "steady": []}, "placement_note": "최근 소개 4개 + …", "badge_notes": {}},
    }


@pytest.fixture(scope="module")
def site():
    if not (DIST / "index.html").is_file():
        pytest.skip("화면 빌드(frontend/dist)가 없어요 — npm --prefix frontend run build")
    import uvicorn
    from fastapi import FastAPI

    from app.api import trend_routes
    from app.services.trends import home_rankings as hr
    from app.web_frontend import mount_frontend

    app = FastAPI()

    @app.get("/api/trend-examples")
    def _examples():
        return {"items": []}

    @app.get("/api/trends/surge")
    def _surge():
        return SURGE

    @app.post("/api/home/together")
    def _together(body: dict):                         # (from __future__ annotations — 모듈 밖 이름은 못 씀)
        TOGETHER_SEEN.append(",".join(body.get("seeds") or []))
        return together(body.get("seeds") or [])

    app.include_router(trend_routes.router)
    mount_frontend(app, DIST)
    old = hr.build
    hr.build = data                                    # 라우트는 호출할 때 모듈 속성을 읽는다
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    hr.build = old
    server.should_exit = True
    th.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"Chromium 을 띄우지 못했어요 ({type(e).__name__})")
        yield b
        b.close()


def test_home_rankings_flow(site, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    page = ctx.new_page()
    chats: list[str] = []
    page.route("**/api/chat", lambda route: (chats.append(route.request.post_data or ""), route.fulfill(
        status=200, content_type="application/json", body='{"session_id":"s","blocks":[{"type":"text","data":{"text":"좋아요"}}]}'))[1])
    page.route("**/home/go/**", lambda route: route.fulfill(status=200, body="ok"))
    page.goto(site + "/#")
    sec = page.get_by_role("region", name="지금 순위")
    # 홈 첫 탭 = 쿠팡 식품 랭킹: 고지가 첫 상품 링크보다 앞, 링크는 /home/go 경유, 급상승 탭은 홈에 없음
    link = sec.get_by_role("link", name="신선한 대란 — 쿠팡에서 보기 (새 창)")
    link.wait_for()
    assert [t.inner_text() for t in sec.get_by_role("tab").all()] == ["쿠팡 식품 랭킹", "카테고리", "함께 보면 좋은 상품"]
    assert link.get_attribute("href") == "/home/go/7230779632" and "sponsored" in link.get_attribute("rel")
    html = sec.inner_html()
    assert html.index("쿠팡 파트너스") < html.index("/home/go/")
    assert sec.get_by_text("새로 진입").count() == 1 and sec.get_by_text("대방어").count() == 0
    with ctx.expect_page() as popup:
        sec.get_by_role("link", name="돌 스위티오 바나나 — 쿠팡에서 보기 (새 창)").click()
    popup.value.close()
    # 카테고리 → 칩 → 오르는 중이 기본, 원래 순위 번호
    sec.get_by_role("tab", name="카테고리").click()
    sec.get_by_role("button", name="사과 대화로 묻기 · 식품 검색어 7위").wait_for()
    assert sec.get_by_text("상위 500위 진입").count() == 1
    sec.get_by_role("button", name="요리/식재료").click()
    # 11-23 저녁: 홈은 오르는 중 먼저 + 나머지 순위순으로 채우므로 '비교 자료 없음' 안내는 전체 화면에서만
    sec.get_by_role("button", name="쌀20kg 대화로 묻기 · 식품 검색어 12위").wait_for()
    # 함께 보면 좋은 상품: 방금 누른 품목(바나나)을 본문으로 보냄 → 맞춤 끄기면 보내지 않음
    sec.get_by_role("tab", name="함께 보면 좋은 상품").click()
    sec.get_by_text("맞춤 추천 · 이 브라우저에서 최근 누른 품목 기준").wait_for()
    assert TOGETHER_SEEN[-1] == "바나나"
    tl = sec.get_by_role("link", name="곰곰 아삭한 콩나물 — 쿠팡에서 보기 (새 창)")
    assert tl.get_attribute("href") == "/home/go/1275124832?from=together"
    sec.get_by_role("button", name="맞춤 추천 끄기").click()
    sec.get_by_text("일반 추천 · 쿠팡 식품 랭킹 1위").wait_for()
    assert TOGETHER_SEEN[-1] == ""
    assert page.evaluate(NAMELESS_JS) == []
    body = page.locator("body").inner_text()
    assert "장바구니" not in body and "주문" not in body
    # 키워드를 두 번 눌러도 질문은 한 번
    sec.get_by_role("tab", name="카테고리").click()
    sec.get_by_role("button", name="과일").click()
    btn = sec.get_by_role("button", name="사과 대화로 묻기 · 식품 검색어 7위")
    btn.dblclick()
    page.get_by_text("좋아요").wait_for()
    assert len(chats) == 1 and "사과 추천해 줘" in chats[0]
    ctx.close()


def test_hot_page_shows_only_surge_foods(site, browser):
    """2026-11-23 사용자 요청: 지금 뜨는 식품은 예전처럼 급상승 식품만 — 급상승·카테고리·쿠팡 식품 랭킹 탭 없음."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, locale="ko-KR")
    page = ctx.new_page()
    page.goto(site + "/#/hot")
    page.get_by_role("heading", name="지금 뜨는 식품", level=1).wait_for()
    page.locator("li.card").first.wait_for()                   # 급상승 카드 그대로
    assert page.get_by_role("region", name="지금 순위").count() == 0
    assert page.get_by_role("tab").count() == 0
    assert page.get_by_text("쿠팡 식품 랭킹").count() == 0 and page.get_by_text("순위 전체").count() == 0
    assert page.evaluate(NAMELESS_JS) == []
    ctx.close()


def test_privacy_in_one_place(site, browser):
    """2026-11-23: 개인정보 설명은 처리방침 한 곳 — 입력창 안내·맞춤 추천 칸·바닥글의 링크가 모두 /#/privacy."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    page = ctx.new_page()
    page.goto(site + "/#")
    page.get_by_role("region", name="지금 순위").get_by_role("tab", name="함께 보면 좋은 상품").wait_for()
    links = page.get_by_role("link", name="개인정보처리방침")
    assert links.count() >= 2 and {links.nth(i).get_attribute("href") for i in range(links.count())} == {"/#/privacy"}
    assert "서버에 저장하지 않" not in page.locator("body").inner_text()
    links.last.click()
    page.get_by_role("heading", name="개인정보처리방침", level=1).wait_for()
    for h in ("1. 처리하는 정보와 목적", "3. 보유 기간과 파기", "4. 국외 이전"):
        assert page.get_by_role("heading", name=h).count() == 1
    assert page.get_by_text("맞춤 추천 끄기").count() >= 1 and page.get_by_text("시행 전 안내").count() == 1
    assert page.evaluate(NAMELESS_JS) == []
    ctx.close()


def test_home_fold_more_and_category_art_no_full_link(site, browser):
    """2026-11-23 사용자 요청: 홈 '전체 보기' 링크 없음 · 쿠팡 식품 랭킹 30개까지(처음 6개 + 더보기/접기) · 카테고리는 그림 아이콘 타일."""
    extra = [dict(CP[0], rank=10 + i, product_id=f"90{i}", title=f"시험 상품 {i}", go_url=f"/home/go/90{i}") for i in range(7)]
    CP.extend(extra)
    try:
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
        page = ctx.new_page()
        page.goto(site + "/#")
        sec = page.get_by_role("region", name="지금 순위")
        sec.get_by_role("tab", name="쿠팡 식품 랭킹").wait_for()
        assert sec.get_by_role("link", name="전체 보기").count() == 0 and page.get_by_text("전체 보기").count() == 0
        tiles = sec.locator("ul li a[aria-label$='쿠팡에서 보기 (새 창)']")
        assert tiles.count() == 6
        more = sec.get_by_role("button", name="더보기 3개")
        more.click()
        assert tiles.count() == 9
        sec.get_by_role("button", name="접기").click()
        assert tiles.count() == 6
        sec.get_by_role("tab", name="카테고리").click()
        grid = sec.get_by_role("group", name="카테고리")
        assert grid.get_by_role("button", name="과일").get_attribute("aria-pressed") == "true"
        assert grid.locator("svg").count() >= 2
        grid.get_by_role("button", name="요리/식재료").click()
        sec.get_by_role("button", name="쌀20kg 대화로 묻기 · 식품 검색어 12위").wait_for()
        assert page.evaluate(NAMELESS_JS) == []
        ctx.close()
    finally:
        del CP[len(CP) - len(extra):]


def test_recent_viewed_and_policy_page(site, browser):
    """2026-11-23 사용자 채택: 최근 본 상품(이 브라우저에만, 홈 가로 줄·내 보관함) · 갱신 간격 등 기준은 운영정책(/#/policy) 한 곳에."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    ctx.route("**/home/go/**", lambda r: r.fulfill(status=200, body="ok"))   # 판매처로 나가지 않게
    page = ctx.new_page()
    page.goto(site + "/#")
    sec = page.get_by_role("region", name="지금 순위")
    sec.get_by_role("tab", name="쿠팡 식품 랭킹").wait_for()
    assert page.get_by_role("region", name="최근 본 상품").count() == 0          # 본 상품이 없으면 줄도 없음
    sec.get_by_role("button", name="순위 기준 설명").click()
    assert "10분" not in sec.inner_text() and "1시간" not in sec.inner_text()
    with ctx.expect_page() as pop:
        sec.locator("a[aria-label^='신선한 대란']").click()
    pop.value.close()
    row = page.get_by_role("region", name="최근 본 상품")
    row.wait_for()
    assert row.get_by_role("link", name="신선한 대란 — 판매처에서 보기 (새 창)").get_attribute("href") == "/home/go/7230779632"
    stored = page.evaluate("localStorage.getItem('ai-food-viewed')")
    assert "7230779632" in stored and "7880" not in stored                    # 가격은 남기지 않음
    page.goto(site + "/#/me")
    page.get_by_role("heading", name="최근 본 상품").wait_for()
    page.get_by_role("button", name="신선한 대란 최근 본 상품에서 빼기").click()
    page.get_by_text("최근에 연 상품이 없어요.").wait_for()
    page.goto(site + "/#")
    page.get_by_role("link", name="운영정책").first.click()
    page.get_by_role("heading", name="운영정책", level=1).wait_for()
    assert "10분" in page.locator("main").inner_text()
    assert page.evaluate(NAMELESS_JS) == []
    ctx.close()



def test_home_category_shows_six_then_more(site, browser):
    """2026-11-23 저녁 사용자 요청: 카테고리도 6개만 보이고 '더보기'로 펼치기·접기, 카테고리를 바꾸면 다시 6개."""
    EXTRA_FRUIT.extend(kw(50 + i, f"과일{i}", ["fruit"]) for i in range(6))
    try:
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
        page = ctx.new_page()
        page.goto(site + "/#")
        sec = page.get_by_role("region", name="지금 순위")
        sec.get_by_role("tab", name="카테고리").click()
        rows = sec.locator("ol li button[aria-label*='대화로 묻기']")
        rows.first.wait_for()
        assert rows.count() == 6
        sec.get_by_role("button", name="더보기 2개").click()
        assert rows.count() == 8
        sec.get_by_role("group", name="카테고리").get_by_role("button", name="요리/식재료").click()
        sec.get_by_role("group", name="카테고리").get_by_role("button", name="과일").click()
        assert rows.count() == 6                                   # 바꾸면 다시 접힘
        ctx.close()
    finally:
        EXTRA_FRUIT.clear()



def test_category_keyword_products_and_highlight(site, browser, monkeypatch):
    """2026-11-23 밤: 그래프 없음 · '이번 주 주목'과 키워드마다 쿠팡 상품 사진 3개 + 더보기/접기 · 순위·늘 인기·변화 표기 ·
    광고 표시가 링크보다 앞."""
    from app.services.trends import highlight as hl

    HIGHLIGHT.append({"keyword": "사과", "rank": 7, "change_7d": 5, "change_kind": "compared", "ask": "사과 추천해 줘"})
    monkeypatch.setattr(hl, "picks", lambda kw, search=None: [{
        "keyword": kw, "title": f"{kw} 상품 {i}", "image": "data:image/gif;base64,R0lGODlhAQABAAAAACw=", "price_krw": 19900 + i,
        "rocket": i == 1, "go_url": f"/home/hgo/{abs(hash(kw)) % 10**6:06d}{i:06d}", "fetched_at": "2026-11-23T17:30+09:00"}
        for i in range(1, 6)])
    try:
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
        page = ctx.new_page()
        page.goto(site + "/#")
        sec = page.get_by_role("region", name="지금 순위")
        sec.get_by_role("tab", name="카테고리").click()
        hcard = sec.get_by_role("region", name="이번 주 주목")
        hcard.get_by_text("7일 새 5계단 올랐어요").wait_for()
        hcard.get_by_role("link", name="사과 상품 1 — 쿠팡에서 보기 (새 창)").wait_for()
        assert hcard.get_by_role("link").count() == 3 and hcard.locator("img").count() == 3
        html = hcard.inner_html()
        assert html.index("광고") < html.index("/home/hgo/")
        hcard.get_by_role("button", name="더보기 2개").click()
        fold = hcard.get_by_role("button", name="접기")
        assert hcard.get_by_role("link").count() == 5 and fold.get_attribute("aria-expanded") == "true"
        fold.click()
        assert hcard.get_by_role("link").count() == 3
        # 키워드마다 상품 3개 + 더보기 · 순위·변화 표기
        shelf = sec.get_by_role("listitem", name="사과 · 식품 검색어 7위")
        shelf.get_by_role("link", name="사과 상품 1 — 쿠팡에서 보기 (새 창)").wait_for()
        assert shelf.get_by_role("link").count() == 3
        assert shelf.get_by_text("7위").count() >= 1 and shelf.get_by_text("↑", exact=False).count() >= 1
        shelf.get_by_role("button", name="더보기 2개").click()
        assert shelf.get_by_role("link").count() == 5
        assert sec.get_by_role("button", name="사과 대화로 묻기 · 식품 검색어 7위").count() == 1
        lst = sec.inner_html()
        assert lst.index("광고") < lst.index("/home/hgo/")
        assert page.evaluate(NAMELESS_JS) == []
        ctx.close()
    finally:
        HIGHLIGHT.clear()


def test_keyword_without_coupang_products_links_to_naver(site, browser, monkeypatch):
    """2026-11-23: 쿠팡에 맞는 식품 상품이 없는 키워드(예: 정관장)는 네이버쇼핑 검색 링크 (제휴 아님 표기)."""
    from app.services.trends import highlight as hl

    monkeypatch.setattr(hl, "picks", lambda kw, search=None: [] if kw == "대봉감" else [{
        "keyword": kw, "title": f"{kw} 상품", "image": None, "price_krw": 1000, "rocket": False,
        "go_url": "/home/hgo/0123456789ab", "fetched_at": "2026-11-23T22:50+09:00"}])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    page = ctx.new_page()
    page.goto(site + "/#")
    sec = page.get_by_role("region", name="지금 순위")
    sec.get_by_role("tab", name="카테고리").click()
    shelf = sec.get_by_role("listitem", name="대봉감 · 식품 검색어 18위")
    link = shelf.get_by_role("link", name="네이버쇼핑에서 대봉감 찾아보기 (새 창, 제휴 아님)")
    link.wait_for()
    assert link.get_attribute("href") == "https://search.shopping.naver.com/search/all?query=%EB%8C%80%EB%B4%89%EA%B0%90"
    assert "sponsored" not in (link.get_attribute("rel") or "") and shelf.get_by_text("제휴 아님 · 수수료 없음").count() == 1
    ctx.close()
