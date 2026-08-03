from __future__ import annotations

from typing import Iterable

from app.ui.html_utils import safe_html


def _normalize_reasons(
    reasons: Iterable | None,
    *,
    limit: int | None = None,
) -> list[str]:
    """빈 값과 중복을 제거한 추천 이유 목록을 반환합니다."""

    normalized = []
    seen = set()

    for reason in reasons or []:
        text = str(
            reason or ""
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


def render_reason_box(
    st,
    *,
    heading: str,
    title: str = "",
    summary: str = "",
    reasons=None,
    top_limit: int = 3,
    extra_label: str = "추가 참고",
    summary_style: str = "info",
):
    """
    Hero와 상품 카드가 공유하는 추천 이유 박스입니다.
    """

    normalized_reasons = _normalize_reasons(
        reasons
    )

    if not (
        str(title or "").strip()
        or str(summary or "").strip()
        or normalized_reasons
    ):
        return

    if heading:
        st.markdown(
            heading
        )

    if title:
        st.markdown(
            f"**{safe_html(title)}**"
        )

    if summary:
        if summary_style == "caption":
            st.caption(
                summary
            )
        else:
            st.info(
                summary
            )

    top_reasons = normalized_reasons[
        :top_limit
    ]

    extra_reasons = normalized_reasons[
        top_limit:
    ]

    for reason in top_reasons:
        st.markdown(
            f"- {safe_html(reason)}"
        )

    if extra_reasons:
        with st.expander(
            extra_label,
            expanded=False,
        ):
            for reason in extra_reasons:
                st.markdown(
                    f"- {safe_html(reason)}"
                )