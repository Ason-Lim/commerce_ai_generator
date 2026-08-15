import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.services.market.collector import collect_market_products
from app.services.ai_ranking_engine_v8 import rank_market_items_v8
from app.services.deduplication_engine_v83 import deduplicate_market_items
from app.services.food_intelligence.food_intelligence_engine import enrich_items_with_food_intelligence
from app.services.platform_normalizer_v84 import normalize_platform_items

load_dotenv(".env")

DB_URL = (
    os.getenv("COMMERCE_DB_URL")
    or os.getenv("FRUIT_DB_URL")
    or "postgresql+psycopg2://mom@localhost:5432/dashboard_db"
)

engine = create_engine(DB_URL)


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


def run_recommendation_pipeline(
    q: str,
    priority: str = "ranking",
    session_id: str | None = None,
    limit: int = 10,
) -> dict:
    cleaned_query = clean_query(q)

    if not cleaned_query:
        return {
            "summary": "검색어를 입력해 주세요.",
            "items": [],
        }

    market_items = collect_market_products(cleaned_query, limit=limit)

    if not market_items:
        return {
            "summary": f"'{q}' 기준으로 추천 가능한 상품을 찾지 못했습니다.",
            "items": [],
        }

    market_items = deduplicate_market_items(market_items)

    market_items = normalize_platform_items(market_items)

    market_items = enrich_items_with_food_intelligence(market_items)


    if not market_items:
        return {
            "summary": f"'{q}' 기준으로 추천 가능한 상품을 찾지 못했습니다.",
            "items": [],
        }

    ranked_items = rank_market_items_v8(market_items)
    ranked_items = apply_priority_sort(ranked_items, priority)

    items = [
        enrich_response_compatibility(item, cleaned_query, priority)
        for item in ranked_items
    ]

    for idx, item in enumerate(items, start=1):
        item["rank"] = idx
        item["v7_rank"] = idx

    return {
        "summary": f"'{q}' 기준으로 네이버와 쿠팡 상품을 함께 비교해 추천했습니다.",
        "items": items,
        "engine_version": "recommendation_pipeline_v8",
        "market_sources": ["naver", "coupang"],
    }
