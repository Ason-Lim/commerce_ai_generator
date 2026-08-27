"""Project ShipStation V2 tracking-log evidence into the canonical history."""

from collections.abc import Mapping

from app.services.cross_border.observed_route_event_history import (
    ObservedRouteEvent,
    ObservedRouteEventHistory,
    ObservedRouteEventHistoryCompleteness,
    ObservedRouteEventHistoryOrdering,
    ObservedRouteEventLocation,
)
from app.services.cross_border.provenance import EvidenceProvenance


_REPORTING_SOURCE_ID = "candidate:shipping:shipstation-api"
_CONSTRAINTS = (
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


def _optional_source_string(name: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string or None")
    normalized = value.strip()
    return normalized or None


def _project_event(source_event: Mapping[str, object], index: int) -> ObservedRouteEvent:
    provider_event_code = _optional_source_string(
        "status_code", source_event.get("status_code")
    )
    raw_status = _optional_source_string(
        "carrier_status_code", source_event.get("carrier_status_code")
    )
    raw_status_description = _optional_source_string(
        "carrier_status_description",
        source_event.get("carrier_status_description"),
    )
    country_code = _optional_source_string(
        "country_code", source_event.get("country_code")
    )
    company_name = _optional_source_string(
        "company_name", source_event.get("company_name")
    )
    carrier_detail_code = _optional_source_string(
        "carrier_detail_code", source_event.get("carrier_detail_code")
    )

    location = None
    if country_code is not None or company_name is not None:
        location = ObservedRouteEventLocation(
            country_code=country_code,
            raw_description=company_name,
        )

    if all(
        value is None
        for value in (
            provider_event_code,
            raw_status,
            raw_status_description,
            location,
        )
    ):
        raise ValueError(f"events[{index}] has no supported minimum content")

    metadata = {}
    if carrier_detail_code is not None:
        metadata["carrier_detail_code"] = carrier_detail_code

    return ObservedRouteEvent(
        provider_event_code=provider_event_code,
        raw_status=raw_status,
        raw_status_description=raw_status_description,
        location=location,
        metadata=metadata,
    )


def project_shipstation_v2_tracking_log(
    response: Mapping[str, object],
    *,
    tracking_number: str,
    provenance: EvidenceProvenance,
    carrier_code: str | None = None,
) -> ObservedRouteEventHistory:
    """Project one already-acquired ShipStation V2 tracking-log response."""
    if not isinstance(response, Mapping):
        raise TypeError("response must be a mapping")
    if not isinstance(tracking_number, str):
        raise TypeError("tracking_number must be a string")
    normalized_tracking_number = tracking_number.strip()
    if not normalized_tracking_number:
        raise ValueError("tracking_number must be non-empty")
    normalized_carrier_code = _optional_source_string("carrier_code", carrier_code)
    if not isinstance(provenance, EvidenceProvenance):
        raise TypeError("provenance must be EvidenceProvenance")
    if provenance.source_id != _REPORTING_SOURCE_ID:
        raise ValueError("provenance source_id does not match ShipStation V2")
    if "events" not in response:
        raise ValueError("response must contain an events key")
    source_events = response["events"]
    if not isinstance(source_events, (list, tuple)):
        raise TypeError("response events must be a list or tuple")

    projected_events = []
    for index, source_event in enumerate(source_events):
        if not isinstance(source_event, Mapping):
            raise TypeError(f"events[{index}] must be a mapping")
        projected_events.append(_project_event(source_event, index))

    return ObservedRouteEventHistory(
        reporting_source_id=_REPORTING_SOURCE_ID,
        provenance=provenance,
        events=tuple(projected_events),
        carrier_reference=normalized_carrier_code,
        tracking_number=normalized_tracking_number,
        source_record_id=None,
        request_correlation_id=None,
        completeness=ObservedRouteEventHistoryCompleteness.UNKNOWN,
        ordering=ObservedRouteEventHistoryOrdering.SOURCE_ORDER,
        has_more=None,
        next_page_token=None,
        freshness=None,
        constraints=_CONSTRAINTS,
        metadata={},
    )
