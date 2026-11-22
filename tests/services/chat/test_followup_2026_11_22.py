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
    assert view["title"] == f"가격 낮은 순 · {len(view['items'])}개 · 추천순 아님" and "추천 순서가 아니에요" in view["note"]
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
    assert more["title"] == "다른 검색어로 찾은 추가 후보 1개" and "함께 정렬하지 않았어요" in more["note"]
    again = svc.handle(first["session_id"], message="더 찾아보기")
    assert "더 찾아볼 다른 검색어가 없어요" in md(again)


def test_research_cap_per_session(sqlite_db, monkeypatch):
    monkeypatch.setenv("CHAT_FOLLOWUP_SEARCH_MAX", "1")
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    first = svc.handle(None, message="올리브유")
    svc.handle(first["session_id"], message="2kg으로")
    n = len(shop.calls)
    res = svc.handle(first["session_id"], message="선물용으로")
    assert len(shop.calls) == n and "다시 찾는 한도(다시 찾기 요청 1번)를 다 썼어요" in md(res)


def test_no_hijack_without_previous_shopping(sqlite_db):
    svc, shop = chat(sqlite_db, {"싼 순으로": []})
    res = svc.handle(None, message="싼 순으로")
    assert res["stage"] != "shopping_followup"


def test_new_product_sentence_still_searches(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE, "사과 2kg": [_cp("부사 사과 2kg", 19900, 20)]})
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="사과 2kg")
    assert res["stage"] == "shopping"


# ── 2026-11-22 외부 검토 반영 ─────────────────────────────────────────────

def test_call_meter_counts_real_calls_and_dedupes_within_turn(sqlite_db):
    # '엑스트라버진 올리브유' → 0건 → '엑스트라 버진 올리브유' 0건 → '올리브유' (3번) — 같은 차례 같은 말은 한 번만
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    res = svc.handle(None, message="엑스트라버진 올리브유")
    assert res["meta"]["coupang_calls"] == len(shop.calls) == len(set(shop.calls))
    assert res["meta"]["session_coupang_calls"] == len(shop.calls)


def test_api_call_cap_blocks_followup_research(sqlite_db, monkeypatch):
    monkeypatch.setenv("CHAT_FOLLOWUP_API_MAX", "1")
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    first = svc.handle(None, message="올리브유")          # 1번 호출 → 세션 상한 도달
    n = len(shop.calls)
    res = svc.handle(first["session_id"], message="2kg으로")
    assert len(shop.calls) == n and "쿠팡 호출 1회" in md(res)
    assert lists(svc.handle(first["session_id"], message="싼 순으로"))    # 보기 바꾸기는 계속 됨


def test_meta_is_not_sent_to_customers():
    from app.api.chat_routes import public

    assert "meta" not in public({"session_id": "s", "stage": "shopping", "blocks": [], "meta": {"coupang_calls": 1}})


def test_conditions_stack_and_carry_into_research(sqlite_db):
    one_l = [OLIVE[1], _cp("해표 올리브유 1L", 12900, 11) | {"is_rocket": True},
             _cp("코스트코 올리브유 1L", 14900, 12) | {"is_rocket": True}]
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE, "올리브유 1L": one_l})
    sid = svc.handle(None, message="올리브유")["session_id"]
    r1 = svc.handle(sid, message="로켓배송만")
    assert all(c.get("rocket") for c in lists(r1)[0]["items"])
    r2 = svc.handle(sid, message="해표 빼고")              # 쌓임: 로켓배송만 + 해표 빼고
    assert "로켓배송 표시 상품만 · '해표' 빼고" in md(r2)
    assert [c["title"] for c in lists(r2)[0]["items"]] == ["커클랜드 엑스트라버진 올리브유 3L"]
    r3 = svc.handle(sid, message="1L짜리로")               # 다시 찾아도 조건 이어 적용
    assert "앞서 고른 조건(로켓배송 표시 상품만 · '해표' 빼고)도 이어서 적용해요" in md(r3)
    carried = [d for d in lists(r3) if (d.get("title") or "").startswith("로켓배송 표시 상품만")]
    assert carried and [c["title"] for c in carried[0]["items"]] == ["코스트코 올리브유 1L"]
    back = svc.handle(sid, message="처음 조건으로")
    assert "한 단계 되돌리기가 아니라 **처음 찾은 후보**" in md(back) and "풀린 조건" in md(back)
    assert "1L" in md(back)                                # 풀린 조건에 양 바꾸기도 적힘
    r5 = svc.handle(sid, message="싼 순으로")              # 처음으로 돌아간 뒤에는 조건이 비어 있음
    assert "지금 조건: 가격 낮은 순" in md(r5)


def test_failed_research_keeps_previous_candidates(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    sid = svc.handle(None, message="올리브유")["session_id"]
    svc.handle(sid, message="로켓배송만")
    res = svc.handle(sid, message="3kg으로")              # '올리브유 3kg' 결과 없음
    assert "앞서 보여 드린 '올리브유' 후보와 조건은 그대로예요" in md(res)
    after = svc.handle(sid, message="싼 순으로")
    assert "로켓배송 표시 상품만 · 가격 낮은 순" in md(after)
    assert all(c.get("rocket") for c in lists(after)[0]["items"])


def test_grade_unlabelled_goes_to_separate_section(sqlite_db):
    from tests.services.chat.test_evoo_retry_2026_11_22 import BASE

    svc, shop = chat(sqlite_db, {"엑스트라버진 올리브유": [BASE[0], BASE[2], BASE[4]]})
    res = svc.handle(None, message="엑스트라버진 올리브유")
    titles_by = {d.get("title"): [c["title"] for c in d["items"]] for d in lists(res)}
    main = titles_by[None]
    assert main == [BASE[2]["product_name"]]               # 표기 상품만 추천 후보
    unk = next(v for k, v in titles_by.items() if k and k.startswith("등급 확인 필요"))
    assert set(unk) == {BASE[0]["product_name"], BASE[4]["product_name"]}


def test_only_unlabelled_shows_grade_section_not_picks(sqlite_db):
    from tests.services.chat.test_evoo_retry_2026_11_22 import BASE

    svc, shop = chat(sqlite_db, {"엑스트라버진 올리브유": [BASE[0], BASE[4]]})
    res = svc.handle(None, message="엑스트라버진 올리브유")
    assert "**엑스트라버진** 표기가 있는 '엑스트라버진 올리브유' 상품은 찾지 못했어요" in md(res)
    assert [d["title"] for d in lists(res)] == ["등급 확인 필요 2개 · 엑스트라버진 표기 없음"]
