"""Bounded request-local Hero trace; no DB, marketplace call, or persistence."""

import builtins
import importlib
from typing import List
from unittest.mock import patch

import pytest
import requests

from app.services.price_intelligence_engine import build_price_intelligence
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.provider import RecommendationProvider, build_score_components
from app.services.recommendation_story_engine_v61 import build_recommendation_story_v61
from app.services.recommendation_pipeline import canonical_result_to_compatibility_response


def _candidate(name, rank, api_score, public_score):
    return RecommendationCandidate(
        item={
            "product_name": name,
            "seller_name": f"{name}몰",
            "product_id": name,
            "price": 12000,
            "v7_final_score": public_score,
            "_canonical_price_selected_field": "price_score",
            "_canonical_price_utility_source": "price",
            "price_score": 65,
        },
        score=RecommendationScoreResult(
            final_score=api_score,
            priority=RecommendationPriority.TRUST,
            components=RecommendationScoreComponents(quality=70, price=65, trust=80),
            weights={"quality": 0.2, "trust": 0.8},
            version="canonical-test",
        ),
        rank=rank,
    )


def _result():
    return RecommendationResult(
        context=RecommendationContext(query="사과", priority=RecommendationPriority.TRUST),
        candidates=(_candidate("A", 1, 82, 77), _candidate("B", 2, 79, 74)),
        summary="합성 요청",
    )


@pytest.fixture(scope="module")
def ui_module():
    def deny_network(*args, **kwargs):
        raise AssertionError("network access is prohibited")

    with (
        patch.object(builtins, "List", List, create=True),
        patch.object(requests, "get", deny_network),
        patch.object(requests, "post", deny_network),
    ):
        importlib.import_module("app.ui.product_card_renderer")
        yield importlib.import_module("app.ui.streamlit_app")


def test_default_compatibility_response_has_no_linkage_fields():
    response = canonical_result_to_compatibility_response(_result(), q="사과", priority="trust")
    assert "request_linkage" not in response
    assert all("recommendation_linkage" not in item for item in response["items"])
    assert all("_canonical_price_selected_field" not in item for item in response["items"])
    assert all("_canonical_price_utility_source" not in item for item in response["items"])
    assert [item["score"] for item in response["items"]] == [77, 74]


def test_price_component_and_public_score_source_follow_selection_branch():
    source = {}
    components = build_score_components(
        {"v8_price_score": "invalid", "price_score": 0, "v7_price_score": 99},
        source_record=source,
    )
    assert components.price == 0
    assert source["price_component_source"] == "price_score"

    identity = lambda items: list(items)
    provider = RecommendationProvider(
        collector=lambda query, limit: [{
            "product_id": "zero-price-score", "product_name": "사과",
            "price": 12000, "v8_price_score": "invalid",
            "price_score": 0, "v7_price_score": 99,
        }],
        deduplicator=identity, normalizer=identity, food_enricher=identity,
        price_preparer=identity, trust_preparer=identity,
        popularity_preparer=identity, market_preparer=identity,
        identity_preparer=identity,
    )
    selected = provider.recommend(RecommendationContext(query="사과")).candidates[0]
    assert selected.score.components.price == 0
    assert selected.item["_canonical_price_selected_field"] == "price_score"

    response = canonical_result_to_compatibility_response(
        _result(), q="사과", priority="trust", include_linkage=True
    )
    api = response["items"][0]["recommendation_linkage"]["api"]
    assert api["public_score"] == 77
    assert api["public_score_source"] == "v7_final_score"
    assert api["price_component_source"] == "price_score"
    assert response["items"][0]["recommendation_linkage"]["prices"]["price_score_origin"] == "candidate_relative_price_utility"

    fallback = _candidate("C", 1, 50, 0)
    fallback = RecommendationCandidate(
        item={**fallback.item, "final_recommendation_score": 55},
        score=fallback.score,
        rank=fallback.rank,
    )
    fallback_result = RecommendationResult(context=_result().context, candidates=(fallback,))
    fallback_api = canonical_result_to_compatibility_response(
        fallback_result, q="사과", priority="trust", include_linkage=True
    )["items"][0]["recommendation_linkage"]["api"]
    assert fallback_api["public_score"] == 55
    assert fallback_api["public_score_source"] == "final_recommendation_score"


def test_price_display_sources_are_selected_with_values(monkeypatch):
    monkeypatch.setattr(
        "app.services.price_intelligence_engine.extract_price_signals", lambda item: {}
    )
    price = build_price_intelligence({
        "sale_price": "invalid", "price": 12000,
        "coupon_applied_price": "invalid", "coupon_price": 10000,
    })
    assert price["sale_price"] == 12000
    assert price["coupon_applied_price"] == 10000
    assert price["ai_price"] == 10000
    assert price["selected_source_fields"]["sale_price"] == "item.price"
    assert price["selected_source_fields"]["coupon_applied_price"] == "item.coupon_price"
    assert price["selected_source_fields"]["ai_price"] == "item.coupon_price"


def test_ui_price_selection_records_extra_candidate_branch(ui_module, monkeypatch):
    monkeypatch.setattr(ui_module, "build_price_intelligence", lambda item: {
        "original_price": 15000, "sale_price": 12000,
        "member_price": 0, "coupon_applied_price": 0,
        "ai_price": 12000, "confidence": 100,
        "selected_source_fields": {"sale_price": "item.price"},
    })
    monkeypatch.setattr(ui_module, "apply_known_price_corrections", lambda item, info: info)
    monkeypatch.setattr(ui_module, "is_unreliable_search_price_item", lambda item: False)
    price = ui_module.calculate_price_intelligence({
        "product_name": "일반 사과", "max_benefit_price": 8000,
        "benefit_price": 9000,
    })
    assert price["ai_price"] == 8000
    assert price["selected_source_fields"]["ai_price"] == "item.max_benefit_price"


def test_api_first_can_become_ui_second_with_trace(ui_module, monkeypatch):
    monkeypatch.setitem(ui_module.st.session_state, "include_new_items", True)
    monkeypatch.setattr(ui_module, "enrich_identity_v3", lambda item: item)
    monkeypatch.setattr(ui_module, "enrich_item_identity", lambda item: {
        "is_valid": True, "identity_score": 80,
        "price_confidence": 70, "brix_confidence": 70,
    })
    monkeypatch.setattr(ui_module, "is_mode_candidate", lambda item, mode: True)
    monkeypatch.setattr(ui_module, "get_v8_market_score", lambda context: 0)
    monkeypatch.setattr(ui_module, "calculate_ai_scores", lambda item, priority: {
        "quality": 95 if item["product_name"] == "B" else 30,
        "trust": 90 if item["product_name"] == "B" else 40,
        "price": 80, "popularity": 50,
    })
    response = canonical_result_to_compatibility_response(
        _result(), q="사과", priority="trust", include_linkage=True
    )
    assert response["items"][0]["product_name"] == "A"
    visible = ui_module.build_visible_recommendation_items(
        response["items"], limit=2, priority="trust"
    )
    ui_module.attach_visible_request_linkage(visible)
    assert [item["product_name"] for item in visible] == ["B", "A"]
    hero = visible[0]
    link = hero["recommendation_linkage"]
    score, source, rendered = ui_module.select_hero_rendered_score(
        hero, hero["_ai_scores"], "trust"
    )
    assert link["api"]["rank"] == 2
    assert link["api"]["calculated_score"] == 79
    assert link["api"]["public_score"] == 74
    assert link["ui"]["rank"] == 1
    assert link["ui"]["display_score"] == score
    assert source == "_display_score"
    assert rendered == int(score)
    _, alternate_source, alternate_rendered = ui_module.select_hero_rendered_score(
        {"_display_score": 0, "v8_final_score": 71.9, "score": 90}, {}, "trust"
    )
    assert (alternate_source, alternate_rendered) == ("v8_final_score", 71)
    assert link["hero"] is True
    assert response["request_linkage"]["request_id"] == link["request_id"]


def test_unverified_review_and_composite_explanation_remain_unknown():
    story = build_recommendation_story_v61(
        {"product_name": "15brix 고당도 사과", "review_count": 300, "price": 12000},
        {"name": "15brix 고당도 사과", "ai_estimated_price": 10000,
         "ai_estimated_price_label": "쿠폰 적용가",
         "price_source_fields": {"ai_price": "item.coupon_price"}},
    )
    claims = story["claim_sources"]
    assert any("brix" in claim["text"] and claim["source_field"] == "item.product_name"
               and claim["kind"] == "seller_page_claim" for claim in claims)
    assert any("리뷰" in claim["text"] and claim["kind"] == "UNKNOWN" for claim in claims)
    assert any(claim["text"] == story["story_summary"] and claim["kind"] == "UNKNOWN"
               for claim in claims)
    assert any("기준으로" in claim["text"] and claim["source_field"] == "item.coupon_price"
               for claim in claims)
