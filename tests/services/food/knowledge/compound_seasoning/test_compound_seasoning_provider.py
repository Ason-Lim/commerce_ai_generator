"""Test-first provider composition and transparent scoring contracts."""

from importlib import import_module

import pytest


PACKAGE = "app.services.food.knowledge.compound_seasoning"


def _modules():
    return import_module(f"{PACKAGE}.provider"), import_module(f"{PACKAGE}.scoring")


def test_provider_and_scoring_contract_exports_are_explicit():
    provider, scoring = _modules()
    assert provider.Provider
    assert provider.ProviderResult
    assert provider.ProviderValidationError
    assert scoring.ScoreResult
    assert scoring.ScoringValidationError
    assert callable(scoring.score_components)


def test_fixed_weights_are_exact_and_sum_to_one():
    _, scoring = _modules()
    assert scoring.WEIGHTS == {"form": 0.30, "composition": 0.40, "usage": 0.30}
    assert sum(scoring.WEIGHTS.values()) == pytest.approx(1.0)


def test_fully_known_score_exposes_reproducible_detail():
    _, scoring = _modules()
    result = scoring.score_components({"form": 1.0, "composition": 0.5, "usage": 1.0})
    assert result.raw_sum == pytest.approx(0.80)
    assert result.final_score == pytest.approx(0.80)
    assert result.weights == scoring.WEIGHTS
    assert result.unresolved_inputs == ()
    assert result.state == "RESOLVED"
    assert result.cap_applied is False


def test_partially_unknown_score_uses_zero_without_renormalization():
    _, scoring = _modules()
    result = scoring.score_components(
        {"form": 1.0, "composition": None, "usage": 1.0},
        unresolved_inputs=("composition",),
    )
    assert result.raw_sum == pytest.approx(0.60)
    assert result.final_score == pytest.approx(0.60)
    assert result.unresolved_inputs == ("composition",)
    assert result.state == "PARTIALLY_UNRESOLVED"


def test_fully_unresolved_score_is_zero_and_not_negative_judgment():
    _, scoring = _modules()
    result = scoring.score_components(
        {"form": None, "composition": None, "usage": None},
        unresolved_inputs=("form", "composition", "usage"),
    )
    assert result.raw_sum == 0.0
    assert result.final_score == 0.0
    assert result.state == "UNRESOLVED"
    assert not hasattr(result, "passed")


def test_conflicting_input_is_explicit_and_zero_contribution():
    _, scoring = _modules()
    result = scoring.score_components(
        {"form": 1.0, "composition": None, "usage": 0.0},
        unresolved_inputs=("composition",),
    )
    assert result.components["composition"] == 0.0
    assert result.unresolved_inputs == ("composition",)


def test_score_cap_is_explicit():
    _, scoring = _modules()
    result = scoring.score_components({"form": 1.0, "composition": 1.0, "usage": 1.0})
    assert 0.0 <= result.final_score <= 1.0
    assert result.raw_sum == pytest.approx(1.0)
    assert result.cap_applied is False


@pytest.mark.parametrize(
    "components",
    [
        {"form": -0.01, "composition": 1.0, "usage": 1.0},
        {"form": 1.0, "composition": 1.01, "usage": 1.0},
        {"form": 1.0, "composition": "high", "usage": 1.0},
    ],
)
def test_invalid_component_value_fails_closed(components):
    _, scoring = _modules()
    with pytest.raises(scoring.ScoringValidationError):
        scoring.score_components(components)


def test_provider_aliases_are_preserved_without_resolution_ownership():
    provider_module, _ = _modules()
    aliases = ("curry powder", "seasoning blend")
    provider = provider_module.Provider(aliases=aliases)
    assert provider.aliases is aliases
    assert not hasattr(provider, "resolve_alias")


def test_provider_composes_parser_registry_rules_and_scoring_transparently():
    provider_module, _ = _modules()
    result = provider_module.Provider(aliases=()).evaluate(
        "curry powder seasoning blend",
        expected={"form": "powder", "composition": "multi ingredient blend", "usage": "general seasoning"},
    )
    assert result.attributes
    assert result.rule_result
    assert result.score_result
    assert result.unresolved_inputs == result.score_result.unresolved_inputs


def test_provider_equivalent_input_is_deterministic():
    provider_module, _ = _modules()
    provider = provider_module.Provider(aliases=())
    expected_a = {"form": "powder", "composition": "blend", "usage": "seasoning"}
    expected_b = {"usage": "seasoning", "composition": "blend", "form": "powder"}
    assert provider.evaluate("curry powder", expected=expected_a) == provider.evaluate("curry powder", expected=expected_b)


def test_provider_rejects_malformed_input():
    provider_module, _ = _modules()
    with pytest.raises(provider_module.ProviderValidationError):
        provider_module.Provider(aliases=()).evaluate(None, expected={})


def test_provider_result_excludes_prohibited_semantics():
    provider_module, _ = _modules()
    result = provider_module.Provider(aliases=()).evaluate("unknown blend", expected={})
    prohibited = {
        "recommendation_rank",
        "quality",
        "safety",
        "health",
        "authenticity",
        "regulatory",
        "nutrition",
        "allergen",
    }
    assert prohibited.isdisjoint(vars(result))
