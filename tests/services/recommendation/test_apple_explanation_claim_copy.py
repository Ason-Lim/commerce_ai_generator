"""Synthetic checks of text returned by the active recommendation display builders."""

import ast
from pathlib import Path
from types import SimpleNamespace
import textwrap
from typing import Callable

from app.services.recommendation.compare_engine import build_compare_message
from app.services.recommendation.reason_engine import build_reason_list
from app.services.recommendation_story_engine_v61 import build_recommendation_story_v61
from app.services.explainability_service import build_explainability
from app.services.food_intelligence.engines.fruit_engine import calculate_fruit_quality
from app.services.recommendation_pipeline import enrich_response_compatibility
from app.services.recommendation.claim_source import brix_claim_source
from app.services.recommendation.score_engine import get_brix_value


ROOT = Path(__file__).resolve().parents[3]


def _ui_function(name, **dependencies):
    """Load an actual UI function without importing the unrelated badge module."""
    source = (ROOT / "app/ui/streamlit_app.py").read_text(encoding="utf-8")
    functions = [
        node for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert functions
    node = functions[-1]  # The live selection-reason definition is the last one.
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    namespace = dict(dependencies)
    exec(compile(module, "app/ui/streamlit_app.py", "exec"), namespace)
    return namespace[name]


def _badge_builder():
    """Run the real badge function while leaving the existing List import error separate."""
    source = (ROOT / "app/services/badge_engine.py").read_text(encoding="utf-8")
    functions = [
        node for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name in ("_safe_float", "_safe_list", "build_ai_badges")
    ]
    module = ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[]))
    namespace = {"List": list, "brix_claim_source": brix_claim_source}
    exec(compile(module, "app/services/badge_engine.py", "exec"), namespace)
    return namespace["build_ai_badges"]


def _product_card_badges(item):
    """Capture the actual renderer without importing the unrelated badge module."""
    source = (ROOT / "app/ui/product_card_renderer.py").read_text(encoding="utf-8")
    functions = [
        node for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "render_product_badges"
    ]
    assert len(functions) == 1
    module = ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[]))
    rendered = []
    namespace = {
        "Callable": Callable,
        "brix_claim_source": brix_claim_source,
        "safe_html": lambda value: value,
        "textwrap": textwrap,
        "st": SimpleNamespace(markdown=lambda value, **kwargs: rendered.append(value)),
    }
    exec(compile(module, "app/ui/product_card_renderer.py", "exec"), namespace)
    namespace["render_product_badges"](
        item, {}, get_brix_value_fn=get_brix_value,
        has_coupon_signal_fn=lambda _: False, fmt_money_fn=str,
    )
    return " ".join(rendered)


def test_review_counts_and_ratings_do_not_become_buyer_evidence():
    item = {
        "product_name": "사과 16brix 고당도",
        "brix": 16,
        "is_high_brix": True,
        "review_count": 9999,
        "propagated_review_count": 9999,
        "rating": 4.9,
        "_ai_scores": {"quality": 0, "price": 0, "popularity": 0},
    }
    story = build_recommendation_story_v61(item)
    text = " ".join(
        [story["story_summary"], story["story_detail"], *story["caution_story"]]
    )
    reasons = " ".join(build_reason_list(item, priority="trust"))
    compare = build_compare_message(item, priority="trust")
    for rendered in (text, reasons, compare):
        assert "구매자 반응" not in rendered
        assert "만족도가 높" not in rendered
        assert "리뷰 9,999" not in rendered
    assert "표기" in text
    assert "실제 당도는 확인되지 않았습니다" in text
    assert "연결은 확인되지 않았습니다" in text


def test_hero_and_summary_do_not_infer_buyer_response_from_review_count():
    item = {"brix": 16, "is_high_brix": True, "review_count": 1000, "rating": 4.9}
    summary = _ui_function("build_customer_summary", brix_claim_source=brix_claim_source)([item], "trust")
    hero = _ui_function(
        "build_hero_message",
        classify_recommendation_type=lambda *a, **kw: ("인기", ""),
        brix_claim_source=brix_claim_source,
    )(item, priority="discovery")
    rank = _ui_function("build_hero_rank_reason")({}, priority="trust")
    assert "상품 정보에 고당도로 표기" not in summary
    assert "고당도" not in summary
    assert "Brix 입력값의 출처는 확인되지 않았어요" in hero
    for rendered in (summary, hero, rank):
        assert "사용자 반응" not in rendered
        assert "리뷰" not in rendered
        assert "만족도" not in rendered


def test_revisit_insight_refers_to_interest_without_claiming_product_reaction():
    insight = _ui_function(
        "build_ai_insight_message",
        st=SimpleNamespace(session_state={"session_id": "synthetic"}),
        load_revisit_recommendations=lambda session: {"fruit_name": "사과"},
    )()
    assert "사과 추천 후보를 다시 살펴볼 수 있어요" in insight
    assert "반응이 좋았던" not in insight


def test_hero_explainability_filters_inherited_unlinked_review_copy():
    explain = build_explainability({
        "review_count": 9999,
        "rating": 4.9,
        "market_signal_score_final": 90,
        "recommendation_reason_1": "리뷰 9,999건으로 구매자 반응이 확인됩니다.",
    })
    visible = " ".join([
        explain["summary"], explain["story"], *explain["reasons"],
    ])
    assert "구매자 반응" not in visible
    assert "리뷰 9,999" not in visible
    assert "실제 구매 만족도는 확인되지 않았습니다" in visible
    assert "상품·옵션·판매 제안 연결" in " ".join(explain["cautions"])


def test_product_name_brix_is_reported_as_a_claim():
    result = calculate_fruit_quality({"product_name": "16brix 고당도 사과"})
    assert "상품명·상세 설명에 16brix로 표기" in result["fruit_quality_reason"]
    assert "실제 당도는 확인되지 않았습니다" in result["fruit_quality_reason"]


def test_fruit_reason_does_not_attribute_unidentified_name_or_brix_feature_to_page():
    result = calculate_fruit_quality({"name": "16brix 사과", "brix": 16})
    assert result["fruit_brix"] == 16
    assert "Brix 입력값 16의 출처" in result["fruit_quality_reason"]
    assert "상품명·상세 설명에" not in result["fruit_quality_reason"]
    feature_only = calculate_fruit_quality({"product_name": "사과", "brix": 16})
    assert feature_only["fruit_brix"] == 0  # Existing scoring reads the name, not the feature.
    assert "상품명·상세 설명에" not in feature_only["fruit_quality_reason"]


def test_normal_api_reason_does_not_relabel_unlinked_reviews_as_buyers():
    item = enrich_response_compatibility({
        "rank": 2,
        "v7_final_score": 37,
        "v8_score_reason": "리뷰 999건으로 구매자 반응이 확인됩니다.",
    }, "사과", "ranking")
    assert item["rank"] == 2
    assert item["score"] == 37
    assert "구매자 반응 근거는 확인되지 않았습니다" in item["recommendation_reason"]
    assert "리뷰 999건" not in item["v8_score_reason"]


def test_brix_source_separates_page_claim_from_unattributed_feature_in_public_copy():
    from app.services.recommendation.compare_engine import build_info_chips

    unknown = {"product_name": "사과", "brix": 16, "is_high_brix": True}
    page_claim = {"product_name": "16brix 고당도 사과", "brix": 16, "is_high_brix": True}
    assert brix_claim_source(unknown, 16) == "UNKNOWN"
    assert brix_claim_source(page_claim, 16) == "seller_page_claim"
    for item, expected in (
        (unknown, "출처"), (page_claim, "상품명·상세 설명"),
    ):
        story = build_recommendation_story_v61(item)
        assert expected in story["story_summary"]
        assert expected in build_compare_message(item)
        assert expected in " ".join(build_reason_list(item))
    assert "출처 불명 입력" in build_info_chips(unknown)[0][0]
    assert "상품명·상세 설명 표기" in build_info_chips(page_claim)[0][0]

    unknown_summary = _ui_function("build_customer_summary", brix_claim_source=brix_claim_source)([unknown], "trust")
    known_summary = _ui_function("build_customer_summary", brix_claim_source=brix_claim_source)([page_claim], "trust")
    assert "고당도로 표기" not in unknown_summary
    assert "고당도로 표기" in known_summary


def test_detail_description_only_brix_uses_matching_scope_in_chips_and_badges():
    from app.services.recommendation.compare_engine import build_info_chips

    detail = {"product_name": "사과", "detail_description": "최대 16brix", "brix": 16, "fruit_brix": 16}
    unknown = {"product_name": "사과", "brix": 16, "fruit_brix": 16}
    assert brix_claim_source(detail, 16) == "seller_page_claim"
    assert brix_claim_source(unknown, 16) == "UNKNOWN"
    assert "상품명·상세 설명 표기 16brix" in build_info_chips(detail)[0][0]
    assert "출처 불명 입력 16brix" in build_info_chips(unknown)[0][0]
    assert "상품명·상세 설명 표기 16Brix" in _badge_builder()(detail)[0]
    assert "Brix 입력 출처 불명" in _badge_builder()(unknown)[0]
    assert "상품명·상세 설명 표기 16brix" in _product_card_badges(detail)
    assert "출처 불명 입력 16brix" in _product_card_badges(unknown)

    high_only = {"product_name": "사과", "detail_description": "고당도 사과", "is_high_brix": True}
    assert "상품명·상세 설명 고당도 표기" in _product_card_badges(high_only)


def test_normal_api_brix_reason_preserves_only_matching_page_claim():
    for name, expected in (("사과", "출처와 실제 당도는 확인되지"), ("16brix 사과", "상품명·상세 설명에 16brix로 표기")):
        item = enrich_response_compatibility({
            "product_name": name,
            "brix": 16,
            "v7_final_score": 70,
            "v8_score_reason": "상품 정보에 16brix로 표기되어 있습니다.",
        }, "사과", "ranking")
        assert expected in item["recommendation_reason"]
        assert expected in item["v8_score_reason"]
        assert item["score"] == 70
