"""창 4 ③-2 — 식품 안전 신고 상품 노출 임시 중지 (2026-11-23). 설계 claude/stage4_design_2026-11-23.md §3.

* 대화에서 보여 준 상품을 집어 신고하면 그 상품을 막는다(하나로 알아볼 때만). 아니면 후보만 티켓에.
* 표시에서만 뺀다: 대화 검색 결과 · 쿠팡 식품 랭킹 · 함께 보면 좋은 상품 · 트렌드 글. 순위 번호는 그대로.
* 푸는 건 관리자만.
"""
from __future__ import annotations

import datetime as dt
import inspect
import json

from app.services.chat.service import ChatService
from app.services.cs import blocked as BL
from app.services.cs import tickets as T
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

OWNER = "11111111-2222-3333-4444-555555555555"


def _url(pid):
    return f"https://link.coupang.com/re/AFFSDP?lptag=AF1&pageKey={pid}&itemId=1&vendorItemId=2&traceid=x"


ITEMS = [{"product_name": "상주 반건시 곶감 1kg", "price": 19900, "product_url": _url(111), "platform_name": "coupang", "is_coupang": True},
         {"product_name": "영동 곶감 말랭이 500g", "price": 12900, "product_url": _url(222), "platform_name": "coupang", "is_coupang": True},
         {"product_name": "청도 대봉 곶감 2kg", "price": 15900, "product_url": _url(333), "platform_name": "coupang", "is_coupang": True}]


class _NLU:
    def parse(self, text):
        return {"action_intent": "shopping"}


def _svc(db, items=ITEMS):
    return ChatService(db, shopping=FakeShopping(items=list(items)), nlu_loader=lambda: _NLU(),
                       recipe_chat=RecipeChat(statement_factory=str))


def _md(res):
    return json.dumps(res["blocks"], ensure_ascii=False)


def test_product_id_from_card_and_url():
    assert BL.product_id({"product_id": "9202103586"}) == "9202103586"
    assert BL.product_id({"url": _url(6241417032)}) == "6241417032"
    assert BL.product_id({"url": "https://www.coupang.com/vp/products/77?itemId=1"}) == "77"
    assert BL.product_id({"url": "https://shop.example.com/a"}) is None


def test_report_by_name_blocks_that_product_and_admin_unblocks(sqlite_db):
    svc = _svc(sqlite_db)
    sid = svc.handle(None, message="곶감 추천해줘", owner=OWNER)["session_id"]
    res = svc.handle(sid, message="상주 곶감 먹고 배탈 났어요", owner=OWNER)
    t = T.queue()[0]
    assert t["domain"] == "food_safety" and t["blocked_product"] == "111"
    assert {p["product_id"] for p in t["products"]} == {"111", "222", "333"}
    assert "먹고" not in json.dumps(BL.listing(), ensure_ascii=False)        # 손님 문장은 목록에 없음
    assert "잠시 보여 드리지 않아요" in _md(res) and "상주 반건시 곶감" in _md(res)
    # 다음 검색부터 빠지고, 뺐다고 알린다
    again = svc.handle(None, message="곶감 추천해줘", owner=OWNER)
    shown = [c["title"] for b in again["blocks"] if b["type"] == "product_list" for c in b["data"]["items"]]
    assert "상주 반건시 곶감 1kg" not in shown and shown
    assert "1개는 판매처 확인 중인 상품이라" in _md(again)
    # 풀기는 관리자만 — 대화 코드에는 푸는 길이 없다
    from app.services.chat import service as chat_service
    assert "unblock" not in inspect.getsource(chat_service)
    assert BL.unblock("111", by="operator")["active"] is False
    back = svc.handle(None, message="곶감 추천해줘", owner=OWNER)
    assert "상주 반건시 곶감 1kg" in _md(back) and "판매처 확인 중" not in _md(back)


def test_report_by_number_uses_last_list_rank(sqlite_db):
    svc = _svc(sqlite_db)
    first = svc.handle(None, message="곶감 추천해줘", owner=OWNER)
    second = [c for b in first["blocks"] if b["type"] == "product_list" for c in b["data"]["items"]][1]
    svc.handle(first["session_id"], message="2번 상품에 곰팡이가 피어 있어요", owner=OWNER)
    assert BL.blocked_ids() == frozenset({BL.product_id({"url": second["url"]})})


def test_unclear_report_only_attaches_candidates(sqlite_db):
    svc = _svc(sqlite_db)
    sid = svc.handle(None, message="곶감 추천해줘", owner=OWNER)["session_id"]
    res = svc.handle(sid, message="곶감 먹고 나서 배가 너무 아파요 식중독 같아요", owner=OWNER)   # 세 상품 모두 '곶감' 
    t = T.queue()[0]
    assert BL.blocked_ids() == frozenset() and "blocked_product" not in t and len(t["products"]) == 3
    assert "잠시 보여 드리지 않아요" not in _md(res)


def test_report_without_shown_products_blocks_nothing(sqlite_db):
    _svc(sqlite_db).handle(None, message="어제 산 굴 먹고 배탈 났어요", owner=OWNER)
    assert BL.blocked_ids() == frozenset() and "products" not in T.queue()[0]


def test_empty_list_changes_nothing():
    items = [{"product_id": "1"}, {"url": _url(2)}]
    assert BL.visible(items) == (items, 0)


def test_home_ranking_together_and_search_hide_blocked(monkeypatch):
    from app.services.trends import coupang_best as cb

    snap = {"fetched_at": "2026-11-23T22:00+09:00", "items": [
        {"rank": i, "product_id": str(i), "title": f"상품 {i}", "image": None, "price_krw": 1000, "rocket": False,
         "url": _url(i)} for i in (1, 2, 3)]}
    BL.block("2", title="상품 2", by="operator")
    got = cb.ranked(dt.date(2026, 11, 23), dt.datetime(2026, 11, 23, 22, 0), 10, snap=snap)
    assert [it["rank"] for it in got["items"]] == [1, 3]                       # 순위 번호는 그대로, 표시에서만 빠짐
    from app.services.trends import together

    pool = together.pool(dt.date(2026, 11, 23), dt.datetime(2026, 11, 23, 22, 0), posts=type("P", (), {"published": lambda self: []})(),
                         snap=snap)
    assert "2" not in {it["product_id"] for it in pool}
    # 쿠팡 검색(홈 키워드 상품·이번 주 주목도 이 함수를 씀) — 캐시 뒤에서 거름
    from app.services import coupang_api

    monkeypatch.setattr(coupang_api, "_search_coupang_products_cached", lambda k, n: [
        {"product_name": "a", "product_url": _url(2), "product_id": "2"}, {"product_name": "b", "product_url": _url(4)}])
    assert [x["product_name"] for x in coupang_api.search_coupang_products("곶감", 10)] == ["b"]
    # 홈 쿠팡 랭킹 이동 주소도 막힘
    from fastapi.testclient import TestClient

    from app.main import app
    r = TestClient(app).get("/home/go/2", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"



def test_trend_post_page_hides_blocked_product_keeps_numbers():
    from app.services.trend_posts import draft, policy, render
    from app.services.trend_posts.model import Post
    from tests.services.trend_posts.test_trend_posts import search_result

    prods = draft.products_from_result(search_result())[:2]
    prods = [p.model_copy(update={"url": _url(500 + i)}) for i, p in enumerate(prods)]
    post = Post(id="2026-11-23-x", topic="x", title="[광고] x", disclosure=policy.disclosure_text(), products=prods,
                created_at="2026-11-23T00:00:00+00:00", updated_at="2026-11-23T00:00:00+00:00")
    BL.block("500", title=prods[0].title, by="operator")
    html = render.post_page(post)
    assert prods[0].title not in html and "1번 상품은 판매처 확인 중인 상품이라" in html
    assert prods[1].title in html and "/go/2" in html and "/go/1" not in html


def test_admin_routes_block_only_ticket_candidates_and_unblock(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("ADMIN_ACCESS_TOKEN", "test-token")
    t = T.create("food_safety", sid="abcd1234", owner=None, summary="곶감 먹고 배탈")
    T.attach_products(t["id"], [{"product_id": "111", "title": "상주 반건시 곶감 1kg"}])
    c = TestClient(app)
    h = {"X-Access-Token": "test-token"}
    assert c.post("/admin/api/cs/blocked", json={"product_id": "999", "ticket_id": t["id"]}, headers=h).status_code == 400
    r = c.post("/admin/api/cs/blocked", json={"product_id": "111", "ticket_id": t["id"]}, headers=h)
    assert r.status_code == 200 and BL.blocked_ids() == frozenset({"111"})
    assert c.get("/admin/api/cs/blocked", headers=h).json()["products"][0]["title"] == "상주 반건시 곶감 1kg"
    assert c.post("/admin/api/cs/blocked/111/unblock").status_code in (401, 403)             # 토큰 없으면 못 풂
    assert c.post("/admin/api/cs/blocked/111/unblock", headers=h).status_code == 200 and BL.blocked_ids() == frozenset()
