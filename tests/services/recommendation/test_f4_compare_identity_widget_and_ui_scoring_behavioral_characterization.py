from __future__ import annotations

import importlib
import builtins
from typing import List
from unittest.mock import patch

import pytest
import requests

from app.services.experience import comparison


def _item(
    name: str,
    *,
    price: int = 10_000,
    seller: str = "테스트몰",
    url: str | None = None,
) -> dict:
    item = {
        "product_name": name,
        "platform": "NAVER",
        "seller_name": seller,
        "price": price,
        "weight_text": "1kg",
    }
    if url is not None:
        item["product_url"] = url
    return item


@pytest.fixture(scope="module")
def renderer_module():
    with patch.object(builtins, "List", List, create=True):
        yield importlib.import_module("app.ui.product_card_renderer")


@pytest.fixture(scope="module")
def ui_module(renderer_module):
    def deny_network(*args, **kwargs):
        raise AssertionError("external network access is prohibited")

    with (
        patch.object(requests, "get", deny_network),
        patch.object(requests, "post", deny_network),
    ):
        yield importlib.import_module("app.ui.streamlit_app")


def test_compare_identity_normalization_and_stability_behavior():
    item = _item("  프리미엄 사과  ", seller="  테스트몰  ")

    first = comparison.transition_comparison_selection(
        current_items=[],
        selected=True,
        item=item,
    )
    second = comparison.transition_comparison_selection(
        current_items=first.items,
        selected=True,
        item=dict(item),
    )

    assert first.compare_identity == (
        "fallback::naver::테스트몰::프리미엄 사과::10000::1kg"
    )
    assert second.compare_identity == first.compare_identity
    assert second.items == first.items
    assert len(second.items) == 1


def test_compare_snapshot_shape_and_ordering_behavior():
    current = [
        _item("사과", url="https://example.test/apple"),
        _item("배", price=12_000, url="https://example.test/pear"),
    ]
    selected = _item("복숭아", price=15_000)

    result = comparison.transition_comparison_selection(
        current_items=current,
        selected=True,
        item=selected,
        display={
            "name": "복숭아 특선",
            "price": 13_500,
            "original_price": 15_000,
        },
    )

    assert [item["product_name"] for item in result.items] == [
        "사과",
        "배",
        "복숭아",
    ]
    snapshot = result.items[-1]
    assert snapshot["price"] == 13_500.0
    assert snapshot["original_price"] == 15_000.0
    assert snapshot["discount_rate"] == 10.0
    assert snapshot["price_per_100g"] == 1_350.0
    assert snapshot["_compare_identity"] == result.compare_identity
    assert current[0]["product_name"] == "사과"


def test_compare_widget_key_determinism_and_isolation_behavior(renderer_module):
    item = _item("사과", url="https://example.test/apple")

    first = renderer_module.build_compare_widget_key(
        item,
        section="main",
        generation=4,
    )
    repeated = renderer_module.build_compare_widget_key(
        dict(item),
        section="main",
        generation=4,
    )
    other_section = renderer_module.build_compare_widget_key(
        item,
        section="hero",
        generation=4,
    )
    other_generation = renderer_module.build_compare_widget_key(
        item,
        section="main",
        generation=5,
    )

    assert first == repeated
    assert first.startswith("compare_select_4_main_")
    assert len(first.rsplit("_", 1)[-1]) == 12
    assert len({first, other_section, other_generation}) == 3


def test_product_card_compare_bridge_behavior(renderer_module):
    class FakeStreamlit:
        def __init__(self):
            self.session_state = {}
            self.warnings = []

        def warning(self, message):
            self.warnings.append(message)

    fake_st = FakeStreamlit()

    with patch.object(renderer_module, "st", fake_st):
        for index, name in enumerate(("사과", "배", "복숭아"), start=1):
            key = f"compare_{index}"
            fake_st.session_state[key] = True
            renderer_module.sync_compare_selection(
                checkbox_key=key,
                compare_identity="ignored",
                item=_item(name, price=10_000 + index),
                display={},
            )

        fake_st.session_state["compare_4"] = True
        renderer_module.sync_compare_selection(
            checkbox_key="compare_4",
            compare_identity="ignored",
            item=_item("포도", price=14_000),
            display={},
        )

    assert len(fake_st.session_state["compare_items"]) == 3
    assert fake_st.session_state["compare_4"] is False
    assert fake_st.warnings == [
        "상품 비교는 최대 3개까지 선택할 수 있습니다."
    ]


def test_ui_mode_and_ai_scoring_behavior(ui_module):
    item = {
        "impression_count": 100,
        "click_count": 20,
        "ctr_pct": 10,
        "rating": 4.7,
        "review_count": 500,
        "price_per_100g": 600,
        "discount_rate": 15,
        "brix": 14,
    }
    scores = ui_module.calculate_ai_scores(
        dict(item),
        priority="trust",
    )

    first = ui_module.calculate_mode_score(
        dict(item),
        dict(scores),
        "trust",
        search_context={"market_score": 125},
    )
    repeated = ui_module.calculate_mode_score(
        dict(item),
        dict(scores),
        "trust",
        search_context={"market_score": 125},
    )

    assert isinstance(first, (int, float))
    assert repeated == first
    assert ui_module.get_v8_market_score({"market_score": 125}) == 100.0
    assert ui_module.get_v8_market_score({"trend_score": "42.5"}) == 42.5
    assert ui_module.get_v8_market_score({"latest_ratio": "invalid"}) == 0.0


def test_ui_product_identity_v8_and_compare_integration_behavior(
    ui_module,
    renderer_module,
    monkeypatch,
):
    monkeypatch.setitem(ui_module.st.session_state, "include_new_items", True)
    monkeypatch.setitem(
        ui_module.st.session_state,
        "last_search_context",
        {"market_score": 55},
    )
    monkeypatch.setattr(
        ui_module,
        "enrich_identity_v3",
        lambda item: {
            **item,
            "_identity_v3": {"identity_score": item["identity_rank"]},
        },
    )
    monkeypatch.setattr(
        ui_module,
        "enrich_item_identity",
        lambda item: {
            "is_valid": True,
            "identity_score": item["identity_rank"],
            "price_confidence": item["identity_rank"],
            "brix_confidence": item["identity_rank"],
        },
    )
    monkeypatch.setattr(ui_module, "is_mode_candidate", lambda item, mode: True)
    monkeypatch.setattr(
        ui_module,
        "calculate_ai_scores",
        lambda item, priority: {
            "trust": item["score_rank"],
            "quality": item["score_rank"],
            "price": item["score_rank"],
        },
    )

    observed_market_scores = []

    def apply_v8(item, scores, **kwargs):
        observed_market_scores.append(kwargs["market_score"])
        item["v8_final_score"] = item["score_rank"]
        return item

    monkeypatch.setattr(ui_module, "apply_recommendation_score_v8", apply_v8)

    items = [
        {
            **_item("낮은 점수", seller="판매자 A"),
            "_product_identity_key": "low",
            "identity_rank": 70,
            "score_rank": 20,
        },
        {
            **_item("높은 점수", seller="판매자 B"),
            "_product_identity_key": "high",
            "identity_rank": 90,
            "score_rank": 90,
        },
        {
            **_item("중복 판매자", seller="판매자 B"),
            "_product_identity_key": "duplicate-seller",
            "identity_rank": 95,
            "score_rank": 100,
        },
    ]

    result = ui_module.build_visible_recommendation_items(
        items,
        limit=3,
        priority="trust",
    )

    assert [item["product_name"] for item in result] == [
        "높은 점수",
        "낮은 점수",
    ]
    assert observed_market_scores == [55.0, 55.0]
    assert all("_ai_scores" in item for item in result)
    assert len(
        {
            renderer_module.get_compare_identity(item)
            for item in result
        }
    ) == 2
