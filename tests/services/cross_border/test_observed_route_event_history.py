from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from enum import Enum

import pytest

from app.services.cross_border import (
    ObservedRouteEvent,
    ObservedRouteEventActor,
    ObservedRouteEventActorRole,
    ObservedRouteEventHistory,
    ObservedRouteEventHistoryCompleteness,
    ObservedRouteEventHistoryOrdering,
    ObservedRouteEventLocation,
    ObservedRouteEventRelationship,
    ObservedRouteEventRelationshipType,
    ObservedRouteEventScope,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
)
from app.services.cross_border.provenance import EvidenceProvenance


def provenance() -> EvidenceProvenance:
    return EvidenceProvenance(source_id="source", source_type="api")


def event(value: str = "event") -> ObservedRouteEvent:
    return ObservedRouteEvent(provider_event_id=value)


def history(**changes: object) -> ObservedRouteEventHistory:
    values = {
        "reporting_source_id": "source",
        "provenance": provenance(),
        "tracking_number": "tracking",
    }
    values.update(changes)
    return ObservedRouteEventHistory(**values)


def test_at_01_exact_enum_vocabularies_and_no_normalized_status() -> None:
    expected = {
        ObservedRouteEventHistoryCompleteness: ("complete", "partial", "unknown"),
        ObservedRouteEventHistoryOrdering: ("chronological", "source_order", "unknown"),
        ObservedRouteEventScope: ("shipment", "piece", "package", "unknown"),
        ObservedRouteEventActorRole: (
            "carrier", "postal_operator", "customs_authority",
            "fulfillment_provider", "shipping_aggregator", "tracking_provider",
            "facility", "unknown",
        ),
        ObservedRouteEventRelationshipType: (
            "duplicate_of", "corrects", "supersedes",
        ),
    }
    for enum_type, values in expected.items():
        assert issubclass(enum_type, (str, Enum))
        assert tuple(member.value for member in enum_type) == values
    assert not hasattr(ObservedRouteEvent, "normalized_status")


def test_at_02_conservative_enum_defaults() -> None:
    actor = ObservedRouteEventActor(actor_name="actor")
    item = event()
    aggregate = history()
    assert actor.actor_role is ObservedRouteEventActorRole.UNKNOWN
    assert item.scope is ObservedRouteEventScope.UNKNOWN
    assert aggregate.completeness is ObservedRouteEventHistoryCompleteness.UNKNOWN
    assert aggregate.ordering is ObservedRouteEventHistoryOrdering.UNKNOWN


def test_at_03_location_normalization_and_minimum_content() -> None:
    location = ObservedRouteEventLocation(
        country_code=" kr ", locality=" Seoul ", raw_description=" raw "
    )
    assert (location.country_code, location.locality, location.raw_description) == (
        "KR", "Seoul", "raw"
    )
    with pytest.raises(ValueError):
        ObservedRouteEventLocation(locality="  ")
    with pytest.raises(TypeError):
        ObservedRouteEventLocation(locality=1)


def test_at_04_actor_minimum_content_without_source_inference() -> None:
    assert ObservedRouteEventActor(actor_reference=" ref ").actor_reference == "ref"
    assert ObservedRouteEventActor(actor_name=" name ").actor_name == "name"
    with pytest.raises(ValueError):
        ObservedRouteEventActor(actor_name=" ")
    assert history().events == ()


@pytest.mark.parametrize("kind", tuple(ObservedRouteEventRelationshipType))
def test_at_05_relationship_validation(kind: ObservedRouteEventRelationshipType) -> None:
    relation = ObservedRouteEventRelationship(kind, " local ")
    assert relation.related_event_reference == "local"
    with pytest.raises(ValueError):
        ObservedRouteEventRelationship(kind, " ")
    with pytest.raises(TypeError):
        ObservedRouteEventRelationship("corrects", "local")


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("provider_event_id", "id"), ("provider_event_code", "code"),
        ("raw_status", "status"), ("raw_status_description", "description"),
        ("occurred_at", datetime(2026, 1, 1, tzinfo=timezone.utc)),
        ("occurred_at_raw", "unknown-zone"),
        ("recorded_at", datetime(2026, 1, 2, tzinfo=timezone.utc)),
        ("recorded_at_raw", "date-only"),
        ("location", ObservedRouteEventLocation(locality="Seoul")),
        ("actor", ObservedRouteEventActor(actor_name="carrier")),
    ),
)
def test_at_06_each_event_minimum_content_alternative(name: str, value: object) -> None:
    assert getattr(ObservedRouteEvent(**{name: value}), name) is not None
    with pytest.raises(ValueError):
        ObservedRouteEvent()


def test_at_07_provider_identity_preserved_without_manufacture() -> None:
    item = ObservedRouteEvent(provider_event_code=" code ")
    assert item.provider_event_id is None
    assert item.provider_event_code == "code"
    assert not hasattr(item, "canonical_event_id")


def test_at_08_raw_status_fields_stay_distinct() -> None:
    item = ObservedRouteEvent(raw_status_description=" delivered text ")
    assert item.raw_status is None
    assert item.raw_status_description == "delivered text"
    assert not hasattr(item, "delivery_state")


def test_at_09_aware_occurred_time_and_naive_rejection() -> None:
    aware = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=9)))
    assert ObservedRouteEvent(occurred_at=aware).occurred_at is aware
    with pytest.raises(ValueError):
        ObservedRouteEvent(occurred_at=datetime(2026, 1, 1))


def test_at_10_recorded_time_is_independent() -> None:
    aware = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item = ObservedRouteEvent(occurred_at=aware)
    assert item.recorded_at is None
    with pytest.raises(ValueError):
        ObservedRouteEvent(recorded_at=datetime(2026, 1, 1))


def test_at_11_raw_times_are_not_parsed_or_copied() -> None:
    item = ObservedRouteEvent(occurred_at_raw=" 2026-01-01 ")
    assert item.occurred_at_raw == "2026-01-01"
    assert item.occurred_at is None and item.recorded_at is None
    assert ObservedRouteEvent(recorded_at_raw=" raw ").recorded_at_raw == "raw"


def test_at_12_nested_types_are_checked_and_retained() -> None:
    location = ObservedRouteEventLocation(locality="Seoul")
    actor = ObservedRouteEventActor(actor_name="actor")
    relation = ObservedRouteEventRelationship(
        ObservedRouteEventRelationshipType.CORRECTS, "old"
    )
    item_provenance = provenance()
    item = ObservedRouteEvent(
        location=location, actor=actor, relationships=(relation,),
        provenance=item_provenance,
    )
    assert (item.location, item.actor, item.provenance) == (
        location, actor, item_provenance
    )
    for name, value in (("location", object()), ("actor", object()),
                        ("relationships", (object(),)), ("provenance", object())):
        with pytest.raises(TypeError):
            ObservedRouteEvent(provider_event_id="id", **{name: value})


def test_at_13_relationship_tuple_copy_order_and_duplicates() -> None:
    first = ObservedRouteEventRelationship(
        ObservedRouteEventRelationshipType.DUPLICATE_OF, "same"
    )
    values = [first, first]
    item = ObservedRouteEvent(provider_event_id="id", relationships=values)
    values.clear()
    assert item.relationships == (first, first)


def test_at_14_event_metadata_top_level_freeze_and_copy() -> None:
    values = {"key": "value"}
    item = ObservedRouteEvent(provider_event_id="id", metadata=values)
    values["key"] = "changed"
    assert item.metadata["key"] == "value"
    with pytest.raises(TypeError):
        item.metadata["new"] = "value"


def test_at_15_reporting_source_normalization_and_actor_separation() -> None:
    aggregate = history(reporting_source_id=" source ")
    assert aggregate.reporting_source_id == "source"
    with pytest.raises(ValueError):
        history(reporting_source_id=" ")
    assert aggregate.events == ()


def test_at_16_history_requires_existing_provenance() -> None:
    source = provenance()
    assert history(provenance=source).provenance is source
    for invalid in (None, object()):
        with pytest.raises(TypeError):
            history(provenance=invalid)


@pytest.mark.parametrize(
    "name",
    ("carrier_reference", "tracking_number", "source_record_id", "request_correlation_id"),
)
def test_at_17_each_correlation_reference_satisfies_invariant(name: str) -> None:
    values = {"tracking_number": None, name: " reference "}
    assert getattr(history(**values), name) == "reference"
    with pytest.raises(ValueError):
        history(tracking_number=" ")


def test_at_18_event_collection_copy_order_type_and_duplicates() -> None:
    first, second = event("one"), event("two")
    values = [first, second, first]
    aggregate = history(events=values)
    values.clear()
    assert aggregate.events == (first, second, first)
    with pytest.raises(TypeError):
        history(events=(object(),))


def test_at_19_empty_history_does_not_imply_complete() -> None:
    aggregate = history()
    assert aggregate.events == ()
    assert aggregate.completeness is ObservedRouteEventHistoryCompleteness.UNKNOWN


def test_at_20_explicit_completeness_preserved_without_promotion() -> None:
    for value in ObservedRouteEventHistoryCompleteness:
        assert history(completeness=value).completeness is value


def test_at_21_ordering_preserved_without_sorting() -> None:
    values = (event("two"), event("one"))
    for ordering in ObservedRouteEventHistoryOrdering:
        assert history(events=values, ordering=ordering).events == values


def test_at_22_has_more_requires_partial() -> None:
    assert history(
        has_more=True, completeness=ObservedRouteEventHistoryCompleteness.PARTIAL
    ).has_more is True
    for value in (
        ObservedRouteEventHistoryCompleteness.UNKNOWN,
        ObservedRouteEventHistoryCompleteness.COMPLETE,
    ):
        with pytest.raises(ValueError):
            history(has_more=True, completeness=value)


def test_at_23_page_token_requires_partial_and_empty_normalizes() -> None:
    assert history(
        next_page_token=" token ",
        completeness=ObservedRouteEventHistoryCompleteness.PARTIAL,
    ).next_page_token == "token"
    for value in (
        ObservedRouteEventHistoryCompleteness.UNKNOWN,
        ObservedRouteEventHistoryCompleteness.COMPLETE,
    ):
        with pytest.raises(ValueError):
            history(next_page_token="token", completeness=value)
    assert history(next_page_token=" ").next_page_token is None


def test_at_24_has_more_false_never_promotes_completeness() -> None:
    for value in ObservedRouteEventHistoryCompleteness:
        aggregate = history(has_more=False, completeness=value)
        assert aggregate.has_more is False and aggregate.completeness is value


def test_at_25_freshness_is_reused_without_evaluation() -> None:
    assert history(freshness=None).freshness is None
    freshness = EvidenceFreshness(EvidenceFreshnessState.UNKNOWN)
    assert history(freshness=freshness).freshness is freshness
    with pytest.raises(TypeError):
        history(freshness=object())


def test_at_26_constraints_normalize_validate_copy() -> None:
    values = [" first ", " ", "second"]
    aggregate = history(constraints=values)
    values.clear()
    assert aggregate.constraints == ("first", "second")
    with pytest.raises(TypeError):
        history(constraints=("valid", 1))


def test_at_27_history_metadata_top_level_freeze_and_copy() -> None:
    values = {"key": "value"}
    aggregate = history(metadata=values)
    values["key"] = "changed"
    assert aggregate.metadata["key"] == "value"
    with pytest.raises(TypeError):
        aggregate.metadata["new"] = "value"


@pytest.mark.parametrize(
    "value",
    (
        ObservedRouteEventLocation(locality="Seoul"),
        ObservedRouteEventActor(actor_name="actor"),
        ObservedRouteEventRelationship(
            ObservedRouteEventRelationshipType.CORRECTS, "event"
        ),
        event(),
        history(),
    ),
)
def test_at_28_all_dataclasses_are_frozen(value: object) -> None:
    with pytest.raises(FrozenInstanceError):
        value.arbitrary = "changed"


def test_at_29_all_ten_types_are_publicly_exported() -> None:
    import app.services.cross_border as package
    names = (
        "ObservedRouteEventHistoryCompleteness", "ObservedRouteEventHistoryOrdering",
        "ObservedRouteEventScope", "ObservedRouteEventActorRole",
        "ObservedRouteEventRelationshipType", "ObservedRouteEventLocation",
        "ObservedRouteEventActor", "ObservedRouteEventRelationship",
        "ObservedRouteEvent", "ObservedRouteEventHistory",
    )
    assert all(getattr(package, name) for name in names)
    assert all(name in package.__all__ for name in names)


def test_at_30_no_planned_route_fields_or_dependency() -> None:
    names = {item.name for item in fields(ObservedRouteEventHistory)}
    assert names.isdisjoint({"shipping_route", "route_type", "price", "duration", "availability"})


def test_at_31_exact_schema_and_no_serialization_or_persistence() -> None:
    assert tuple(item.name for item in fields(ObservedRouteEvent)) == (
        "provider_event_id", "provider_event_code", "raw_status",
        "raw_status_description", "occurred_at", "occurred_at_raw",
        "recorded_at", "recorded_at_raw", "location", "actor", "scope",
        "scope_reference", "source_sequence", "relationships", "provenance",
        "metadata",
    )
    assert tuple(item.name for item in fields(ObservedRouteEventHistory)) == (
        "reporting_source_id", "provenance", "events", "carrier_reference",
        "tracking_number", "source_record_id", "request_correlation_id",
        "completeness", "ordering", "has_more", "next_page_token", "freshness",
        "constraints", "metadata",
    )
    for name in ("canonical_event_id", "normalized_status", "to_dict", "from_dict", "save"):
        assert not hasattr(ObservedRouteEvent, name)


def test_at_32_repeated_similar_events_are_preserved() -> None:
    first, second = event("same"), event("same")
    aggregate = history(events=(first, second))
    assert len(aggregate.events) == 2
    assert aggregate.events[0] is first and aggregate.events[1] is second
