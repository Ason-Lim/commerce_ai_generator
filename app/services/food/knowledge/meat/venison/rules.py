from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.meat.venison.parser_models import (
    VenisonParseResult,
)


def apply_venison_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, float],
    parse_result: VenisonParseResult,
) -> tuple[list[str], list[str]]:
    """
    사슴고기 분석 결과를 기반으로 추천 이유와 경고를 생성한다.

    Rules는 설명과 경고만 생성하며,
    attributes, scores 또는 parse_result를 변경하지 않는다.
    """
    if not isinstance(attributes, Mapping):
        raise TypeError(
            "attributes must be a Mapping"
        )

    if not isinstance(scores, Mapping):
        raise TypeError(
            "scores must be a Mapping"
        )

    if not isinstance(
        parse_result,
        VenisonParseResult,
    ):
        raise TypeError(
            "parse_result must be VenisonParseResult"
        )

    reasons: list[str] = []
    warnings: list[str] = list(
        parse_result.warnings
    )

    country = attributes.get("country")
    venison_type = attributes.get(
        "venison_type"
    )
    breed = attributes.get("breed")
    cut = attributes.get("cut")

    if venison_type:
        reasons.append(
            f"사슴고기 유형은 {venison_type}입니다."
        )

        type_description = attributes.get(
            "venison_type_description"
        )

        if type_description:
            reasons.append(
                str(type_description)
            )

    if breed:
        reasons.append(
            f"사슴 품종 또는 종은 {breed}입니다."
        )

        breed_description = attributes.get(
            "breed_description"
        )

        if breed_description:
            reasons.append(
                str(breed_description)
            )

    if country:
        reasons.append(
            f"원산지는 {country}입니다."
        )
    elif not any(
        "원산지" in warning
        for warning in warnings
    ):
        warnings.append(
            "원산지 정보가 확인되지 않았습니다."
        )

    if cut:
        reasons.append(
            f"{cut} 부위 상품입니다."
        )

        cut_description = attributes.get(
            "cut_description"
        )

        if cut_description:
            reasons.append(
                str(cut_description)
            )

    cooking_methods = (
        attributes.get(
            "cut_cooking_methods"
        )
        or []
    )

    if cooking_methods:
        method_text = ", ".join(
            str(method).strip()
            for method in cooking_methods
            if str(method).strip()
        )

        if method_text:
            reasons.append(
                "Registry 기준 권장 조리 방식은 "
                f"{method_text}입니다."
            )

    typical_uses = (
        attributes.get(
            "venison_type_typical_uses"
        )
        or []
    )

    if typical_uses:
        use_text = ", ".join(
            str(use).strip()
            for use in typical_uses
            if str(use).strip()
        )

        if use_text:
            reasons.append(
                "Registry 기준 대표 활용 방식은 "
                f"{use_text}입니다."
            )

    flavor_intensity = attributes.get(
        "venison_type_flavor_intensity"
    )

    if flavor_intensity == "mild":
        reasons.append(
            "사슴고기 유형 기준 풍미가 비교적 "
            "순한 편입니다."
        )
    elif flavor_intensity == "medium":
        reasons.append(
            "사슴고기 유형 기준 적당한 풍미를 "
            "기대할 수 있습니다."
        )
    elif flavor_intensity == "strong":
        reasons.append(
            "사슴고기 유형 기준 풍미가 진한 "
            "편입니다."
        )

    tenderness_level = attributes.get(
        "venison_type_tenderness_level"
    )

    if tenderness_level == "high":
        reasons.append(
            "사슴고기 유형 기준 부드러운 육질을 "
            "기대할 수 있습니다."
        )
    elif tenderness_level == "low":
        warnings.append(
            "사슴고기 유형 기준 육질이 단단할 수 있어 "
            "장시간 조리가 적합할 수 있습니다."
        )

    if scores.get(
        "venison_type",
        0.0,
    ) >= 85.0:
        reasons.append(
            "사슴고기 유형 Registry 기준 평가가 "
            "높은 유형입니다."
        )

    if scores.get(
        "breed",
        0.0,
    ) >= 85.0:
        reasons.append(
            "품종 Registry 기준 평가가 "
            "높은 품종 또는 종입니다."
        )

    if scores.get(
        "cut",
        0.0,
    ) >= 85.0:
        reasons.append(
            "Registry 기준 상품성이 높은 "
            "부위입니다."
        )

    if scores.get(
        "tenderness",
        0.0,
    ) >= 85.0:
        reasons.append(
            "품종과 부위 기준 부드러운 식감을 "
            "기대할 수 있습니다."
        )

    if scores.get(
        "flavor",
        0.0,
    ) >= 85.0:
        reasons.append(
            "품종과 부위 기준 풍미 평가가 "
            "높은 상품입니다."
        )

    if scores.get(
        "rarity",
        0.0,
    ) >= 80.0:
        reasons.append(
            "품종 Registry 기준 희소성이 "
            "높은 상품입니다."
        )

    if (
        attributes.get(
            "venison_type_premium"
        )
        or attributes.get(
            "breed_premium"
        )
        or attributes.get(
            "cut_premium"
        )
    ):
        reasons.append(
            "Registry에서 프리미엄 속성이 "
            "확인되었습니다."
        )

    storage_type = attributes.get(
        "storage_type"
    )

    if storage_type:
        reasons.append(
            f"보관 상태는 {storage_type}입니다."
        )

    certifications = (
        attributes.get("certifications")
        or []
    )

    if certifications:
        certification_text = ", ".join(
            str(certification).strip()
            for certification in certifications
            if str(certification).strip()
        )

        if certification_text:
            reasons.append(
                "표시된 인증 정보는 "
                f"{certification_text}입니다."
            )

    bone_status = attributes.get(
        "bone_status"
    )

    if bone_status:
        reasons.append(
            f"뼈 상태 표시는 {bone_status}입니다."
        )

    skin_status = attributes.get(
        "skin_status"
    )

    if skin_status:
        reasons.append(
            f"껍질 상태 표시는 {skin_status}입니다."
        )

    if not parse_result.is_complete:
        warnings.append(
            "사슴고기 유형, 품종, 부위 정보가 "
            "모두 확인되지 않았습니다."
        )

    if scores.get(
        "knowledge",
        0.0,
    ) <= 0.0:
        warnings.append(
            "사슴고기 Registry 기반 평가 점수를 "
            "계산할 수 없습니다."
        )

    return (
        deduplicate_strings(reasons),
        deduplicate_strings(warnings),
    )


def deduplicate_strings(
    values: list[str],
) -> list[str]:
    """
    빈 문자열과 중복 문자열을 제거한다.

    최초 등장 순서는 유지한다.
    """
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(value).strip()

        if (
            not normalized
            or normalized in seen
        ):
            continue

        seen.add(normalized)
        result.append(normalized)

    return result


__all__ = [
    "apply_venison_rules",
    "deduplicate_strings",
]
