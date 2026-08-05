from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.services.food.knowledge.tea.parser_models import (
    TeaParseResult,
)


def deduplicate_strings(
    values: Iterable[Any],
) -> list[str]:
    """
    빈 문자열을 제거하고 최초 등장 순서를 유지하면서
    중복 문자열을 제거한다.
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


def apply_tea_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
    parse_result: TeaParseResult,
) -> tuple[list[str], list[str]]:
    """
    Tea Attributes와 Scores를 바탕으로
    설명 이유와 경고를 생성한다.

    이 함수는 다음 작업을 수행하지 않는다.

    - 상품명 재파싱
    - Registry 재조회
    - 점수 재계산
    - Final Score 계산
    - Provider orchestration
    - attributes, scores, parse_result 수정
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
        TeaParseResult,
    ):
        raise TypeError(
            "parse_result must be TeaParseResult"
        )

    reasons: list[str] = []
    warnings: list[str] = list(
        parse_result.warnings
    )

    _apply_information_rules(
        attributes=attributes,
        parse_result=parse_result,
        reasons=reasons,
        warnings=warnings,
    )

    _apply_product_information_rules(
        attributes=attributes,
        reasons=reasons,
    )

    _apply_registry_rules(
        attributes=attributes,
        reasons=reasons,
    )

    _apply_score_rules(
        scores=scores,
        reasons=reasons,
        warnings=warnings,
    )

    _apply_data_consistency_rules(
        attributes=attributes,
        warnings=warnings,
    )

    return (
        deduplicate_strings(reasons),
        deduplicate_strings(warnings),
    )


def _apply_information_rules(
    *,
    attributes: Mapping[str, Any],
    parse_result: TeaParseResult,
    reasons: list[str],
    warnings: list[str],
) -> None:
    tea_type = _optional_text(
        attributes.get("tea_type")
    )
    origin = _optional_text(
        attributes.get("origin")
    )
    country = _optional_text(
        attributes.get("country")
    )
    variety = _optional_text(
        attributes.get("variety")
    )
    processing = _optional_text(
        attributes.get("processing")
    )
    oxidation = _optional_text(
        attributes.get("oxidation")
    )
    flavor = _optional_text(
        attributes.get("flavor")
    )

    if parse_result.is_complete:
        reasons.append(
            "차 종류, 산지, 품종, 가공 방식, "
            "산화도, 향미 정보가 모두 확인되었습니다."
        )
    elif parse_result.is_usable:
        reasons.append(
            "Tea 분석에 활용할 수 있는 "
            "핵심 정보가 확인되었습니다."
        )
    else:
        warnings.append(
            "Tea 도메인 분석에 필요한 정보가 "
            "충분하지 않습니다."
        )

    if tea_type:
        reasons.append(
            f"차 종류는 {tea_type}입니다."
        )
    else:
        warnings.append(
            "차 종류 정보가 확인되지 않았습니다."
        )

    resolved_origin = country or origin

    if resolved_origin:
        reasons.append(
            f"원산지는 {resolved_origin}입니다."
        )
    else:
        warnings.append(
            "차 원산지 정보가 확인되지 않았습니다."
        )

    if variety:
        reasons.append(
            f"차 품종은 {variety}입니다."
        )
    else:
        warnings.append(
            "차 품종 정보가 확인되지 않았습니다."
        )

    if processing:
        reasons.append(
            f"가공 방식은 {processing}입니다."
        )
    else:
        warnings.append(
            "차 가공 방식 정보가 확인되지 않았습니다."
        )

    if oxidation:
        reasons.append(
            f"산화 단계는 {oxidation}입니다."
        )
    else:
        warnings.append(
            "차 산화도 정보가 확인되지 않았습니다."
        )

    if flavor:
        reasons.append(
            f"대표 향미는 {flavor}입니다."
        )
    else:
        warnings.append(
            "차 향미 정보가 확인되지 않았습니다."
        )


def _apply_product_information_rules(
    *,
    attributes: Mapping[str, Any],
    reasons: list[str],
) -> None:
    weight = _optional_text(
        attributes.get("weight")
    )
    packaging_type = _optional_text(
        attributes.get("packaging_type")
    )
    harvest_year = _optional_text(
        attributes.get("harvest_year")
    )
    grade = _optional_text(
        attributes.get("grade")
    )
    leaf_style = _optional_text(
        attributes.get("leaf_style")
    )
    caffeine_status = _optional_text(
        attributes.get("caffeine_status")
    )

    certifications = deduplicate_strings(
        attributes.get("certifications")
        or []
    )

    flavor_notes = deduplicate_strings(
        attributes.get("flavor_notes")
        or []
    )

    if weight:
        reasons.append(
            f"표시 중량은 {weight}입니다."
        )

    if packaging_type:
        reasons.append(
            f"상품 형태는 {packaging_type}입니다."
        )

    if harvest_year:
        reasons.append(
            f"수확 연도 표시는 {harvest_year}입니다."
        )

    if grade:
        reasons.append(
            f"표시 등급은 {grade}입니다."
        )

    if leaf_style:
        reasons.append(
            f"잎 형태는 {leaf_style}입니다."
        )

    if caffeine_status == "decaf":
        reasons.append(
            "디카페인 상품으로 표시되어 있습니다."
        )
    elif caffeine_status == "regular":
        reasons.append(
            "일반 카페인 상품으로 표시되어 있습니다."
        )
    elif caffeine_status:
        reasons.append(
            "카페인 관련 표시는 "
            f"{caffeine_status}입니다."
        )

    if certifications:
        reasons.append(
            "표시된 인증 정보는 "
            f"{', '.join(certifications)}입니다."
        )

    if flavor_notes:
        reasons.append(
            "표시된 향미 노트는 "
            f"{', '.join(flavor_notes)}입니다."
        )


def _apply_registry_rules(
    *,
    attributes: Mapping[str, Any],
    reasons: list[str],
) -> None:
    premium_fields = _premium_fields(
        attributes
    )

    if premium_fields:
        reasons.append(
            "Registry에서 프리미엄 속성이 "
            "확인되었습니다."
        )

    if attributes.get(
        "processing_heat_fixation"
    ) is True:
        reasons.append(
            "열 고정 가공 특성이 확인되었습니다."
        )

    if attributes.get(
        "processing_microbial_fermentation"
    ) is True:
        reasons.append(
            "미생물 발효 가공 특성이 확인되었습니다."
        )

    if attributes.get(
        "processing_smoke_applied"
    ) is True:
        reasons.append(
            "훈연 가공 특성이 확인되었습니다."
        )

    if attributes.get(
        "oxidation_fully_oxidized"
    ) is True:
        reasons.append(
            "완전 산화된 차 특성이 확인되었습니다."
        )

    if attributes.get(
        "flavor_aroma_dominant"
    ) is True:
        reasons.append(
            "향 중심의 감각 특성이 확인되었습니다."
        )

    if attributes.get(
        "flavor_taste_dominant"
    ) is True:
        reasons.append(
            "맛 중심의 감각 특성이 확인되었습니다."
        )


def _apply_score_rules(
    *,
    scores: Mapping[str, Any],
    reasons: list[str],
    warnings: list[str],
) -> None:
    quality_score = _safe_score(
        scores.get("quality")
    )
    trust_score = _safe_score(
        scores.get("trust")
    )
    knowledge_score = _safe_score(
        scores.get("knowledge")
    )

    if quality_score >= 90.0:
        reasons.append(
            "Tea 품질 평가가 매우 우수합니다."
        )
    elif quality_score >= 80.0:
        reasons.append(
            "Tea 품질 평가가 우수합니다."
        )
    elif 0.0 < quality_score < 60.0:
        warnings.append(
            "Tea 품질 평가 점수가 낮습니다."
        )

    if trust_score >= 80.0:
        reasons.append(
            "구조화된 상품 정보의 신뢰도 평가가 "
            "충분합니다."
        )
    elif 0.0 < trust_score < 40.0:
        warnings.append(
            "상품 정보의 신뢰도 평가가 낮습니다."
        )

    if knowledge_score >= 90.0:
        reasons.append(
            "Tea Knowledge 평가가 "
            "매우 높은 수준입니다."
        )
    elif knowledge_score >= 80.0:
        reasons.append(
            "Tea Knowledge 평가가 "
            "높은 수준입니다."
        )
    elif knowledge_score > 0.0:
        reasons.append(
            "Tea Knowledge 평가가 "
            "확인되었습니다."
        )
    else:
        warnings.append(
            "Tea Registry 기반 평가 점수가 "
            "아직 설정되지 않았거나 "
            "계산할 수 없습니다."
        )


def _apply_data_consistency_rules(
    *,
    attributes: Mapping[str, Any],
    warnings: list[str],
) -> None:
    harvest_year = attributes.get(
        "harvest_year"
    )

    if harvest_year is not None:
        try:
            harvest_value = int(
                harvest_year
            )
        except (TypeError, ValueError):
            warnings.append(
                "수확 연도 값이 올바른 "
                "연도 형식이 아닙니다."
            )
        else:
            if (
                harvest_value < 1800
                or harvest_value > 2100
            ):
                warnings.append(
                    "수확 연도 값이 허용 범위를 "
                    "벗어났습니다."
                )

    oxidation_min = attributes.get(
        "oxidation_min_percent"
    )
    oxidation_max = attributes.get(
        "oxidation_max_percent"
    )

    if (
        oxidation_min is not None
        and oxidation_max is not None
    ):
        try:
            minimum = float(
                oxidation_min
            )
            maximum = float(
                oxidation_max
            )
        except (TypeError, ValueError):
            warnings.append(
                "산화도 범위 값이 숫자 형식이 아닙니다."
            )
        else:
            if (
                minimum < 0.0
                or maximum > 100.0
                or minimum > maximum
            ):
                warnings.append(
                    "산화도 범위 값이 허용 범위를 "
                    "벗어났습니다."
                )

    if (
        attributes.get(
            "processing_microbial_fermentation"
        )
        is True
        and attributes.get("oxidation")
        == "unoxidized"
    ):
        warnings.append(
            "미생물 발효 가공과 비산화 표시가 "
            "동시에 존재하여 확인이 필요합니다."
        )


def _premium_fields(
    attributes: Mapping[str, Any],
) -> list[str]:
    premium_keys = {
        "tea_type_premium": "tea_type",
        "origin_premium": "origin",
        "variety_premium": "variety",
        "processing_premium": "processing",
        "oxidation_premium": "oxidation",
        "flavor_premium": "flavor",
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

    normalized = str(value).strip()

    return normalized or None


__all__ = [
    "apply_tea_rules",
    "deduplicate_strings",
]
