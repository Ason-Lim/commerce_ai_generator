"""Test-first contracts for deterministic Compound Seasoning rules."""

from importlib import import_module

import pytest


ATTRIBUTES_MODULE = "app.services.food.knowledge.compound_seasoning.attributes"
RULES_MODULE = "app.services.food.knowledge.compound_seasoning.rules"


def _modules():
    return import_module(ATTRIBUTES_MODULE), import_module(RULES_MODULE)


def _evidence(value="powder", status="VERIFIED"):
    attributes, _ = _modules()
    return attributes.normalize_evidence(value, status)


def test_rule_contract_exports_are_explicit():
    _, rules = _modules()
    assert rules.ComponentRuleResult
    assert rules.CompoundSeasoningRuleResult
    assert rules.RuleValidationError
    assert callable(rules.evaluate_component)
    assert callable(rules.evaluate_rules)


def test_known_exact_match_scores_one():
    _, rules = _modules()
    result = rules.evaluate_component("powder", _evidence())
    assert result.value == 1.0
    assert result.unresolved is False
    assert result.reason == "MATCH"


def test_known_mismatch_scores_zero_without_inventing_unknown():
    _, rules = _modules()
    result = rules.evaluate_component("granules", _evidence())
    assert result.value == 0.0
    assert result.unresolved is False
    assert result.reason == "NO_MATCH"


@pytest.mark.parametrize(
    "status",
    ["PARTIALLY_VERIFIED", "REPORTED", "MISSING", "CONFLICTING"],
)
def test_non_verified_evidence_scores_zero_and_remains_unresolved(status):
    _, rules = _modules()
    result = rules.evaluate_component("powder", _evidence("powder", status))
    assert result.value == 0.0
    assert result.unresolved is True
    assert result.reason == status


def test_missing_expected_value_fails_closed():
    _, rules = _modules()
    with pytest.raises(rules.RuleValidationError):
        rules.evaluate_component(None, _evidence())


def test_malformed_evidence_fails_closed():
    _, rules = _modules()
    with pytest.raises(rules.RuleValidationError):
        rules.evaluate_component("powder", object())


def test_rule_collection_exposes_exact_components():
    attributes, rules = _modules()
    projected = attributes.project_attributes(
        form=("powder", "VERIFIED"),
        composition=("multi ingredient blend", "VERIFIED"),
        usage=("general seasoning", "VERIFIED"),
    )
    result = rules.evaluate_rules(
        projected,
        expected={
            "form": "powder",
            "composition": "multi ingredient blend",
            "usage": "general seasoning",
        },
    )
    assert tuple(result.components) == ("form", "composition", "usage")


def test_rule_evaluation_is_order_independent():
    attributes, rules = _modules()
    projected = attributes.project_attributes(
        usage=("general seasoning", "VERIFIED"),
        form=("powder", "VERIFIED"),
        composition=("multi ingredient blend", "VERIFIED"),
    )
    left = rules.evaluate_rules(
        projected,
        expected={"form": "powder", "composition": "multi ingredient blend", "usage": "general seasoning"},
    )
    right = rules.evaluate_rules(
        projected,
        expected={"usage": "general seasoning", "composition": "multi ingredient blend", "form": "powder"},
    )
    assert left == right


def test_all_unresolved_components_are_preserved():
    attributes, rules = _modules()
    projected = attributes.project_attributes(
        form=(None, "MISSING"),
        composition=(None, "MISSING"),
        usage=(None, "MISSING"),
    )
    result = rules.evaluate_rules(
        projected,
        expected={"form": "powder", "composition": "blend", "usage": "seasoning"},
    )
    assert result.unresolved_inputs == ("form", "composition", "usage")
    assert all(component.value == 0.0 for component in result.components.values())


def test_unknown_rule_component_is_rejected():
    attributes, rules = _modules()
    projected = attributes.project_attributes(
        form=("powder", "VERIFIED"),
        composition=("blend", "VERIFIED"),
        usage=("seasoning", "VERIFIED"),
    )
    with pytest.raises(rules.RuleValidationError):
        rules.evaluate_rules(projected, expected={"origin": "korean"})


def test_repeated_rule_evaluation_is_deterministic():
    _, rules = _modules()
    evidence = _evidence("powder", "VERIFIED")
    assert rules.evaluate_component("powder", evidence) == rules.evaluate_component("powder", evidence)
