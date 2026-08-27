from dataclasses import FrozenInstanceError
import ast
import inspect
from pathlib import Path

import pytest

from app.services.cross_border import (
    ObservedRouteEvent,
    ObservedRouteEventHistory,
    ObservedRouteEventHistoryCompleteness,
    ObservedRouteEventHistoryOrdering,
    ObservedRouteEventLocation,
    ObservedRouteEventScope,
)
from app.services.cross_border.provenance import EvidenceProvenance
from app.services.cross_border.shipstation_v2_observed_route_event_history_projector import (
    project_shipstation_v2_tracking_log,
)


SOURCE_ID = "candidate:shipping:shipstation-api"


def provenance(source_id: str = SOURCE_ID) -> EvidenceProvenance:
    return EvidenceProvenance(source_id=source_id, source_type="api")


def project(events: object, **changes: object) -> ObservedRouteEventHistory:
    values = {
        "tracking_number": " tracking ",
        "provenance": provenance(),
    }
    values.update(changes)
    return project_shipstation_v2_tracking_log({"events": events}, **values)


def test_at_01_exact_function_signature() -> None:
    signature = inspect.signature(project_shipstation_v2_tracking_log)
    assert tuple(signature.parameters) == (
        "response", "tracking_number", "provenance", "carrier_code"
    )
    assert signature.parameters["response"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in ("tracking_number", "provenance", "carrier_code")
    )
    assert signature.return_annotation in (
        ObservedRouteEventHistory,
        "ObservedRouteEventHistory",
    )


def test_at_02_fixed_reporting_source_identity() -> None:
    assert project([]).reporting_source_id == SOURCE_ID


@pytest.mark.parametrize("source_id", ("shipengine", "shipstation-v1", "other"))
def test_at_03_mismatched_and_adjacent_source_rejected(source_id: str) -> None:
    with pytest.raises(ValueError):
        project([], provenance=provenance(source_id))


def test_at_04_response_mapping_required() -> None:
    assert project_shipstation_v2_tracking_log(
        {"events": []}, tracking_number="t", provenance=provenance()
    ).events == ()
    with pytest.raises(TypeError):
        project_shipstation_v2_tracking_log(
            [], tracking_number="t", provenance=provenance()
        )


def test_at_05_tracking_number_validation_and_normalization() -> None:
    assert project([]).tracking_number == "tracking"
    with pytest.raises(ValueError):
        project([], tracking_number=" ")
    with pytest.raises(TypeError):
        project([], tracking_number=1)


def test_at_06_carrier_code_validation_and_normalization() -> None:
    assert project([], carrier_code=" carrier ").carrier_reference == "carrier"
    assert project([], carrier_code=" ").carrier_reference is None
    with pytest.raises(TypeError):
        project([], carrier_code=1)


def test_at_07_provenance_reused_and_type_checked() -> None:
    item = provenance()
    assert project([], provenance=item).provenance is item
    with pytest.raises(TypeError):
        project([], provenance=object())


def test_at_08_events_key_is_required() -> None:
    with pytest.raises(ValueError):
        project_shipstation_v2_tracking_log(
            {}, tracking_number="t", provenance=provenance()
        )


@pytest.mark.parametrize("events", ([], ()))
def test_at_09_event_list_and_tuple_are_accepted(events: object) -> None:
    assert project(events).events == ()
    with pytest.raises(TypeError):
        project({})


def test_at_10_present_empty_collection_is_valid() -> None:
    result = project([])
    assert result.events == ()
    assert result.completeness is ObservedRouteEventHistoryCompleteness.UNKNOWN


def test_at_11_event_elements_must_be_mappings() -> None:
    assert len(project([{"status_code": "x"}]).events) == 1
    with pytest.raises(TypeError, match=r"events\[0\]"):
        project([object()])


def test_at_12_status_code_maps_to_provider_event_code() -> None:
    assert project([{"status_code": " code "}]).events[0].provider_event_code == "code"


def test_at_13_carrier_status_code_maps_to_raw_status() -> None:
    assert project([{"carrier_status_code": " raw "}]).events[0].raw_status == "raw"


def test_at_14_carrier_description_maps_to_raw_description() -> None:
    item = project([{"carrier_status_description": " text "}]).events[0]
    assert item.raw_status_description == "text"


def test_at_15_country_code_maps_through_canonical_location() -> None:
    location = project([{"country_code": " kr "}]).events[0].location
    assert location is not None and location.country_code == "KR"


def test_at_16_company_name_maps_only_to_raw_location_description() -> None:
    item = project([{"company_name": " Depot "}]).events[0]
    assert item.location == ObservedRouteEventLocation(raw_description="Depot")
    assert item.actor is None
    assert item.location.facility_name is None


def test_at_17_empty_location_fields_do_not_create_location() -> None:
    item = project([{"status_code": "x", "country_code": " ", "company_name": ""}]).events[0]
    assert item.location is None


def test_at_18_detail_code_is_preserved_in_metadata() -> None:
    item = project([{"status_code": "x", "carrier_detail_code": " detail "}]).events[0]
    assert dict(item.metadata) == {"carrier_detail_code": "detail"}


def test_at_19_unsupported_fields_create_no_claims() -> None:
    item = project([{"status_code": "x", "timestamp": "now", "actor": "carrier"}]).events[0]
    assert item.occurred_at is None and item.actor is None
    assert "timestamp" not in item.metadata and "actor" not in item.metadata


@pytest.mark.parametrize(
    "event",
    (
        {"status_code": "x"},
        {"carrier_status_code": "x"},
        {"carrier_status_description": "x"},
        {"country_code": "kr"},
        {"company_name": "depot"},
    ),
)
def test_at_20_each_canonical_minimum_content_alternative_projects(
    event: dict[str, object],
) -> None:
    assert isinstance(project([event]).events[0], ObservedRouteEvent)


@pytest.mark.parametrize("event", ({}, {"unknown": "x"}, {"carrier_detail_code": "x"}))
def test_at_21_empty_or_unsupported_event_fails_with_index(
    event: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=r"events\[1\]"):
        project([{"status_code": "ok"}, event])


@pytest.mark.parametrize(
    "field",
    (
        "status_code", "carrier_status_code", "carrier_detail_code",
        "carrier_status_description", "country_code", "company_name",
    ),
)
def test_at_22_supported_source_fields_must_be_strings(field: str) -> None:
    with pytest.raises(TypeError, match=field):
        project([{field: 1}])


def test_at_23_event_defaults_remain_conservative() -> None:
    item = project([{"status_code": "x"}]).events[0]
    assert item.provider_event_id is None
    assert item.occurred_at is None and item.occurred_at_raw is None
    assert item.recorded_at is None and item.recorded_at_raw is None
    assert item.actor is None and item.scope is ObservedRouteEventScope.UNKNOWN
    assert item.scope_reference is None and item.source_sequence is None
    assert item.relationships == () and item.provenance is None


def test_at_24_history_defaults_are_conservative() -> None:
    result = project([])
    assert result.completeness is ObservedRouteEventHistoryCompleteness.UNKNOWN
    assert result.ordering is ObservedRouteEventHistoryOrdering.SOURCE_ORDER
    assert result.has_more is None and result.next_page_token is None
    assert result.freshness is None


def test_at_25_exact_constraint_tuple_and_order() -> None:
    assert project([]).constraints == (
        "history_completeness_not_documented",
        "chronological_order_not_documented",
        "event_occurrence_time_not_documented",
        "event_identity_not_documented",
        "provider_recorded_time_not_documented",
        "duplicate_and_revision_semantics_not_documented",
        "event_level_actor_identity_not_documented",
        "pagination_and_truncation_semantics_not_documented",
        "provider_freshness_semantics_not_documented",
    )


def test_at_26_source_order_is_preserved() -> None:
    result = project([{"status_code": "second"}, {"status_code": "first"}])
    assert tuple(item.provider_event_code for item in result.events) == ("second", "first")
    assert result.ordering is ObservedRouteEventHistoryOrdering.SOURCE_ORDER


def test_at_27_duplicate_events_are_preserved() -> None:
    source = {"status_code": "same"}
    result = project([source, source])
    assert len(result.events) == 2 and result.events[0] == result.events[1]


def test_at_28_later_input_mutation_cannot_change_output() -> None:
    source_event = {"status_code": "before", "carrier_detail_code": "d"}
    response = {"events": [source_event]}
    result = project_shipstation_v2_tracking_log(
        response, tracking_number="t", provenance=provenance()
    )
    source_event["status_code"] = "after"
    response["events"].clear()
    assert result.events[0].provider_event_code == "before"
    assert dict(result.events[0].metadata) == {"carrier_detail_code": "d"}


def test_at_29_invalid_event_prevents_partial_output() -> None:
    with pytest.raises(ValueError, match=r"events\[1\]"):
        project([{"status_code": "valid"}, {}])


def test_at_30_module_has_no_network_or_credentials_dependency() -> None:
    module_path = Path(
        "app/services/cross_border/shipstation_v2_observed_route_event_history_projector.py"
    )
    tree = ast.parse(module_path.read_text())
    names = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    }
    names.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert names.isdisjoint({"requests", "httpx", "urllib", "boto3"})
    assert not any(term in module_path.read_text().lower() for term in ("credential", "webhook", "polling"))


def test_at_31_module_has_no_registry_dependency() -> None:
    source = Path(
        "app/services/cross_border/shipstation_v2_observed_route_event_history_projector.py"
    ).read_text()
    assert "external_evidence_ingress" not in source
    assert "external_evidence_projection" not in source
    assert "registry" not in source.lower()


def test_at_32_projector_is_not_exported_from_package() -> None:
    import app.services.cross_border as package

    assert not hasattr(package, "project_shipstation_v2_tracking_log")
    assert "project_shipstation_v2_tracking_log" not in package.__all__


def test_at_33_no_serialization_persistence_or_api_surface() -> None:
    module = __import__(
        "app.services.cross_border.shipstation_v2_observed_route_event_history_projector",
        fromlist=["*"],
    )
    assert not any(
        hasattr(module, name)
        for name in ("to_dict", "serialize", "save", "persist", "router", "app")
    )


def test_at_34_existing_canonical_classes_are_reused() -> None:
    result = project([{"country_code": "kr"}])
    assert type(result) is ObservedRouteEventHistory
    assert type(result.events[0]) is ObservedRouteEvent
    assert type(result.events[0].location) is ObservedRouteEventLocation


def test_at_35_result_collections_and_metadata_are_immutable() -> None:
    result = project([{"status_code": "x", "carrier_detail_code": "d"}])
    assert isinstance(result.events, tuple)
    with pytest.raises(FrozenInstanceError):
        result.events[0].raw_status = "changed"
    with pytest.raises(TypeError):
        result.events[0].metadata["carrier_detail_code"] = "changed"


def test_at_36_projection_makes_no_inferred_claims() -> None:
    result = project([{"status_code": "delivered", "company_name": "Depot"}])
    item = result.events[0]
    assert item.provider_event_id is None
    assert item.occurred_at is None and item.recorded_at is None
    assert item.actor is None and item.scope is ObservedRouteEventScope.UNKNOWN
    assert item.relationships == ()
    assert item.location is not None
    assert item.location.facility_code is None and item.location.facility_name is None
    assert result.completeness is ObservedRouteEventHistoryCompleteness.UNKNOWN
    assert result.ordering is ObservedRouteEventHistoryOrdering.SOURCE_ORDER
