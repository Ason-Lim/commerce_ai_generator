from dataclasses import FrozenInstanceError

import pytest


def _result_type():
    from app.services.food.knowledge.sauce import SauceParseResult

    return SauceParseResult


def test_parser_result_contract_is_exported_from_sauce_package() -> None:
    assert _result_type().__name__ == "SauceParseResult"


def test_defaults_preserve_unknown_and_empty_values() -> None:
    result = _result_type()()
    assert result.family == "unknown"
    assert result.texture == "unknown"
    assert result.heat_level == "unknown"
    assert result.intended_uses == ()
    assert result.matched_evidence == ()
    assert result.unresolved_evidence == ()
    assert result.conflicts == ()
    assert result.confidence == 0.0
    assert result.completeness == 0.0


def test_explicit_supported_normalized_values_are_retained() -> None:
    result = _result_type()(
        family="fermented-liquid",
        texture="liquid",
        heat_level="mild",
        intended_uses=("dipping", "cooking"),
        confidence=0.75,
        completeness=0.5,
    )
    assert result.family == "fermented-liquid"
    assert result.texture == "liquid"
    assert result.heat_level == "mild"
    assert result.intended_uses == ("dipping", "cooking")


def test_collection_fields_use_immutable_tuple_contracts() -> None:
    result = _result_type()(
        intended_uses=("finishing",),
        matched_evidence=("ponzu",),
        unresolved_evidence=("generic paste",),
        conflicts=("liquid", "paste-like"),
    )
    assert isinstance(result.intended_uses, tuple)
    assert isinstance(result.matched_evidence, tuple)
    assert isinstance(result.unresolved_evidence, tuple)
    assert isinstance(result.conflicts, tuple)
    with pytest.raises(FrozenInstanceError):
        result.family = "other"


def test_unresolved_evidence_and_conflicts_remain_explicit() -> None:
    result = _result_type()(
        unresolved_evidence=("ambiguous condiment",),
        conflicts=("sauce", "ingredient"),
    )
    assert result.unresolved_evidence == ("ambiguous condiment",)
    assert result.conflicts == ("sauce", "ingredient")


def test_equality_is_deterministic() -> None:
    result_type = _result_type()
    left = result_type(family="emulsified", matched_evidence=("mayonnaise",))
    right = result_type(family="emulsified", matched_evidence=("mayonnaise",))
    assert left == right
    assert left != result_type(family="other", matched_evidence=("mayonnaise",))


@pytest.mark.parametrize(
    ("field", "value"),
    (("confidence", -0.01), ("completeness", -0.01)),
)
def test_confidence_and_completeness_reject_values_below_zero(
    field: str, value: float
) -> None:
    with pytest.raises(ValueError):
        _result_type()(**{field: value})


def test_confidence_rejects_values_above_one() -> None:
    with pytest.raises(ValueError):
        _result_type()(confidence=1.01)
