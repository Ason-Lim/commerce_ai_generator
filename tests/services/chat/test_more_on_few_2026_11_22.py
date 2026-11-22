"""2026-11-22 사용자 결정: 쿠팡이 준 상품이 적으면 ① '다른 후보'를 접지 않고 ② 바꿔 쓸 말로 더 찾아 **따로** 보여 준다.

위 후보·순서는 그대로(순위 동결) — 더 찾은 상품은 '다른 말로 더 찾은 상품 · 추천순 아님' 칸.
같은 관련성·식품 분류 거르기를 지나고, 이미 보인 상품(같은 이름)은 빼며, 쿠팡 호출은 최대 2번 더.
"""

from __future__ import annotations

import pytest

from app.services.chat.service import ChatService
from app.services.commerce.search import CHECK_AT_MALL
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.test_evoo_retry_2026_11_22 import ByQuery, _cp, md


@pytest.fixture(autouse=True)
def _on(monkeypatch):
    monkeypatch.setenv("COUPANG_MORE_ON_FEW", "on")


def lists(res):
    return {b["data"].get("title"): b["data"] for b in res["blocks"] if b["type"] == "product_list"}


def test_few_results_search_more_with_synonym(sqlite_db):
    shop = ByQuery({
        "올리브유": [_cp("해표 압착 올리브유 500ml", 6900, 1), _cp("해표 압착 올리브유 900ml", 11900, 2)],
        "올리브오일": [
            _cp("해표 압착 올리브유 500ml", 6900, 1),                       # 이미 보인 상품 → 빼기
            _cp("올리타리아 엑스트라버진 올리브오일 1L", 15900, 3),
            _cp("듀라셀 건전지 AA", 9900, 4) | {"category_name": "생활용품"},   # 식품 아님 → 빼기
        ],
    })
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="올리브유")
    assert shop.calls == ["올리브유", "올리브오일"]
    more = lists(res)["다른 검색어로 찾은 추가 후보 1개"]
    assert [i["title"] for i in more["items"]] == ["올리타리아 엑스트라버진 올리브오일 1L"]
    assert "기존 추천 목록과 함께 정렬하지 않았어요" in more["note"] and "'올리브오일'" in more["note"]
    assert not more.get("collapsed")
    assert CHECK_AT_MALL in md(res) and "검색 API" not in md(res)


def test_many_results_do_not_search_more(sqlite_db):
    shop = ByQuery({"올리브유": [_cp(f"올리브유 상품 {n}호 500ml", 6900 + n * 100, n) for n in range(1, 8)]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="올리브유")
    assert shop.calls == ["올리브유"]
    assert not any(t and t.startswith("다른 검색어로 찾은") for t in lists(res))


def test_off_switch(sqlite_db, monkeypatch):
    monkeypatch.setenv("COUPANG_MORE_ON_FEW", "off")
    shop = ByQuery({"올리브유": [_cp("해표 압착 올리브유 500ml", 6900, 1)],
                    "올리브오일": [_cp("올리타리아 엑스트라버진 올리브오일 1L", 15900, 3)]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    svc.handle(None, message="올리브유")
    assert shop.calls == ["올리브유"]


def test_more_search_failure_keeps_first_results(sqlite_db):
    class Flaky(ByQuery):
        def __call__(self, query, priority, session_id):
            if query == "올리브오일":
                self.calls.append(query)
                raise RuntimeError("rate limited")
            return super().__call__(query, priority, session_id)

    shop = Flaky({"올리브유": [_cp("해표 압착 올리브유 500ml", 6900, 1)]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="올리브유")
    assert "해표 압착 올리브유 500ml" in [i["title"] for d in lists(res).values() for i in d["items"]]
    assert "불러오지 못했어요" not in md(res)


def test_few_others_are_not_collapsed(sqlite_db):
    shop = ByQuery({"참기름": [_cp(f"참기름 {n}호 300ml", 6900 + n * 700, n) for n in range(1, 6)]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="참기름")
    other = [d for t, d in lists(res).items() if t and t.startswith("다른 후보")]
    assert other and not other[0].get("collapsed")


def test_many_others_stay_collapsed(sqlite_db):
    shop = ByQuery({"참기름": [_cp(f"참기름 {n}호 300ml", 6900 + n * 700, n) for n in range(1, 9)]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="참기름")
    other = [d for t, d in lists(res).items() if t and t.startswith("다른 후보")]
    assert other and other[0].get("collapsed")
