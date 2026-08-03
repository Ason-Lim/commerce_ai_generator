from __future__ import annotations

from typing import Iterable

from app.ui.html_utils import safe_html


def _normalize_chips(
    chips: Iterable | None,
    *,
    limit: int | None = None,
) -> list[str]:
    """
    빈 값과 중복을 제거하고 표시 가능한 칩 문자열로 정리합니다.
    """
    normalized = []
    seen = set()

    for chip in chips or []:
        text = str(
            chip or ""
        ).strip()

        if not text:
            continue

        if text in seen:
            continue

        seen.add(text)
        normalized.append(text)

        if (
            limit is not None
            and len(normalized) >= limit
        ):
            break

    return normalized


def render_chip_row(
    st,
    *,
    highlight_chips=None,
    normal_chips=None,
    compact: bool = False,
    limit: int | None = None,
):
    """
    Hero와 상품 카드가 공유하는 칩 행 렌더러입니다.

    compact=True:
        Hero용 한 줄 caption

    compact=False:
        상품 카드용 HTML 칩 행
    """
    highlight = _normalize_chips(
        highlight_chips
    )

    normal = _normalize_chips(
        normal_chips
    )

    combined = _normalize_chips(
        highlight + normal,
        limit=limit,
    )

    if not combined:
        return

    if compact:
        st.caption(
            " · ".join(combined)
        )
        return

    highlight_set = set(
        highlight
    )

    chips_html = "".join(
        (
            "<div class='highlight-chip'>"
            f"{safe_html(chip)}"
            "</div>"
            if chip in highlight_set
            else
            "<div class='normal-chip'>"
            f"{safe_html(chip)}"
            "</div>"
        )
        for chip in combined
    )

    if not chips_html:
        return

    st.html(
        "<div class='info-chip-row'>"
        f"{chips_html}"
        "</div>"
    )