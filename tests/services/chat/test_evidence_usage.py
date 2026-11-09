"""근거 값의 용도별 판정 (2026-11-03 p29) — policies.decide_usage."""
from __future__ import annotations

import itertools

import pytest

from app.domain.commerce import policies
from app.domain.commerce.models import Evidence
from app.domain.commerce.requests import SearchRequest
from app.services.commerce.search import search_products
from tests.services.chat.conftest import FakeShopping

METHODS = ["api", "public_api", "title_parse", "partner_feed", "registry", "html", "ocr", "unknown"]
STATUSES = ["verified", "unverified", "conflict", "missing"]


def verdicts(ev, **kw):
    return {d.use: d.verdict for d in policies.decide_usage(ev, **kw)}


def test_every_value_gets_exactly_one_decision_per_use():
    for m, s, f in itertools.product(METHODS, STATUSES, (False, True)):
        ds = policies.decide_usage(Evidence(field="x", method=m, status=s, usable_for_score=f))
        assert [d.use for d in ds] == list(policies.USES)
        assert all(d.reason for d in ds)
        assert all((d.label is not None) == (d.verdict == "allow_labelled") for d in ds)


def test_score_decision_is_the_same_rule_as_score_usable():
    for m, s, f in itertools.product(METHODS, STATUSES, (False, True)):
        ev = Evidence(field="x", method=m, status=s, usable_for_score=f)
        assert policies.usable(ev, "score") == policies.score_usable(ev)
        allowed = f and s == "verified" and m not in ("html", "ocr", "unknown")
        assert policies.score_usable(ev) is allowed, (m, s, f)


@pytest.mark.parametrize("method", ["html", "ocr", "unknown"])
def test_page_ocr_and_unknown_never_reach_score_even_verified_with_flag(method):
    ev = Evidence(field="weight_g", method=method, status="verified", usable_for_score=True)
    assert verdicts(ev)["score"] == "block"


@pytest.mark.parametrize("method", ["html", "ocr"])
def test_unverified_page_or_ocr_values_are_held_for_display_filter_and_compare(method):
    v = verdicts(Evidence(field="weight_g", method=method))
    assert v == {"display": "hold", "filter": "hold", "price_compare": "hold", "score": "block"}
    v = verdicts(Evidence(field="weight_g", method=method, status="verified"))
    assert v == {"display": "allow_labelled", "filter": "allow_labelled", "price_compare": "allow_labelled",
                 "score": "block"}


def test_conflict_is_held_and_missing_blocked_and_score_is_never_hold():
    for m, s, f in itertools.product(METHODS, STATUSES, (False, True)):
        assert verdicts(Evidence(field="x", method=m, status=s, usable_for_score=f))["score"] in ("allow", "block")
    conflict = verdicts(Evidence(field="x", method="api", status="conflict", usable_for_score=True))
    assert conflict == {"display": "hold", "filter": "hold", "price_compare": "hold", "score": "block"}
    assert set(verdicts(Evidence(field="x", method="api", status="missing")).values()) == {"block"}


def test_existing_behaviour_is_recorded_not_changed():
    # 상품명 중량 → 100g당 비교(explain.choose 가성비)는 지금도 쓰인다: 표기를 붙여 허용, 거르기·점수는 아님
    title = verdicts(Evidence(field="weight_g", method="title_parse"))
    assert title == {"display": "allow_labelled", "filter": "hold", "price_compare": "allow_labelled", "score": "block"}
    # 평점·후기(출처 미확인): 기존 배지 표시만, 거르기·비교·점수 불가
    rating = verdicts(Evidence(field="rating", method="unknown"))
    assert rating == {"display": "allow_labelled", "filter": "block", "price_compare": "block", "score": "block"}
    # 쇼핑커넥트 등록부 가격: 견주지 않음 (별도 목록)
    assert verdicts(Evidence(field="price", method="registry"))["price_compare"] == "block"


def test_partner_price_compare_follows_the_permission_record():
    ev = Evidence(field="price", method="partner_feed")
    assert verdicts(ev)["price_compare"] == "block"
    assert verdicts(ev, partner_compare_allowed=True)["price_compare"] == "allow_labelled"


ITEMS = [
    {"product_name": "국산 삼겹살 500g", "price": 9000, "product_url": "https://www.coupang.com/vp/products/1",
     "platform_name": "쿠팡", "is_coupang": True, "is_rocket": True},
    {"product_name": "국산 삼겹살 1kg", "price": 23000, "product_url": "https://www.coupang.com/vp/products/2",
     "platform_name": "쿠팡", "is_coupang": True},
    {"product_name": "국산 삼겹살 2kg", "price": 42000, "product_url": "https://www.coupang.com/vp/products/3",
     "platform_name": "naver"},
]


def test_search_items_carry_decisions_and_policy_version():
    res = search_products(SearchRequest(text="삼겹살 추천"), shopping=FakeShopping(items=ITEMS))
    for item in res.items:
        assert item.evidence and all(e.policy_version == policies.POLICY_VERSION for e in item.evidence)
        weight = next(e for e in item.evidence if e.field == "weight_g")
        assert {d.use: d.label for d in weight.usage}["price_compare"] == "상품명 표기 기준"


def test_unknown_source_ratings_do_not_change_products_ranks_or_roles():
    """평점·후기를 붙였다 떼도 선택·순위·역할이 같다 — 출처 미확인 값이 공통 서비스 안에서 우회 반영되지 않음.
    (상위 추천 엔진 내부의 소비 여부는 이 테스트 범위 밖)"""
    rated = [dict(it, rating=r, review_count=c) for it, (r, c) in zip(ITEMS, [(4.9, 900), (3.1, 2), (4.5, 50)])]
    sig = lambda res: [(i.product.key, i.score.rank, i.score.role) for i in res.items]  # noqa: E731
    plain = search_products(SearchRequest(text="삼겹살 추천"), shopping=FakeShopping(items=ITEMS))
    with_rating = search_products(SearchRequest(text="삼겹살 추천"), shopping=FakeShopping(items=rated))
    assert sig(plain) == sig(with_rating)
    assert any(e.field == "rating" for i in with_rating.items for e in i.evidence)
