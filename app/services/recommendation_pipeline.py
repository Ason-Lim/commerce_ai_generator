import os
from dotenv import load_dotenv
from sqlalchemy import text

from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
)
from app.services.recommendation.cross_border_production_provider_composition import (
    compose_production_recommendation_provider,
)
from app.services.recommendation.claim_source import brix_claim_source
import re

load_dotenv(".env")


def resolve_canonical_priority(
    priority: str,
) -> tuple[RecommendationPriority, bool]:
    """
    Resolve the legacy/API priority vocabulary at the compatibility
    boundary without extending the canonical priority contract.
    """
    raw = priority or "ranking"
    adaptive = raw.endswith("_adaptive")
    base = raw.removesuffix("_adaptive")

    aliases = {
        "ranking": RecommendationPriority.MIX,
        "balanced": RecommendationPriority.MIX,
        "mix": RecommendationPriority.MIX,
        "value": RecommendationPriority.PRICE,
        "price": RecommendationPriority.PRICE,
        "quality": RecommendationPriority.QUALITY,
        "trust": RecommendationPriority.TRUST,
        "exploration": RecommendationPriority.EXPLORATION,
        "discovery": RecommendationPriority.DISCOVERY,
        "revisit": RecommendationPriority.REVISIT,
    }

    return (
        aliases.get(
            base,
            RecommendationPriority.MIX,
        ),
        adaptive,
    )


def build_canonical_context(
    *,
    q: str,
    priority: str,
    session_id: str | None,
    limit: int,
) -> RecommendationContext:
    canonical_priority, adaptive = (
        resolve_canonical_priority(
            priority
        )
    )

    return RecommendationContext(
        query=clean_query(q),
        priority=canonical_priority,
        session_id=session_id,
        limit=limit,
        adaptive=adaptive,
        metadata={
            "requested_query": q,
            "requested_priority": priority,
        },
    )


def clean_query(q: str) -> str:
    q = q or ""

    remove_words = [
        "신뢰도 높은",
        "가성비 좋은",
        "고당도 품질 좋은",
        "추천해줘",
        "추천",
        "부모님",
        "선물용",
        "선물",
        "명절",
        "어버이날",
    ]

    for word in remove_words:
        q = q.replace(word, "")

    return q.strip()


def normalize_priority(priority: str) -> tuple[str, bool]:
    priority = priority or "ranking"
    use_adaptive = priority.endswith("_adaptive")
    base_priority = priority.replace("_adaptive", "")

    priority_to_mode = {
        "value": "price",
        "price": "price",
        "quality": "quality",
        "trust": "trust",
        "ranking": "ranking",
        "exploration": "exploration",
        "revisit": "revisit",
        "balanced": "balanced",
        "discovery": "discovery",
    }

    return priority_to_mode.get(base_priority, "ranking"), use_adaptive


def present_recommendation_reason(value, item=None):
    """Keep unlinked review claims and unverified sweetness out of public copy."""
    if not isinstance(value, str):
        return value
    if any(token in value for token in ("리뷰", "평점", "만족도", "사용자 반응", "구매자 반응", "구매 반응")):
        return "가격·품질 계산 지표를 반영한 추천 후보입니다. 구매자 반응 근거는 확인되지 않았습니다."
    if ("brix" in value.lower() or "고당도" in value) and any(
        token in value for token in ("상품 정보", "표기", "확인", "검증", "실측", "보장")
    ):
        match = re.search(r"(\d{1,2}(?:\.\d+)?)\s*brix", value, re.IGNORECASE)
        if match and brix_claim_source(item, float(match.group(1))) == "seller_page_claim":
            return f"상품명·상세 설명에 {match.group(1)}brix로 표기되어 있습니다. 실제 당도는 확인되지 않았습니다."
        if not match and "고당도" in value and brix_claim_source(item) == "seller_page_claim":
            return "상품명·상세 설명에 고당도로 표기되어 있습니다. 실제 당도는 확인되지 않았습니다."
        return "Brix·고당도 입력의 출처와 실제 당도는 확인되지 않았습니다."
    return value


def present_recommendation_label(value):
    """Avoid presenting an unlinked legacy reaction label as buyer evidence."""
    if value == "사용자 반응 우수 추천":
        return "계산 지표 기반 추천"
    return value


def apply_priority_sort(items: list[dict], priority: str) -> list[dict]:
    base_priority = (priority or "ranking").replace("_adaptive", "")

    if base_priority == "price":
        return sorted(
            items,
            key=lambda x: (
                x.get("price") or 999999999,
                -(x.get("v7_final_score") or 0),
            ),
        )

    if base_priority == "quality":
        return sorted(
            items,
            key=lambda x: (
                x.get("v7_quality_score") or 0,
                x.get("v7_final_score") or 0,
            ),
            reverse=True,
        )

    if base_priority == "trust":
        return sorted(
            items,
            key=lambda x: (
                x.get("v7_platform_score") or 0,
                x.get("v7_final_score") or 0,
            ),
            reverse=True,
        )

    return sorted(
        items,
        key=lambda x: x.get("v7_final_score") or 0,
        reverse=True,
    )


def enrich_response_compatibility(item: dict, query: str, priority: str) -> dict:
    result = dict(item)

    score = result.get("v7_final_score") or result.get("final_recommendation_score") or 0

    result["score"] = score
    result["final_recommendation_score"] = score
    result["adaptive_score"] = score

    result["recommendation_mode"], use_adaptive = normalize_priority(priority)
    result["selected_priority"] = priority.replace("_adaptive", "")
    result["sort_mode"] = "adaptive" if use_adaptive else "v8"

    result["seller_name"] = (
        result.get("seller_name")
        or result.get("mall_name")
        or result.get("platform")
        or ""
    )

    result["platform_name"] = (
        result.get("platform_name")
        or result.get("mall_name")
        or result.get("platform")
        or ""
    )

    result["product_name"] = (
        result.get("product_name")
        or result.get("name")
        or ""
    )

    result["recommendation_reason"] = present_recommendation_reason(
        result.get("v8_score_reason")
        or result.get("v7_score_reason")
        or result.get("food_intelligence_reason")
        or "AI가 가격, 품질, 혜택 정보를 종합해 추천했습니다.",
        result,
    )
    # The source narrative fields also pass through in the public item dict.
    for key in (
        "v8_score_reason", "v7_score_reason", "food_intelligence_reason",
        "fruit_quality_reason", "recommendation_reason_1",
        "recommendation_reason_2", "recommendation_reason_3",
    ):
        if key in result:
            result[key] = present_recommendation_reason(result[key], result)

    result["final_recommendation_label"] = (
        "강력추천"
        if score >= 80
        else "추천"
        if score >= 65
        else "비교 추천"
        if score >= 50
        else "조건부 추천"
    )

    result["fruit_name"] = result.get("fruit_name") or query
    result["query"] = query

    return result


def canonical_result_to_compatibility_response(
    result: RecommendationResult,
    *,
    q: str,
    priority: str,
) -> dict:
    """
    Convert the canonical RecommendationResult into the existing
    public/API compatibility response without moving compatibility
    concerns into RecommendationProvider.
    """
    items = []

    for candidate in result.candidates:
        item = dict(candidate.item)

        item["rank"] = candidate.rank
        item["v7_rank"] = candidate.rank

        item = enrich_response_compatibility(
            item,
            result.context.query or q,
            priority,
        )

        cross_border = candidate.metadata.get("cross_border")
        if cross_border:
            item["cross_border"] = dict(cross_border)

        # Compatibility enrichment must not replace the canonical rank.
        item["rank"] = candidate.rank
        item["v7_rank"] = candidate.rank

        items.append(item)

    response = {
        "summary": result.summary,
        "items": items,
        "engine_version": "recommendation_provider_canonical",
        "market_sources": ["naver", "coupang"],
    }

    if result.warnings:
        response["warnings"] = list(
            result.warnings
        )

    return response


def run_recommendation_pipeline(
    q: str,
    priority: str = "ranking",
    session_id: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Public/API compatibility facade for the canonical
    RecommendationProvider production composition.
    """
    context = build_canonical_context(
        q=q,
        priority=priority,
        session_id=session_id,
        limit=limit,
    )

    provider = compose_production_recommendation_provider()

    result = provider.recommend(
        context
    )

    return canonical_result_to_compatibility_response(
        result,
        q=q,
        priority=priority,
    )
