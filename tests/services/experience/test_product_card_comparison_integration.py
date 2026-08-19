from unittest.mock import patch

import app.ui.product_card_renderer as renderer


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.warnings = []

    def warning(self, message):
        self.warnings.append(message)


def _item(
    name: str,
    *,
    price: int = 10000,
) -> dict:
    return {
        "product_name": name,
        "platform": "naver",
        "seller_name": "테스트몰",
        "price": price,
        "weight_text": "1kg",
    }


def _run_sync(
    fake_st,
    *,
    key,
    selected,
    item,
    display=None,
):
    fake_st.session_state[key] = selected

    with patch.object(
        renderer,
        "st",
        fake_st,
    ):
        renderer.sync_compare_selection(
            checkbox_key=key,
            compare_identity="unused-by-delegation",
            item=item,
            display=display or {},
        )


def test_selected_item_persists_to_compare_items():
    fake_st = FakeStreamlit()

    _run_sync(
        fake_st,
        key="compare_a",
        selected=True,
        item=_item("사과"),
    )

    items = fake_st.session_state[
        "compare_items"
    ]

    assert len(items) == 1
    assert items[0]["product_name"] == "사과"


def test_duplicate_selection_remains_stable():
    fake_st = FakeStreamlit()

    _run_sync(
        fake_st,
        key="compare_a",
        selected=True,
        item=_item("사과"),
    )

    first = list(
        fake_st.session_state["compare_items"]
    )

    _run_sync(
        fake_st,
        key="compare_a",
        selected=True,
        item=_item("사과"),
    )

    assert (
        fake_st.session_state["compare_items"]
        == first
    )


def test_deselection_removes_matching_item():
    fake_st = FakeStreamlit()

    _run_sync(
        fake_st,
        key="compare_a",
        selected=True,
        item=_item("사과"),
    )

    _run_sync(
        fake_st,
        key="compare_a",
        selected=False,
        item=_item("사과"),
    )

    assert (
        fake_st.session_state["compare_items"]
        == []
    )


def test_third_item_is_accepted():
    fake_st = FakeStreamlit()

    for index, name in enumerate(
        ("사과", "배", "복숭아"),
        start=1,
    ):
        _run_sync(
            fake_st,
            key=f"compare_{index}",
            selected=True,
            item=_item(
                name,
                price=10000 + index,
            ),
        )

    assert len(
        fake_st.session_state["compare_items"]
    ) == 3

    assert fake_st.warnings == []


def test_fourth_item_rolls_back_checkbox():
    fake_st = FakeStreamlit()

    for index, name in enumerate(
        ("사과", "배", "복숭아"),
        start=1,
    ):
        _run_sync(
            fake_st,
            key=f"compare_{index}",
            selected=True,
            item=_item(
                name,
                price=10000 + index,
            ),
        )

    _run_sync(
        fake_st,
        key="compare_4",
        selected=True,
        item=_item(
            "포도",
            price=14000,
        ),
    )

    assert len(
        fake_st.session_state["compare_items"]
    ) == 3

    assert (
        fake_st.session_state["compare_4"]
        is False
    )

    assert fake_st.warnings == [
        "상품 비교는 최대 3개까지 선택할 수 있습니다."
    ]


def test_transition_result_controls_persisted_state():
    fake_st = FakeStreamlit()

    fake_result = type(
        "Result",
        (),
        {
            "items": (
                {
                    "product_name": "경계 테스트",
                },
            ),
            "limit_reached": False,
        },
    )()

    with (
        patch.object(
            renderer,
            "st",
            fake_st,
        ),
        patch.object(
            renderer,
            "transition_comparison_selection",
            return_value=fake_result,
        ) as transition,
    ):
        fake_st.session_state[
            "compare_test"
        ] = True

        renderer.sync_compare_selection(
            checkbox_key="compare_test",
            compare_identity="legacy-id",
            item=_item("사과"),
            display={},
        )

    transition.assert_called_once()

    assert fake_st.session_state[
        "compare_items"
    ] == [
        {
            "product_name": "경계 테스트",
        }
    ]
