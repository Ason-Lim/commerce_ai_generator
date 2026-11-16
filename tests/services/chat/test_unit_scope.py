"""개당 가격의 적용 범위 (2026-11-03 p39, GPT 검토 17:13).

옵션 목록('1kg … 2개, 500g')·소수/여러 번 곱하기·서로 다른 개수 표기는 가격이 어느 구성의 것인지 모른다
→ 중량뿐 아니라 개당 가격도 비우고, 개당 가격 기반 '가성비' 선택·설명에서도 뺀다.  상품은 계속 보인다.
'100g 10팩'·'200g, 3개'는 개수가 하나로 적혀 있어 개당 가격을 계산한다 (중량은 2026-11-12부터 곱해서 계산).
"""
from __future__ import annotations

import pytest

from app.domain.commerce.requests import SearchRequest
from app.services.chat import explain
from app.services.commerce.search import search_products, to_item
from tests.services.chat.conftest import FakeShopping

OPTION_MIX = "한돈 냉동삼겹살 1kg (구이용,바베큐용), 2개, 500g"      # 실제 MCP 응답(17:07)에서 발견


@pytest.mark.parametrize("title, clear", [
    (OPTION_MIX, False),                                    # 중량 여러 개(옵션 목록)
    ("국산 삼겹살 500g × 2.5팩", False),                     # 소수 곱하기
    ("견과 25g x 30봉 x 2박스", False),                     # 여러 번 곱하기
    ("사과 부사 2개 3개 선택", False),                       # 서로 다른 개수
    ("[꿈에그린한우] 한우 1++등급 등심 구이용 (냉장), 200g, 3개", True),   # 중량만 불명 (p33)
    ("닭가슴살 100g 10팩", True),
    ("국산 삼겹살 500g x 2팩", True),
    ("사과 10개입 10개입", True),                            # 같은 값 반복은 하나
    ("한우 등심 300g", True),
])
def test_unit_scope(title, clear):
    assert explain.unit_scope(title)["clear"] is clear


def _card(title, price, **kw):
    return dict({"key": title[:6], "title": title, "price": price, "total": price, "mall": "쿠팡"}, **kw)


def test_enrich_leaves_per_unit_empty_when_the_count_scope_is_unclear():
    card = explain.enrich(_card(OPTION_MIX, 28400), {})
    assert card["unit_count"] == 2 and card["per_unit"] is None and card["weight_g"] is None
    kept = explain.enrich(_card("[꿈에그린한우] 한우 1++등급 등심 구이용 (냉장), 200g, 3개", 73170), {})
    assert kept["per_unit"] == 24390 and kept["weight_g"] == 600     # 2026-11-12: '200g, 3개' → 600g (사용자 결정)


def it(n, title, price):
    return {"product_name": title, "price": price, "product_url": f"https://www.coupang.com/vp/products/{n}",
            "platform_name": "쿠팡", "is_coupang": True}


def test_first_search_projection_and_selection():
    items = [it(1, OPTION_MIX, 28400), it(2, "사과 부사 2개 3개 선택", 9000), it(3, "한돈 삼겹살 구이용", 12000)]
    res = search_products(SearchRequest(text="삼겹살 추천"), shopping=FakeShopping(items=items))
    mix = next(i for i in res.items if i.product.title == OPTION_MIX)
    assert mix.offer.per_unit_krw is None and mix.offer.per100g_krw is None
    ev = next(e for e in mix.evidence if e.field == "unit_count")
    assert ev.value is None and ev.status == "conflict" and "개수 적용 범위 불명확" in ev.source
    assert ev.raw_text == "1kg, 500g, 2개"
    assert {d.use: d.verdict for d in ev.usage}["price_compare"] == "hold"
    # 개당 비교 후보가 없으니 '가성비(개당)'가 아니라 '최저가'
    assert all(i.score.role != "value" for i in res.items)
    assert not any("개당" in r.text for i in res.items for r in i.score.reasons)
    assert len(res.items) >= 1 and any(i.product.title == OPTION_MIX for i in res.items)   # 상품은 계속 보인다


def test_per_unit_value_still_works_when_counts_are_clear():
    picked = explain.choose([explain.enrich(_card("귤 10개입", 10000), {}), explain.enrich(_card("귤 20개입", 16000), {}),
                             explain.enrich(_card(OPTION_MIX, 2000), {})], ask="귤")
    value = next(p for p in picked["picks"] if p["role"] == "value")
    assert value["title"] == "귤 20개입" and "개당 800원" in value["why"][0]["text"]
    assert all(OPTION_MIX not in w["text"] for p in picked["picks"] for w in p["why"])


def test_saved_and_reselected_cards_drop_old_per_unit():
    from app.services.commerce.reselect import compare_saved, rechoose

    stale = [_card(OPTION_MIX, 2000, unit_count=2, per_unit=1000, query="삼겹살"),     # 예전 규칙으로 저장된 값
             _card("한돈 삼겹살 2개입", 9000, unit_count=2, per_unit=4500, query="삼겹살"),
             _card("한돈 삼겹살 3개입", 15000, unit_count=3, per_unit=5000, query="삼겹살")]
    for picked in (rechoose(stale, ask="삼겹살"), compare_saved(stale)["groups"][0]["picked"]):
        cards = picked["picks"] + picked["others"]
        mix = next(c for c in cards if c["title"] == OPTION_MIX)
        assert mix["per_unit"] is None
        value = next(c for c in picked["picks"] if c["role"] == "value")
        assert value["title"] == "한돈 삼겹살 2개입"                  # 1,000원/개 옛 값이 이기지 않는다
        assert to_item(mix, "others").offer.per_unit_krw is None
