from __future__ import annotations

import pytest

from app.services.cross_border.evidence import (
    has_usable_evidence,
    is_unknown,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)


@pytest.mark.parametrize(
    "state",
    [
        EvidenceState.VERIFIED,
        EvidenceState.OBSERVED,
        EvidenceState.ESTIMATED,
    ],
)
def test_evidence_bearing_states_are_usable(
    state: EvidenceState,
) -> None:
    evidence = CrossBorderEvidence(
        state=state,
        value=0,
    )

    assert has_usable_evidence(evidence) is True
    assert is_unknown(evidence) is False


def test_unknown_is_not_usable_evidence() -> None:
    evidence = CrossBorderEvidence(
        state=EvidenceState.UNKNOWN,
        value=None,
    )

    assert has_usable_evidence(evidence) is False
    assert is_unknown(evidence) is True


@pytest.mark.parametrize(
    "value",
    [
        0,
        0.0,
        False,
        "",
    ],
)
def test_value_shape_does_not_define_unknown_state(
    value: object,
) -> None:
    evidence = CrossBorderEvidence(
        state=EvidenceState.OBSERVED,
        value=value,
    )

    assert is_unknown(evidence) is False
    assert has_usable_evidence(evidence) is True
