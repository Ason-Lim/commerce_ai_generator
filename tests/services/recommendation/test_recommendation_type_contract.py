from app.services.recommendation.reason_engine import (
    classify_recommendation_type,
)


def test_recommendation_type_contract_quality() -> None:
    label, message = classify_recommendation_type(
        {},
        priority="quality",
    )

    assert label == "🍬 품질 추천"
    assert message


def test_recommendation_type_contract_price() -> None:
    label, message = classify_recommendation_type(
        {},
        priority="price",
    )

    assert label == "💰 가성비 추천"
    assert message


def test_recommendation_type_contract_trust() -> None:
    label, message = classify_recommendation_type(
        {},
        priority="trust",
    )

    assert label == "✅ 신뢰 추천"
    assert message


def test_recommendation_type_contract_exploration() -> None:
    label, message = classify_recommendation_type(
        {},
        priority="exploration",
    )

    assert label == "🧭 탐색 추천"
    assert message


def test_recommendation_type_contract_discovery() -> None:
    label, message = classify_recommendation_type(
        {},
        priority="discovery",
    )

    assert label == "💎 발견 추천"
    assert message


def test_recommendation_type_contract_revisit() -> None:
    label, message = classify_recommendation_type(
        {},
        priority="revisit",
    )

    assert label == "🛍️ 함께 보면 좋은 상품"
    assert message
