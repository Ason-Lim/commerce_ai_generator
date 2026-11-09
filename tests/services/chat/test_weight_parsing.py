"""상품명 중량 해석 (2026-11-03 p32): 옵션 목록은 쓰지 않고, 명시된 곱하기만 계산한다."""
from __future__ import annotations

import pytest

from app.domain.commerce.requests import SearchRequest
from app.services.chat import explain
from app.services.chat.explain import parse_units, parse_weight
from app.services.commerce.search import search_products
from tests.services.chat.conftest import FakeShopping


@pytest.mark.parametrize("title, weight, kind, formula", [
    ("한우 등심 300g", 300, "single", None),
    ("고구마 3kg 꿀고구마 3kg", 3000, "single", None),                   # 같은 값 반복은 하나
    ("국산 삼겹살 500g x 2팩", 1000, "multiplied", "500g×2"),
    ("국산 삼겹살 500g×2팩", 1000, "multiplied", "500g×2"),
    ("귤 2.5kg X 2박스", 5000, "multiplied", "2.5kg×2"),
    ("삼겹살 500g x 2 총 1kg", 1000, "multiplied", "500g×2"),             # 곱한 값과 총량이 같으면 그 값
    ("사과 경북 청송 안동 가정용 못난이 부사 5kg 10kg", None, "ambiguous", None),
    ("사과유명한곳 사과10키로 햇 부사 선물용 5kg 3kg 충주", None, "ambiguous", None),
    ("삼겹살 500g x 2 총 1.2kg", None, "ambiguous", None),               # 곱한 값과 총량이 다르면 모름
    ("닭가슴살 100g 10팩", None, "count_unclear", None),                 # p33: 개당·전체 불명 → 쓰지 않음
    ("삼겹살 500g 1팩", 500, "single", None),                             # 1개면 그대로
    ("닭가슴살 1kg (100g x 10팩)", 1000, "multiplied", "100g×10"),       # 곱한 값과 총량이 같음
    ("우유 900ml x 2개", None, "none", None),
    ("국산 삼겹살 500g × 2.5팩", None, "multiply_unclear", None),       # p34: 소수 수량은 일부만 계산하지 않음
    ("국산 삼겹살 500g × 2팩 × 3세트", None, "multiply_unclear", None),  # p34: 여러 번 곱하기
    ("견과 25g x 30봉 x 2박스", None, "multiply_unclear", None),
    ("귤 1.5kg x 2", 3000, "multiplied", "1.5kg×2"),
])
def test_parse_weight(title, weight, kind, formula):
    got = parse_weight(title)
    assert (got["weight"], got["kind"], got["formula"]) == (weight, kind, formula)
    assert parse_units(title)[1] == weight


def it(n, title, price):
    return {"product_name": title, "price": price, "product_url": f"https://www.coupang.com/vp/products/{n}",
            "platform_name": "쿠팡", "is_coupang": True}


def test_option_list_titles_are_not_compared_by_weight():
    items = [it(1, "사과 경북 청송 가정용 부사 5kg 10kg", 25000), it(2, "부사 사과 5kg", 30000),
             it(3, "부사 사과 3kg", 21000)]
    res = search_products(SearchRequest(text="사과 추천"), shopping=FakeShopping(items=items))
    opt = next(i for i in res.items if i.product.title.endswith("5kg 10kg"))
    assert opt.product.weight_g is None and opt.offer.per100g_krw is None and opt.score.role != "value"
    ev = next(e for e in opt.evidence if e.field == "weight_g")
    assert ev.status == "conflict" and ev.raw_text == "5kg, 10kg" and "옵션 목록" in ev.source
    assert {d.use: d.verdict for d in ev.usage}["price_compare"] == "hold"
    value = next(i for i in res.items if i.score.role == "value")
    assert value.product.title == "부사 사과 5kg"                       # 100g당 600원 < 700원


def test_explicit_multiplication_uses_total_and_says_how():
    items = [it(1, "국산 삼겹살 500g x 2팩", 18000), it(2, "국산 삼겹살 1kg", 20000), it(3, "국산 삼겹살 300g", 7000)]
    res = search_products(SearchRequest(text="삼겹살 추천"), shopping=FakeShopping(items=items))
    two = next(i for i in res.items if i.product.title == "국산 삼겹살 500g x 2팩")
    assert two.product.weight_g == 1000 and two.offer.per100g_krw == 1800
    ev = next(e for e in two.evidence if e.field == "weight_g")
    assert ev.method == "title_parse" and ev.raw_text == "500g×2" and "계산" in ev.source
    assert two.score.role == "value"
    texts = [r.text for i in res.items for r in i.score.reasons]
    assert not any("500g×2" in t and "상품명 표기 기준" in t for t in texts)


def test_saved_cards_from_before_are_recomputed_with_the_new_rule():
    old = {"key": "a", "title": "사과 부사 5kg 10kg", "price": 25000, "total": 25000, "weight_g": 10000,
           "per100g": 250, "weight_source": "title"}
    # p31 에 '상품명 표기'로 저장된 카드도, 출처 기록이 없는 예전 카드도 지금 규칙으로 다시 계산
    for card in (old, {k: v for k, v in old.items() if k != "weight_source"}):
        fixed = explain.reweigh(card)
        assert fixed["weight_g"] is None and fixed["per100g"] is None and fixed["weight_source"] == "title_ambiguous"
    # p34: 상위 중량 카드도 지금 허용 조건을 다시 확인 (아래 test_saved_upstream_* 참고)


def test_count_unclear_titles_keep_per_pack_price_but_no_weight_comparison():
    items = [it(1, "닭가슴살 100g 10팩", 15000), it(2, "닭가슴살 1kg", 16000), it(3, "닭가슴살 500g", 9000)]
    res = search_products(SearchRequest(text="닭가슴살 추천"), shopping=FakeShopping(items=items))
    packs = next(i for i in res.items if i.product.title == "닭가슴살 100g 10팩")
    assert packs.product.weight_g is None and packs.offer.per100g_krw is None
    assert packs.offer.per_unit_krw == 1500                       # 개당 가격은 그대로 (100g 해석과 무관)
    ev = next(e for e in packs.evidence if e.field == "weight_g")
    assert ev.status == "conflict" and ev.raw_text == "100g, 10팩" and "총중량 불명확" in ev.source
    assert packs.score.role not in ("value", "ample")


# ── p34: 저장된 상위(DB) 중량 카드의 우회 사용 차단 (GPT 재현 1) ─────────────────────────────

def _stale_upstream():
    """설정이 켜져 있던 때 상위 중량으로 저장됐지만 행별 확인 표시가 없는 카드 + 상품명 중량 카드."""
    return [{"key": "db", "title": "국산 삼겹살 구이용", "price": 10000, "total": 10000, "weight_g": 1000, "per100g": 1000,
             "weight_source": "upstream", "role": "value", "role_label": "가성비",
             "why": [{"text": "후보 2개 중 100g당 가장 저렴해요 (1,000원/100g)", "basis": "calc"}],
             "reason": "후보 2개 중 100g당 가장 저렴해요 (1,000원/100g)", "mall": "쿠팡", "query": "삼겹살"},
            {"key": "t1", "title": "국산 삼겹살 600g", "price": 12600, "total": 12600, "weight_g": 600, "per100g": 2100,
             "weight_source": "title", "mall": "쿠팡", "query": "삼겹살"},
            {"key": "t2", "title": "국산 삼겹살 300g", "price": 7000, "total": 7000, "weight_g": 300, "per100g": 2333,
             "weight_source": "title", "mall": "쿠팡", "query": "삼겹살"}]


@pytest.mark.parametrize("flag, verified", [(None, None), ("0", True), ("1", None)])
def test_saved_upstream_weight_is_not_reused_without_current_permission(monkeypatch, flag, verified):
    from app.services.commerce.reselect import rechoose

    if flag is None:
        monkeypatch.delenv("CHAT_TRUST_UPSTREAM_WEIGHT", raising=False)
    else:
        monkeypatch.setenv("CHAT_TRUST_UPSTREAM_WEIGHT", flag)
    cards = _stale_upstream()
    if verified:
        cards[0]["weight_verified"] = True
    picked = rechoose(cards, ask="삼겹살")
    db = next(c for c in picked["picks"] + picked["others"] if c["key"] == "db")
    assert db["weight_g"] is None and db["per100g"] is None and db["role"] != "value"
    assert not any("100g당" in w["text"] for w in db.get("why") or [])
    value = next(c for c in picked["picks"] if c["role"] == "value")
    assert value["key"] == "t1"                                   # 상품명 중량끼리: 600g 2,100원 < 300g 2,333원


def test_saved_upstream_weight_is_kept_only_with_flag_and_row_verification(monkeypatch):
    monkeypatch.setenv("CHAT_TRUST_UPSTREAM_WEIGHT", "1")
    card = dict(_stale_upstream()[0], weight_verified=True)
    assert explain.reweigh(card) is card
