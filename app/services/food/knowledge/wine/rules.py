from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.wine.parser_models import (
    WineParseResult,
)


def apply_wine_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
    parse_result: WineParseResult,
) -> tuple[list[str], list[str]]:
    """
    Wine Attributes와 Scores를 기반으로
    추천 이유와 경고를 생성한다.

    이 함수는 Parser 재실행, Registry 조회,
    점수 계산을 수행하지 않는다.
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
        WineParseResult,
    ):
        raise TypeError(
            "parse_result must be WineParseResult"
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

    _apply_quality_rules(
        attributes=attributes,
        scores=scores,
        reasons=reasons,
        warnings=warnings,
    )

    _apply_style_rules(
        attributes=attributes,
        reasons=reasons,
    )

    _apply_certification_rules(
        attributes=attributes,
        reasons=reasons,
    )

    _apply_data_consistency_rules(
        attributes=attributes,
        warnings=warnings,
    )

    return (
        _deduplicate_strings(reasons),
        _deduplicate_strings(warnings),
    )


def _apply_information_rules(
    *,
    attributes: Mapping[str, Any],
    parse_result: WineParseResult,
    reasons: list[str],
    warnings: list[str],
) -> None:
    if parse_result.is_complete:
        reasons.append(
            "와인 타입, 품종, 산지, 당도, 바디, "
            "산도 정보가 모두 확인되었습니다."
        )
    elif parse_result.is_usable:
        reasons.append(
            "추천에 활용할 수 있는 와인 핵심 정보가 "
            "확인되었습니다."
        )
    else:
        warnings.append(
            "추천에 필요한 와인 핵심 정보가 부족합니다."
        )

    if parse_result.vintage is not None:
        reasons.append(
            f"{parse_result.vintage} 빈티지 정보가 "
            "제공되었습니다."
        )
    else:
        warnings.append(
            "빈티지 정보가 확인되지 않았습니다."
        )

    if parse_result.alcohol_percent is not None:
        reasons.append(
            f"알코올 도수 {parse_result.alcohol_percent:g}%가 "
            "확인되었습니다."
        )
    else:
        warnings.append(
            "알코올 도수 정보가 확인되지 않았습니다."
        )

    if not attributes.get("producer"):
        warnings.append(
            "생산자 또는 와이너리 정보가 확인되지 않았습니다."
        )

    if not attributes.get("volume"):
        warnings.append(
            "상품 용량 정보가 확인되지 않았습니다."
        )


def _apply_quality_rules(
    *,
    attributes: Mapping[str, Any],
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
            "와인 품질 평가가 매우 우수합니다."
        )
    elif quality_score >= 80.0:
        reasons.append(
            "와인 품질 평가가 우수합니다."
        )
    elif 0.0 < quality_score < 60.0:
        warnings.append(
            "와인 품질 평가 점수가 낮습니다."
        )

    if trust_score >= 80.0:
        reasons.append(
            "구조화된 상품 정보와 분석 신뢰도가 "
            "충분합니다."
        )
    elif trust_score < 40.0:
        warnings.append(
            "상품 정보가 부족하여 신뢰도 평가가 낮습니다."
        )

    if knowledge_score >= 90.0:
        reasons.append(
            "품종과 산지 등 Wine Knowledge 정보가 "
            "매우 우수합니다."
        )
    elif knowledge_score >= 80.0:
        reasons.append(
            "Wine Knowledge 정보가 충분합니다."
        )
    elif knowledge_score == 0.0:
        warnings.append(
            "Wine Registry 기반 지식 점수를 "
            "계산할 수 없습니다."
        )

    if (
        attributes.get("region_premium") is True
        or attributes.get("grape_premium") is True
    ):
        reasons.append(
            "프리미엄 산지 또는 품종 정보가 확인되었습니다."
        )


def _apply_style_rules(
    *,
    attributes: Mapping[str, Any],
    reasons: list[str],
) -> None:
    if attributes.get(
        "wine_type_sparkling"
    ) is True:
        reasons.append(
            "스파클링 와인 특성이 확인되었습니다."
        )

    if attributes.get(
        "wine_type_fortified"
    ) is True:
        reasons.append(
            "주정 강화 와인 특성이 확인되었습니다."
        )

    if attributes.get("body") == "full":
        reasons.append(
            "풀 바디 와인으로 풍부한 질감이 기대됩니다."
        )

    if attributes.get("acidity") == "high":
        reasons.append(
            "높은 산도로 선명한 산미가 기대됩니다."
        )

    if attributes.get("sweetness") == "dry":
        reasons.append(
            "드라이 스타일의 와인입니다."
        )

    if attributes.get(
        "grape_aromatic"
    ) is True:
        reasons.append(
            "아로마틱 품종 특성이 확인되었습니다."
        )


def _apply_certification_rules(
    *,
    attributes: Mapping[str, Any],
    reasons: list[str],
) -> None:
    certifications = attributes.get(
        "certifications"
    )

    if isinstance(certifications, list):
        if certifications:
            reasons.append(
                "인증 또는 품질 표시 정보가 제공되었습니다."
            )

    if attributes.get("organic") is True:
        reasons.append(
            "유기농 와인 정보가 확인되었습니다."
        )

    if attributes.get("biodynamic") is True:
        reasons.append(
            "바이오다이나믹 와인 정보가 확인되었습니다."
        )


def _apply_data_consistency_rules(
    *,
    attributes: Mapping[str, Any],
    warnings: list[str],
) -> None:
    vintage = attributes.get("vintage")

    if vintage is not None:
        try:
            vintage_value = int(vintage)
        except (TypeError, ValueError):
            warnings.append(
                "빈티지 값이 올바른 연도 형식이 아닙니다."
            )
        else:
            if (
                vintage_value < 1800
                or vintage_value > 2100
            ):
                warnings.append(
                    "빈티지 값이 허용 범위를 벗어났습니다."
                )

    alcohol_percent = attributes.get(
        "alcohol_percent"
    )

    if alcohol_percent is not None:
        try:
            alcohol_value = float(
                alcohol_percent
            )
        except (TypeError, ValueError):
            warnings.append(
                "알코올 도수 값이 숫자 형식이 아닙니다."
            )
        else:
            if (
                alcohol_value < 0.0
                or alcohol_value > 100.0
            ):
                warnings.append(
                    "알코올 도수 값이 허용 범위를 벗어났습니다."
                )

    if (
        attributes.get("wine_type_sparkling")
        is True
        and attributes.get("wine_type_fortified")
        is True
    ):
        warnings.append(
            "스파클링 및 주정 강화 속성이 동시에 "
            "표시되어 확인이 필요합니다."
        )


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


def _deduplicate_strings(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(value).strip()

        if not text or text in seen:
            continue

        seen.add(text)
        result.append(text)

    return result


__all__ = [
    "apply_wine_rules",
]
