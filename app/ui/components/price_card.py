from __future__ import annotations

from typing import Any


def _clean_html(
    html: Any,
) -> str:
    """
    HTML 문자열을 안전하게 정리합니다.
    """
    if html is None:
        return ""

    return "".join(
        line.strip()
        for line in str(html).splitlines()
        if line.strip()
    )


def render_price_card(
    st,
    *,
    display_price: str,
    price_meta_html: str = "",
    metric_label: str = "구매 기준가",
):
    """
    Hero와 상품 카드에서 공통으로 사용하는 가격 카드입니다.
    """

    st.metric(
        metric_label,
        display_price or "가격 확인",
    )

    cleaned_html = _clean_html(
        price_meta_html
    )

    if cleaned_html:
        st.html(
            cleaned_html
        )