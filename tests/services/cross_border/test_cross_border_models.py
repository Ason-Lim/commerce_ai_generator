from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)


def test_evidence_state_has_canonical_vocabulary() -> None:
    assert {
        state.value
        for state in EvidenceState
    } == {
        "verified",
        "observed",
        "estimated",
        "unknown",
    }


@pytest.mark.parametrize(
    "value",
    [
        0,
        0.0,
        False,
        "",
    ],
)
def test_observed_values_do_not_become_unknown(
    value: object,
) -> None:
    evidence = CrossBorderEvidence(
        state=EvidenceState.OBSERVED,
        value=value,
    )

    assert evidence.state is EvidenceState.OBSERVED
    assert evidence.value == value


def test_unknown_preserves_none_without_manufacturing_value() -> None:
    evidence = CrossBorderEvidence(
        state=EvidenceState.UNKNOWN,
    )

    assert evidence.state is EvidenceState.UNKNOWN
    assert evidence.value is None


def test_evidence_is_immutable() -> None:
    evidence = CrossBorderEvidence(
        state=EvidenceState.VERIFIED,
        value=100,
    )

    with pytest.raises(FrozenInstanceError):
        evidence.value = 200


def test_provenance_is_defensively_copied_and_read_only() -> None:
    source = {
        "record_id": "cbc-test-001",
    }

    evidence = CrossBorderEvidence(
        state=EvidenceState.VERIFIED,
        provenance=source,
    )

    source["record_id"] = "changed"

    assert (
        evidence.provenance["record_id"]
        == "cbc-test-001"
    )

    with pytest.raises(TypeError):
        evidence.provenance["record_id"] = "mutated"
