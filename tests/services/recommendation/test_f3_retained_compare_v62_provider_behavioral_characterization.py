import importlib.util
from pathlib import Path

from app.services.recommendation_compare_engine_v62 import (
    build_hero_compare_v62,
    build_item_compare_v62,
    build_pair_compare_v62,
    build_short_compare_text,
)


ROOT = Path(__file__).resolve().parents[3]
ACTIVE_CHARACTERIZATION = ROOT / "tests/services/recommendation/test_f3_active_ui_story_v61_and_local_compare_behavioral_characterization.py"


def _item(name="대표 상품", price=12000, brix=15, review_count=2400, rating=4.8):
    return {
        "name": name,
        "title": name,
        "product_name": name,
        "price": price,
        "sale_price": price,
        "brix": brix,
        "review_count": review_count,
        "rating": rating,
        "mall_name": "test-platform",
    }


def _display(name="대표 상품", price=12000, brix=15):
    return {
        "name": name,
        "title": name,
        "price": price,
        "price_per_100g": price / 10,
        "brix": brix,
    }


def _load_active_characterization():
    spec = importlib.util.spec_from_file_location("f3_active_ui_behavioral_characterization", ACTIVE_CHARACTERIZATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pair_compare_representative_output_capture():
    result = build_pair_compare_v62(
        _item(),
        _item("비교 상품", 15000, 12, 300, 4.2),
        _display(),
        _display("비교 상품", 15000, 12),
    )
    assert set(result) == {"compare_summary", "compare_bullets", "advantage_count", "caution_count"}
    assert isinstance(result["compare_summary"], str)
    assert isinstance(result["compare_bullets"], list)
    assert result["compare_bullets"]


def test_hero_compare_representative_output_capture():
    other = _item("비교 상품", 15000, 12, 300, 4.2)
    result = build_hero_compare_v62(
        _item(),
        [other],
        _display(),
        {2: _display("비교 상품", 15000, 12)},
    )
    assert set(result) == {"compare_title", "compare_summary", "compare_bullets", "pair_summaries", "compare_score"}
    assert result["compare_title"] == "AI 비교 분석"
    assert isinstance(result["compare_bullets"], list)
    assert len(result["pair_summaries"]) == 1


def test_hero_compare_empty_input_output_capture():
    result = build_hero_compare_v62(_item(), [], _display(), {})
    assert result == {
        "compare_title": "AI 비교 분석",
        "compare_summary": "1위 상품을 다른 후보와 가격·품질·배송 기준으로 비교했습니다.",
        "compare_bullets": ["1위 상품은 가격·품질·시장 신호를 종합해 우선 추천되었습니다."],
        "pair_summaries": [],
        "compare_score": 60,
    }


def test_item_compare_output_capture():
    result = build_item_compare_v62(
        _item("비교 상품", 15000, 12, 300, 4.2),
        _item(),
        _display("비교 상품", 15000, 12),
        _display(),
    )
    assert set(result) == {"compare_title", "compare_summary", "compare_bullets", "compare_score"}
    assert result["compare_title"] == "1위 상품과 비교"
    assert isinstance(result["compare_bullets"], list)


def test_short_compare_text_output_capture():
    result = build_short_compare_text(
        _item(),
        [_item("비교 상품", 15000, 12, 300, 4.2)],
        _display(),
    )
    assert isinstance(result, str)
    assert result


def test_local_compare_and_provider_preserve_distinct_behavioral_relation_boundary():
    active = _load_active_characterization()
    local_builder = active._load_local_compare()
    local_result = local_builder(
        active._item(),
        [active._item("비교 상품", 15000, 0.82)],
        active._display(),
        {2: active._display("비교 상품", 15000)},
    )
    provider_result = build_hero_compare_v62(
        _item(),
        [_item("비교 상품", 15000, 12, 300, 4.2)],
        _display(),
        {2: _display("비교 상품", 15000, 12)},
    )
    assert set(local_result) == {"compare_summary", "compare_bullets"}
    assert {"compare_title", "pair_summaries", "compare_score"} <= set(provider_result)
    assert local_result != provider_result
