from decimal import Decimal
from unittest.mock import patch

import app.ui.product_card_renderer as renderer


class FakeStreamlit:
    def __init__(self):
        self.markdowns = []
        self.captions = []

    def markdown(self, text, **kwargs):
        self.markdowns.append(text)

    def caption(self, text):
        self.captions.append(text)


def _cross_border_payload():
    return {
        "candidate_ref": "candidate:first",
        "candidate_position": 1,
        "landed_cost": 78.0,
        "estimate_disclosure": {
            "total": Decimal("108420"),
            "currency": "KRW",
            "aggregation_state": "aggregated",
            "aggregation_quality": "estimated",
            "aggregation_reason": (
                "estimated landed cost"
            ),
            "temporal_state": "evaluable",
            "temporal_reason": (
                "currency evidence is fresh"
            ),
            "fx_base_currency": "USD",
            "fx_quote_currency": "KRW",
            "fx_rate": Decimal("1390"),
            "fx_retrieved_at": (
                "2026-08-24T07:00:00Z"
            ),
            "fx_effective_at": (
                "2026-08-24T06:55:00Z"
            ),
        },
    }


def test_renders_customer_facing_cross_border_estimate_disclosure():
    fake_st = FakeStreamlit()

    item = {
        "cross_border": _cross_border_payload(),
    }

    with patch.object(
        renderer,
        "st",
        fake_st,
    ):
        renderer.render_cross_border_estimate_disclosure(
            item
        )

    assert fake_st.markdowns == [
        "**예상 최종도착비용 108,420원**"
    ]

    assert fake_st.captions == [
        "환율 1,390KRW/USD 기준",
        (
            "해외결제 카드 수수료는 카드사 및 "
            "결제수단에 따라 추가될 수 있습니다."
        ),
        (
            "실제 결제 시 환율·카드 수수료·상품가격 등의 "
            "변동으로 최종 결제금액이 달라질 수 있습니다."
        ),
    ]


def test_standard_product_renders_no_cross_border_disclosure():
    fake_st = FakeStreamlit()

    with patch.object(
        renderer,
        "st",
        fake_st,
    ):
        renderer.render_cross_border_estimate_disclosure(
            {
                "price": 10000,
            }
        )

    assert fake_st.markdowns == []
    assert fake_st.captions == []


def test_internal_cross_border_states_are_not_rendered():
    fake_st = FakeStreamlit()

    cross_border = _cross_border_payload()

    with patch.object(
        renderer,
        "st",
        fake_st,
    ):
        renderer.render_cross_border_estimate_disclosure(
            {
                "cross_border": cross_border,
            }
        )

    rendered = " ".join(
        fake_st.markdowns
        + fake_st.captions
    )

    for forbidden in (
        "aggregation_state",
        "aggregation_quality",
        "temporal_state",
        "aggregated",
        "estimated",
        "evaluable",
        "estimated landed cost",
        "currency evidence is fresh",
    ):
        assert forbidden not in rendered


def test_non_krw_amount_is_preserved_without_ui_conversion():
    fake_st = FakeStreamlit()

    cross_border = _cross_border_payload()

    cross_border["estimate_disclosure"]["total"] = (
        Decimal("78.00")
    )
    cross_border["estimate_disclosure"]["currency"] = (
        "USD"
    )

    with patch.object(
        renderer,
        "st",
        fake_st,
    ):
        renderer.render_cross_border_estimate_disclosure(
            {
                "cross_border": cross_border,
            }
        )

    assert fake_st.markdowns == [
        "**예상 최종도착비용 78.00 USD**"
    ]

    assert fake_st.captions[0] == (
        "환율 1,390KRW/USD 기준"
    )

    rendered = " ".join(
        fake_st.markdowns
        + fake_st.captions
    )

    assert "108,420원" not in rendered
    assert "%" not in rendered


def test_missing_authoritative_disclosure_renders_nothing():
    fake_st = FakeStreamlit()

    with patch.object(
        renderer,
        "st",
        fake_st,
    ):
        renderer.render_cross_border_estimate_disclosure(
            {
                "cross_border": {
                    "landed_cost": {
                        "amount": 108420,
                        "currency": "KRW",
                    }
                }
            }
        )

    assert fake_st.markdowns == []
    assert fake_st.captions == []
