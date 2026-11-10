"""POST /api/chat and GET /go through FastAPI, plus shopping regression."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.api import chat_routes
from app.services.chat import service as chat_service
from app.services.chat.service import ChatService, item_to_card
from app.services.recipe_chat.service import RecipeChat


@pytest.fixture
def client(sqlite_db, shopping):
    svc = ChatService(sqlite_db, shopping=shopping, recipe_chat=RecipeChat(statement_factory=str))
    main.app.dependency_overrides[chat_routes.get_chat_service] = lambda: svc
    try:
        yield TestClient(main.app)
    finally:
        main.app.dependency_overrides.pop(chat_routes.get_chat_service, None)


def test_shopping_request_keeps_existing_recommendation_flow(client, shopping):
    r = client.post("/api/chat", json={"session_id": None, "message": "사과 추천해줘"})
    assert r.status_code == 200
    body = r.json()
    assert body["stage"] == "shopping"
    assert shopping.calls == [("사과", "ranking", body["session_id"])]   # 2026-11-02: 상품어만 검색
    lists = [b for b in body["blocks"] if b["type"] == "product_list"]
    assert len(lists) == 1
    a, b = lists[0]["data"]["items"]
    assert (a["rank"], a["title"], a["price"], a["shipping_fee"], a["total"]) == (1, "테스트 사과 A", 12000, None, None)
    assert (b["rank"], b["price"], b["shipping_fee"], b["total"]) == (2, 9900, 3000, 12900)


def test_priority_words_are_passed_through(client, shopping):
    client.post("/api/chat", json={"message": "사과 최저가 알려줘"})
    assert shopping.calls[-1][1] == "price"


def test_recipe_turns_render_in_the_same_conversation(client, shopping):
    first = client.post("/api/chat", json={"message": "사과 추천해줘"}).json()
    sid = first["session_id"]
    calls = len(shopping.calls)
    r = client.post("/api/chat", json={"session_id": sid, "message": "크림파스타 만드는 법"}).json()
    assert r["session_id"] == sid and r["stage"] == "recipe_guide"
    r = client.post("/api/chat", json={"session_id": sid, "message": "생크림 100mL 있어요"}).json()
    assert r["stage"] == "recipe_stock_saved"
    r = client.post("/api/chat", json={"session_id": sid, "message": "아니, 200mL예요"}).json()
    assert r["stage"] == "recipe_stock_saved"
    r = client.post("/api/chat", json={"session_id": sid, "message": "생크림 대신 뭘 넣어요?"}).json()
    assert r["stage"] == "recipe_answer"
    assert len(shopping.calls) == calls  # no product API call during recipe turns
    assert {b["type"] for b in r["blocks"]} <= {"text", "notice", "verdict", "chips", "clarify_form", "product_list"}

    r = client.post("/api/chat", json={"session_id": sid, "message": "배 추천해줘"}).json()
    assert r["stage"] == "shopping"  # back to shopping in the same session


def test_clarify_answers_payload(client):
    sid = client.post("/api/chat", json={"message": "파스타 요리방법"}).json()["session_id"]
    r = client.post("/api/chat", json={"session_id": sid, "answers": {"recipe": "EPIS:467"}}).json()
    assert r["stage"] == "recipe_guide"


def test_chip_payload_is_treated_as_message(client):
    sid = client.post("/api/chat", json={"message": "크림파스타 만드는 법"}).json()["session_id"]
    r = client.post("/api/chat", json={"session_id": sid, "chip": "소스가 너무 묽어요"}).json()
    assert r["stage"] == "recipe_answer"


def test_go_click_log_carries_the_shown_product_name(client, monkeypatch):
    """2026-11-10 (R0): 상품명 없이 기록하면 user_product_preference(NOT NULL)가 실패해 클릭까지 되돌려졌다."""
    logged = []
    import app.services.analytics_logger as al
    monkeypatch.setattr(al, "log_product_click", lambda **kw: logged.append(kw))
    sid = client.post("/api/chat", json={"message": "사과 추천해줘"}).json()["session_id"]
    r = client.get(f"/go/{sid}/1", follow_redirects=False)
    assert r.headers["location"] == "https://shop.example.com/a"
    product = logged[-1]["product"]
    assert product["product_url"] == "https://shop.example.com/a"
    assert product["product_name"] and product["product_name"] != product["product_url"]
    assert product["rank"] == 1 and product["selected_section"] == "chat"


def test_go_redirects_only_to_items_shown_in_that_session(client):
    sid = client.post("/api/chat", json={"message": "사과 추천해줘"}).json()["session_id"]
    r = client.get(f"/go/{sid}/1", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "https://shop.example.com/a"
    r = client.get(f"/go/{sid}/2", follow_redirects=False)  # javascript: URL rejected
    assert r.headers["location"] == "/"
    r = client.get(f"/go/{sid}/9", follow_redirects=False)
    assert r.headers["location"] == "/"
    r = client.get("/go/00000000-0000-0000-0000-000000000000/1", follow_redirects=False)
    assert r.headers["location"] == "/"


def test_message_length_is_limited(client):
    r = client.post("/api/chat", json={"message": "가" * 501})
    assert r.status_code == 422


def test_shopping_failure_is_reported_in_conversation(sqlite_db):
    from tests.services.chat.conftest import FakeShopping

    svc = ChatService(sqlite_db, shopping=FakeShopping(error=RuntimeError("down")),
                      recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천해줘")
    assert res["stage"] == "shopping"
    assert res["blocks"][0]["type"] == "notice" and res["blocks"][0]["data"]["tone"] == "warn"


def test_default_shopping_is_the_existing_nl_endpoint(monkeypatch):
    """Regression: chat shopping returns exactly what /recommendations/nl returns."""
    captured = []

    def fake_pipeline(q, priority, session_id, limit):
        captured.append((q, priority, session_id, limit))
        return {"summary": "s", "items": [{"product_name": "사과 3kg", "price": 19000,
                                            "product_url": "https://x.example/1"}]}

    monkeypatch.setattr(main, "run_recommendation_pipeline", fake_pipeline)
    via_chat = chat_service.default_shopping("사과 추천해줘", "price", "sid-1")
    via_api = TestClient(main.app).get("/recommendations/nl",
                                       params={"q": "사과 추천해줘", "priority": "price", "session_id": "sid-1"}).json()
    assert via_chat == via_api
    assert via_chat["recommendation_path"] == main.NL_PATH_CANONICAL
    assert captured == [("사과 추천해줘", "price", "sid-1", 10)] * 2


def test_without_database_shopping_still_works_and_stock_is_not_claimed_saved(shopping):
    svc = ChatService(None, shopping=shopping, recipe_chat=RecipeChat(statement_factory=str))
    assert svc.handle(None, message="사과 추천해줘")["stage"] == "shopping"
    res = svc.handle(None, message="크림파스타 만드는 법")
    assert res["stage"] == "recipe_guide"
    res = svc.handle(res["session_id"], message="생크림 100mL 있어요")
    assert res["stage"] in ("recipe_needed", "storage_error")
    assert "기록했어요" not in str(res)


def test_item_to_card_never_invents_shipping():
    card = item_to_card({"product_name": "x", "price": "1000"}, 1)
    assert card["shipping_fee"] is None and card["total"] is None


def test_direct_link_clicks_are_logged_only_for_shown_products(client, tmp_path, monkeypatch):
    """2026-11-02: 쇼핑커넥트는 naver.me 로 바로 열고, /api/click 으로 클릭만 기록한다 (보여 준 상품의 링크일 때만)."""
    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n영주사과 홍로 2kg,햇살품은사과,22900,https://naver.me/s,사과\n",
                   encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    logged = []
    import app.services.analytics_logger as al
    monkeypatch.setattr(al, "log_product_click", lambda **kw: logged.append(kw))
    body = client.post("/api/chat", json={"session_id": None, "message": "사과 추천해줘"}).json()
    card = next(i for b in body["blocks"] if b["type"] == "product_list" for i in b["data"]["items"] if i.get("direct"))
    sid = body["session_id"]
    assert client.post("/api/click", json={"session_id": sid, "rank": card["rank"], "url": "https://evil.example/x"}).status_code == 204
    assert logged == []
    assert client.post("/api/click", json={"session_id": sid, "rank": card["rank"], "url": card["url"]}).status_code == 204
    assert logged and logged[0]["product"]["product_url"] == "https://naver.me/s"
    assert logged[0]["product"]["selected_section"] == "chat_direct" and logged[0]["product"]["product_name"] == "영주사과 홍로 2kg"
