from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from app.services.cross_border.freshness import EvidenceFreshness
from app.services.cross_border.provenance import EvidenceProvenance


class ObservedRouteEventHistoryCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ObservedRouteEventHistoryOrdering(str, Enum):
    CHRONOLOGICAL = "chronological"
    SOURCE_ORDER = "source_order"
    UNKNOWN = "unknown"


class ObservedRouteEventScope(str, Enum):
    SHIPMENT = "shipment"
    PIECE = "piece"
    PACKAGE = "package"
    UNKNOWN = "unknown"


class ObservedRouteEventActorRole(str, Enum):
    CARRIER = "carrier"
    POSTAL_OPERATOR = "postal_operator"
    CUSTOMS_AUTHORITY = "customs_authority"
    FULFILLMENT_PROVIDER = "fulfillment_provider"
    SHIPPING_AGGREGATOR = "shipping_aggregator"
    TRACKING_PROVIDER = "tracking_provider"
    FACILITY = "facility"
    UNKNOWN = "unknown"


class ObservedRouteEventRelationshipType(str, Enum):
    DUPLICATE_OF = "duplicate_of"
    CORRECTS = "corrects"
    SUPERSEDES = "supersedes"


def _optional_string(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string or None")
    normalized = value.strip()
    return normalized or None


def _required_string(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _optional_aware_datetime(
    name: str,
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime or None")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _enum(name: str, value: object, expected_type: type[Enum]) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"{name} must be {expected_type.__name__}")


def _typed_tuple(name: str, values: object, element_type: type) -> tuple:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of {element_type.__name__}")
    try:
        result = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(
            f"{name} must be an iterable of {element_type.__name__}"
        ) from exc
    if any(not isinstance(value, element_type) for value in result):
        raise TypeError(f"every {name} element must be {element_type.__name__}")
    return result


def _metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    if any(not isinstance(key, str) for key in value):
        raise TypeError("every metadata key must be a string")
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ObservedRouteEventLocation:
    country_code: str | None = None
    subdivision_code: str | None = None
    locality: str | None = None
    postal_code: str | None = None
    facility_code: str | None = None
    facility_name: str | None = None
    raw_description: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "country_code",
            "subdivision_code",
            "locality",
            "postal_code",
            "facility_code",
            "facility_name",
            "raw_description",
        ):
            value = _optional_string(name, getattr(self, name))
            if name == "country_code" and value is not None:
                value = value.upper()
            object.__setattr__(self, name, value)
        if all(value is None for value in self.__dict__.values()):
            raise ValueError("location must contain at least one non-empty field")


@dataclass(frozen=True)
class ObservedRouteEventActor:
    actor_reference: str | None = None
    actor_name: str | None = None
    actor_role: ObservedRouteEventActorRole = ObservedRouteEventActorRole.UNKNOWN

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "actor_reference",
            _optional_string("actor_reference", self.actor_reference),
        )
        object.__setattr__(
            self,
            "actor_name",
            _optional_string("actor_name", self.actor_name),
        )
        _enum("actor_role", self.actor_role, ObservedRouteEventActorRole)
        if self.actor_reference is None and self.actor_name is None:
            raise ValueError("actor_reference or actor_name is required")


@dataclass(frozen=True)
class ObservedRouteEventRelationship:
    relationship_type: ObservedRouteEventRelationshipType
    related_event_reference: str

    def __post_init__(self) -> None:
        _enum(
            "relationship_type",
            self.relationship_type,
            ObservedRouteEventRelationshipType,
        )
        object.__setattr__(
            self,
            "related_event_reference",
            _required_string(
                "related_event_reference",
                self.related_event_reference,
            ),
        )


@dataclass(frozen=True)
class ObservedRouteEvent:
    provider_event_id: str | None = None
    provider_event_code: str | None = None
    raw_status: str | None = None
    raw_status_description: str | None = None
    occurred_at: datetime | None = None
    occurred_at_raw: str | None = None
    recorded_at: datetime | None = None
    recorded_at_raw: str | None = None
    location: ObservedRouteEventLocation | None = None
    actor: ObservedRouteEventActor | None = None
    scope: ObservedRouteEventScope = ObservedRouteEventScope.UNKNOWN
    scope_reference: str | None = None
    source_sequence: str | None = None
    relationships: tuple[ObservedRouteEventRelationship, ...] = ()
    provenance: EvidenceProvenance | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "provider_event_id",
            "provider_event_code",
            "raw_status",
            "raw_status_description",
            "occurred_at_raw",
            "recorded_at_raw",
            "scope_reference",
            "source_sequence",
        ):
            object.__setattr__(
                self,
                name,
                _optional_string(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "occurred_at",
            _optional_aware_datetime("occurred_at", self.occurred_at),
        )
        object.__setattr__(
            self,
            "recorded_at",
            _optional_aware_datetime("recorded_at", self.recorded_at),
        )
        if self.location is not None and not isinstance(
            self.location,
            ObservedRouteEventLocation,
        ):
            raise TypeError("location must be ObservedRouteEventLocation or None")
        if self.actor is not None and not isinstance(
            self.actor,
            ObservedRouteEventActor,
        ):
            raise TypeError("actor must be ObservedRouteEventActor or None")
        _enum("scope", self.scope, ObservedRouteEventScope)
        object.__setattr__(
            self,
            "relationships",
            _typed_tuple(
                "relationships",
                self.relationships,
                ObservedRouteEventRelationship,
            ),
        )
        if self.provenance is not None and not isinstance(
            self.provenance,
            EvidenceProvenance,
        ):
            raise TypeError("provenance must be EvidenceProvenance or None")
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        minimum_content = (
            self.provider_event_id,
            self.provider_event_code,
            self.raw_status,
            self.raw_status_description,
            self.occurred_at,
            self.occurred_at_raw,
            self.recorded_at,
            self.recorded_at_raw,
            self.location,
            self.actor,
        )
        if all(value is None for value in minimum_content):
            raise ValueError("event must contain source-reported content")


@dataclass(frozen=True)
class ObservedRouteEventHistory:
    reporting_source_id: str
    provenance: EvidenceProvenance
    events: tuple[ObservedRouteEvent, ...] = ()
    carrier_reference: str | None = None
    tracking_number: str | None = None
    source_record_id: str | None = None
    request_correlation_id: str | None = None
    completeness: ObservedRouteEventHistoryCompleteness = (
        ObservedRouteEventHistoryCompleteness.UNKNOWN
    )
    ordering: ObservedRouteEventHistoryOrdering = (
        ObservedRouteEventHistoryOrdering.UNKNOWN
    )
    has_more: bool | None = None
    next_page_token: str | None = None
    freshness: EvidenceFreshness | None = None
    constraints: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reporting_source_id",
            _required_string("reporting_source_id", self.reporting_source_id),
        )
        if not isinstance(self.provenance, EvidenceProvenance):
            raise TypeError("provenance must be EvidenceProvenance")
        object.__setattr__(
            self,
            "events",
            _typed_tuple("events", self.events, ObservedRouteEvent),
        )
        for name in (
            "carrier_reference",
            "tracking_number",
            "source_record_id",
            "request_correlation_id",
            "next_page_token",
        ):
            object.__setattr__(
                self,
                name,
                _optional_string(name, getattr(self, name)),
            )
        if all(
            value is None
            for value in (
                self.carrier_reference,
                self.tracking_number,
                self.source_record_id,
                self.request_correlation_id,
            )
        ):
            raise ValueError("at least one correlation reference is required")
        _enum(
            "completeness",
            self.completeness,
            ObservedRouteEventHistoryCompleteness,
        )
        _enum("ordering", self.ordering, ObservedRouteEventHistoryOrdering)
        if self.has_more is not None and not isinstance(self.has_more, bool):
            raise TypeError("has_more must be a bool or None")
        if self.freshness is not None and not isinstance(
            self.freshness,
            EvidenceFreshness,
        ):
            raise TypeError("freshness must be EvidenceFreshness or None")
        normalized_constraints = _typed_tuple(
            "constraints",
            self.constraints,
            str,
        )
        object.__setattr__(
            self,
            "constraints",
            tuple(
                normalized
                for constraint in normalized_constraints
                if (normalized := _optional_string("constraint", constraint))
                is not None
            ),
        )
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        if (
            self.has_more is True or self.next_page_token is not None
        ) and self.completeness is not ObservedRouteEventHistoryCompleteness.PARTIAL:
            raise ValueError(
                "pagination evidence requires completeness=PARTIAL"
            )
