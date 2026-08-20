import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
)
from app.services.recommendation.provider import (
    RecommendationProvider,
)

load_dotenv(".env")

DB_URL = (
    os.getenv("COMMERCE_DB_URL")
    or os.getenv("FRUIT_DB_URL")
    or "postgresql+psycopg2://mom@localhost:5432/dashboard_db"
)

engine = create_engine(DB_URL)


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

    result["recommendation_reason"] = (
        result.get("v8_score_reason")
        or result.get("v7_score_reason")
        or result.get("food_intelligence_reason")
        or "AI가 가격, 품질, 혜택 정보를 종합해 추천했습니다."
    )

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

    provider = RecommendationProvider()

    result = provider.recommend(
        context
    )

    return canonical_result_to_compatibility_response(
        result,
        q=q,
        priority=priority,
    )
