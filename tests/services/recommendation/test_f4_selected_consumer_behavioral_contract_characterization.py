from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_recommendation_pipeline_model_and_provider_contract():
    source = _source("app/services/recommendation_pipeline.py")
    for symbol in (
        "RecommendationContext",
        "RecommendationPriority",
        "RecommendationResult",
        "compose_production_recommendation_provider",
    ):
        assert symbol in source


def test_generator_compatibility_and_context_bridge_contract():
    compatibility = _source("app/services/generator_compatibility.py")
    service = _source("app/services/generator_service.py")
    assert "RecommendationCandidate" in compatibility
    assert "RecommendationResult" in compatibility
    assert "build_canonical_context" in service
    assert "compose_production_recommendation_provider" in service


def test_compare_identity_snapshot_and_widget_key_contract():
    comparison = _source("app/services/experience/comparison.py")
    renderer = _source("app/ui/product_card_renderer.py")
    assert "get_compare_identity" in comparison
    assert "build_compare_snapshot" in comparison
    assert "get_compare_identity" in renderer
    assert "build_compare_snapshot" in renderer
    assert "build_compare_widget_key" in renderer


def test_streamlit_scoring_identity_v8_and_compare_contract():
    source = _source("app/ui/streamlit_app.py")
    for symbol in (
        "calculate_mode_score",
        "calculate_ai_scores",
        "validate_product_identity",
        "apply_recommendation_score_v8",
        "get_compare_identity",
    ):
        assert symbol in source


def test_api_generator_and_pipeline_bridge_contract():
    source = _source("app/main.py")
    assert "from app.services.generator_service import generate_product_strategy" in source
    assert "from app.services.recommendation_pipeline import run_recommendation_pipeline" in source
    assert 'result = generate_product_strategy(request)' in source
    assert source.count("return run_recommendation_pipeline(") == 2
    assert '@app.post("/generate")' in source
    assert '@app.get("/recommendations/v2")' in source
    assert '@app.get("/recommendations/nl")' in source
