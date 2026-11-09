"""추천 사유 · 예산 질문 · 관심 상품 (2026-11-01).

* 후보를 검색 순서대로 늘어놓지 않고 역할(가성비·빠른 배송·넉넉한 양·선물용)별로 고르고, 사유마다 근거 종류를 단다.
* 평점·후기·도착일은 만들지 않는다 — 판매처 확인 안내만.  판매자 문구는 사유가 아니라 '판매자 표기'로만.
* 예산은 버튼이 아니라 말로 받는다: '3만원 이하요' → 새 검색 없이 찾은 후보 안에서 다시 고른다.
* 다른 질문으로 넘어가도 지난 카드의 판매처 링크는 제 상품으로 간다 (/go/{sid}/k/{key}).
* ♡ 관심 상품은 브라우저 보관함(owner)에 남고, 같은 검색에서 담은 것끼리 비교한다.
"""
from __future__ import annotations

import uuid

from app.services.chat.budget import is_budget_answer, parse_budget, strip_budget
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping


def cp(name, price, *, rocket=None, free=None, url=None):
    return {"product_name": name, "price": price, "product_url": url or f"https://www.coupang.com/vp/{abs(hash(name))}",
            "platform_name": "쿠팡", "is_coupang": True, "is_rocket": rocket, "is_free_shipping": free,
            "recommendation_reason": "AI가 가격, 품질, 혜택 정보를 종합해 추천했습니다."}


BEEF = [
    cp("한우 1++ 등심 구이용 300g", 39000, rocket=True, free=True),
    cp("한우 등심 500g 냉장", 52000),
    cp("호주산 소고기 등심 1kg", 45000, free=True),
    cp("한우 등심 선물세트 1.2kg 보자기 포장", 129000),
    cp("미국산 척아이롤 2kg 대용량", 59000),
]


def svc(db, items):
    return ChatService(db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str))


def lists(res):
    return [b for b in res["blocks"] if b["type"] == "product_list"]


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_budget_is_read_from_words():
    assert parse_budget("3만원 이하")["max"] == 30000
    assert parse_budget("10만원대")["min"] == 100000 and parse_budget("10만원대")["max"] == 199999
    assert parse_budget("2~3만원")["min"] == 20000
    assert parse_budget("800g 3인분") is None
    assert parse_budget("예산 상관없어요")["none"]
    assert is_budget_answer("예산은 5만원 정도요") and not is_budget_answer("5만원 이하 한우 등심")
    assert strip_budget("5만원 이하 한우 등심") == "한우 등심"


def test_picks_have_roles_and_grounded_reasons(sqlite_db):
    res = svc(sqlite_db, BEEF).handle(None, message="소고기 등심 추천")
    main = lists(res)[0]["data"]["items"]
    roles = [c["role"] for c in main]
    assert roles[0] == "value" and "fast" in roles and len(main) <= 4
    value = main[0]
    assert value["title"] == "미국산 척아이롤 2kg 대용량" or value["per100g"] == min(c["per100g"] for c in main)
    for c in main:
        assert c["why"] and all(w["basis"] in {"calc", "mall", "you"} for w in c["why"])
        assert c["reason"] == c["why"][0]["text"]
        assert "AI가 가격" not in c["reason"]          # 근거 없는 일반 문구는 사유가 아니다
        assert c["check_at_mall"] is True and c["evidence"] == []
        assert c["go"].startswith(f"/go/{res['session_id']}/k/")
    fast = next(c for c in main if c["role"] == "fast")
    assert fast["title"].startswith("한우 1++") and fast["why"][0]["basis"] == "mall"
    assert "등급 표기" in fast["seller_claims"]       # 1++ 는 판매자 표기로만
    assert not any("1++" in w["text"] for c in main for w in c["why"])
    # 평점·후기를 지어내지 않는다
    assert not any(c.get("badges") for c in main)
    assert "평점·후기·도착일은 쿠팡·네이버 검색 API가 제공하지 않아요" in md(res)
    # 나머지 후보는 접어서
    assert lists(res)[1]["data"]["collapsed"] is True


def test_gift_role_only_when_the_customer_asks_for_a_gift(sqlite_db):
    plain = lists(svc(sqlite_db, BEEF).handle(None, message="소고기 등심 추천"))[0]["data"]["items"]
    gift = lists(svc(sqlite_db, BEEF).handle(None, message="부모님 선물 소고기 등심 추천"))[0]["data"]["items"]
    assert "gift" not in [c["role"] for c in plain]
    assert "gift" in [c["role"] for c in gift]


def test_budget_question_then_answer_rechecks_without_a_new_search(sqlite_db):
    shop = FakeShopping(items=BEEF)
    s = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    first = s.handle(None, message="소고기 등심 추천")
    assert "예산이 있으면 편하게 말씀해 주세요" in md(first)
    again = s.handle(first["session_id"], message="5만원 이하요")
    assert len(shop.calls) == 1                         # 다시 검색하지 않음
    assert again["stage"] == "shopping_budget"
    main = lists(again)[0]["data"]["items"]
    assert all((c["total"] or c["price"]) <= 50000 for c in main)
    assert any(w["basis"] == "you" and "5만원 이하" in w["text"] for c in main for w in c["why"])


def test_budget_in_the_first_sentence_is_not_sent_to_the_search(sqlite_db):
    shop = FakeShopping(items=BEEF)
    s = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = s.handle(None, message="5만원 이하 한우 등심")
    assert shop.calls[0][0] == "한우 등심"
    assert "예산이 있으면" not in md(res)
    assert all((c["total"] or c["price"]) <= 50000 for c in lists(res)[0]["data"]["items"])


def test_no_product_in_budget_is_said_plainly(sqlite_db):
    res = svc(sqlite_db, BEEF).handle(None, message="1만원 이하 한우 등심")
    assert "예산 1만원 이하 안에 드는 후보가 없어요" in md(res)


def test_earlier_cards_keep_their_own_link_after_a_new_question(sqlite_db):
    s = svc(sqlite_db, BEEF)
    first = s.handle(None, message="소고기 등심 추천")
    old = lists(first)[0]["data"]["items"][0]
    s.shopping = FakeShopping(items=[cp("부사 사과 5kg", 30000)])
    s.handle(first["session_id"], message="사과 추천")
    key = old["go"].rsplit("/", 1)[1]
    assert s.resolve_go_key(first["session_id"], key) == old["url"]


def test_saved_items_survive_a_new_conversation_and_compare_within_one_search(sqlite_db):
    owner = str(uuid.uuid4())
    s = svc(sqlite_db, BEEF)
    res = s.handle(None, message="소고기 등심 추천", owner=owner)
    a, b = lists(res)[0]["data"]["items"][:2]
    assert s.set_saved(owner, res["session_id"], a["key"], True)["ok"]
    out = s.set_saved(owner, res["session_id"], b["key"], True)
    assert [c["key"] for c in out["saved"]] == [b["key"], a["key"]]
    assert out["saved"][0]["go"] == f"/go/s/{owner}/{b['key']}"
    # 브라우저가 지어낸 키는 담지 않는다
    assert s.set_saved(owner, res["session_id"], "0123456789ab", True)["error"] == "unknown_item"
    # 새 대화(새 세션)에서도 남아 있고, 비교할 수 있다
    cmp = s.handle(None, message="관심 상품 비교해줘", owner=owner)
    assert cmp["stage"] == "saved_compare"
    block = lists(cmp)[0]["data"]
    assert block["title"] == "'소고기 등심' 관심 상품 2개 비교" and len(block["items"]) == 2
    assert s.resolve_saved_go(owner, a["key"]) == a["url"]
    assert [c["key"] for c in s.set_saved(owner, None, a["key"], False)["saved"]] == [b["key"]]


def test_compare_with_nothing_saved(sqlite_db):
    res = svc(sqlite_db, BEEF).handle(None, message="관심 상품 보여줘", owner=str(uuid.uuid4()))
    assert "아직 담아 둔 관심 상품이 없어요" in md(res)


def test_recent_searches_are_listed(sqlite_db):
    s = svc(sqlite_db, BEEF)
    res = s.handle(None, message="소고기 등심 추천")
    s.shopping = FakeShopping(items=[cp("부사 사과 5kg", 30000)])
    s.handle(res["session_id"], message="사과 추천")
    view = s.saved_view(None, res["session_id"])
    assert [r["query"] for r in view["recent"]] == ["사과", "소고기 등심"]
    assert view["recent"][1]["cards"][0]["go"].startswith(f"/go/{res['session_id']}/k/")


def test_ample_role_when_a_bigger_pack_exists(sqlite_db):
    items = [cp("국산 삼겹살 500g", 9000), cp("국산 삼겹살 2kg", 42000), cp("국산 삼겹살 1kg", 23000)]
    main = lists(svc(sqlite_db, items).handle(None, message="삼겹살 추천"))[0]["data"]["items"]
    assert [c["role"] for c in main][:2] == ["value", "ample"]
    assert main[1]["title"] == "국산 삼겹살 2kg" and "양이 가장 많아요" in main[1]["reason"]


def test_without_comparable_amounts_it_is_called_lowest_price_not_value(sqlite_db):
    items = [cp("휘태커스 초콜릿 선물", 12000), cp("휘태커스 초콜릿 세트", 9000)]
    main = lists(svc(sqlite_db, items).handle(None, message="휘태커스 초콜릿"))[0]["data"]["items"]
    assert main[0]["role"] == "lowest" and main[0]["role_label"] == "최저가"


# ── 2026-11-01: 쿠팡 제휴(수수료) 상품에 가점을 주지 않는다 ──────────────────────────────

def test_affiliate_flag_never_changes_which_products_are_picked_or_their_order(sqlite_db):
    """같은 상품을 제휴/비제휴로만 바꿔도 고르는 상품·순서·사유가 같아야 한다 (표시만 달라짐)."""
    def run(flag):
        items = [dict(it, is_coupang=flag, is_ad=flag) for it in BEEF]
        res = svc(sqlite_db, items).handle(None, message="소고기 등심 추천")
        return [(c["title"], c["role"], [w["text"] for w in c["why"]], c["affiliate"])
                for b in lists(res) for c in b["data"]["items"]]
    with_fee, without_fee = run(True), run(False)
    assert [x[:3] for x in with_fee] == [x[:3] for x in without_fee]
    assert all(x[3] for x in with_fee) and not any(x[3] for x in without_fee)


def test_mixed_affiliate_and_plain_products_are_ranked_by_the_numbers_only(sqlite_db):
    plain = dict(cp("국산 삼겹살 1kg", 15000), is_coupang=False, is_ad=False, platform_name="네이버")
    fee = cp("국산 삼겹살 1kg 냉장", 23000)
    main = lists(svc(sqlite_db, [fee, plain]).handle(None, message="삼겹살 추천"))[0]["data"]["items"]
    assert main[0]["title"] == "국산 삼겹살 1kg" and main[0]["affiliate"] is False


def test_legacy_platform_scores_ignore_the_affiliate_flag():
    from app.services.platform_score_engine import calculate_platform_boost, calculate_platform_scores

    base = {"platform": "coupang", "price": 10000}
    ad = dict(base, is_ad=True, product_url="https://link.coupang.com/a")
    assert calculate_platform_scores(base) == calculate_platform_scores(ad)
    assert calculate_platform_boost(base) == calculate_platform_boost(ad)


def test_a_coupang_product_is_called_fast_only_when_marked_rocket():
    from app.services.recommendation.reason_engine import build_reason_list

    def texts(item):
        out = build_reason_list(item, "ranking")
        return " ".join(r if isinstance(r, str) else str(r) for r in out)
    assert "로켓배송" not in texts({"platform_name": "쿠팡", "product_name": "사과", "price": 1000})
    assert "빠른배송이 가능해" not in texts({"platform_name": "쿠팡", "product_name": "사과", "price": 1000, "is_rocket": True})
