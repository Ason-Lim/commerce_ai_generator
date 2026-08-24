from __future__ import annotations

from typing import Any, Mapping


def _non_empty(value: Any) -> bool:
    return value is not None and value != ""


def _format_amount(
    amount: Any,
    currency: Any,
) -> str | None:
    if not _non_empty(amount):
        return None

    if not _non_empty(currency):
        return None

    try:
        numeric_amount = float(amount)
    except (TypeError, ValueError):
        return None

    if currency == "KRW":
        return f"{numeric_amount:,.0f}원"

    return f"{numeric_amount:,.2f} {currency}"


def _format_fx_rate(
    disclosure: Mapping[str, Any],
) -> str | None:
    rate = disclosure.get("fx_rate")
    base_currency = disclosure.get("fx_base_currency")
    quote_currency = disclosure.get("fx_quote_currency")

    if not (
        _non_empty(rate)
        and _non_empty(base_currency)
        and _non_empty(quote_currency)
    ):
        return None

    try:
        numeric_rate = float(rate)
    except (TypeError, ValueError):
        return None

    if quote_currency == "KRW":
        rate_text = f"{numeric_rate:,.0f}"
    else:
        rate_text = (
            f"{numeric_rate:,.4f}"
            .rstrip("0")
            .rstrip(".")
        )

    return (
        f"환율 {rate_text}"
        f"{quote_currency}/{base_currency} 기준"
    )


def build_cross_border_estimate_disclosure(
    cross_border: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Render already-established Cross-Border estimate evidence into a
    customer-facing presentation model.

    Presentation-only authority.

    This function MUST NOT:
    - calculate landed cost;
    - convert currency;
    - calculate or fetch FX;
    - calculate card/payment fees;
    - infer missing volatile facts;
    - mutate the authoritative input.
    """

    if not isinstance(cross_border, Mapping):
        return None

    disclosure = cross_border.get("estimate_disclosure")

    if not isinstance(disclosure, Mapping):
        return None

    total = disclosure.get("total")
    currency = disclosure.get("currency")

    amount_text = _format_amount(
        total,
        currency,
    )

    if amount_text is None:
        return None

    exchange_rate_text = _format_fx_rate(
        disclosure
    )

    notices = [
        (
            "해외결제 카드 수수료는 카드사 및 결제수단에 따라 "
            "추가될 수 있습니다."
        ),
        (
            "실제 결제 시 환율·카드 수수료·상품가격 등의 변동으로 "
            "최종 결제금액이 달라질 수 있습니다."
        ),
    ]

    return {
        "title": (
            f"예상 최종도착비용 {amount_text}"
        ),
        "exchange_rate_text": exchange_rate_text,
        "notices": notices,
        "aggregation_state": disclosure.get(
            "aggregation_state"
        ),
        "aggregation_quality": disclosure.get(
            "aggregation_quality"
        ),
        "temporal_state": disclosure.get(
            "temporal_state"
        ),
    }
