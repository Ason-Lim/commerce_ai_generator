from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.services.food.knowledge.cheese.parser_models import (
    CheeseParseResult,
)


def deduplicate_strings(
    values: Iterable[Any],
) -> list[str]:
    """
    빈 문자열을 제거하고 입력 순서를 유지하며 중복을 제거한다.
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
        result.append(normalized)

    return result


def apply_cheese_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
    parse_result: CheeseParseResult,
) -> tuple[list[str], list[str]]:
    """
    Cheese Attributes와 Scores를 바탕으로
    설명 이유와 경고를 생성한다.

    이 함수는 입력을 수정하지 않으며 Parser 또는 Scoring을
    다시 실행하지 않는다.
    """
    if not isinstance(
        attributes,
        Mapping,
    ):
        raise TypeError(
            "attributes must be a Mapping"
        )

    if not isinstance(
        scores,
        Mapping,
    ):
        raise TypeError(
            "scores must be a Mapping"
        )

    if not isinstance(
        parse_result,
        CheeseParseResult,
    ):
        raise TypeError(
            "parse_result must be CheeseParseResult"
        )

    reasons: list[str] = []
    warnings: list[str] = list(
        parse_result.warnings
    )

    cheese_type = _optional_text(
        attributes.get("cheese_type")
    )
    milk_source = _optional_text(
        attributes.get("milk_source")
    )
    origin = _optional_text(
        attributes.get("origin")
    )
    country = _optional_text(
        attributes.get("country")
    )
    texture = _optional_text(
        attributes.get("texture")
    )
    aging = _optional_text(
        attributes.get("aging")
    )
    storage_type = _optional_text(
        attributes.get("storage_type")
    )
    packaging_type = _optional_text(
        attributes.get("packaging_type")
    )
    pasteurization = _optional_text(
        attributes.get("pasteurization")
    )
    rind_type = _optional_text(
        attributes.get("rind_type")
    )

    certifications = deduplicate_strings(
        attributes.get("certifications")
        or []
    )

    typical_uses = deduplicate_strings(
        attributes.get(
            "cheese_type_typical_uses"
        )
        or []
    )

    if cheese_type:
        reasons.append(
            f"치즈 종류는 {cheese_type}입니다."
        )

    if milk_source:
        reasons.append(
            f"사용 원유는 {milk_source}입니다."
        )

    resolved_origin = country or origin

    if resolved_origin:
        reasons.append(
            f"원산지는 {resolved_origin}입니다."
        )

    if texture:
        reasons.append(
            f"치즈 질감은 {texture}입니다."
        )

    if aging:
        reasons.append(
            f"숙성 유형은 {aging}입니다."
        )

    if storage_type:
        reasons.append(
            f"보관 상태는 {storage_type}입니다."
        )

    if packaging_type:
        reasons.append(
            f"상품 형태는 {packaging_type}입니다."
        )

    if pasteurization:
        reasons.append(
            "원유 처리 표시는 "
            f"{pasteurization}입니다."
        )

    if rind_type:
        reasons.append(
            f"외피 표시는 {rind_type}입니다."
        )

    if certifications:
        reasons.append(
            "표시된 인증 정보는 "
            f"{', '.join(certifications)}입니다."
        )

    if typical_uses:
        reasons.append(
            "Registry 기준 대표 활용 방식은 "
            f"{', '.join(typical_uses)}입니다."
        )

    premium_fields = _premium_fields(
        attributes
    )

    if premium_fields:
        reasons.append(
            "Registry에서 프리미엄 속성이 "
            "확인되었습니다."
        )

    knowledge_score = _safe_score(
        scores.get("knowledge")
    )

    if knowledge_score >= 90.0:
        reasons.append(
            "Cheese Knowledge 평가가 "
            "매우 높은 수준입니다."
        )
    elif knowledge_score >= 80.0:
        reasons.append(
            "Cheese Knowledge 평가가 "
            "높은 수준입니다."
        )
    elif knowledge_score > 0.0:
        reasons.append(
            "Cheese Knowledge 평가가 "
            "확인되었습니다."
        )

    if not cheese_type:
        warnings.append(
            "치즈 종류 정보가 확인되지 않았습니다."
        )

    if not milk_source:
        warnings.append(
            "원유 종류 정보가 확인되지 않았습니다."
        )

    if not resolved_origin:
        warnings.append(
            "원산지 정보가 확인되지 않았습니다."
        )

    if not texture:
        warnings.append(
            "치즈 질감 정보가 확인되지 않았습니다."
        )

    if not aging:
        warnings.append(
            "치즈 숙성 정보가 확인되지 않았습니다."
        )

    if knowledge_score <= 0.0:
        warnings.append(
            "치즈 Registry 기반 평가 점수를 "
            "계산할 수 없습니다."
        )

    if not parse_result.is_usable:
        warnings.append(
            "치즈 도메인 분석에 필요한 정보가 "
            "충분하지 않습니다."
        )

    return (
        deduplicate_strings(reasons),
        deduplicate_strings(warnings),
    )


def _premium_fields(
    attributes: Mapping[str, Any],
) -> list[str]:
    premium_keys = {
        "cheese_type_premium": "cheese_type",
        "milk_source_premium": "milk_source",
        "origin_premium": "origin",
        "texture_premium": "texture",
        "aging_premium": "aging",
    }

    return [
        label
        for key, label in premium_keys.items()
        if bool(attributes.get(key))
    ]


def _safe_score(
    value: Any,
) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    return max(
        0.0,
        min(
            100.0,
            score,
        ),
    )


def _optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(
        value
    ).strip()

    return normalized or None


__all__ = [
    "apply_cheese_rules",
    "deduplicate_strings",
]
