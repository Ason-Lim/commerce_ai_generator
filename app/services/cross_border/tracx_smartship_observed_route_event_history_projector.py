"""Project TracX SmartShip polling tracking history into the canonical history."""

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


_REPORTING_SOURCE_ID = "candidate:shipping-aggregator:tracx-smartship"
_CORRELATION_KEYS = (
    "shipping_no",
    "ref_no",
    "qs_no",
)
_CONSTRAINTS = (
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


def _optional_source_string(name: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string or None")
    normalized = value.strip()
    return normalized or None


def _required_correlation_key(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("correlation_key must be a string")
    if value not in _CORRELATION_KEYS:
        raise ValueError("correlation_key is not supported")
    return value


def _normalize_correlations(
    response: Mapping[str, object],
    *,
    correlation_key: str,
    correlation_value: object,
) -> tuple[str, dict[str, str]]:
    if not isinstance(correlation_value, str):
        raise TypeError("correlation_value must be a string")
    normalized_correlation_value = correlation_value.strip()
    if not normalized_correlation_value:
        raise ValueError("correlation_value must be non-empty")

    normalized_correlations: dict[str, str] = {}
    for key in _CORRELATION_KEYS:
        if key not in response:
            if key == correlation_key:
                raise ValueError(f"response must contain selected correlation {key}")
            continue
        value = response[key]
        if value is None:
            if key == correlation_key:
                raise ValueError(f"response correlation {key} must be non-empty")
            continue
        if not isinstance(value, str):
            raise TypeError(f"response correlation {key} must be a string or None")
        normalized = value.strip()
        if not normalized:
            if key == correlation_key:
                raise ValueError(f"response correlation {key} must be non-empty")
            continue
        normalized_correlations[key] = normalized

    selected_value = normalized_correlations[correlation_key]
    if selected_value != normalized_correlation_value:
        raise ValueError("selected response correlation does not match correlation_value")
    return normalized_correlation_value, normalized_correlations


def _project_location(
    value: object,
    *,
    index: int,
) -> ObservedRouteEventLocation | None:
    raw_description = _optional_source_string(
        f"tracking_history[{index}].location",
        value,
    )
    if raw_description is None:
        return None
    return ObservedRouteEventLocation(raw_description=raw_description)


def _project_event(
    source_event: Mapping[str, object],
    *,
    index: int,
) -> ObservedRouteEvent:
    provider_event_code = _optional_source_string(
        f"tracking_history[{index}].status_code",
        source_event.get("status_code"),
    )
    raw_status = _optional_source_string(
        f"tracking_history[{index}].status",
        source_event.get("status"),
    )
    raw_status_description = _optional_source_string(
        f"tracking_history[{index}].details",
        source_event.get("details"),
    )
    occurred_at_raw = _optional_source_string(
        f"tracking_history[{index}].date",
        source_event.get("date"),
    )
    location = _project_location(
        source_event.get("location"),
        index=index,
    )

    if all(
        value is None
        for value in (
            provider_event_code,
            raw_status,
            raw_status_description,
            occurred_at_raw,
            location,
        )
    ):
        raise ValueError(
            f"tracking_history[{index}] has no supported minimum content"
        )

    return ObservedRouteEvent(
        provider_event_id=None,
        provider_event_code=provider_event_code,
        raw_status=raw_status,
        raw_status_description=raw_status_description,
        occurred_at=None,
        occurred_at_raw=occurred_at_raw,
        recorded_at=None,
        recorded_at_raw=None,
        location=location,
        actor=None,
        scope=ObservedRouteEventScope.UNKNOWN,
        scope_reference=None,
        source_sequence=None,
        relationships=(),
        provenance=None,
        metadata={},
    )


def project_tracx_smartship_tracking_history(
    response: Mapping[str, object],
    *,
    correlation_key: str,
    correlation_value: str,
    provenance: EvidenceProvenance,
) -> ObservedRouteEventHistory:
    """Project one already-acquired SmartShipService.Tracking response."""
    if not isinstance(response, Mapping):
        raise TypeError("response must be a mapping")

    normalized_correlation_key = _required_correlation_key(correlation_key)
    normalized_correlation_value, normalized_correlations = _normalize_correlations(
        response,
        correlation_key=normalized_correlation_key,
        correlation_value=correlation_value,
    )

    if not isinstance(provenance, EvidenceProvenance):
        raise TypeError("provenance must be EvidenceProvenance")
    if provenance.source_id != _REPORTING_SOURCE_ID:
        raise ValueError("provenance source_id does not match TracX SmartShip")

    if "tracking_history" not in response:
        raise ValueError("response must contain a tracking_history key")
    source_events = response["tracking_history"]
    if not isinstance(source_events, (list, tuple)):
        raise TypeError("response tracking_history must be a list or tuple")

    projected_events: list[ObservedRouteEvent] = []
    for index, source_event in enumerate(source_events):
        if not isinstance(source_event, Mapping):
            raise TypeError(f"tracking_history[{index}] must be a mapping")
        projected_events.append(_project_event(source_event, index=index))

    return ObservedRouteEventHistory(
        reporting_source_id=_REPORTING_SOURCE_ID,
        provenance=provenance,
        events=tuple(projected_events),
        carrier_reference=None,
        tracking_number=normalized_correlation_value,
        source_record_id=None,
        request_correlation_id=None,
        completeness=ObservedRouteEventHistoryCompleteness.UNKNOWN,
        ordering=ObservedRouteEventHistoryOrdering.SOURCE_ORDER,
        has_more=None,
        next_page_token=None,
        freshness=None,
        constraints=_CONSTRAINTS,
        metadata=normalized_correlations,
    )
