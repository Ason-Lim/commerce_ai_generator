from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)
from app.services.cross_border.regulatory import (
    RegulatoryEvidence,
)
from app.services.cross_border.regulatory_applicability import (
    RegulatoryApplicability,
    RegulatoryApplicabilityState,
    evaluate_regulatory_applicability,
)


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="regulatory-source",
        source_type="regulatory",
        record_id="reg-001",
    )


def _regulatory(
    *,
    jurisdiction: str | None = "US",
    destination_country: str | None = "US",
    state: EvidenceState = EvidenceState.VERIFIED,
) -> RegulatoryEvidence:
    return RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=state,
        ),
        provenance=_provenance(),
        context=CrossBorderEvaluationContext(
            origin_country="KR",
            destination_country=destination_country,
        ),
        observation=(
            None
            if state is EvidenceState.UNKNOWN
            else "external regulatory observation"
        ),
        jurisdiction=jurisdiction,
    )


def test_applicability_state_vocabulary() -> None:
    assert {
        state.value
        for state in RegulatoryApplicabilityState
    } == {
        "applicable",
        "not_applicable",
        "unknown",
    }


@pytest.mark.parametrize(
    "state",
    [
        EvidenceState.VERIFIED,
        EvidenceState.OBSERVED,
        EvidenceState.ESTIMATED,
    ],
)
def test_matching_jurisdiction_is_applicable(
    state: EvidenceState,
) -> None:
    result = evaluate_regulatory_applicability(
        _regulatory(
            jurisdiction="US",
            destination_country="US",
            state=state,
        )
    )

    assert (
        result.state
        is RegulatoryApplicabilityState.APPLICABLE
    )
    assert result.jurisdiction == "US"
    assert result.destination_country == "US"


def test_different_jurisdiction_is_not_applicable() -> None:
    result = evaluate_regulatory_applicability(
        _regulatory(
            jurisdiction="JP",
            destination_country="US",
        )
    )

    assert (
        result.state
        is RegulatoryApplicabilityState.NOT_APPLICABLE
    )
    assert result.jurisdiction == "JP"
    assert result.destination_country == "US"


def test_missing_jurisdiction_is_unknown() -> None:
    result = evaluate_regulatory_applicability(
        _regulatory(
            jurisdiction=None,
            destination_country="US",
        )
    )

    assert (
        result.state
        is RegulatoryApplicabilityState.UNKNOWN
    )
    assert result.jurisdiction is None


def test_unknown_evidence_is_unknown() -> None:
    result = evaluate_regulatory_applicability(
        _regulatory(
            jurisdiction="US",
            destination_country="US",
            state=EvidenceState.UNKNOWN,
        )
    )

    assert (
        result.state
        is RegulatoryApplicabilityState.UNKNOWN
    )


def test_unknown_evidence_does_not_become_applicable() -> None:
    result = evaluate_regulatory_applicability(
        _regulatory(
            jurisdiction="US",
            destination_country="US",
            state=EvidenceState.UNKNOWN,
        )
    )

    assert (
        result.state
        is not RegulatoryApplicabilityState.APPLICABLE
    )


def test_country_comparison_is_case_insensitive() -> None:
    result = evaluate_regulatory_applicability(
        _regulatory(
            jurisdiction=" us ",
            destination_country="us",
        )
    )

    assert (
        result.state
        is RegulatoryApplicabilityState.APPLICABLE
    )
    assert result.jurisdiction == "US"
    assert result.destination_country == "US"


def test_not_applicable_is_not_a_prohibition_decision() -> None:
    result = evaluate_regulatory_applicability(
        _regulatory(
            jurisdiction="JP",
            destination_country="US",
        )
    )

    assert (
        result.state
        is RegulatoryApplicabilityState.NOT_APPLICABLE
    )

    assert "prohibit" not in result.reason.lower()
    assert "illegal" not in result.reason.lower()


def test_applicability_result_is_immutable() -> None:
    result = RegulatoryApplicability(
        state=RegulatoryApplicabilityState.APPLICABLE,
        jurisdiction="US",
        destination_country="US",
        reason="test",
    )

    with pytest.raises(FrozenInstanceError):
        result.state = (
            RegulatoryApplicabilityState.NOT_APPLICABLE
        )


def test_contract_does_not_expose_legal_authority() -> None:
    forbidden = {
        "allow",
        "prohibit",
        "restrict",
        "determine_import_eligibility",
        "calculate_duty",
        "classify_hs_code",
    }

    public_names = {
        name.lower()
        for name in dir(
            RegulatoryApplicability
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
