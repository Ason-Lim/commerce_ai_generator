"""2026-11-22 사용자 대화 확인: '올리브유' → '엑스트라 버전' → '쿠팡에서 엑스트라버진 올리브유 관련 상품을 찾지 못했어요'.

쿠팡 파트너스 검색은 '엑스트라버진 올리브유'(붙여 씀)에 0건, '올리브유 엑스트라'·'버진 올리브유'에는 상품을 돌려줬다(MCP 재현).
→ 0건이면 '엑스트라 버진 올리브유' → '올리브유' 순으로 다시 찾고, 엑스트라버진을 찾았으니 포마스·퓨어는 빼고
  등급 표기 상품을 먼저 견준다.
"""

from __future__ import annotations

from app.services.chat.service import ChatService
from app.services.commerce.search import grade_filter, retry_queries
from app.services.recipe_chat.service import RecipeChat


def _cp(name, price, item_id):
    return {
        "product_name": name,
        "price": price,
        "platform": "coupang",
        "mall_name": "쿠팡",
        "is_coupang": True,
        "product_url": f"https://link.coupang.com/re/AFFSDP?pageKey=100&itemId={item_id}&vendorItemId=9{item_id}",
        "category_name": "식품",
    }


BASE = [
    _cp("해표 압착 올리브유", 6900, 1),
    _cp("살부루아 올리브 포마스유 1L (PET)", 19900, 2),
    _cp("커클랜드 엑스트라버진 올리브유 3L 스페인산 저온압착 올리브오일", 71980, 3),
    _cp("올리타리아 엑스트라 버진 올리브유, 1L, 1개", 15900, 4),
    _cp("피에트로코리첼리 올리브유", 11500, 5),
]


class ByQuery:
    """쿠팡처럼 검색어마다 다른 결과 — 없는 말은 0건."""

    def __init__(self, table):
        self.table, self.calls = table, []

    def __call__(self, query, priority, session_id):
        self.calls.append(query)
        return {"items": list(self.table.get(query, [])), "recommendation_path": "canonical_provider"}


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def titles(res):
    return [i["title"] for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]


def test_retry_queries():
    assert retry_queries("엑스트라버진 올리브유") == ["엑스트라 버진 올리브유", "올리브유"]
    assert retry_queries("올리브유") == ["올리브오일"]          # 2026-11-22: 바꿔 쓸 말 표 (data/query_synonyms.csv)
    assert retry_queries("참기름") == []


def test_grade_filter_drops_other_grades_and_unlabelled_when_enough():
    cards = [{"title": t["product_name"]} for t in BASE]
    kept, info = grade_filter("엑스트라버진 올리브유", cards)
    assert [c["title"] for c in kept] == [BASE[2]["product_name"], BASE[3]["product_name"]]
    assert info == {"stated": 2, "unknown": 0, "dropped": 3}


def test_grade_filter_keeps_unlabelled_with_note_when_few():
    cards = [
        {"title": "커클랜드 엑스트라버진 올리브유 3L"},
        {"title": "피에트로코리첼리 올리브유"},
        {"title": "프리모셰프 포마스 올리브오일"},
    ]
    kept, info = grade_filter("엑스트라버진 올리브유", cards)
    assert [c["title"] for c in kept] == ["커클랜드 엑스트라버진 올리브유 3L", "피에트로코리첼리 올리브유"]
    assert "grade_note" in kept[1] and "grade_note" not in kept[0]
    assert info == {"stated": 1, "unknown": 1, "dropped": 1}
    assert grade_filter("올리브유", cards) == (cards, None)


def test_chat_retries_when_coupang_returns_nothing(sqlite_db):
    shop = ByQuery({"올리브유": BASE})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라 버진 올리브유")
    assert shop.calls == ["엑스트라버진 올리브유", "엑스트라 버진 올리브유", "올리브유"]
    got = titles(res)
    assert BASE[2]["product_name"] in got and BASE[3]["product_name"] in got
    assert not any("포마스" in t for t in got) and "해표 압착 올리브유" not in got
    text = md(res)
    assert "'올리브유'로 다시 찾았어요" in text and "엑스트라버진 표기가 있는 상품 2개" in text
    assert "찾지 못했어요" not in text


def test_followup_after_olive_oil_uses_retry(sqlite_db):
    shop = ByQuery({"올리브유": BASE})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="엑스트라 버전")
    assert "엑스트라버진 올리브유" in shop.calls[1]
    assert BASE[2]["product_name"] in titles(res)
    assert "grade_note" not in str([b for b in res["blocks"] if b["type"] == "product_list"])


def test_no_retry_when_first_search_has_results(sqlite_db):
    shop = ByQuery({"엑스트라버진 올리브유": [BASE[2]]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    svc.handle(None, message="엑스트라버진 올리브유")
    assert shop.calls == ["엑스트라버진 올리브유"]


def test_still_empty_after_retries(sqlite_db):
    shop = ByQuery({})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라버진 올리브유")
    assert len(shop.calls) == 3
    assert "찾지 못했어요" in md(res)
