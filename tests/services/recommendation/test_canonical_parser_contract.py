from app.services.recommendation.parser import (
    parse_recommendation_query,
)


def test_plain_query_is_preserved():
    parsed = parse_recommendation_query(
        "사과"
    )

    assert parsed.raw_query == "사과"
    assert parsed.search_query == "사과"
    assert parsed.priority_hint is None
    assert parsed.gift_intent is False


def test_recommendation_noise_is_removed():
    parsed = parse_recommendation_query(
        "사과 추천해줘"
    )

    assert parsed.search_query == "사과"


def test_price_signal_is_preserved_semantically():
    parsed = parse_recommendation_query(
        "가성비 좋은 배 추천"
    )

    assert parsed.search_query == "배"
    assert parsed.priority_hint == "price"


def test_quality_signal_is_preserved_semantically():
    parsed = parse_recommendation_query(
        "고당도 품질 좋은 복숭아"
    )

    assert parsed.search_query == "복숭아"
    assert parsed.priority_hint == "quality"


def test_trust_signal_is_preserved_semantically():
    parsed = parse_recommendation_query(
        "신뢰도 높은 사과 추천"
    )

    assert parsed.search_query == "사과"
    assert parsed.priority_hint == "trust"


def test_parent_gift_intent_is_preserved():
    parsed = parse_recommendation_query(
        "부모님 선물 사과"
    )

    assert parsed.search_query == "사과"
    assert parsed.gift_target == "parents"
    assert parsed.gift_intent is True


def test_holiday_gift_intent_is_preserved():
    parsed = parse_recommendation_query(
        "명절 선물용 배"
    )

    assert parsed.search_query == "배"
    assert parsed.occasion == "holiday"
    assert parsed.gift_intent is True


def test_parents_day_is_preserved():
    parsed = parse_recommendation_query(
        "어버이날 사과 추천"
    )

    assert parsed.search_query == "사과"
    assert parsed.occasion == "parents_day"


def test_unknown_semantic_words_are_not_destroyed():
    parsed = parse_recommendation_query(
        "프리미엄 사과"
    )

    assert parsed.search_query == "프리미엄 사과"


def test_marketplace_terms_are_not_destroyed():
    parsed = parse_recommendation_query(
        "쿠팡 사과 추천"
    )

    assert parsed.search_query == "쿠팡 사과"


def test_parser_is_deterministic():
    first = parse_recommendation_query(
        "부모님 선물 사과 추천해줘"
    )

    second = parse_recommendation_query(
        "부모님 선물 사과 추천해줘"
    )

    assert first == second


def test_empty_query_is_safe():
    parsed = parse_recommendation_query(
        None
    )

    assert parsed.raw_query == ""
    assert parsed.search_query == ""
