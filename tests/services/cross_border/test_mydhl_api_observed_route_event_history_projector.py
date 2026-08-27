from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
import inspect
from pathlib import Path

import pytest

from app.services.cross_border.mydhl_api_observed_route_event_history_projector import (
    project_mydhl_api_tracking_events,
)
from app.services.cross_border.observed_route_event_history import (
    ObservedRouteEventHistory,
    ObservedRouteEventHistoryCompleteness,
    ObservedRouteEventHistoryOrdering,
    ObservedRouteEventLocation,
    ObservedRouteEventScope,
)
from app.services.cross_border.provenance import EvidenceProvenance


SOURCE_ID = "candidate:shipping:mydhl-api"

EXPECTED_CONSTRAINTS = (
    "history_completeness_not_documented",
    "chronological_order_not_documented",
    "stable_event_identity_not_documented",
    "provider_recorded_time_not_documented",
    "event_level_actor_identity_not_documented",
    "duplicate_and_revision_semantics_not_documented",
    "pagination_and_truncation_semantics_not_documented",
    "provider_freshness_semantics_not_documented",
    "temporal_format_constraints_unresolved",
    "service_area_semantics_partially_unresolved",
)


def provenance(
    source_id: str = SOURCE_ID,
) -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id=source_id,
        source_type="api",
    )


def project(
    events: object,
    *,
    tracking_number: object = " tracking-123 ",
    collection_scope: object = ObservedRouteEventScope.SHIPMENT,
    provenance_value: object | None = None,
) -> ObservedRouteEventHistory:
    source_provenance = (
        provenance()
        if provenance_value is None
        else provenance_value
    )

    return project_mydhl_api_tracking_events(
        {"events": events},
        tracking_number=tracking_number,  # type: ignore[arg-type]
        collection_scope=collection_scope,  # type: ignore[arg-type]
        provenance=source_provenance,  # type: ignore[arg-type]
    )


def test_at_01_minimal_mapping_with_empty_events_is_valid() -> None:
    result = project_mydhl_api_tracking_events(
        {"events": []},
        tracking_number="tracking-123",
        collection_scope=ObservedRouteEventScope.SHIPMENT,
        provenance=provenance(),
    )

    assert result.events == ()
    assert result.tracking_number == "tracking-123"


def test_at_02_tuple_valued_empty_events_is_accepted() -> None:
    assert project(()).events == ()


@pytest.mark.parametrize(
    "response",
    (
        [],
        (),
        "events",
        None,
    ),
)
def test_at_03_wrong_top_level_response_type_raises(
    response: object,
) -> None:
    with pytest.raises(TypeError):
        project_mydhl_api_tracking_events(
            response,  # type: ignore[arg-type]
            tracking_number="tracking-123",
            collection_scope=ObservedRouteEventScope.SHIPMENT,
            provenance=provenance(),
        )


def test_at_04_missing_events_key_raises() -> None:
    with pytest.raises(
        ValueError,
        match="events key",
    ):
        project_mydhl_api_tracking_events(
            {},
            tracking_number="tracking-123",
            collection_scope=ObservedRouteEventScope.SHIPMENT,
            provenance=provenance(),
        )


@pytest.mark.parametrize(
    "events",
    (
        None,
        {},
        "events",
        1,
    ),
)
def test_at_05_non_list_or_tuple_events_raises(
    events: object,
) -> None:
    with pytest.raises(TypeError):
        project(events)


@pytest.mark.parametrize(
    "event",
    (
        "event",
        1,
        None,
        [],
    ),
)
def test_at_06_wrong_event_element_type_raises(
    event: object,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"events\[0\]",
    ):
        project([event])


@pytest.mark.parametrize(
    "tracking_number",
    (
        1,
        None,
        [],
    ),
)
def test_at_07_wrong_tracking_number_type_raises(
    tracking_number: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [],
            tracking_number=tracking_number,
        )


def test_at_08_tracking_number_is_trimmed_and_required() -> None:
    result = project(
        [],
        tracking_number="  tracking-123  ",
    )

    assert result.tracking_number == "tracking-123"

    with pytest.raises(ValueError):
        project(
            [],
            tracking_number="   ",
        )


@pytest.mark.parametrize(
    "collection_scope",
    (
        "shipment",
        None,
        1,
    ),
)
def test_at_09_wrong_collection_scope_type_raises(
    collection_scope: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [],
            collection_scope=collection_scope,
        )


def test_at_10_shipment_scope_uses_tracking_reference() -> None:
    result = project(
        [{"typeCode": "PU"}],
        tracking_number="  shipment-123  ",
        collection_scope=ObservedRouteEventScope.SHIPMENT,
    )

    item = result.events[0]

    assert item.scope is ObservedRouteEventScope.SHIPMENT
    assert item.scope_reference == "shipment-123"


def test_at_11_piece_scope_uses_tracking_reference() -> None:
    result = project(
        [{"typeCode": "PU"}],
        tracking_number="  piece-123  ",
        collection_scope=ObservedRouteEventScope.PIECE,
    )

    item = result.events[0]

    assert item.scope is ObservedRouteEventScope.PIECE
    assert item.scope_reference == "piece-123"


def test_at_12_package_scope_is_rejected() -> None:
    with pytest.raises(ValueError):
        project(
            [],
            collection_scope=ObservedRouteEventScope.PACKAGE,
        )


def test_at_13_unknown_scope_is_rejected() -> None:
    with pytest.raises(ValueError):
        project(
            [],
            collection_scope=ObservedRouteEventScope.UNKNOWN,
        )


@pytest.mark.parametrize(
    "provenance_value",
    (
        "provenance",
        object(),
        1,
    ),
)
def test_at_14_wrong_provenance_type_raises(
    provenance_value: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [],
            provenance_value=provenance_value,
        )

    with pytest.raises(ValueError):
        project(
            [],
            provenance_value=provenance(
                "candidate:shipping:dhl-unified-tracking"
            ),
        )


def test_at_15_type_code_maps_to_provider_event_code() -> None:
    result = project(
        [{"typeCode": "  PU  "}],
    )

    assert result.events[0].provider_event_code == "PU"


def test_at_16_description_maps_to_raw_status_description() -> None:
    result = project(
        [{"description": "  Shipment delivered  "}],
    )

    assert result.events[0].raw_status_description == (
        "Shipment delivered"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("typeCode", 1),
        ("typeCode", []),
        ("description", 1),
        ("description", {}),
    ),
)
def test_at_17_wrong_code_or_description_type_raises(
    field: str,
    value: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [
                {
                    "typeCode": "PU",
                    field: value,
                }
            ]
        )


def test_at_18_unsupported_event_identity_fields_remain_absent() -> None:
    result = project(
        [{"typeCode": "PU"}],
    )

    item = result.events[0]

    assert item.provider_event_id is None
    assert item.raw_status is None
    assert item.source_sequence is None
    assert item.relationships == ()
    assert item.actor is None
    assert item.provenance is None
    assert item.recorded_at is None
    assert item.recorded_at_raw is None


def test_at_19_occurred_at_always_remains_none() -> None:
    result = project(
        [
            {
                "date": "2026-08-27",
                "time": "12:34:56",
                "GMTOffset": "+09:00",
            }
        ]
    )

    assert result.events[0].occurred_at is None


def test_at_20_complete_temporal_raw_composite_is_exact() -> None:
    result = project(
        [
            {
                "date": "2026-08-27",
                "time": "12:34:56",
                "GMTOffset": "+09:00",
            }
        ]
    )

    assert result.events[0].occurred_at_raw == (
        "date:10:2026-08-27|"
        "time:8:12:34:56|"
        "GMTOffset:6:+09:00"
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    (
        (
            {"date": "2026-08-27"},
            (
                "date:10:2026-08-27|"
                "time:-1:|"
                "GMTOffset:-1:"
            ),
        ),
        (
            {"time": "12:34"},
            (
                "date:-1:|"
                "time:5:12:34|"
                "GMTOffset:-1:"
            ),
        ),
        (
            {"GMTOffset": "+09:00"},
            (
                "date:-1:|"
                "time:-1:|"
                "GMTOffset:6:+09:00"
            ),
        ),
    ),
)
def test_at_21_missing_temporal_components_use_minus_one(
    source: dict[str, object],
    expected: str,
) -> None:
    result = project([source])

    assert result.events[0].occurred_at_raw == expected


def test_at_22_temporal_delimiters_are_length_framed() -> None:
    result = project(
        [
            {
                "date": "a|b",
                "time": "c:d",
                "GMTOffset": "+0|:0",
            }
        ]
    )

    assert result.events[0].occurred_at_raw == (
        "date:3:a|b|"
        "time:3:c:d|"
        "GMTOffset:5:+0|:0"
    )


@pytest.mark.parametrize(
    "field",
    (
        "date",
        "time",
        "GMTOffset",
    ),
)
@pytest.mark.parametrize(
    "value",
    (
        1,
        [],
        {},
    ),
)
def test_at_23_wrong_temporal_component_type_raises(
    field: str,
    value: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [
                {
                    "typeCode": "PU",
                    field: value,
                }
            ]
        )


@pytest.mark.parametrize(
    "temporal_fields",
    (
        {},
        {
            "date": None,
            "time": None,
            "GMTOffset": None,
        },
        {
            "date": " ",
            "time": "",
            "GMTOffset": "   ",
        },
    ),
)
def test_at_24_absent_or_empty_temporal_values_produce_none(
    temporal_fields: dict[str, object],
) -> None:
    source = {
        "typeCode": "PU",
        **temporal_fields,
    }

    result = project([source])

    assert result.events[0].occurred_at_raw is None
    assert result.events[0].occurred_at is None


@pytest.mark.parametrize(
    "source",
    (
        {"typeCode": "PU"},
        {
            "typeCode": "PU",
            "serviceArea": None,
        },
        {
            "typeCode": "PU",
            "serviceArea": [],
        },
        {
            "typeCode": "PU",
            "serviceArea": (),
        },
    ),
)
def test_at_25_empty_service_area_produces_no_location(
    source: dict[str, object],
) -> None:
    result = project([source])

    assert result.events[0].location is None


@pytest.mark.parametrize(
    "service_area",
    (
        {},
        "SEOUL",
        1,
    ),
)
def test_at_26_wrong_service_area_collection_type_raises(
    service_area: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [
                {
                    "typeCode": "PU",
                    "serviceArea": service_area,
                }
            ]
        )


@pytest.mark.parametrize(
    "service_area",
    (
        [
            {"description": "A"},
            {"description": "B"},
        ],
        (
            {"description": "A"},
            {"description": "B"},
        ),
    ),
)
def test_at_27_multiple_service_area_items_raise(
    service_area: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="at most one",
    ):
        project(
            [
                {
                    "typeCode": "PU",
                    "serviceArea": service_area,
                }
            ]
        )


@pytest.mark.parametrize(
    "item",
    (
        "SEOUL",
        1,
        [],
    ),
)
def test_at_28_wrong_service_area_item_type_raises(
    item: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [
                {
                    "typeCode": "PU",
                    "serviceArea": [item],
                }
            ]
        )


def test_at_29_description_creates_raw_only_location() -> None:
    result = project(
        [
            {
                "serviceArea": [
                    {
                        "description": "  SEOUL SERVICE AREA  ",
                    }
                ]
            }
        ]
    )

    location = result.events[0].location

    assert location == ObservedRouteEventLocation(
        raw_description="SEOUL SERVICE AREA",
    )
    assert location.country_code is None
    assert location.subdivision_code is None
    assert location.locality is None
    assert location.postal_code is None
    assert location.facility_code is None
    assert location.facility_name is None


def test_at_30_service_area_code_is_metadata_only() -> None:
    result = project(
        [
            {
                "typeCode": "PU",
                "serviceArea": [
                    {
                        "code": "  SEL  ",
                    }
                ],
            }
        ]
    )

    item = result.events[0]

    assert item.location is None
    assert dict(item.metadata) == {
        "service_area_code": "SEL",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("description", 1),
        ("description", []),
        ("code", 1),
        ("code", {}),
    ),
)
def test_at_31_wrong_service_area_field_type_raises(
    field: str,
    value: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [
                {
                    "typeCode": "PU",
                    "serviceArea": [
                        {
                            field: value,
                        }
                    ],
                }
            ]
        )


@pytest.mark.parametrize(
    "remarks",
    (
        "remark",
        {},
        1,
        ["valid", 1],
        ("valid", None),
    ),
)
def test_at_32_wrong_remarks_collection_or_item_type_raises(
    remarks: object,
) -> None:
    with pytest.raises(TypeError):
        project(
            [
                {
                    "typeCode": "PU",
                    "remarks": remarks,
                }
            ]
        )


@pytest.mark.parametrize(
    "remarks",
    (
        [
            " first ",
            "",
            "same",
            "  ",
            "same",
            " last ",
        ],
        (
            " first ",
            "",
            "same",
            "  ",
            "same",
            " last ",
        ),
    ),
)
def test_at_33_remarks_normalization_preserves_order_and_duplicates(
    remarks: object,
) -> None:
    result = project(
        [
            {
                "typeCode": "PU",
                "remarks": remarks,
            }
        ]
    )

    assert dict(result.events[0].metadata) == {
        "remarks": (
            "first",
            "same",
            "same",
            "last",
        )
    }


def test_at_34_only_authorized_metadata_keys_are_emitted() -> None:
    result = project(
        [
            {
                "typeCode": "PU",
                "serviceArea": [
                    {
                        "code": "SEL",
                        "unknownServiceAreaKey": "ignored",
                    }
                ],
                "remarks": [
                    "one",
                    "two",
                ],
                "unknownEventKey": "ignored",
            }
        ]
    )

    assert dict(result.events[0].metadata) == {
        "service_area_code": "SEL",
        "remarks": (
            "one",
            "two",
        ),
    }


@pytest.mark.parametrize(
    "source",
    (
        {
            "serviceArea": [
                {
                    "code": "SEL",
                }
            ],
        },
        {
            "remarks": [
                "metadata only",
            ],
        },
        {
            "serviceArea": [
                {
                    "code": "SEL",
                }
            ],
            "remarks": [
                "metadata only",
            ],
        },
    ),
)
def test_at_35_metadata_only_event_fails_minimum_content(
    source: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="no supported minimum content",
    ):
        project([source])


@pytest.mark.parametrize(
    "source",
    (
        {},
        {
            "typeCode": " ",
            "description": "",
        },
        {
            "date": " ",
            "time": "",
            "GMTOffset": "   ",
        },
        {
            "serviceArea": [
                {
                    "description": " ",
                    "code": "",
                }
            ],
            "remarks": [
                "",
                "   ",
            ],
        },
    ),
)
def test_at_36_empty_or_whitespace_content_raises(
    source: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="no supported minimum content",
    ):
        project([source])


def test_at_37_invalid_event_makes_projection_atomic() -> None:
    response = {
        "events": [
            {
                "typeCode": "A",
            },
            {
                "remarks": [
                    "metadata only",
                ],
            },
            {
                "typeCode": "C",
            },
        ]
    }

    with pytest.raises(
        ValueError,
        match=r"events\[1\]",
    ):
        project_mydhl_api_tracking_events(
            response,
            tracking_number="tracking-123",
            collection_scope=ObservedRouteEventScope.SHIPMENT,
            provenance=provenance(),
        )


def test_at_38_source_order_and_duplicates_are_preserved() -> None:
    result = project(
        [
            {
                "typeCode": "A",
            },
            {
                "typeCode": "B",
            },
            {
                "typeCode": "A",
            },
        ]
    )

    assert tuple(
        item.provider_event_code
        for item in result.events
    ) == (
        "A",
        "B",
        "A",
    )
    assert len(result.events) == 3


def test_at_39_reporting_source_identity_is_exact() -> None:
    assert project([]).reporting_source_id == SOURCE_ID


def test_at_40_history_defaults_are_conservative() -> None:
    result = project(
        [{"typeCode": "PU"}],
    )

    assert result.completeness is (
        ObservedRouteEventHistoryCompleteness.UNKNOWN
    )
    assert result.ordering is (
        ObservedRouteEventHistoryOrdering.SOURCE_ORDER
    )


def test_at_41_pagination_fields_remain_none() -> None:
    result = project(
        [{"typeCode": "PU"}],
    )

    assert result.has_more is None
    assert result.next_page_token is None


def test_at_42_exact_ten_item_constraint_tuple_is_emitted() -> None:
    result = project([])

    assert result.constraints == EXPECTED_CONSTRAINTS
    assert len(result.constraints) == 10


def test_at_43_exact_caller_provenance_is_reused() -> None:
    source_provenance = provenance()

    result = project(
        [],
        provenance_value=source_provenance,
    )

    assert result.provenance is source_provenance


def test_at_44_canonical_result_is_immutable() -> None:
    result = project(
        [
            {
                "typeCode": "PU",
                "remarks": [
                    "before",
                ],
            }
        ]
    )

    with pytest.raises(FrozenInstanceError):
        result.tracking_number = "changed"

    with pytest.raises(FrozenInstanceError):
        result.events[0].provider_event_code = "changed"

    with pytest.raises(TypeError):
        result.events[0].metadata["remarks"] = ("changed",)

    assert isinstance(result.events, tuple)


def test_at_45_unknown_keys_do_not_leak() -> None:
    result = project(
        [
            {
                "typeCode": "PU",
                "unknownEventKey": "secret",
                "anotherUnknownKey": {
                    "nested": "ignored",
                },
            }
        ]
    )

    item = result.events[0]

    assert dict(item.metadata) == {}
    assert not hasattr(item, "unknownEventKey")
    assert "secret" not in repr(item)
    assert "nested" not in repr(item)


def test_at_46_direct_module_has_one_public_function() -> None:
    module = __import__(
        (
            "app.services.cross_border."
            "mydhl_api_observed_route_event_history_projector"
        ),
        fromlist=["*"],
    )

    public_functions = [
        name
        for name, value in inspect.getmembers(
            module,
            inspect.isfunction,
        )
        if not name.startswith("_")
    ]

    assert public_functions == [
        "project_mydhl_api_tracking_events",
    ]

    source = Path(
        "app/services/cross_border/"
        "mydhl_api_observed_route_event_history_projector.py"
    ).read_text(
        encoding="utf-8",
    )

    tree = ast.parse(source)

    public_definitions = [
        node.name
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and not node.name.startswith("_")
    ]

    assert public_definitions == [
        "project_mydhl_api_tracking_events",
    ]


def test_at_47_package_export_remains_absent() -> None:
    package_path = Path(
        "app/services/cross_border/__init__.py"
    )
    package_source = package_path.read_text(
        encoding="utf-8",
    )

    assert (
        "mydhl_api_observed_route_event_history_projector"
        not in package_source
    )
    assert (
        "project_mydhl_api_tracking_events"
        not in package_source
    )

    package = __import__(
        "app.services.cross_border",
        fromlist=["*"],
    )

    assert not hasattr(
        package,
        "project_mydhl_api_tracking_events",
    )


def test_at_48_forbidden_dependencies_remain_absent() -> None:
    source = Path(
        "app/services/cross_border/"
        "mydhl_api_observed_route_event_history_projector.py"
    ).read_text(
        encoding="utf-8",
    ).lower()

    forbidden = (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "webhook",
        "polling",
        "external_evidence_ingress",
        "external_evidence_projection",
        "registry",
        "persistence",
        "app.main",
        "streamlit",
        "select_provider",
        "fallback_provider",
    )

    for token in forbidden:
        assert token not in source
