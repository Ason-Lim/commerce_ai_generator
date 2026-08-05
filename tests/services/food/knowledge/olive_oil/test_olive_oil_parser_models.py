from app.services.food.knowledge.olive_oil.grade_registry import (
    OliveOilGradeRegistry,
)
from app.services.food.knowledge.olive_oil.parser_models import (
    OliveOilParseResult,
)


def test_parse_result_normalizes_confidence() -> None:
    result = OliveOilParseResult(
        original_text="테스트 올리브오일",
        normalized_text="테스트 올리브오일",
        confidence=1.5,
        olive_oil_type_confidence=-0.5,
        grade_confidence=2.0,
    )

    assert result.confidence == 1.0
    assert result.olive_oil_type_confidence == 0.0
    assert result.grade_confidence == 1.0


def test_parse_result_deduplicates_keywords_and_warnings() -> None:
    result = OliveOilParseResult(
        original_text="테스트 올리브오일",
        normalized_text="테스트 올리브오일",
        confidence=0.8,
        detected_keywords=[
            "올리브오일",
            "올리브오일",
            "",
        ],
        warnings=[
            "정보 부족",
            "정보 부족",
            "",
        ],
    )

    assert result.detected_keywords == [
        "올리브오일"
    ]
    assert result.warnings == [
        "정보 부족"
    ]


def test_parse_result_counts_matched_fields() -> None:
    result = OliveOilParseResult(
        original_text="스페인 아르베키나 엑스트라 버진",
        normalized_text="스페인 아르베키나 엑스트라 버진",
        confidence=0.9,
        olive_oil_type="single_varietal",
        variety="arbequina",
        origin="spain",
        processing="cold_pressed",
        grade="extra_virgin",
    )

    assert result.matched_field_count == 5
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.has_match is True


def test_parse_result_is_usable_with_grade_only() -> None:
    result = OliveOilParseResult(
        original_text="엑스트라 버진",
        normalized_text="엑스트라 버진",
        confidence=0.8,
        grade="extra_virgin",
    )

    assert result.matched_field_count == 1
    assert result.is_usable is True
    assert result.is_complete is False


def test_parse_result_serializes_registry_match() -> None:
    grade_match = OliveOilGradeRegistry().match(
        "엑스트라 버진 올리브오일"
    )

    assert grade_match is not None

    result = OliveOilParseResult(
        original_text="엑스트라 버진 올리브오일",
        normalized_text="엑스트라 버진 올리브오일",
        confidence=0.9,
        grade="extra_virgin",
        grade_confidence=grade_match.confidence,
        grade_match=grade_match,
        detected_keywords=[
            grade_match.matched_alias
        ],
    )

    payload = result.to_dict()

    assert payload["grade"] == "extra_virgin"
    assert payload["grade_match"] is not None
    assert (
        payload["grade_match"]["registry_key"]
        == "extra_virgin"
    )
    assert payload["matched_field_count"] == 1
    assert payload["is_usable"] is True
