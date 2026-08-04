from __future__ import annotations

import pytest

from app.services.food.knowledge.wine.parser import (
    WineParser,
)
from app.services.food.knowledge.wine.scoring import (
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_wine_final_score,
    calculate_wine_knowledge_score,
    calculate_wine_price_score,
    calculate_wine_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


def test_safe_float() -> None:
    assert safe_float("12.5") == 12.5
    assert safe_float(None) == 0.0
    assert safe_float("invalid", 3.0) == 3.0


@pytest.mark.parametrize(
    (
        "value",
        "expected",
    ),
    [
        (-10, 0.0),
        (0, 0.0),
        (50, 50.0),
        (100, 100.0),
        (120, 100.0),
        ("85.5", 85.5),
    ],
)
def test_clamp_score(
    value: object,
    expected: float,
) -> None:
    assert clamp_score(value) == expected


def test_calculate_available_average() -> None:
    assert (
        calculate_available_average(
            80,
            90,
            0,
            None,
        )
        == 85.0
    )

    assert (
        calculate_available_average(
            0,
            None,
        )
        == 0.0
    )


def test_calculate_available_weighted_score() -> None:
    result = calculate_available_weighted_score(
        scores={
            "a": 80,
            "b": 100,
            "c": 0,
        },
        weights={
            "a": 0.25,
            "b": 0.75,
            "c": 1.0,
        },
    )

    assert result == 95.0


def test_calculate_available_weighted_score_rejects_invalid_input() -> None:
    with pytest.raises(TypeError):
        calculate_available_weighted_score(
            scores=[],  # type: ignore[arg-type]
            weights={},
        )

    with pytest.raises(TypeError):
        calculate_available_weighted_score(
            scores={},
            weights=[],  # type: ignore[arg-type]
        )


def test_extract_registry_scores() -> None:
    parse_result = WineParser().parse(
        "보르도 카베르네 소비뇽 "
        "레드 와인 드라이 풀 바디 높은 산도"
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["wine_type"] == 85.0
    assert scores["grape"] == 90.0
    assert scores["region"] == 92.0
    assert scores["sweetness"] == 85.0
    assert scores["body"] == 88.0
    assert scores["acidity"] == 87.0


def test_extract_registry_scores_for_empty_result() -> None:
    parse_result = WineParser().parse(
        "등록되지 않은 상품"
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores == {
        "wine_type": 0.0,
        "grape": 0.0,
        "region": 0.0,
        "sweetness": 0.0,
        "body": 0.0,
        "acidity": 0.0,
    }


def test_calculate_wine_knowledge_score() -> None:
    score = calculate_wine_knowledge_score(
        wine_type_score=85,
        grape_score=90,
        region_score=92,
        sweetness_score=85,
        body_score=88,
        acidity_score=87,
    )

    assert 0.0 <= score <= 100.0
    assert score == 88.5


def test_calculate_wine_knowledge_score_renormalizes_missing_values() -> None:
    score = calculate_wine_knowledge_score(
        grape_score=90,
        region_score=80,
    )

    expected = round(
        (
            (90 * 0.20)
            + (80 * 0.25)
        )
        / (0.20 + 0.25),
        2,
    )

    assert score == expected


def test_calculate_wine_price_score() -> None:
    assert (
        calculate_wine_price_score(
            {
                "price_score": 77.5,
            }
        )
        == 77.5
    )

    assert (
        calculate_wine_price_score({})
        == 0.0
    )


def test_calculate_wine_scores() -> None:
    product = {
        "product_name": (
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인 드라이 풀 바디 "
            "높은 산도 13.5%"
        ),
        "producer": "Example Winery",
        "country": "France",
        "certifications": ["AOC"],
        "volume": "750ml",
        "price_score": 75,
    }

    parse_result = WineParser().parse_product(
        product
    )

    scores = calculate_wine_scores(
        product=product,
        parse_result=parse_result,
    )

    assert set(scores) == {
        "quality",
        "price",
        "trust",
        "knowledge",
        "wine_type",
        "grape",
        "region",
        "sweetness",
        "body",
        "acidity",
    }

    assert scores["price"] == 75.0
    assert scores["knowledge"] == 88.5
    assert 0.0 <= scores["quality"] <= 100.0
    assert 0.0 <= scores["trust"] <= 100.0


def test_calculate_wine_scores_without_registry_match() -> None:
    product = {
        "product_name": (
            "등록되지 않은 임의의 상품"
        ),
    }

    parse_result = WineParser().parse_product(
        product
    )

    scores = calculate_wine_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["knowledge"] == 0.0
    assert scores["quality"] == 0.0
    assert scores["trust"] == 0.0
    assert scores["price"] == 0.0


def test_calculate_wine_final_score() -> None:
    score = calculate_wine_final_score(
        {
            "quality": 90,
            "price": 70,
            "trust": 80,
            "knowledge": 88,
        }
    )

    assert score == 85.1


def test_calculate_wine_final_score_ignores_missing_scores() -> None:
    score = calculate_wine_final_score(
        {
            "quality": 90,
            "knowledge": 80,
        }
    )

    expected = round(
        (
            (90 * 0.25)
            + (80 * 0.45)
        )
        / (0.25 + 0.45),
        2,
    )

    assert score == expected


def test_wine_scoring_is_deterministic() -> None:
    product = {
        "product_name": (
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인 드라이"
        ),
        "price_score": 70,
    }

    parse_result = WineParser().parse_product(
        product
    )

    first = calculate_wine_scores(
        product=product,
        parse_result=parse_result,
    )
    second = calculate_wine_scores(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
    assert (
        calculate_wine_final_score(first)
        == calculate_wine_final_score(second)
    )


def test_wine_scoring_rejects_invalid_inputs() -> None:
    parse_result = WineParser().parse(
        "보르도 레드 와인"
    )

    with pytest.raises(TypeError):
        calculate_wine_scores(
            product="invalid",  # type: ignore[arg-type]
            parse_result=parse_result,
        )

    with pytest.raises(TypeError):
        calculate_wine_scores(
            product={},
            parse_result=None,  # type: ignore[arg-type]
        )
