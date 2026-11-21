"""비식품(재배·원예용) 판별 — 식용 반례 필수 (2026-11-21 사용자 결정)."""

from __future__ import annotations

import pytest

from app.services.commerce.nonfood import is_non_food_item

NON_FOOD = [
    "천수무 씨앗 2000립",
    "청상추 모종 10개",
    "파종용 종자 무",
    "사과나무 묘목 1주",
    "씨감자 수미 5kg",
    "다육이 화분 세트",
    "텃밭 상토 50L",
    "고추 비료 2kg",
    "열무 씨앗",
    "들깨 씨앗(파종용)",
    "배추 모종 30구",
]
EDIBLE = [
    "치아씨드 1kg",
    "햄프씨드 500g",
    "볶은 해바라기씨 300g",
    "호박씨 1kg",
    "국산 참깨 1kg",
    "들깨 500g",
    "씨앗 호떡 믹스 400g",
    "토종자연산 더덕 1kg",
    "벌화분 500g",
    "아마씨 분말",
    "천수무 5kg 3~7개 내외",
    "견과류 씨앗 강정",
    "절임배추 10kg",
]


@pytest.mark.parametrize("name", NON_FOOD)
def test_growing_items_are_non_food(name):
    assert is_non_food_item(name)


@pytest.mark.parametrize("name", EDIBLE)
def test_edible_seeds_and_lookalikes_pass(name):
    assert not is_non_food_item(name)


def test_category_alone_marks_non_food():
    assert is_non_food_item("무 5kg", "가드닝 > 씨앗") and not is_non_food_item("무 5kg", "신선식품 > 채소")


def test_trend_post_products_skip_non_food():
    from app.services.trend_posts import draft
    from tests.services.trend_posts.helpers import pick

    res = {
        "items": [
            pick("천수무 5kg", "https://link.coupang.com/a/1"),
            pick("천수무 씨앗 2000립", "https://link.coupang.com/a/2"),
            pick("치아씨드 1kg", "https://link.coupang.com/a/3"),
        ]
    }
    assert [p.title for p in draft.products_from_result(res)] == ["천수무 5kg", "치아씨드 1kg"]
