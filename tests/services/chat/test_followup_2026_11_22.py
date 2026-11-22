"""2026-11-22 대화 이어 묻기 1단계 (claude/chat_followup_design_2026-11-20.md · 쿠팡 빈칸 3단계).

사용자 결정(16:12): 정렬 보기 허용('추천순 아님' 라벨), 쿠팡 다시 찾기 세션당 10번.
"""

from __future__ import annotations

import pytest

from app.services.chat import followup as fu
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.test_evoo_retry_2026_11_22 import ByQuery, _cp, md

# ── 의도 시험 세트: (말, 기대 의도) — None 은 평소 경로(새 검색·다른 경로)여야 하는 말 ─────────
INTENTS = [
    ("싼 순으로", {"kind": "sort", "by": "price"}),
    ("가격 낮은 순으로", {"kind": "sort", "by": "price"}),
    ("가격순으로 보여줘", {"kind": "sort", "by": "price"}),
    ("저렴한 순서로", {"kind": "sort", "by": "price"}),
    ("더 싼 거", {"kind": "sort", "by": "price"}),
    ("더 싼 거 없어?", {"kind": "sort", "by": "price"}),
    ("더 저렴한 거 있어요?", {"kind": "sort", "by": "price"}),
    ("싼 거부터", {"kind": "sort", "by": "price"}),
    ("100g당 싼 순", {"kind": "sort", "by": "per100g"}),
    ("100g당 가격 낮은 순으로 보여줘", {"kind": "sort", "by": "per100g"}),
    ("그램당 순서로", {"kind": "sort", "by": "per100g"}),
    ("로켓배송만", {"kind": "filter", "field": "rocket"}),
    ("로켓배송만 보여줘", {"kind": "filter", "field": "rocket"}),
    ("로켓으로", {"kind": "filter", "field": "rocket"}),
    ("로켓프레시만", {"kind": "filter", "field": "rocket"}),
    ("무료배송만", {"kind": "filter", "field": "free_shipping"}),
    ("무료배송 상품만 보여줘", {"kind": "filter", "field": "free_shipping"}),
    ("수입산 빼고", {"kind": "exclude", "word": "수입산"}),
    ("냉동은 빼고", {"kind": "exclude", "word": "냉동"}),
    ("해표 말고", {"kind": "exclude", "word": "해표"}),
    ("포마스 제외하고", {"kind": "exclude", "word": "포마스"}),
    ("2kg으로", {"kind": "size", "value": "2kg"}),
    ("1kg짜리", {"kind": "size", "value": "1kg"}),
    ("500g으로 찾아줘", {"kind": "size", "value": "500g"}),
    ("1L짜리 있어?", {"kind": "size", "value": "1L"}),
    ("3킬로", {"kind": "size", "value": "3kg"}),
    ("10개짜리", {"kind": "count", "value": "10개"}),
    ("2팩으로", {"kind": "count", "value": "2팩"}),
    ("선물용으로", {"kind": "gift"}),
    ("선물세트로 보여줘", {"kind": "gift"}),
    ("더 찾아보기", {"kind": "more"}),
    ("더 찾아봐", {"kind": "more"}),
    ("다른 상품 더 있어?", {"kind": "more"}),
    ("다른 거 더 보여줘", {"kind": "more"}),
    ("더 보여줘", {"kind": "more"}),
    ("처음 조건으로", {"kind": "reset"}),
    ("처음으로", {"kind": "reset"}),
    ("원래대로", {"kind": "reset"}),
    ("추천순으로", {"kind": "reset"}),
    # 평소 경로여야 하는 말 (품목·질문이 들어감)
    ("사과 2kg", None),
    ("올리브유 싼 거", None),
    ("싼 올리브유 추천해줘", None),
    ("로켓배송 되는 사과 추천", None),
    ("고기 말고 생선 추천해줘", None),
    ("선물용 한우 세트 추천", None),
    ("3만원 이하", None),
    ("고마워", None),
    ("엑스트라버진", None),
    ("국산은요?", None),
    ("올리브유 보관법", None),
    ("이거 빼고", None),
]


@pytest.mark.parametrize("text,want", INTENTS)
def test_intent_set(text, want):
    assert fu.parse(text) == want


def test_research_text():
    assert fu.research_text("size", "사과 1kg", "2kg") == "사과 2kg"
    assert fu.research_text("count", "올리브유 2개", "4개") == "올리브유 4개"
    assert fu.research_text("gift", "한우") == "한우 선물세트"
    assert fu.research_text("gift", "한우 선물세트") == "한우 선물세트"


OLIVE = [
    _cp("해표 압착 올리브유 500ml", 6900, 1) | {"is_rocket": True},
    _cp("살부루아 올리브유 1L", 19900, 2),
    _cp("커클랜드 엑스트라버진 올리브유 3L", 71980, 3) | {"is_rocket": True},
    _cp("올리타리아 엑스트라 버진 올리브유 1L", 15900, 4),
    _cp("피에트로코리첼리 올리브유 500ml", 11500, 5),
    _cp("데체코 올리브유 1L", 17900, 6),
]


def chat(sqlite_db, table):
    shop = ByQuery(table)
    return ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str)), shop


def lists(res):
    return [b["data"] for b in res["blocks"] if b["type"] == "product_list"]


def chips(res):
    return [i for b in res["blocks"] if b["type"] == "chips" for i in b["data"]["items"]]


def test_shopping_answer_offers_followup_chips(sqlite_db):
    svc, _ = chat(sqlite_db, {"올리브유": OLIVE})
    res = svc.handle(None, message="올리브유")
    assert "가격 낮은 순으로" in chips(res) and "더 찾아보기" in chips(res)   # 바꿔 쓸 말 '올리브오일'이 남음


def test_sort_view_uses_shown_candidates_without_new_search(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    first = svc.handle(None, message="올리브유")
    n = len(shop.calls)
    res = svc.handle(first["session_id"], message="싼 순으로")
    assert res["stage"] == "shopping_followup" and len(shop.calls) == n
    view = lists(res)[0]
    assert view["title"] == "가격 낮은 순 보기 · 추천순 아님" and "추천 순서가 아니에요" in view["note"]
    prices = [c.get("total") or c["price"] for c in view["items"]]
    assert prices == sorted(prices)
    assert all(c["go"].startswith(f"/go/{first['session_id']}/k/") for c in view["items"])
    assert "처음 조건으로" in chips(res)
    assert any(b["data"].get("affiliate") for b in res["blocks"][:2])      # 제휴 고지가 상품 목록보다 앞


def test_exclude_and_reset(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="해표 빼고")
    titles = [c["title"] for c in lists(res)[0]["items"]]
    assert titles and not any("해표" in t for t in titles)
    n = len(shop.calls)
    back = svc.handle(first["session_id"], message="처음 조건으로")
    assert len(shop.calls) == n and "처음 조건으로 돌아왔어요" in md(back)
    shown = [c["title"] for d in lists(back) for c in d["items"]]
    assert "해표 압착 올리브유 500ml" in shown


def test_filter_with_no_match_says_so(sqlite_db):
    svc, _ = chat(sqlite_db, {"올리브유": OLIVE})
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="무료배송만")
    assert "없어요" in md(res) or lists(res)


def test_size_change_searches_again_and_reset_returns_to_origin(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE, "올리브유 1L": OLIVE[1:2] + OLIVE[3:4] + OLIVE[5:6]})
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="1L짜리로")
    assert shop.calls[-1].startswith("올리브유 1L") or "올리브유 1L" in shop.calls
    assert "조건을 **1L**(으)로 바꿔 **올리브유 1L** 로 다시 찾았어요" in md(res)
    assert "처음 조건으로" in chips(res)
    back = svc.handle(first["session_id"], message="처음 조건으로")
    assert "**올리브유** 후보" in md(back)


def test_more_uses_unused_synonym(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE, "올리브오일": [_cp("코스트코 올리브오일 2L", 29900, 9)]})
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="더 찾아보기")
    assert shop.calls[-1] == "올리브오일"
    more = lists(res)[0]
    assert more["title"] == "다른 말로 더 찾은 상품 1개" and "추천 순서가 아니고" in more["note"]
    again = svc.handle(first["session_id"], message="더 찾아보기")
    assert "더 찾아볼 다른 말이 없어요" in md(again)


def test_research_cap_per_session(sqlite_db, monkeypatch):
    monkeypatch.setenv("CHAT_FOLLOWUP_SEARCH_MAX", "1")
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    first = svc.handle(None, message="올리브유")
    svc.handle(first["session_id"], message="2kg으로")
    n = len(shop.calls)
    res = svc.handle(first["session_id"], message="선물용으로")
    assert len(shop.calls) == n and "다시 찾는 횟수(1번)를 다 썼어요" in md(res)


def test_no_hijack_without_previous_shopping(sqlite_db):
    svc, shop = chat(sqlite_db, {"싼 순으로": []})
    res = svc.handle(None, message="싼 순으로")
    assert res["stage"] != "shopping_followup"


def test_new_product_sentence_still_searches(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE, "사과 2kg": [_cp("부사 사과 2kg", 19900, 20)]})
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="사과 2kg")
    assert res["stage"] == "shopping"
