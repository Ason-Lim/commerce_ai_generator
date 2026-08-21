from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def test_provenance_preserves_required_identity() -> None:
    provenance = EvidenceProvenance(
        source_id="amazon-us",
        source_type="marketplace",
    )

    assert provenance.source_id == "amazon-us"
    assert provenance.source_type == "marketplace"


def test_provenance_normalizes_outer_whitespace() -> None:
    provenance = EvidenceProvenance(
        source_id=" amazon-us ",
        source_type=" marketplace ",
        record_id=" sku-001 ",
        source_reference=" https://example.test/item/1 ",
        retrieved_at=" 2026-08-21T22:59:00+09:00 ",
        effective_at=" 2026-08-21T22:58:00+09:00 ",
    )

    assert provenance.source_id == "amazon-us"
    assert provenance.source_type == "marketplace"
    assert provenance.record_id == "sku-001"
    assert (
        provenance.source_reference
        == "https://example.test/item/1"
    )
    assert (
        provenance.retrieved_at
        == "2026-08-21T22:59:00+09:00"
    )
    assert (
        provenance.effective_at
        == "2026-08-21T22:58:00+09:00"
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "source_id",
        "source_type",
    ],
)
def test_required_provenance_identity_rejects_blank(
    field_name: str,
) -> None:
    values = {
        "source_id": "source-001",
        "source_type": "marketplace",
    }

    values[field_name] = "   "

    with pytest.raises(ValueError):
        EvidenceProvenance(
            **values,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "record_id",
        "source_reference",
        "retrieved_at",
        "effective_at",
    ],
)
def test_optional_blank_fields_normalize_to_none(
    field_name: str,
) -> None:
    values = {
        "source_id": "source-001",
        "source_type": "marketplace",
        field_name: "   ",
    }

    provenance = EvidenceProvenance(
        **values,
    )

    assert getattr(
        provenance,
        field_name,
    ) is None


def test_provenance_is_immutable() -> None:
    provenance = EvidenceProvenance(
        source_id="source-001",
        source_type="marketplace",
    )

    with pytest.raises(FrozenInstanceError):
        provenance.source_id = "changed"


def test_metadata_is_defensively_copied() -> None:
    metadata = {
        "request_id": "req-001",
    }

    provenance = EvidenceProvenance(
        source_id="source-001",
        source_type="marketplace",
        metadata=metadata,
    )

    metadata["request_id"] = "changed"

    assert (
        provenance.metadata["request_id"]
        == "req-001"
    )


def test_metadata_is_read_only() -> None:
    provenance = EvidenceProvenance(
        source_id="source-001",
        source_type="marketplace",
        metadata={
            "request_id": "req-001",
        },
    )

    with pytest.raises(TypeError):
        provenance.metadata[
            "request_id"
        ] = "changed"


def test_retrieved_and_effective_time_are_distinct() -> None:
    provenance = EvidenceProvenance(
        source_id="regulatory-source",
        source_type="regulatory",
        retrieved_at="2026-08-21T23:00:00+09:00",
        effective_at="2026-08-01T00:00:00+09:00",
    )

    assert (
        provenance.retrieved_at
        != provenance.effective_at
    )


def test_provenance_does_not_assign_freshness_state() -> None:
    provenance = EvidenceProvenance(
        source_id="source-001",
        source_type="marketplace",
    )

    assert not hasattr(
        provenance,
        "freshness"
    )

    assert not hasattr(
        provenance,
        "is_stale"
    )
