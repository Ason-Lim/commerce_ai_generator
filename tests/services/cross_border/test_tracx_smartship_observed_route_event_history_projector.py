import ast
import inspect
import subprocess
from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import app.services.cross_border.tracx_smartship_observed_route_event_history_projector as projector
from app.services.cross_border.observed_route_event_history import (
    ObservedRouteEventHistory,
    ObservedRouteEventHistoryCompleteness,
    ObservedRouteEventHistoryOrdering,
    ObservedRouteEventScope,
)
from app.services.cross_border.provenance import EvidenceProvenance


SOURCE_ID = "candidate:shipping-aggregator:tracx-smartship"
PROJECTOR_PATH = Path(
    "app/services/cross_border/"
    "tracx_smartship_observed_route_event_history_projector.py"
)
TEST_PATH = Path(
    "tests/services/cross_border/"
    "test_tracx_smartship_observed_route_event_history_projector.py"
)
CONSTRAINTS = (
    "history_completeness_not_documented",
    "chronological_order_not_documented",
    "stable_event_identity_not_documented",
    "stable_event_sequence_not_documented",
    "provider_recorded_time_not_documented",
    "event_level_actor_identity_not_documented",
    "event_level_carrier_identity_not_documented",
    "duplicate_and_revision_semantics_not_documented",
    "pagination_and_truncation_semantics_not_documented",
    "retention_and_update_latency_not_documented",
    "temporal_format_and_timezone_unresolved",
    "proof_of_delivery_identity_semantics_unresolved",
    "polling_webhook_surface_separation_required",
)


def provenance(source_id: str = SOURCE_ID) -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id=source_id,
        source_type="commerce-ai-evaluation",
        record_id="sealed-tracx-observation",
        metadata={"boundary": "polling-only"},
    )


def response(
    events: object = (),
    **correlations: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "tracking_history": events,
        "shipping_no": "SHIP-001",
    }
    value.update(correlations)
    return value


def project(
    value: Mapping[str, object],
    *,
    correlation_key: str = "shipping_no",
    correlation_value: str = "SHIP-001",
    evidence: EvidenceProvenance | None = None,
) -> ObservedRouteEventHistory:
    return projector.project_tracx_smartship_tracking_history(
        value,
        correlation_key=correlation_key,
        correlation_value=correlation_value,
        provenance=evidence or provenance(),
    )


def test_at_01_exact_public_signature() -> None:
    function = projector.project_tracx_smartship_tracking_history
    signature = inspect.signature(function)
    parameters = list(signature.parameters.values())
    assert function.__name__ == "project_tracx_smartship_tracking_history"
    assert [parameter.name for parameter in parameters] == [
        "response",
        "correlation_key",
        "correlation_value",
        "provenance",
    ]
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in parameters[1:]
    )
    assert parameters[0].annotation == Mapping[str, object]
    assert parameters[1].annotation is str
    assert parameters[2].annotation is str
    assert parameters[3].annotation is EvidenceProvenance
    assert signature.return_annotation is ObservedRouteEventHistory


def test_at_02_fixed_reporting_source_identity() -> None:
    result = project(response())
    assert result.reporting_source_id == SOURCE_ID


def test_at_03_wrong_provenance_type_raises_type_error() -> None:
    with pytest.raises(TypeError, match="provenance"):
        projector.project_tracx_smartship_tracking_history(
            response(),
            correlation_key="shipping_no",
            correlation_value="SHIP-001",
            provenance=object(),  # type: ignore[arg-type]
        )


def test_at_04_mismatched_provenance_source_raises_value_error() -> None:
    with pytest.raises(ValueError, match="source_id"):
        project(response(), evidence=provenance("candidate:shipping:adjacent"))


def test_at_05_exact_provenance_object_is_reused() -> None:
    evidence = provenance()
    result = project(response(), evidence=evidence)
    assert result.provenance is evidence
    assert dict(evidence.metadata) == {"boundary": "polling-only"}


def test_at_06_mapping_response_and_non_mapping_failure() -> None:
    class ResponseMapping(dict[str, object]):
        pass

    result = project(ResponseMapping(response()))
    assert result.events == ()
    with pytest.raises(TypeError, match="response"):
        project(None)  # type: ignore[arg-type]


def test_at_07_missing_tracking_history_raises_value_error() -> None:
    with pytest.raises(ValueError, match="tracking_history"):
        project({"shipping_no": "SHIP-001"})


@pytest.mark.parametrize("events", [None, {}, "events", 1])
def test_at_08_wrong_history_collection_type(events: object) -> None:
    with pytest.raises(TypeError, match="tracking_history"):
        project(response(events))


@pytest.mark.parametrize("events", [[], ()])
def test_at_09_empty_history_collection_is_valid(events: object) -> None:
    assert project(response(events)).events == ()


def test_at_10_non_mapping_event_has_indexed_error() -> None:
    with pytest.raises(TypeError, match=r"tracking_history\[1\]"):
        project(response([{"status": "FIRST"}, "invalid"]))


@pytest.mark.parametrize("key", [None, 1, " shipping_no", "SHIPPING_NO", "id"])
def test_at_11_correlation_key_is_exact(key: object) -> None:
    expected = TypeError if not isinstance(key, str) else ValueError
    with pytest.raises(expected, match="correlation_key"):
        project(response(), correlation_key=key)  # type: ignore[arg-type]


def test_at_12_correlation_value_failures_are_deterministic() -> None:
    with pytest.raises(TypeError, match="correlation_value"):
        project(response(), correlation_value=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="correlation_value"):
        project(response(), correlation_value="  ")
    with pytest.raises(TypeError):
        projector.project_tracx_smartship_tracking_history(
            response(),
            correlation_key="shipping_no",
            provenance=provenance(),
        )


@pytest.mark.parametrize(
    "selected",
    [
        {"tracking_history": []},
        {"tracking_history": [], "shipping_no": None},
        {"tracking_history": [], "shipping_no": "  "},
    ],
)
def test_at_13_selected_response_correlation_is_required(
    selected: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="shipping_no"):
        project(selected)


def test_at_14_selected_correlation_mismatch_raises_value_error() -> None:
    with pytest.raises(ValueError, match="does not match"):
        project(response(), correlation_value="SHIP-002")


@pytest.mark.parametrize("key", ["shipping_no", "ref_no", "qs_no"])
def test_at_15_wrong_recognized_correlation_type(key: str) -> None:
    with pytest.raises(TypeError, match=key):
        project(response(**{key: 7}))


def test_at_16_multiple_correlations_remain_separate() -> None:
    result = project(
        response(ref_no=" REF-2 ", qs_no=" QS-3 "),
    )
    assert dict(result.metadata) == {
        "shipping_no": "SHIP-001",
        "ref_no": "REF-2",
        "qs_no": "QS-3",
    }


def test_at_17_selected_correlation_only_populates_tracking_number() -> None:
    result = project(
        response(shipping_no=" SHIP-001 ", ref_no="REF-2"),
    )
    assert result.tracking_number == "SHIP-001"
    assert result.carrier_reference is None
    assert result.source_record_id is None
    assert result.request_correlation_id is None


def test_at_18_status_maps_to_raw_status() -> None:
    event = project(response([{"status": " Delivered "}])).events[0]
    assert event.raw_status == "Delivered"
    assert event.provider_event_code is None


def test_at_19_status_code_maps_to_provider_event_code() -> None:
    event = project(response([{"status_code": " D01 "}])).events[0]
    assert event.provider_event_code == "D01"
    assert event.raw_status is None


def test_at_20_details_map_to_raw_status_description() -> None:
    event = project(response([{"details": " Handed over "}])).events[0]
    assert event.raw_status_description == "Handed over"


def test_at_21_location_is_raw_description_only() -> None:
    location = project(response([{"location": " Seoul Hub "}])).events[0].location
    assert location is not None
    assert location.raw_description == "Seoul Hub"
    assert location.country_code is None
    assert location.subdivision_code is None
    assert location.locality is None
    assert location.postal_code is None
    assert location.facility_code is None
    assert location.facility_name is None


@pytest.mark.parametrize("location", [None, "", "  "])
def test_at_22_empty_location_creates_no_location(location: object) -> None:
    event = project(response([{"status": "IN_TRANSIT", "location": location}])).events[0]
    assert event.location is None


def test_at_23_date_maps_only_to_occurred_at_raw() -> None:
    event = project(response([{"date": " 2026/08/28 01:02 "}])).events[0]
    assert event.occurred_at_raw == "2026/08/28 01:02"
    assert event.occurred_at is None
    assert event.recorded_at is None
    assert event.recorded_at_raw is None


def test_at_24_canonical_temporal_instants_remain_none() -> None:
    event = project(response([{"date": "not-a-validated-date"}])).events[0]
    assert event.occurred_at is None
    assert event.recorded_at is None
    assert event.recorded_at_raw is None


@pytest.mark.parametrize("key", ["status", "status_code", "details", "location", "date"])
def test_at_25_wrong_supported_event_value_type(key: str) -> None:
    with pytest.raises(TypeError, match=key):
        project(response([{key: 7}]))


def test_at_26_supported_strings_are_trimmed_and_empty_omitted() -> None:
    event = project(
        response(
            [
                {
                    "status": " MOVING ",
                    "status_code": " ",
                    "details": " Detail ",
                    "location": " ",
                    "date": " raw-date ",
                }
            ]
        )
    ).events[0]
    assert event.raw_status == "MOVING"
    assert event.provider_event_code is None
    assert event.raw_status_description == "Detail"
    assert event.location is None
    assert event.occurred_at_raw == "raw-date"


def test_at_27_unknown_and_deferred_keys_do_not_leak() -> None:
    event = project(
        response(
            [
                {
                    "status": "MOVING",
                    "reason": "unsealed",
                    "auxiliary_tracking_code": "AUX",
                    "proof_of_delivery_reference": "POD",
                    "unknown": "value",
                }
            ]
        )
    ).events[0]
    assert dict(event.metadata) == {}
    assert not hasattr(event, "reason")
    assert not hasattr(event, "auxiliary_tracking_code")
    assert not hasattr(event, "proof_of_delivery_reference")


@pytest.mark.parametrize(
    "key",
    ["reason", "auxiliary_tracking_code", "proof_of_delivery_reference"],
)
def test_at_28_deferred_only_event_fails_minimum_content(key: str) -> None:
    with pytest.raises(ValueError, match=r"tracking_history\[0\]"):
        project(response([{key: "unsealed"}]))


@pytest.mark.parametrize(
    "event",
    [
        {},
        {"status": " ", "status_code": "", "details": None, "location": " "},
        {"unsupported": "value"},
    ],
)
def test_at_29_empty_or_unsupported_event_has_indexed_error(
    event: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=r"tracking_history\[0\]"):
        project(response([event]))


def test_at_30_multi_event_projection_fails_atomically() -> None:
    with pytest.raises(ValueError, match=r"tracking_history\[1\]"):
        project(response([{"status": "VALID"}, {"unknown": "invalid"}]))


def test_at_31_source_order_is_preserved() -> None:
    result = project(
        response(
            [
                {"status": "SECOND", "date": "2026-08-28T02:00"},
                {"status": "FIRST", "date": "2026-08-28T01:00"},
            ]
        )
    )
    assert [event.raw_status for event in result.events] == ["SECOND", "FIRST"]


def test_at_32_duplicate_entries_remain_separate() -> None:
    source_event = {"status": "DUPLICATE"}
    result = project(response([source_event, dict(source_event)]))
    assert len(result.events) == 2
    assert result.events[0] == result.events[1]
    assert result.events[0] is not result.events[1]


def test_at_33_raw_dates_do_not_trigger_chronological_sorting() -> None:
    result = project(response([{"date": "z-last"}, {"date": "a-first"}]))
    assert [event.occurred_at_raw for event in result.events] == [
        "z-last",
        "a-first",
    ]


def test_at_34_uninferred_event_fields_remain_absent() -> None:
    event = project(response([{"status": "OBSERVED"}])).events[0]
    assert event.provider_event_id is None
    assert event.actor is None
    assert event.scope is ObservedRouteEventScope.UNKNOWN
    assert event.scope_reference is None
    assert event.source_sequence is None
    assert event.relationships == ()
    assert event.provenance is None


def test_at_35_unknown_completeness_and_source_order() -> None:
    result = project(response())
    assert result.completeness is ObservedRouteEventHistoryCompleteness.UNKNOWN
    assert result.ordering is ObservedRouteEventHistoryOrdering.SOURCE_ORDER


def test_at_36_pagination_and_freshness_remain_none() -> None:
    result = project(response())
    assert result.has_more is None
    assert result.next_page_token is None
    assert result.freshness is None


def test_at_37_exact_ordered_constraint_tuple() -> None:
    assert project(response()).constraints == CONSTRAINTS
    assert len(CONSTRAINTS) == 13


def test_at_38_history_metadata_contains_only_correlations() -> None:
    source = response(ref_no=" REF ", qs_no=None)
    source["metadata"] = {"unsafe": "value"}
    source["caller"] = "ignored"
    result = project(source)
    assert dict(result.metadata) == {
        "shipping_no": "SHIP-001",
        "ref_no": "REF",
    }


def test_at_39_canonical_collections_and_metadata_are_immutable() -> None:
    result = project(response([{"status": "OBSERVED"}]))
    event = result.events[0]
    assert isinstance(result.events, tuple)
    assert isinstance(result.constraints, tuple)
    assert isinstance(event.relationships, tuple)
    with pytest.raises(TypeError):
        result.metadata["shipping_no"] = "MUTATED"  # type: ignore[index]
    with pytest.raises(TypeError):
        event.metadata["unsafe"] = "MUTATED"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        event.raw_status = "MUTATED"  # type: ignore[misc]


def test_at_40_source_mutation_cannot_change_output() -> None:
    source_event = {"status": " OBSERVED ", "location": " Seoul "}
    source = response([source_event], ref_no=" REF ")
    result = project(source)
    source_event["status"] = "MUTATED"
    source_event["location"] = "Busan"
    source["shipping_no"] = "MUTATED"
    source["ref_no"] = "MUTATED"
    assert result.events[0].raw_status == "OBSERVED"
    assert result.events[0].location is not None
    assert result.events[0].location.raw_description == "Seoul"
    assert result.tracking_number == "SHIP-001"
    assert dict(result.metadata) == {
        "shipping_no": "SHIP-001",
        "ref_no": "REF",
    }


def test_at_41_webhook_only_keys_create_no_attribution() -> None:
    with pytest.raises(ValueError, match="minimum content"):
        project(
            response(
                [
                    {
                        "Date": "2026-08-28T01:00:00+09:00",
                        "Carrier": "unattributed",
                        "Webhook": "delivery",
                    }
                ]
            )
        )


def test_at_42_multitracking_is_not_accepted_or_assembled() -> None:
    with pytest.raises(ValueError, match="tracking_history"):
        project(
            {
                "shipping_no": "SHIP-001",
                "MultiTracking": [{"tracking_history": [{"status": "X"}]}],
            }
        )


def test_at_43_direct_module_import_has_one_public_function() -> None:
    public_functions = {
        name
        for name, value in vars(projector).items()
        if not name.startswith("_") and inspect.isfunction(value)
    }
    assert public_functions == {"project_tracx_smartship_tracking_history"}


def test_at_44_provider_neutral_package_export_is_absent() -> None:
    import app.services.cross_border as package

    assert not hasattr(package, "project_tracx_smartship_tracking_history")
    package_source = Path(package.__file__).read_text(encoding="utf-8")
    assert "tracx_smartship_observed_route_event_history_projector" not in package_source


def test_at_45_registries_remain_unchanged() -> None:
    symbol = "project_tracx_smartship_tracking_history"
    matches = []
    for path in Path("app/services/cross_border").rglob("*.py"):
        if path == PROJECTOR_PATH:
            continue
        if symbol in path.read_text(encoding="utf-8"):
            matches.append(path)
    assert matches == []


def test_at_46_projector_dependency_boundary_is_static() -> None:
    tree = ast.parse(PROJECTOR_PATH.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imports == {
        "collections.abc",
        "app.services.cross_border.observed_route_event_history",
        "app.services.cross_border.provenance",
    }
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))


def test_at_47_canonical_models_are_reused_without_parallel_classes() -> None:
    local_classes = {
        name
        for name, value in vars(projector).items()
        if inspect.isclass(value) and value.__module__ == projector.__name__
    }
    assert local_classes == set()
    assert isinstance(project(response()), ObservedRouteEventHistory)


def test_at_48_pending_scope_is_exactly_two_files() -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert status == [f"?? {PROJECTOR_PATH}", f"?? {TEST_PATH}"]
