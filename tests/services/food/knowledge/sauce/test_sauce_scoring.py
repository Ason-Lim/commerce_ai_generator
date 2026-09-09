from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest


def _score(**components):
    return import_module("app.services.food.knowledge.sauce.scoring").score_sauce_evidence(**components)


def test_fixed_component_weights_are_exposed() -> None:
    assert _score().weights == {"family": 0.30, "texture": 0.15, "heat_level": 0.15, "intended_use": 0.25, "provenance": 0.15}


@pytest.mark.parametrize(("name", "weight"), (("family", 0.30), ("texture", 0.15), ("heat_level", 0.15), ("intended_use", 0.25), ("provenance", 0.15)))
def test_each_component_uses_its_fixed_weight(name: str, weight: float) -> None:
    result = _score(**{name: 1.0})
    assert result.contributions[name] == pytest.approx(weight)
    assert result.final_score == pytest.approx(weight)


@pytest.mark.parametrize(("values", "expected"), (({}, 0.0), ({"family": 1.0, "texture": 1.0, "heat_level": 1.0, "intended_use": 1.0, "provenance": 1.0}, 1.0)))
def test_zero_and_full_evidence_bounds(values: dict, expected: float) -> None:
    assert _score(**values).final_score == pytest.approx(expected)


@pytest.mark.parametrize(("values", "expected"), (({"family": 1.0}, 0.30), ({"intended_use": 1.0}, 0.25), ({"texture": 0.5, "provenance": 1.0}, 0.225)))
def test_partial_scores_are_not_renormalized(values: dict, expected: float) -> None:
    assert _score(**values).final_score == pytest.approx(expected)


@pytest.mark.parametrize("conflicts", (("family",), ("texture", "provenance")))
def test_conflicts_are_transparent_and_score_zero(conflicts: tuple[str, ...]) -> None:
    result = _score(family=1.0, texture=1.0, provenance=1.0, conflicts=conflicts)
    assert result.conflicts == conflicts
    for name in conflicts:
        assert result.contributions[name] == 0.0


@pytest.mark.parametrize(("value", "expected"), ((2.0, 1.0), (-1.0, 0.0)))
def test_component_inputs_are_bounded_and_cap_is_reported(value: float, expected: float) -> None:
    result = _score(family=value)
    assert result.component_inputs["family"] == expected
    assert result.cap_applied is True


@pytest.mark.parametrize("order", (("family", "texture", "intended_use"), ("intended_use", "texture", "family")))
def test_component_order_does_not_change_result(order: tuple[str, ...]) -> None:
    values = {name: 1.0 for name in order}
    assert _score(**values).final_score == pytest.approx(0.70)


@pytest.mark.parametrize("check", ("immutable", "unresolved", "semantic_boundary"))
def test_result_contract_is_immutable_fail_closed_and_domain_only(check: str) -> None:
    result = _score()
    if check == "immutable":
        with pytest.raises((FrozenInstanceError, AttributeError)):
            result.final_score = 1.0
    elif check == "unresolved":
        assert result.state == "UNRESOLVED" and result.unresolved_inputs
    else:
        assert not any(term in repr(result).lower() for term in ("quality rank", "health advice", "safety advice"))
