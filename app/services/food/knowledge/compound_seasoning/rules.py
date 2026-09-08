"""Deterministic fail-closed rules for Compound Seasoning evidence."""

from dataclasses import dataclass
from typing import Mapping

from .attributes import AttributeEvidence, CompoundSeasoningAttributes


class RuleValidationError(ValueError):
    """Raised when deterministic rule evaluation is impossible."""


@dataclass(frozen=True)
class ComponentRuleResult:
    value: float
    unresolved: bool
    reason: str


@dataclass(frozen=True)
class CompoundSeasoningRuleResult:
    components: Mapping[str, ComponentRuleResult]
    unresolved_inputs: tuple[str, ...]


_COMPONENTS = ("form", "composition", "usage")


def _normalize_expected(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuleValidationError("expected component must be a non-empty string")
    return " ".join(value.casefold().strip().split())


def evaluate_component(
    expected: object, evidence: object
) -> ComponentRuleResult:
    normalized_expected = _normalize_expected(expected)
    if not isinstance(evidence, AttributeEvidence):
        raise RuleValidationError("evidence must be AttributeEvidence")
    if evidence.unresolved:
        return ComponentRuleResult(0.0, True, evidence.status.value)
    if evidence.value == normalized_expected:
        return ComponentRuleResult(1.0, False, "MATCH")
    return ComponentRuleResult(0.0, False, "NO_MATCH")


def evaluate_rules(
    attributes: CompoundSeasoningAttributes,
    *,
    expected: Mapping[str, object],
) -> CompoundSeasoningRuleResult:
    if not isinstance(attributes, CompoundSeasoningAttributes):
        raise RuleValidationError("attributes must be CompoundSeasoningAttributes")
    if not isinstance(expected, Mapping) or set(expected) != set(_COMPONENTS):
        raise RuleValidationError("expected must contain exactly form, composition, and usage")
    components = {
        name: evaluate_component(expected[name], getattr(attributes, name))
        for name in _COMPONENTS
    }
    unresolved = tuple(name for name in _COMPONENTS if components[name].unresolved)
    return CompoundSeasoningRuleResult(components, unresolved)
