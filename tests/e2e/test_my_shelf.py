"""화면 시험 '내 보관함' (2026-11-22, 창 3-B — roadmap '고객 화면 상세: 내 보관함' 넘어가는 기준).

- 새 대화를 눌러도 관심·장보기가 남음
- 장보기 칸이 대화와 보관함에 같은 내용
- '기록 지우기'로 최근 검색·관심·장보기·설정이 모두 지워짐(서버 기록 포함)
- 설정 값이 네트워크 요청에 실리지 않음
- 화면에 '장바구니'·'주문' 문구 0, 이름 없는 버튼·링크 0
- PC 사람 아이콘 · 모바일 아래 탭 4번째
실행(맥): uv run playwright install chromium → npm --prefix frontend run build → uv run pytest tests/e2e -q
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time

import pytest

pw = pytest.importorskip("playwright.sync_api")

from tests.e2e.test_site_browser import DIST, NAMELESS_JS, _free_port  # noqa: E402

AVOID = "땅콩버터잼"           # 설정에만 넣는 말 — 어떤 요청에도 실리면 안 됨

BASKET = [{"ingredient": "대파", "mode": "short", "sessionId": None, "blocks": [
    {"type": "product_list", "data": {"items": [{"rank": 1, "title": "국내산 대파 1kg", "price": 3900, "mall": "쿠팡",
                                                  "source": "쿠팡", "key": "aaaaaaaaaaaa"}]}}]}]


@pytest.fixture(scope="module")
def shelf_site(tmp_path_factory):
    if not (DIST / "index.html").is_file():
        pytest.skip("화면 빌드(frontend/dist)가 없어요 — npm --prefix frontend run build")
    import uvicorn
    from fastapi import FastAPI

    from app.api import chat_routes
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat
    from app.web_frontend import mount_frontend
    from tests.services.chat.conftest import DDL, SqliteDb
    from tests.services.chat.test_evoo_retry_2026_11_22 import ByQuery, _cp

    path = tmp_path_factory.mktemp("db") / "chat.sqlite3"
    raw = sqlite3.connect(path)
    raw.executescript(DDL)
    raw.close()
    shop = ByQuery({"사과": [_cp("부사 사과 2kg", 19900, 1), _cp("홍로 사과 3kg", 25900, 2), _cp("시나노골드 사과 2kg", 22900, 3)]})
    svc = ChatService(SqliteDb(path), shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    app = FastAPI()

    @app.get("/api/trend-examples")
    def _examples():
        return {"items": []}

    app.include_router(chat_routes.router)
    app.dependency_overrides[chat_routes.get_chat_service] = lambda: svc
    mount_frontend(app, DIST)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
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


def test_my_shelf_scenario(shelf_site, browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    page = ctx.new_page()
    sent: list[str] = []
    page.on("request", lambda r: sent.append(r.url + " " + (r.post_data or "")))
    page.on("dialog", lambda d: d.accept())

    # 1) 대화에서 검색 → 관심 담기, 장보기 목록은 브라우저에 미리 넣어 둠(레시피 흐름 대신)
    page.goto(shelf_site + "/")
    page.evaluate("b => localStorage.setItem('ai-food-basket', JSON.stringify(b))", BASKET)
    page.reload()
    assert page.get_by_role("link", name="내 보관함").first.is_visible()            # PC 사람 아이콘
    page.get_by_label("쇼핑 질문").fill("사과")
    page.get_by_role("button", name="질문 보내기").click()
    page.get_by_role("button", name="관심 상품에 담기").first.click()
    page.get_by_role("button", name="관심 상품에서 빼기").first.wait_for()
    # 2026-11-23: 레시피 이야기가 아닌 차례(사과 검색)에서는 담아 둔 재료를 이름 한 줄로만 (상품은 보관함)
    assert page.get_by_role("note", name="담아 둔 부족한 재료").get_by_text("대파").is_visible()   # 대화 칸

    # 2) 새 대화 → 보관함: 관심·장보기·최근 검색이 남아 있음
    page.get_by_role("button", name="새 대화").click()
    page.goto(shelf_site + "/#/me")
    page.get_by_role("heading", name="내 보관함").wait_for()
    recent = page.get_by_role("region", name="최근 검색")
    recent.get_by_text("사과").first.wait_for()
    assert page.get_by_role("region", name="관심 상품").get_by_text("에서 담은 상품 1개").is_visible()
    assert page.get_by_role("region", name="장보기 목록").get_by_text("국내산 대파 1kg").is_visible()   # 같은 내용

    # 3) 설정 — 기기 안에만
    page.get_by_label("피하고 싶은 재료 입력").fill(AVOID)
    page.get_by_role("button", name="추가").click()
    page.get_by_label("맵지 않은 것 (매운 상품 표시)").check()
    stored = json.loads(page.evaluate("() => localStorage.getItem('ai-food-prefs')"))
    assert AVOID in stored["avoid"] and stored["mild"] is True

    # 4) 화면 문구·접근성
    text = page.inner_text("main")
    assert "장바구니" not in text and "주문" not in text
    assert page.evaluate(NAMELESS_JS) == []

    # 5) 대화로 돌아가 다시 묻기 — 설정 값은 어떤 요청에도 없음
    recent.get_by_role("button", name="다시 묻기").first.click()
    page.get_by_role("button", name="관심 상품에서 빼기").first.wait_for()
    assert not any(AVOID in s for s in sent), [s for s in sent if AVOID in s]

    # 6) 기록 지우기 — 서버 삭제가 실패하면 아무것도 지우지 않음(세션 값을 남겨 다시 시도)
    page.goto(shelf_site + "/#/me")
    owner_before = page.evaluate("() => localStorage.getItem('ai-food-saved-owner')")
    page.route("**/api/me/forget", lambda route: route.fulfill(status=500, body="{}"))
    page.get_by_role("button", name="보관함·최근 대화 기록 지우기").click()
    page.get_by_text("서버 기록을 지우지 못했어요", exact=False).wait_for()
    assert page.evaluate("() => localStorage.getItem('ai-food-sessions')") is not None
    assert page.get_by_role("region", name="장보기 목록").get_by_text("국내산 대파 1kg").is_visible()
    page.unroute("**/api/me/forget")
    # 다시 누르면 모두 비움 (서버 기록 포함), 보관함 주인 값도 새로
    page.get_by_role("button", name="보관함·최근 대화 기록 지우기").click()
    page.get_by_text("기록을 모두 지웠어요", exact=False).wait_for()
    assert page.evaluate("() => localStorage.getItem('ai-food-saved-owner')") != owner_before
    assert page.evaluate("() => [localStorage.getItem('ai-food-basket'), localStorage.getItem('ai-food-prefs'),"
                         " localStorage.getItem('ai-food-sessions')]") == [None, None, None]
    page.reload()
    page.get_by_role("heading", name="내 보관함").wait_for()
    page.get_by_text("아직 검색한 상품이 없어요.").wait_for()
    # 지운 예전 주인 값으로도 서버에 남은 것이 없음
    gone = page.request.get(f"{shelf_site}/api/me?owner={owner_before}&sessions=").json()
    assert gone["saved"] == []
    assert page.get_by_text("아직 담은 상품이 없어요.", exact=False).is_visible()
    assert not any(AVOID in s for s in sent)
    ctx.close()


def test_mobile_fourth_tab(shelf_site, browser):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, locale="ko-KR", is_mobile=True)
    pg = ctx.new_page()
    pg.goto(shelf_site + "/")
    tabs = pg.locator("nav[aria-label='주요 메뉴']").last
    assert tabs.locator("a").count() == 4
    tabs.get_by_role("link", name="내 보관함").click()
    pg.get_by_role("heading", name="내 보관함").wait_for()
    assert tabs.locator("a[aria-current=page]").inner_text().strip() == "내 보관함"
    ctx.close()


def test_basket_drop_vs_have_same_in_both_places(shelf_site, browser):
    """'목록에서 빼기'는 목록에서만, '가지고 있어요'는 레시피 대화에도 — 대화 칸·보관함이 같은 버튼·같은 뜻."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    page = ctx.new_page()
    chats: list[str] = []
    page.on("request", lambda r: chats.append(r.post_data or "") if r.url.endswith("/api/chat") else None)
    two = BASKET + [dict(BASKET[0], ingredient="양파", sessionId="00000000-0000-4000-8000-000000000001")]
    page.goto(shelf_site + "/#/me")
    page.evaluate("b => localStorage.setItem('ai-food-basket', JSON.stringify(b))", two)
    page.reload()
    region = page.get_by_role("region", name="장보기 목록")
    region.get_by_text("양파", exact=True).wait_for()
    # 레시피 대화가 없는 재료(대파)는 '가지고 있어요'가 없음
    assert region.get_by_role("button", name="대파 가지고 있어요 (레시피에 반영하고 목록에서 빼기)").count() == 0
    region.get_by_role("button", name="대파 장보기 목록에서 빼기").click()
    region.get_by_text("대파", exact=True).wait_for(state="detached")
    assert chats == []                                        # 목록에서만 — 서버에 아무것도 보내지 않음
    region.get_by_role("button", name="양파 가지고 있어요 (레시피에 반영하고 목록에서 빼기)").click()
    region.get_by_text("양파", exact=True).wait_for(state="detached")
    assert any("양파 충분해요" in c for c in chats)           # 레시피 대화에 알림
    assert page.evaluate("() => JSON.parse(localStorage.getItem('ai-food-basket'))") == []
    ctx.close()


def test_basket_opens_only_during_its_recipe_talk(shelf_site, browser):
    """2026-11-23 운영: 닭백숙에서 담은 '닭' 상품이 같은 대화의 절임배추 질문·다른 대화 아래에도 펼쳐졌다 →
    이 대화에서 담았고 지금 레시피 이야기 중일 때만 펼치고, 그 밖에는 재료 이름 + 보관함 링크 한 줄."""
    import json as _json

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    page = ctx.new_page()
    turns = iter([{"session_id": "s-recipe-1", "stage": "recipe_card", "blocks": [{"type": "text", "data": {"md": "닭백숙 레시피예요."}}]},
                  {"session_id": "s-recipe-1", "stage": "shopping", "blocks": [{"type": "text", "data": {"md": "절임배추 후보예요."}}]}])
    page.route("**/api/chat", lambda route: route.fulfill(status=200, content_type="application/json",
                                                         body=_json.dumps(next(turns), ensure_ascii=False)))
    page.goto(shelf_site + "/")
    mine = [dict(BASKET[0], ingredient="닭", sessionId="s-recipe-1")]
    page.evaluate("b => localStorage.setItem('ai-food-basket', JSON.stringify(b))", mine)
    page.reload()
    page.get_by_label("쇼핑 질문").fill("닭백숙 레시피")
    page.get_by_role("button", name="질문 보내기").click()
    page.get_by_role("region", name="부족한 재료 장보기").get_by_text("닭", exact=True).wait_for()      # 레시피 이야기 중 — 펼침
    page.get_by_label("쇼핑 질문").fill("김장용 절임배추10kg 추천")
    page.get_by_role("button", name="질문 보내기").click()
    page.get_by_text("절임배추 후보예요.").wait_for()
    assert page.get_by_role("region", name="부족한 재료 장보기").count() == 0                            # 다른 이야기 — 접음
    note = page.get_by_role("note", name="담아 둔 부족한 재료")
    assert note.get_by_text("닭").is_visible() and note.get_by_role("link", name="내 보관함에서 보기").is_visible()
    ctx.close()


def test_basket_from_another_conversation_is_one_line(shelf_site, browser):
    """다른 대화에서 담은 재료는 레시피 대화 중이어도 펼치지 않는다."""
    import json as _json

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
    page = ctx.new_page()
    page.route("**/api/chat", lambda route: route.fulfill(status=200, content_type="application/json", body=_json.dumps(
        {"session_id": "s-new-2", "stage": "recipe_card", "blocks": [{"type": "text", "data": {"md": "배추속댓국 레시피예요."}}]},
        ensure_ascii=False)))
    page.goto(shelf_site + "/")
    other = [dict(BASKET[0], ingredient="닭", sessionId="old-session-1234")]
    page.evaluate("b => localStorage.setItem('ai-food-basket', JSON.stringify(b))", other)
    page.reload()
    page.get_by_label("쇼핑 질문").fill("배추속댓국 레시피 알려줘")
    page.get_by_role("button", name="질문 보내기").click()
    page.get_by_role("note", name="담아 둔 부족한 재료").get_by_text("닭").wait_for()
    assert page.get_by_role("region", name="부족한 재료 장보기").count() == 0
    ctx.close()
