from copy import deepcopy

import pytest

from app.services.experience.comparison import (
    ComparisonTransitionResult,
    transition_comparison_selection,
)
from app.services.recommendation.compare_identity_engine import (
    get_compare_identity,
)


def _item(
    name: str,
    *,
    price: int = 10000,
    seller: str = "테스트몰",
) -> dict:
    return {
        "product_name": name,
        "platform": "naver",
        "seller_name": seller,
        "price": price,
        "weight_text": "1kg",
    }


def test_empty_selection_returns_empty_items():
    item = _item("사과")

    result = transition_comparison_selection(
        current_items=[],
        selected=False,
        item=item,
    )

    assert isinstance(
        result,
        ComparisonTransitionResult,
    )
    assert result.items == ()
    assert result.accepted is True
    assert result.limit_reached is False
    assert (
        result.compare_identity
        == get_compare_identity(item)
    )


def test_first_item_selection():
    item = _item("사과")

    result = transition_comparison_selection(
        current_items=[],
        selected=True,
        item=item,
    )

    assert result.accepted is True
    assert result.limit_reached is False
    assert len(result.items) == 1
    assert (
        result.items[0]["product_name"]
        == "사과"
    )


def test_multiple_item_selection():
    first = transition_comparison_selection(
        current_items=[],
        selected=True,
        item=_item("사과"),
    )

    second = transition_comparison_selection(
        current_items=first.items,
        selected=True,
        item=_item("배", price=12000),
    )

    assert len(second.items) == 2
    assert [
        item["product_name"]
        for item in second.items
    ] == [
        "사과",
        "배",
    ]


def test_duplicate_selection_is_stable():
    item = _item("사과")

    first = transition_comparison_selection(
        current_items=[],
        selected=True,
        item=item,
    )

    second = transition_comparison_selection(
        current_items=first.items,
        selected=True,
        item=item,
    )

    assert second.accepted is True
    assert second.limit_reached is False
    assert second.items == first.items


def test_third_item_is_accepted():
    current = ()

    for name in (
        "사과",
        "배",
        "복숭아",
    ):
        result = transition_comparison_selection(
            current_items=current,
            selected=True,
            item=_item(name),
        )
        current = result.items

    assert len(current) == 3
    assert result.accepted is True
    assert result.limit_reached is False


def test_fourth_item_is_rejected():
    current = ()

    for name in (
        "사과",
        "배",
        "복숭아",
    ):
        result = transition_comparison_selection(
            current_items=current,
            selected=True,
            item=_item(name),
        )
        current = result.items

    fourth = transition_comparison_selection(
        current_items=current,
        selected=True,
        item=_item("포도"),
    )

    assert fourth.accepted is False
    assert fourth.limit_reached is True
    assert len(fourth.items) == 3


def test_deselection_removes_matching_identity():
    first_item = _item("사과")
    second_item = _item(
        "배",
        price=12000,
    )

    first = transition_comparison_selection(
        current_items=[],
        selected=True,
        item=first_item,
    )

    second = transition_comparison_selection(
        current_items=first.items,
        selected=True,
        item=second_item,
    )

    result = transition_comparison_selection(
        current_items=second.items,
        selected=False,
        item=first_item,
    )

    assert len(result.items) == 1
    assert (
        result.items[0]["product_name"]
        == "배"
    )


def test_identity_is_preserved():
    item = _item("사과")

    result = transition_comparison_selection(
        current_items=[],
        selected=True,
        item=item,
    )

    assert (
        result.compare_identity
        == get_compare_identity(item)
    )


def test_snapshot_normalization_applies_display_values():
    item = _item("사과")
    display = {
        "price": 8900,
    }

    result = transition_comparison_selection(
        current_items=[],
        selected=True,
        item=item,
        display=display,
    )

    assert len(result.items) == 1
    assert (
        result.items[0]["price"]
        == 8900.0
    )


def test_input_list_is_not_mutated():
    current_items = [
        _item("사과"),
    ]
    original = deepcopy(
        current_items
    )

    transition_comparison_selection(
        current_items=current_items,
        selected=True,
        item=_item(
            "배",
            price=12000,
        ),
    )

    assert current_items == original


def test_repeated_execution_is_deterministic():
    current_items = [
        _item("사과"),
    ]
    item = _item(
        "배",
        price=12000,
    )

    first = transition_comparison_selection(
        current_items=current_items,
        selected=True,
        item=item,
    )

    second = transition_comparison_selection(
        current_items=current_items,
        selected=True,
        item=item,
    )

    assert first == second


def test_current_duplicate_items_are_normalized():
    item = _item("사과")

    result = transition_comparison_selection(
        current_items=[
            item,
            dict(item),
        ],
        selected=True,
        item=_item("배"),
    )

    assert len(result.items) == 2


def test_invalid_max_items_is_rejected():
    with pytest.raises(
        ValueError,
        match="max_items must be at least 1",
    ):
        transition_comparison_selection(
            current_items=[],
            selected=True,
            item=_item("사과"),
            max_items=0,
        )
