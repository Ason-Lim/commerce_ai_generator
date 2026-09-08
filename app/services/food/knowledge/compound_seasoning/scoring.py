"""Transparent fixed-weight scoring for Compound Seasoning evidence."""

from dataclasses import dataclass
from numbers import Real
from typing import Mapping


class ScoringValidationError(ValueError):
    """Raised when bounded transparent scoring cannot be performed."""


WEIGHTS = {"form": 0.30, "composition": 0.40, "usage": 0.30}
_COMPONENTS = tuple(WEIGHTS)


@dataclass(frozen=True)
class ScoreResult:
    components: Mapping[str, float]
    weights: Mapping[str, float]
    raw_sum: float
    final_score: float
    unresolved_inputs: tuple[str, ...]
    state: str
    cap_applied: bool


def score_components(
    components: Mapping[str, object],
    *,
    unresolved_inputs: tuple[str, ...] = (),
) -> ScoreResult:
    if not isinstance(components, Mapping) or set(components) != set(_COMPONENTS):
        raise ScoringValidationError("components must contain exactly form, composition, and usage")
    if not isinstance(unresolved_inputs, tuple):
        raise ScoringValidationError("unresolved_inputs must be a tuple")
    unknown = set(unresolved_inputs) - set(_COMPONENTS)
    if unknown:
        raise ScoringValidationError(f"unknown unresolved input: {sorted(unknown)[0]}")

    normalized: dict[str, float] = {}
    for name in _COMPONENTS:
        value = components[name]
        if value is None:
            if name not in unresolved_inputs:
                raise ScoringValidationError(f"None component must be unresolved: {name}")
            normalized[name] = 0.0
            continue
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ScoringValidationError(f"component must be numeric or None: {name}")
        numeric = float(value)
        if not 0.0 <= numeric <= 1.0:
            raise ScoringValidationError(f"component must be between zero and one: {name}")
        normalized[name] = numeric

    ordered_unresolved = tuple(name for name in _COMPONENTS if name in unresolved_inputs)
    raw_sum = sum(normalized[name] * WEIGHTS[name] for name in _COMPONENTS)
    final_score = min(1.0, max(0.0, raw_sum))
    cap_applied = final_score != raw_sum
    if len(ordered_unresolved) == len(_COMPONENTS):
        state = "UNRESOLVED"
    elif ordered_unresolved:
        state = "PARTIALLY_UNRESOLVED"
    else:
        state = "RESOLVED"
    return ScoreResult(
        components=normalized,
        weights=dict(WEIGHTS),
        raw_sum=raw_sum,
        final_score=final_score,
        unresolved_inputs=ordered_unresolved,
        state=state,
        cap_applied=cap_applied,
    )
