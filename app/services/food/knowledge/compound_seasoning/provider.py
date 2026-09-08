"""Compound Seasoning provider composition without alias ownership."""

from dataclasses import dataclass
from typing import Mapping

from .attributes import CompoundSeasoningAttributes, project_attributes
from .composition_registry import resolve as resolve_composition
from .form_registry import resolve as resolve_form
from .parser import parse_compound_seasoning
from .rules import CompoundSeasoningRuleResult, RuleValidationError, evaluate_rules
from .scoring import ScoreResult, score_components
from .usage_registry import resolve as resolve_usage


class ProviderValidationError(ValueError):
    """Raised when provider input cannot satisfy the bounded contract."""


@dataclass(frozen=True)
class ProviderResult:
    attributes: CompoundSeasoningAttributes
    rule_result: CompoundSeasoningRuleResult
    score_result: ScoreResult
    unresolved_inputs: tuple[str, ...]


def _resolved_value(resolver, candidates: tuple[object, ...]) -> tuple[object, str]:
    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate:
            continue
        entry = resolver(candidate)
        if entry is not None:
            return entry.canonical_id, "VERIFIED"
    return None, "MISSING"


class Provider:
    """Compose sealed parsing and registries into transparent scoring input."""

    def __init__(self, *, aliases: tuple[str, ...]) -> None:
        if not isinstance(aliases, tuple):
            raise ProviderValidationError("aliases must preserve the tuple contract")
        self.aliases = aliases

    def evaluate(
        self,
        text: str,
        *,
        expected: Mapping[str, object],
    ) -> ProviderResult:
        if not isinstance(text, str):
            raise ProviderValidationError("text must be a string")
        if not isinstance(expected, Mapping):
            raise ProviderValidationError("expected must be a mapping")

        parsed = parse_compound_seasoning(text)
        conflict_status = "CONFLICTING" if parsed.conflicts else "MISSING"
        form = _resolved_value(resolve_form, (parsed.form,))
        composition = _resolved_value(
            resolve_composition,
            (parsed.canonical_id, parsed.composition_class),
        )
        usage = _resolved_value(resolve_usage, tuple(parsed.usages))
        if parsed.conflicts:
            form = form if form[1] == "VERIFIED" else (None, conflict_status)
            composition = composition if composition[1] == "VERIFIED" else (None, conflict_status)
            usage = usage if usage[1] == "VERIFIED" else (None, conflict_status)

        attributes = project_attributes(
            form=form,
            composition=composition,
            usage=usage,
        )
        if set(expected) - {"form", "composition", "usage"}:
            raise ProviderValidationError("expected contains an unsupported component")
        complete_expected = {
            name: expected.get(name) or getattr(attributes, name).value or "__unresolved__"
            for name in ("form", "composition", "usage")
        }
        try:
            rule_result = evaluate_rules(attributes, expected=complete_expected)
        except RuleValidationError as exc:
            raise ProviderValidationError("provider rule evaluation failed") from exc
        score_result = score_components(
            {name: component.value for name, component in rule_result.components.items()},
            unresolved_inputs=rule_result.unresolved_inputs,
        )
        return ProviderResult(
            attributes=attributes,
            rule_result=rule_result,
            score_result=score_result,
            unresolved_inputs=score_result.unresolved_inputs,
        )
