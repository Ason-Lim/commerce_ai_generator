"""Transparent fixed-weight evidence scoring for the Sauce domain."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple


_WEIGHTS = {"family": 0.30, "texture": 0.15, "heat_level": 0.15, "intended_use": 0.25, "provenance": 0.15}


@dataclass(frozen=True)
class SauceEvidenceScore:
    weights: Mapping[str, float]
    component_inputs: Mapping[str, float]
    contributions: Mapping[str, float]
    final_score: float
    conflicts: Tuple[str, ...]
    unresolved_inputs: Tuple[str, ...]
    cap_applied: bool
    state: str


def score_sauce_evidence(
    *, family: float = 0.0, texture: float = 0.0, heat_level: float = 0.0,
    intended_use: float = 0.0, provenance: float = 0.0,
    conflicts: Tuple[str, ...] = (),
) -> SauceEvidenceScore:
    raw = {"family": family, "texture": texture, "heat_level": heat_level, "intended_use": intended_use, "provenance": provenance}
    bounded = {name: min(1.0, max(0.0, float(value))) for name, value in raw.items()}
    cap_applied = any(bounded[name] != float(raw[name]) for name in raw)
    conflict_set = frozenset(conflicts)
    contributions = {name: 0.0 if name in conflict_set else bounded[name] * _WEIGHTS[name] for name in _WEIGHTS}
    unresolved = tuple(name for name in _WEIGHTS if bounded[name] == 0.0 or name in conflict_set)
    final_score = min(1.0, sum(contributions.values()))
    state = "UNRESOLVED" if final_score == 0.0 else ("RESOLVED" if not unresolved else "PARTIAL")
    return SauceEvidenceScore(
        MappingProxyType(dict(_WEIGHTS)), MappingProxyType(bounded),
        MappingProxyType(contributions), final_score, tuple(conflicts), unresolved,
        cap_applied, state,
    )
