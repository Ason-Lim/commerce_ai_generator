from app.services.food.knowledge.olive_oil.grade_registry import (
    OliveOilGradeRegistry,
)
from app.services.food.knowledge.olive_oil.origin_registry import (
    OliveOilOriginRegistry,
)
from app.services.food.knowledge.olive_oil.processing_registry import (
    OliveOilProcessingRegistry,
)
from app.services.food.knowledge.olive_oil.type_registry import (
    OliveOilTypeRegistry,
)
from app.services.food.knowledge.olive_oil.variety_registry import (
    OliveOilVarietyRegistry,
)


def test_type_registry_matches_korean_alias() -> None:
    match = OliveOilTypeRegistry().match(
        "프리미엄 단일 품종 올리브오일"
    )

    assert match is not None
    assert match.entry.registry_key == "single_varietal"
    assert match.entry.premium is True


def test_variety_registry_matches_arbequina() -> None:
    match = OliveOilVarietyRegistry().match(
        "스페인 아르베키나 올리브오일"
    )

    assert match is not None
    assert match.entry.registry_key == "arbequina"
    assert match.entry.cultivar_origin == "Spain"


def test_origin_registry_matches_greece() -> None:
    match = OliveOilOriginRegistry().match(
        "그리스산 엑스트라 버진 올리브오일"
    )

    assert match is not None
    assert match.entry.registry_key == "greece"
    assert match.entry.country_code == "GR"


def test_processing_registry_matches_cold_pressed() -> None:
    match = OliveOilProcessingRegistry().match(
        "저온 냉압착 엑스트라 버진 올리브오일"
    )

    assert match is not None
    assert match.entry.registry_key == "cold_pressed"
    assert match.entry.mechanical_only is True
    assert match.entry.cold_extracted is True
    assert match.entry.refined is False


def test_grade_registry_matches_extra_virgin() -> None:
    match = OliveOilGradeRegistry().match(
        "스페인산 엑스트라 버진 올리브오일"
    )

    assert match is not None
    assert match.entry.registry_key == "extra_virgin"
    assert match.entry.virgin is True
    assert match.entry.premium is True
    assert match.entry.score == 95.0


def test_grade_registry_matches_pomace() -> None:
    match = OliveOilGradeRegistry().match(
        "업소용 올리브 포마스 오일"
    )

    assert match is not None
    assert match.entry.registry_key == "pomace"
    assert match.entry.pomace is True


def test_registry_returns_none_for_unknown_text() -> None:
    assert OliveOilVarietyRegistry().match(
        "등록되지 않은 품종"
    ) is None



def test_specific_type_has_priority_over_generic() -> None:
    registry = OliveOilTypeRegistry()

    match = registry.match(
        "스페인산 아르베키나 단일 품종 "
        "냉압착 엑스트라 버진 올리브오일"
    )

    assert match is not None
    assert match.registry_key == "single_varietal"
    
    
def test_generic_type_used_as_fallback() -> None:
    registry = OliveOilTypeRegistry()

    match = registry.match("일반 올리브오일")

    assert match is not None
    assert match.registry_key == "olive_oil"