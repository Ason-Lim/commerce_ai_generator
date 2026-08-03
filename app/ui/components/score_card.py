from __future__ import annotations

from typing import Optional


def normalize_score(
    value,
) -> int:
    """
    점수를 0~100 정수로 정규화합니다.
    """
    try:
        score = int(
            float(
                value
                or 0
            )
        )
    except (TypeError, ValueError):
        score = 0

    return max(
        0,
        min(
            score,
            100,
        ),
    )


def build_score_label(
    score,
) -> tuple[str, str]:
    """
    점수에 따른 사용자용 등급과 이모지를 반환합니다.
    """
    score_pct = normalize_score(
        score
    )

    if score_pct >= 85:
        return "매우 추천", "🔥"

    if score_pct >= 70:
        return "추천", "✨"

    if score_pct >= 55:
        return "무난", "👍"

    return "비교 추천", "📌"


def render_score_card(
    st,
    *,
    score,
    metric_label: str = "AI 추천 판단",
    metric_value: Optional[str] = None,
    show_progress: bool = True,
    caption_prefix: str = "종합 추천지수",
):
    """
    Hero와 상품 카드가 공유하는 AI 점수 카드입니다.
    """
    score_pct = normalize_score(
        score
    )

    score_label, score_emoji = (
        build_score_label(
            score_pct
        )
    )

    display_value = (
        metric_value
        or score_label
    )

    st.metric(
        metric_label,
        display_value,
    )

    if show_progress:
        st.progress(
            score_pct
        )

    st.caption(
        f"{score_emoji} {score_label} · "
        f"{caption_prefix} {score_pct}점"
    )