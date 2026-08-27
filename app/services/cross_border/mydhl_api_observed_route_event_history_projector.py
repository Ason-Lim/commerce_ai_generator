"""Project MyDHL tracking-event evidence into the canonical history."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.cross_border.observed_route_event_history import (
    ObservedRouteEvent,
    ObservedRouteEventHistory,
    ObservedRouteEventHistoryCompleteness,
    ObservedRouteEventHistoryOrdering,
    ObservedRouteEventLocation,
    ObservedRouteEventScope,
)
from app.services.cross_border.provenance import EvidenceProvenance


_REPORTING_SOURCE_ID = "candidate:shipping:mydhl-api"

_CONSTRAINTS = (
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


def _optional_source_string(
    name: str,
    value: object,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string or None")
    normalized = value.strip()
    return normalized or None


def _required_collection_scope(
    value: object,
) -> ObservedRouteEventScope:
    if not isinstance(value, ObservedRouteEventScope):
        raise TypeError(
            "collection_scope must be ObservedRouteEventScope"
        )
    if value not in (
        ObservedRouteEventScope.SHIPMENT,
        ObservedRouteEventScope.PIECE,
    ):
        raise ValueError(
            "collection_scope must be SHIPMENT or PIECE"
        )
    return value


def _temporal_raw(
    *,
    date: str | None,
    time: str | None,
    gmt_offset: str | None,
) -> str | None:
    values = (
        ("date", date),
        ("time", time),
        ("GMTOffset", gmt_offset),
    )

    if all(value is None for _, value in values):
        return None

    def frame(name: str, value: str | None) -> str:
        if value is None:
            return f"{name}:-1:"
        return f"{name}:{len(value)}:{value}"

    return "|".join(
        frame(name, value)
        for name, value in values
    )


def _service_area(
    value: object,
    *,
    index: int,
) -> tuple[ObservedRouteEventLocation | None, str | None]:
    if value is None:
        return None, None

    if not isinstance(value, (list, tuple)):
        raise TypeError(
            f"events[{index}].serviceArea must be a list or tuple"
        )

    if len(value) > 1:
        raise ValueError(
            f"events[{index}].serviceArea must contain at most one element"
        )

    if not value:
        return None, None

    item = value[0]

    if not isinstance(item, Mapping):
        raise TypeError(
            f"events[{index}].serviceArea[0] must be a mapping"
        )

    description = _optional_source_string(
        f"events[{index}].serviceArea[0].description",
        item.get("description"),
    )
    code = _optional_source_string(
        f"events[{index}].serviceArea[0].code",
        item.get("code"),
    )

    location = None

    if description is not None:
        location = ObservedRouteEventLocation(
            raw_description=description,
        )

    return location, code


def _remarks(
    value: object,
    *,
    index: int,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(value, (list, tuple)):
        raise TypeError(
            f"events[{index}].remarks must be a list or tuple"
        )

    normalized: list[str] = []

    for item_index, item in enumerate(value):
        if not isinstance(item, str):
            raise TypeError(
                f"events[{index}].remarks[{item_index}] "
                "must be a string"
            )

        trimmed = item.strip()

        if trimmed:
            normalized.append(trimmed)

    return tuple(normalized)


def _project_event(
    source_event: Mapping[str, object],
    *,
    index: int,
    collection_scope: ObservedRouteEventScope,
    tracking_number: str,
) -> ObservedRouteEvent:
    provider_event_code = _optional_source_string(
        f"events[{index}].typeCode",
        source_event.get("typeCode"),
    )
    raw_status_description = _optional_source_string(
        f"events[{index}].description",
        source_event.get("description"),
    )
    date = _optional_source_string(
        f"events[{index}].date",
        source_event.get("date"),
    )
    time = _optional_source_string(
        f"events[{index}].time",
        source_event.get("time"),
    )
    gmt_offset = _optional_source_string(
        f"events[{index}].GMTOffset",
        source_event.get("GMTOffset"),
    )

    location, service_area_code = _service_area(
        source_event.get("serviceArea"),
        index=index,
    )
    remarks = _remarks(
        source_event.get("remarks"),
        index=index,
    )
    occurred_at_raw = _temporal_raw(
        date=date,
        time=time,
        gmt_offset=gmt_offset,
    )

    if all(
        value is None
        for value in (
            provider_event_code,
            raw_status_description,
            occurred_at_raw,
            location,
        )
    ):
        raise ValueError(
            f"events[{index}] has no supported minimum content"
        )

    metadata: dict[str, object] = {}

    if service_area_code is not None:
        metadata["service_area_code"] = service_area_code

    if remarks:
        metadata["remarks"] = remarks

    return ObservedRouteEvent(
        provider_event_code=provider_event_code,
        raw_status_description=raw_status_description,
        occurred_at=None,
        occurred_at_raw=occurred_at_raw,
        location=location,
        scope=collection_scope,
        scope_reference=tracking_number,
        metadata=metadata,
    )


def project_mydhl_api_tracking_events(
    response: Mapping[str, object],
    *,
    tracking_number: str,
    collection_scope: ObservedRouteEventScope,
    provenance: EvidenceProvenance,
) -> ObservedRouteEventHistory:
    """Project one already-acquired MyDHL tracking-event response."""
    if not isinstance(response, Mapping):
        raise TypeError("response must be a mapping")

    if not isinstance(tracking_number, str):
        raise TypeError("tracking_number must be a string")

    normalized_tracking_number = tracking_number.strip()

    if not normalized_tracking_number:
        raise ValueError("tracking_number must be non-empty")

    normalized_scope = _required_collection_scope(
        collection_scope
    )

    if not isinstance(provenance, EvidenceProvenance):
        raise TypeError("provenance must be EvidenceProvenance")

    if provenance.source_id != _REPORTING_SOURCE_ID:
        raise ValueError(
            "provenance source_id does not match MyDHL API"
        )

    if "events" not in response:
        raise ValueError("response must contain an events key")

    source_events = response["events"]

    if not isinstance(source_events, (list, tuple)):
        raise TypeError("response events must be a list or tuple")

    projected_events: list[ObservedRouteEvent] = []

    for index, source_event in enumerate(source_events):
        if not isinstance(source_event, Mapping):
            raise TypeError(
                f"events[{index}] must be a mapping"
            )

        projected_events.append(
            _project_event(
                source_event,
                index=index,
                collection_scope=normalized_scope,
                tracking_number=normalized_tracking_number,
            )
        )

    return ObservedRouteEventHistory(
        reporting_source_id=_REPORTING_SOURCE_ID,
        provenance=provenance,
        events=tuple(projected_events),
        tracking_number=normalized_tracking_number,
        completeness=ObservedRouteEventHistoryCompleteness.UNKNOWN,
        ordering=ObservedRouteEventHistoryOrdering.SOURCE_ORDER,
        has_more=None,
        next_page_token=None,
        freshness=None,
        constraints=_CONSTRAINTS,
        metadata={},
    )
