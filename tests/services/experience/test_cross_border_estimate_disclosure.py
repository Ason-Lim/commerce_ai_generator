from copy import deepcopy
from decimal import Decimal

from app.services.experience.cross_border_estimate_disclosure import (
    build_cross_border_estimate_disclosure,
)


def _sealed_payload():
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


def test_builds_presentation_from_sealed_disclosure_shape():
    result = build_cross_border_estimate_disclosure(
        _sealed_payload()
    )

    assert result == {
        "title": "예상 최종도착비용 108,420원",
        "exchange_rate_text": (
            "환율 1,390KRW/USD 기준"
        ),
        "notices": [
            (
                "해외결제 카드 수수료는 카드사 및 결제수단에 따라 "
                "추가될 수 있습니다."
            ),
            (
                "실제 결제 시 환율·카드 수수료·상품가격 등의 변동으로 "
                "최종 결제금액이 달라질 수 있습니다."
            ),
        ],
        "aggregation_state": "aggregated",
        "aggregation_quality": "estimated",
        "temporal_state": "evaluable",
    }


def test_uses_estimate_disclosure_as_authoritative_amount():
    payload = _sealed_payload()

    payload["landed_cost"] = 1.0
    payload["estimate_disclosure"]["total"] = (
        Decimal("108420")
    )

    result = build_cross_border_estimate_disclosure(
        payload
    )

    assert result is not None
    assert (
        result["title"]
        == "예상 최종도착비용 108,420원"
    )


def test_does_not_calculate_krw_from_usd_fx_evidence():
    payload = _sealed_payload()

    payload["estimate_disclosure"]["total"] = (
        Decimal("78.00")
    )
    payload["estimate_disclosure"]["currency"] = (
        "USD"
    )

    result = build_cross_border_estimate_disclosure(
        payload
    )

    assert result is not None
    assert (
        result["title"]
        == "예상 최종도착비용 78.00 USD"
    )

    assert (
        result["exchange_rate_text"]
        == "환율 1,390KRW/USD 기준"
    )

    assert "108,420원" not in result["title"]


def test_does_not_require_fx_to_present_total():
    payload = _sealed_payload()

    disclosure = payload["estimate_disclosure"]

    disclosure["fx_rate"] = None
    disclosure["fx_base_currency"] = None
    disclosure["fx_quote_currency"] = None

    result = build_cross_border_estimate_disclosure(
        payload
    )

    assert result is not None

    assert (
        result["title"]
        == "예상 최종도착비용 108,420원"
    )

    assert result["exchange_rate_text"] is None


def test_returns_none_without_estimate_disclosure():
    assert (
        build_cross_border_estimate_disclosure(None)
        is None
    )

    assert (
        build_cross_border_estimate_disclosure({})
        is None
    )

    assert (
        build_cross_border_estimate_disclosure(
            {
                "landed_cost": {
                    "amount": 108420,
                    "currency": "KRW",
                }
            }
        )
        is None
    )


def test_returns_none_without_authoritative_total():
    payload = _sealed_payload()

    payload["estimate_disclosure"]["total"] = None

    assert (
        build_cross_border_estimate_disclosure(
            payload
        )
        is None
    )


def test_does_not_calculate_card_fee():
    result = build_cross_border_estimate_disclosure(
        _sealed_payload()
    )

    assert result is not None

    assert "card_fee" not in result
    assert "payment_fee" not in result

    serialized = repr(result)

    assert "%" not in serialized


def test_does_not_mutate_authoritative_input():
    payload = _sealed_payload()
    before = deepcopy(payload)

    build_cross_border_estimate_disclosure(
        payload
    )

    assert payload == before
