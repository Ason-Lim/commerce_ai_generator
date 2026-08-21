from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
    evaluate_evidence_freshness,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _context(
    evaluated_at: str | None = (
        "2026-08-21T23:00:00+09:00"
    ),
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
        evaluated_at=evaluated_at,
    )


def _provenance(
    *,
    effective_at: str | None = None,
    retrieved_at: str | None = None,
) -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="source-001",
        source_type="marketplace",
        effective_at=effective_at,
        retrieved_at=retrieved_at,
    )


def test_freshness_state_has_canonical_vocabulary() -> None:
    assert {
        state.value
        for state in EvidenceFreshnessState
    } == {
        "fresh",
        "stale",
        "unknown",
    }


def test_effective_at_is_primary_freshness_time() -> None:
    result = evaluate_evidence_freshness(
        _provenance(
            effective_at=(
                "2026-08-20T23:00:00+09:00"
            ),
            retrieved_at=(
                "2026-08-21T22:59:00+09:00"
            ),
        ),
        _context(),
        timedelta(hours=12),
    )

    assert result.state is EvidenceFreshnessState.STALE
    assert (
        result.evidence_at
        == "2026-08-20T23:00:00+09:00"
    )
    assert result.age == timedelta(days=1)


def test_retrieved_at_is_fallback_when_effective_missing() -> None:
    result = evaluate_evidence_freshness(
        _provenance(
            retrieved_at=(
                "2026-08-21T22:00:00+09:00"
            ),
        ),
        _context(),
        timedelta(hours=2),
    )

    assert result.state is EvidenceFreshnessState.FRESH
    assert (
        result.evidence_at
        == "2026-08-21T22:00:00+09:00"
    )
    assert result.age == timedelta(hours=1)


def test_missing_provenance_time_is_unknown() -> None:
    result = evaluate_evidence_freshness(
        _provenance(),
        _context(),
        timedelta(hours=1),
    )

    assert result.state is EvidenceFreshnessState.UNKNOWN
    assert result.evidence_at is None
    assert result.age is None


def test_missing_evaluation_time_is_unknown() -> None:
    result = evaluate_evidence_freshness(
        _provenance(
            effective_at=(
                "2026-08-21T22:00:00+09:00"
            ),
        ),
        _context(evaluated_at=None),
        timedelta(hours=2),
    )

    assert result.state is EvidenceFreshnessState.UNKNOWN
    assert (
        result.evidence_at
        == "2026-08-21T22:00:00+09:00"
    )
    assert result.age is None


def test_future_evidence_time_is_unknown() -> None:
    result = evaluate_evidence_freshness(
        _provenance(
            effective_at=(
                "2026-08-21T23:01:00+09:00"
            ),
        ),
        _context(),
        timedelta(hours=1),
    )

    assert result.state is EvidenceFreshnessState.UNKNOWN
    assert result.age is None


def test_evidence_exactly_at_max_age_is_fresh() -> None:
    result = evaluate_evidence_freshness(
        _provenance(
            effective_at=(
                "2026-08-21T22:00:00+09:00"
            ),
        ),
        _context(),
        timedelta(hours=1),
    )

    assert result.state is EvidenceFreshnessState.FRESH
    assert result.age == timedelta(hours=1)


def test_evidence_older_than_max_age_is_stale() -> None:
    result = evaluate_evidence_freshness(
        _provenance(
            effective_at=(
                "2026-08-21T21:59:59+09:00"
            ),
        ),
        _context(),
        timedelta(hours=1),
    )

    assert result.state is EvidenceFreshnessState.STALE
    assert result.age == timedelta(
        hours=1,
        seconds=1,
    )


def test_timezone_offsets_compare_by_actual_instant() -> None:
    result = evaluate_evidence_freshness(
        _provenance(
            effective_at=(
                "2026-08-21T13:30:00+00:00"
            ),
        ),
        _context(
            evaluated_at=(
                "2026-08-21T23:00:00+09:00"
            )
        ),
        timedelta(hours=1),
    )

    assert result.state is EvidenceFreshnessState.FRESH
    assert result.age == timedelta(minutes=30)


@pytest.mark.parametrize(
    "max_age",
    [
        timedelta(microseconds=-1),
        timedelta(seconds=-1),
    ],
)
def test_negative_max_age_is_rejected(
    max_age: timedelta,
) -> None:
    with pytest.raises(
        ValueError,
        match="max_age must not be negative",
    ):
        evaluate_evidence_freshness(
            _provenance(
                effective_at=(
                    "2026-08-21T22:00:00+09:00"
                ),
            ),
            _context(),
            max_age,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        (
            "effective_at",
            "not-a-datetime",
        ),
        (
            "effective_at",
            "2026-08-21T22:00:00",
        ),
        (
            "retrieved_at",
            "not-a-datetime",
        ),
        (
            "retrieved_at",
            "2026-08-21T22:00:00",
        ),
    ],
)
def test_selected_provenance_time_requires_aware_iso_datetime(
    field_name: str,
    value: str,
) -> None:
    values = {
        "effective_at": None,
        "retrieved_at": None,
    }
    values[field_name] = value

    with pytest.raises(ValueError):
        evaluate_evidence_freshness(
            _provenance(**values),
            _context(),
            timedelta(hours=1),
        )


@pytest.mark.parametrize(
    "value",
    [
        "not-a-datetime",
        "2026-08-21T23:00:00",
    ],
)
def test_evaluation_time_requires_aware_iso_datetime(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        evaluate_evidence_freshness(
            _provenance(
                effective_at=(
                    "2026-08-21T22:00:00+09:00"
                ),
            ),
            _context(evaluated_at=value),
            timedelta(hours=1),
        )


def test_freshness_result_is_immutable() -> None:
    result = EvidenceFreshness(
        state=EvidenceFreshnessState.FRESH,
        evidence_at="2026-08-21T22:00:00+09:00",
        age=timedelta(hours=1),
    )

    with pytest.raises(FrozenInstanceError):
        result.state = EvidenceFreshnessState.STALE


def test_freshness_does_not_mutate_provenance() -> None:
    provenance = _provenance(
        effective_at="2026-08-21T22:00:00+09:00",
    )

    evaluate_evidence_freshness(
        provenance,
        _context(),
        timedelta(hours=2),
    )

    assert (
        provenance.effective_at
        == "2026-08-21T22:00:00+09:00"
    )
    assert not hasattr(provenance, "freshness")
    assert not hasattr(provenance, "is_stale")
