import pytest

from app.services.session_context import (
    SessionContext,
    calculate_session_context_boost,
)


def test_no_context_has_zero_boost() -> None:
    assert (
        calculate_session_context_boost(
            None,
            {
                "fruit_name": "apple",
                "product_name": "product-a",
            },
            "quality",
        )
        == 0
    )


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        (
            SessionContext(
                last_fruit="apple",
            ),
            2,
        ),
        (
            SessionContext(
                last_clicked_product="product-a",
            ),
            5,
        ),
        (
            SessionContext(
                last_priority="quality",
            ),
            1,
        ),
        (
            SessionContext(
                last_fruit="apple",
                last_clicked_product="product-a",
                last_priority="quality",
            ),
            8,
        ),
    ],
)
def test_session_context_boost_rules(
    context,
    expected: int,
) -> None:
    result = calculate_session_context_boost(
        context,
        {
            "fruit_name": "apple",
            "product_name": "product-a",
        },
        "quality",
    )

    assert result == expected


def test_mapping_context_is_supported() -> None:
    result = calculate_session_context_boost(
        {
            "last_fruit": "apple",
            "last_clicked_product": "product-a",
            "last_priority": "quality",
        },
        {
            "fruit_name": "apple",
            "product_name": "product-a",
        },
        "quality",
    )

    assert result == 8


def test_non_matching_context_has_zero_boost() -> None:
    result = calculate_session_context_boost(
        SessionContext(
            last_fruit="orange",
            last_clicked_product="product-b",
            last_priority="price",
        ),
        {
            "fruit_name": "apple",
            "product_name": "product-a",
        },
        "quality",
    )

    assert result == 0
