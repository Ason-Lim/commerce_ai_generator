"""2026-11-09 A안 — 상품 목록 끝 비교 카드: 레시피 재료 구매뿐 아니라 일반 상품 추천에도."""
from __future__ import annotations

from app.services.chat import product_compare
from app.services.chat.service import ChatService


def card(key, title, price, rank):
    return {"key": key, "rank": rank, "title": title, "price": price, "shipping_fee": 0, "total": price,
            "affiliate": True, "affiliate_program": "쿠팡 파트너스", "url": f"https://shop.example.com/{key}",
            "role": None, "role_label": None, "why": [], "reason": ""}


def test_result_blocks_end_with_the_compare_card(sqlite_db, shopping):
    svc = ChatService(sqlite_db, shopping=shopping)
    picks = [card("a" * 12, "휘태커스 초콜릿 블록 코코넛 250g", 15800, 1),
             card("b" * 12, "휘태커스 베리 앤 비스킷 250g", 16300, 2)]
    others = [card("c" * 12, "휘태커스 초콜릿 젤리팁", 16330, 3)]
    blocks = svc._result_blocks("s" * 8, "휘태커스초콜릿", {"picks": picks, "others": others, "budget_miss": False},
                                None, 9)
    types = [b["type"] for b in blocks]
    i = types.index("compare_cta")
    assert i > max(n for n, t in enumerate(types) if t == "product_list")
    assert blocks[i]["data"] == {"label": "휘태커스초콜릿 상품 3개, 한눈에 비교하기", "sub": "총가격 · 100g당 가격",
                                 "send": "휘태커스초콜릿 상품 비교"}


def test_partner_products_are_kept_for_links_but_not_compared():
    seen = {"query": "한우", "at": "11/09 14:00", "cards": [
        card("a" * 12, "한우 등심 300g", 30000, 1), card("b" * 12, "한우 채끝 300g", 33000, 2),
        dict(card("c" * 12, "업체 한우 300g", 28000, 3), partner="미트프렌즈")]}
    data = product_compare.build("한우", seen, None, lambda c: f"/go/s/k/{c['key']}")
    assert [r["title"] for r in data["rows"]] == ["한우 등심 300g", "한우 채끝 300g"]


def test_shopping_answer_then_compare(sqlite_db, shopping):
    """맥에서 실행 (일반 상품 검색 경로는 pydantic 필요)."""
    shopping.items = [{"product_name": "휘태커스 초콜릿 블록 코코넛 250g", "price": 15800, "shipping_fee": 0,
                       "is_coupang": True, "product_url": "https://shop.example.com/1"},
                      {"product_name": "휘태커스 베리 앤 비스킷 250g", "price": 16300, "shipping_fee": 0,
                       "is_coupang": True, "product_url": "https://shop.example.com/2"}]
    svc = ChatService(sqlite_db, shopping=shopping)
    res = svc.handle(None, message="휘태커스초콜릿 추천해 줘")
    cta = next(b for b in res["blocks"] if b["type"] == "compare_cta")
    res = svc.handle(res["session_id"], message=cta["data"]["send"])
    assert res["stage"] == "product_compare"
    assert any(b["type"] == "product_compare" for b in res["blocks"])


def test_dish_chips_only_follow_a_compare_of_that_dish_ingredient(sqlite_db, shopping):
    """굴전·굴국밥 다음에 휘태커스초콜릿을 비교해도 '굴전 만드는 법'이 붙지 않는다."""
    from app.services.chat import saved as saved_mod

    svc = ChatService(sqlite_db, shopping=shopping)
    state = {"dish_purchase": {"dishes": ["굴전", "굴국밥"], "ingredient": "굴",
                               "need": {"name": "굴", "amount": "440", "unit": "g", "display": "440g", "basis": "각 2인분"}}}
    choc = [card("a" * 12, "휘태커스 초콜릿 블록 코코넛 250g", 15800, 1), card("b" * 12, "휘태커스 베리 앤 비스킷 250g", 16300, 2)]
    oyster = [card("c" * 12, "통영 생굴 1kg", 13350, 1), card("d" * 12, "통영 깐굴 500g", 9000, 2)]
    state = saved_mod.push_seen(saved_mod.push_seen(state, "굴", oyster), "휘태커스초콜릿", choc)
    chips = lambda res: [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]  # noqa: E731
    sid = "1" * 8 + "-1111-4111-8111-" + "1" * 12
    res = svc._compare_shown_turn(sid, "휘태커스초콜릿", state["seen"][-1], state, 0, False, "휘태커스초콜릿 상품 비교")
    assert chips(res) == []
    res = svc._compare_shown_turn(sid, "굴", state["seen"][0], state, 0, False, "굴 상품 비교")
    assert chips(res) == ["굴전 만드는 법", "굴국밥 만드는 법"]
