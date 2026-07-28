from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.meat.beef.parser_models import (
    BeefParseResult,
)


def apply_beef_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, float],
    parse_result: BeefParseResult,
) -> tuple[
    list[str],
    list[str],
]:
    """
    쇠고기 분석 결과를 기반으로 추천 이유와 경고를 생성한다.

    Args:
        attributes:
            Provider에서 구성한 쇠고기 속성 정보.

        scores:
            scoring.py에서 계산한 상품 및 Registry 점수.

        parse_result:
            BeefParser의 원본 분석 결과.

    Returns:
        중복이 제거된 reasons, warnings 튜플.
    """
    reasons: list[str] = []
    warnings: list[str] = list(
        parse_result.warnings
    )

    country = attributes.get(
        "country"
    )
    breed = attributes.get(
        "breed"
    )
    grade = attributes.get(
        "grade"
    )
    cut = attributes.get(
        "cut"
    )

    if breed:
        reasons.append(
            f"품종은 {breed}입니다."
        )

    if grade:
        grade_system = attributes.get(
            "grade_system"
        )

        if grade_system:
            reasons.append(
                f"{grade_system} 기준 "
                f"{grade} 등급입니다."
            )
        else:
            reasons.append(
                f"표시 등급은 "
                f"{grade}입니다."
            )

    if country:
        reasons.append(
            f"원산지는 "
            f"{country}입니다."
        )
    elif not any(
        "원산지" in warning
        for warning in warnings
    ):
        warnings.append(
            "원산지 정보가 "
            "확인되지 않았습니다."
        )

    if cut:
        reasons.append(
            f"{cut} 부위 상품입니다."
        )

    cooking_methods = (
        attributes.get(
            "cut_cooking_methods"
        )
        or []
    )

    if cooking_methods:
        method_text = ", ".join(
            str(method)
            for method in cooking_methods
        )

        reasons.append(
            "Registry 기준 권장 조리 방식은 "
            f"{method_text}입니다."
        )

    if (
        scores.get(
            "grade",
            0.0,
        )
        >= 85.0
    ):
        reasons.append(
            "등급 기준 품질 기대치가 "
            "높은 상품입니다."
        )

    if (
        scores.get(
            "cut",
            0.0,
        )
        >= 90.0
    ):
        reasons.append(
            "상품성이 높은 부위로 "
            "분류됩니다."
        )

    if (
        scores.get(
            "tenderness",
            0.0,
        )
        >= 85.0
    ):
        reasons.append(
            "부드러운 식감을 기대할 수 "
            "있는 부위입니다."
        )

    if (
        attributes.get(
            "breed_premium"
        )
        or attributes.get(
            "grade_premium"
        )
        or attributes.get(
            "cut_premium"
        )
    ):
        reasons.append(
            "Registry에서 프리미엄 속성이 "
            "확인되었습니다."
        )

    return (
        deduplicate_strings(
            reasons
        ),
        deduplicate_strings(
            warnings
        ),
    )


def deduplicate_strings(
    values: list[str],
) -> list[str]:
    """
    문자열 목록에서 빈 값과 중복 값을 제거한다.

    최초 등장 순서는 유지한다.
    """
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(
            value
        ).strip()

        if (
            not normalized
            or normalized in seen
        ):
            continue

        seen.add(normalized)
        result.append(
            normalized
        )

    return result


__all__ = [
    "apply_beef_rules",
    "deduplicate_strings",
]