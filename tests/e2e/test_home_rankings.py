"""화면 시험 '지금 순위' (창 3-C, 2026-11-22 — 설계 §4 시나리오).

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


def data(view):
    full = view == "full"
    fruit = [APPLE, GAM] + ([kw(40, "귤", ["fruit"], "steady", ch=0, rising=False)] if full else [])
    return {
        "generated_at": "2026-11-22T10:05+09:00", "view": view,
        "surge": {"status": "ok", "data_until": "2026-11-21", "updated_at": "x",
                  "items": [{"n": 1, "keyword": "대방어", "status": "surging", "times": 2.7, "rank": 82, "onset": "2026-11-03", "ask": "대방어 추천해 줘"}]},
        "categories": {"status": "ok", "rank_date": "2026-11-21", "note": "네이버 식품 검색어 순위", "tabs": [
            {"tag": "fruit", "label": "과일", "icon": "Apple", "default_filter": "rising",
             "counts": {"all": len(fruit), "rising": 2, "steady": int(full), "insufficient": 2}, "items": fruit},
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
    page.goto(site + "/#")
    sec = page.get_by_role("region", name="지금 순위")
    sec.get_by_text("대방어").wait_for()
    assert sec.get_by_text("검색량 11/21까지 자료").count() == 1
    # 카테고리 → 칩 → 오르는 중이 기본, 원래 순위 번호
    sec.get_by_role("tab", name="카테고리").click()
    sec.get_by_role("button", name="사과 대화로 묻기 · 식품 검색어 7위").wait_for()
    assert sec.get_by_text("상위 500위 진입").count() == 1
    sec.get_by_role("button", name="요리/식재료").click()
    sec.get_by_text("7일 전 순위와 비교할 자료가 아직 없어").wait_for()
    # 트렌드 상품: 고지가 첫 상품 링크보다 앞, 링크는 /go 경유
    sec.get_by_role("tab", name="트렌드 상품").click()
    link = sec.get_by_role("link", name="부사 사과 3kg 가정용 — 쿠팡에서 보기 (새 창)")
    link.wait_for()
    assert link.get_attribute("href") == "/trends/2026-11-21-a/go/1"
    assert "sponsored" in link.get_attribute("rel")
    html = sec.inner_html()
    assert html.index("쿠팡 파트너스") < html.index("/go/1")
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


def test_full_screen_on_hot_page(site, browser):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, locale="ko-KR")
    page = ctx.new_page()
    page.goto(site + "/#/hot")
    sec = page.get_by_role("region", name="지금 순위")
    sec.locator("li.card").first.wait_for()                  # 급상승 탭 = 기존 카드 그대로
    sec.get_by_role("tab", name="카테고리").click()
    sec.get_by_role("button", name="늘 인기 1").click()
    sec.get_by_role("button", name="귤 대화로 묻기 · 식품 검색어 40위").wait_for()
    assert sec.get_by_text("대봉감").count() == 0
    assert page.evaluate(NAMELESS_JS) == []
    sec.get_by_role("button", name="귤 대화로 묻기 · 식품 검색어 40위").click()
    page.wait_for_function("location.hash === '' || location.hash === '#'")
    ctx.close()
