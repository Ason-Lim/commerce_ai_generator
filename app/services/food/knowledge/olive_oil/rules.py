from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.services.food.knowledge.olive_oil.parser_models import (
    OliveOilParseResult,
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


def apply_olive_oil_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
    parse_result: OliveOilParseResult,
) -> tuple[list[str], list[str]]:
    """
    Olive Oil Attributes와 Scores를 바탕으로
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
        OliveOilParseResult,
    ):
        raise TypeError(
            "parse_result must be OliveOilParseResult"
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
        warnings=warnings,
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
    parse_result: OliveOilParseResult,
    reasons: list[str],
    warnings: list[str],
) -> None:
    olive_oil_type = _optional_text(
        attributes.get("olive_oil_type")
    )
    variety = _optional_text(
        attributes.get("variety")
    )
    origin = _optional_text(
        attributes.get("origin")
    )
    country = _optional_text(
        attributes.get("country")
    )
    processing = _optional_text(
        attributes.get("processing")
    )
    grade = _optional_text(
        attributes.get("grade")
    )

    if parse_result.is_complete:
        reasons.append(
            "올리브오일 종류, 품종, 원산지, "
            "가공 방식, 등급 정보가 모두 확인되었습니다."
        )
    elif parse_result.is_usable:
        reasons.append(
            "Olive Oil 분석에 활용할 수 있는 "
            "핵심 정보가 확인되었습니다."
        )
    else:
        warnings.append(
            "Olive Oil 도메인 분석에 필요한 정보가 "
            "충분하지 않습니다."
        )

    if olive_oil_type:
        reasons.append(
            f"올리브오일 종류는 {olive_oil_type}입니다."
        )
    else:
        warnings.append(
            "올리브오일 종류 정보가 확인되지 않았습니다."
        )

    if variety:
        reasons.append(
            f"올리브 품종은 {variety}입니다."
        )
    else:
        warnings.append(
            "올리브 품종 정보가 확인되지 않았습니다."
        )

    resolved_origin = country or origin

    if resolved_origin:
        reasons.append(
            f"원산지는 {resolved_origin}입니다."
        )
    else:
        warnings.append(
            "올리브오일 원산지 정보가 확인되지 않았습니다."
        )

    if processing:
        reasons.append(
            f"가공 방식은 {processing}입니다."
        )
    else:
        warnings.append(
            "올리브오일 가공 방식 정보가 "
            "확인되지 않았습니다."
        )

    if grade:
        reasons.append(
            f"올리브오일 등급은 {grade}입니다."
        )
    else:
        warnings.append(
            "올리브오일 등급 정보가 확인되지 않았습니다."
        )


def _apply_product_information_rules(
    *,
    attributes: Mapping[str, Any],
    reasons: list[str],
) -> None:
    volume = _optional_text(
        attributes.get("volume")
    )
    packaging_type = _optional_text(
        attributes.get("packaging_type")
    )
    country_code = _optional_text(
        attributes.get("country_code")
    )

    certifications = deduplicate_strings(
        attributes.get("certifications")
        or []
    )

    organic = attributes.get("organic")

    if volume:
        reasons.append(
            f"표시 용량은 {volume}입니다."
        )

    if packaging_type:
        reasons.append(
            f"포장 형태는 {packaging_type}입니다."
        )

    if country_code:
        reasons.append(
            f"원산지 국가 코드는 {country_code}입니다."
        )

    if certifications:
        reasons.append(
            "표시된 인증 정보는 "
            f"{', '.join(certifications)}입니다."
        )

    if organic is True:
        reasons.append(
            "유기농 상품으로 표시되어 있습니다."
        )
    elif organic is False:
        reasons.append(
            "일반 재배 상품으로 표시되어 있습니다."
        )


def _apply_registry_rules(
    *,
    attributes: Mapping[str, Any],
    reasons: list[str],
    warnings: list[str],
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
        "processing_cold_extracted"
    ) is True:
        reasons.append(
            "저온 추출 또는 냉압착 가공 특성이 "
            "확인되었습니다."
        )

    if attributes.get(
        "processing_mechanical_only"
    ) is True:
        reasons.append(
            "기계적 추출 방식이 확인되었습니다."
        )

    if attributes.get(
        "processing_refined"
    ) is True:
        reasons.append(
            "정제 가공 특성이 확인되었습니다."
        )

    if attributes.get(
        "grade_virgin"
    ) is True:
        reasons.append(
            "버진 등급 특성이 확인되었습니다."
        )

    if attributes.get(
        "grade_refined"
    ) is True:
        reasons.append(
            "정제 등급 특성이 확인되었습니다."
        )

    if attributes.get(
        "grade_pomace"
    ) is True:
        reasons.append(
            "포마스 등급 특성이 확인되었습니다."
        )

    grade = _optional_text(
        attributes.get("grade")
    )

    if grade == "extra_virgin":
        reasons.append(
            "엑스트라 버진 등급의 올리브오일입니다."
        )

    if (
        attributes.get("processing_refined")
        is True
        and attributes.get("grade_virgin")
        is True
    ):
        warnings.append(
            "정제 가공 표시와 버진 등급 표시가 "
            "동시에 존재하여 확인이 필요합니다."
        )

    if (
        attributes.get("grade_pomace")
        is True
        and attributes.get(
            "processing_cold_extracted"
        )
        is True
    ):
        warnings.append(
            "포마스 등급과 냉압착 가공 표시가 "
            "동시에 존재하여 확인이 필요합니다."
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
            "Olive Oil 품질 평가가 매우 우수합니다."
        )
    elif quality_score >= 80.0:
        reasons.append(
            "Olive Oil 품질 평가가 우수합니다."
        )
    elif 0.0 < quality_score < 60.0:
        warnings.append(
            "Olive Oil 품질 평가 점수가 낮습니다."
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
            "Olive Oil Knowledge 평가가 "
            "매우 높은 수준입니다."
        )
    elif knowledge_score >= 80.0:
        reasons.append(
            "Olive Oil Knowledge 평가가 "
            "높은 수준입니다."
        )
    elif knowledge_score > 0.0:
        reasons.append(
            "Olive Oil Knowledge 평가가 "
            "확인되었습니다."
        )
    else:
        warnings.append(
            "Olive Oil Registry 기반 평가 점수를 "
            "계산할 수 없습니다."
        )


def _apply_data_consistency_rules(
    *,
    attributes: Mapping[str, Any],
    warnings: list[str],
) -> None:
    country_code = attributes.get(
        "country_code"
    )

    if country_code is not None:
        normalized_code = str(
            country_code
        ).strip()

        if (
            normalized_code
            and (
                len(normalized_code) != 2
                or not normalized_code.isalpha()
            )
        ):
            warnings.append(
                "원산지 국가 코드가 ISO 2자리 "
                "형식이 아닙니다."
            )

    grade_score = attributes.get(
        "grade_score"
    )

    if grade_score is not None:
        try:
            value = float(grade_score)
        except (TypeError, ValueError):
            warnings.append(
                "등급 Registry 점수가 숫자 형식이 아닙니다."
            )
        else:
            if value < 0.0 or value > 100.0:
                warnings.append(
                    "등급 Registry 점수가 허용 범위를 "
                    "벗어났습니다."
                )


def _premium_fields(
    attributes: Mapping[str, Any],
) -> list[str]:
    premium_keys = {
        "olive_oil_type_premium": (
            "olive_oil_type"
        ),
        "variety_premium": "variety",
        "origin_premium": "origin",
        "processing_premium": "processing",
        "grade_premium": "grade",
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
    "apply_olive_oil_rules",
    "deduplicate_strings",
]
