# Observed Route Event History Canonical Contract Definition

## Document status

- Status: `research-level canonical contract definition`
- Contract ID: `CB-EA5B`
- Definition decision: `CB-EA5B-7`
- Sealing gate: `CB-EA5B-8`
- Definition date: `2026-08-26`
- Canonical target family: `observed_route_event_history`
- Canonical owner: `Commerce AI Cross-Border Evidence Layer`
- Production Python implementation: `not authorized`
- Projection registry mutation: `not authorized`
- External-evidence ingress mutation: `not authorized`
- Provider adapter or projector: `not authorized`
- Dossier mutation: `none`
- Existing provider compatibility mutation: `none`

## Purpose

This document defines the minimum research-level canonical contract for
evidence of shipment-related events reported as having occurred.

It establishes:

- history and event object boundaries;
- provider-local identity and correlation;
- immutable collection behavior;
- completeness and ordering;
- duplicate, correction, and revision boundaries;
- occurred, recorded, retrieved, and evaluated-time semantics;
- event location, actor, scope, and provenance;
- validation and non-inference rules.

It does not implement or register the contract in production.

## Semantic boundary

`observed_route_event_history` is independent from
`shipping_route_evidence`.

| Target family | Meaning |
|---|---|
| `shipping_route_evidence` | Planned or prospective route structure, availability, estimate, cost, and constraints |
| `observed_route_event_history` | Source-reported shipment-event history |

Neither target family establishes the other.

An observed tracking event does not establish:

- `ShippingRouteType`;
- planned-route availability;
- legal custody;
- regulatory clearance;
- delivery correctness;
- loss responsibility;
- payment or settlement.

## Canonical object topology

```text
ObservedRouteEventHistory
├── provider-local correlation references
├── immutable events
├── completeness
├── ordering
├── pagination indicators
├── mandatory history provenance
├── optional history freshness
├── constraints
└── metadata

ObservedRouteEvent
├── provider-native identity and status
├── occurred and recorded temporal evidence
├── optional location
├── optional actor
├── event scope and scope reference
├── optional source sequence
├── optional relationships
├── optional event provenance
└── metadata
```

## Canonical vocabulary

### `ObservedRouteEventHistoryCompleteness`

```python
class ObservedRouteEventHistoryCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
```

Meaning:

- `complete`: complete only within an explicitly bounded and supported history
  scope;
- `partial`: source or acquisition evidence establishes incomplete coverage;
- `unknown`: completeness cannot be determined.

Default: `UNKNOWN`.

### `ObservedRouteEventHistoryOrdering`

```python
class ObservedRouteEventHistoryOrdering(str, Enum):
    CHRONOLOGICAL = "chronological"
    SOURCE_ORDER = "source_order"
    UNKNOWN = "unknown"
```

Meaning:

- `chronological`: ordering is supported by an explicit source guarantee or a
  separately authorized complete temporal normalization;
- `source_order`: source response order is preserved without chronological
  meaning;
- `unknown`: even a stable source ordering cannot be established.

Default: `UNKNOWN`.

### `ObservedRouteEventScope`

```python
class ObservedRouteEventScope(str, Enum):
    SHIPMENT = "shipment"
    PIECE = "piece"
    PACKAGE = "package"
    UNKNOWN = "unknown"
```

Default: `UNKNOWN`.

### `ObservedRouteEventActorRole`

```python
class ObservedRouteEventActorRole(str, Enum):
    CARRIER = "carrier"
    POSTAL_OPERATOR = "postal_operator"
    CUSTOMS_AUTHORITY = "customs_authority"
    FULFILLMENT_PROVIDER = "fulfillment_provider"
    SHIPPING_AGGREGATOR = "shipping_aggregator"
    TRACKING_PROVIDER = "tracking_provider"
    FACILITY = "facility"
    UNKNOWN = "unknown"
```

`UNKNOWN` means that an actor is observed while its role remains unresolved.
Absent actor evidence is represented by no actor object.

### `ObservedRouteEventRelationshipType`

```python
class ObservedRouteEventRelationshipType(str, Enum):
    DUPLICATE_OF = "duplicate_of"
    CORRECTS = "corrects"
    SUPERSEDES = "supersedes"
```

Relationships may be constructed only from direct source semantics or a later
authorized deterministic source-local rule.

## Location contract

Research-level candidate:

```python
@dataclass(frozen=True)
class ObservedRouteEventLocation:
    country_code: str | None = None
    subdivision_code: str | None = None
    locality: str | None = None
    postal_code: str | None = None
    facility_code: str | None = None
    facility_name: str | None = None
    raw_description: str | None = None
```

Invariants:

1. All optional strings are trimmed.
2. Empty optional strings normalize to `None`.
3. An instantiated location contains at least one non-empty field.
4. An explicitly documented country code may be uppercased.
5. Country, subdivision, locality, postal code, and facility semantics are not
   inferred from an ambiguous provider code.
6. A raw location is preserved only as `raw_description`.
7. Geocoding is not performed or authorized.

## Actor contract

Research-level candidate:

```python
@dataclass(frozen=True)
class ObservedRouteEventActor:
    actor_reference: str | None = None
    actor_name: str | None = None
    actor_role: ObservedRouteEventActorRole = (
        ObservedRouteEventActorRole.UNKNOWN
    )
```

Invariants:

1. `actor_reference` or `actor_name` is present.
2. The reporting source is not the default event actor.
3. Actor identity or role is not inferred from brand affiliation.
4. `UNKNOWN` means an actor is observed but its role is unresolved.
5. Absent actor evidence is represented by `actor=None`.

## Relationship contract

Research-level candidate:

```python
@dataclass(frozen=True)
class ObservedRouteEventRelationship:
    relationship_type: ObservedRouteEventRelationshipType
    related_event_reference: str
```

Invariants:

1. `related_event_reference` is non-empty.
2. The reference remains provider-local.
3. A relationship does not delete either event.
4. An unresolved relationship is omitted rather than manufactured.

## Individual event contract

Research-level candidate:

```python
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
```

This research definition deliberately does not introduce a manufactured
canonical event identifier or a provider-independent normalized status.

### Event minimum-content invariant

Each event contains at least one of:

- `provider_event_id`;
- `provider_event_code`;
- `raw_status`;
- `raw_status_description`;
- `occurred_at` or `occurred_at_raw`;
- `recorded_at` or `recorded_at_raw`;
- `location`;
- `actor`.

An empty event object is invalid.

### Event identity invariants

1. `provider_event_id` remains provider-native and provider-local.
2. `provider_event_code` does not become a canonical event identifier.
3. Neither source array position nor a content hash becomes canonical identity.
4. Missing provider identity is represented by `None`; it is not manufactured.
5. Correlation across providers is not inferred.

### Provider-native status invariants

1. `raw_status` and `raw_status_description` preserve source meaning.
2. A description is not promoted to a code.
3. A code is not assigned a provider-independent delivery-state meaning.
4. Estimated, planned, and occurred events are not conflated.
5. A normalized status taxonomy remains deferred to a separate authorization.

## Temporal model

| Field | Owner | Meaning |
|---|---|---|
| `occurred_at` | event | Source-supported instant at which the event occurred |
| `recorded_at` | event | Source-supported instant at which the event was recorded or received |
| `retrieved_at` | history provenance | Instant at which the evidence response was retrieved |
| `evaluated_at` | evaluation context | Instant at which a downstream evaluation was performed |

Temporal invariants:

1. Canonical datetime values are timezone-aware ISO-8601 instants.
2. A UTC offset or timezone is never inferred from location, carrier, account,
   request time, or adjacent documentation.
3. Naive, date-only, or otherwise unresolved values remain in the corresponding
   raw field.
4. `occurred_at` is not copied into `recorded_at`, or vice versa.
5. `retrieved_at` does not prove when an event occurred or was recorded.
6. `evaluated_at` is not provider evidence and is not event-owned.
7. Temporal sorting is not authorized when unresolved event times would require
   inference.

### Event location invariants

1. Location remains optional.
2. Location structure does not prove custody, jurisdiction, or legal clearance.
3. A facility label does not establish an actor unless separately supported.
4. Raw and structured location evidence may coexist without forced equivalence.

### Actor and reporting-source invariants

1. The event actor and the reporting source are separate concepts.
2. Carrier identity at history level does not automatically populate event actor.
3. An aggregator or tracking provider does not become the physical carrier by
   default.
4. Actor absence does not invalidate an otherwise non-empty event.

### Scope invariants

1. `scope` defaults to `UNKNOWN`.
2. `scope_reference` is valid only when source evidence supports that reference.
3. A shipment-level response does not make every event shipment-scoped.
4. Piece and package are not treated as aliases without source-specific support.

### Relationship and revision invariants

1. Duplicate, correction, and supersession semantics remain explicit relations.
2. No related event is destructively overwritten or removed.
3. Similar status, time, and location values do not by themselves prove a
   duplicate.
4. A later retrieval does not automatically supersede an earlier snapshot.
5. Provider-native revision semantics are preserved when directly observed.

## History aggregate contract

Research-level candidate:

```python
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
```

The aggregate is an immutable evidence snapshot. It is not a mutable shipment
state record or a planned route topology.

### History correlation invariant

A valid history has:

- a non-empty `reporting_source_id`; and
- at least one non-empty correlation reference among `carrier_reference`,
  `tracking_number`, `source_record_id`, or `request_correlation_id`.

Correlation references remain source-local. Matching text does not establish
cross-provider identity.

### History provenance invariant

1. History-level provenance is mandatory.
2. It identifies the reporting source and acquisition context.
3. `retrieved_at` belongs to this provenance boundary.
4. Event-level provenance is optional and may narrow or supplement history-level
   provenance.
5. Event-level provenance does not replace mandatory history provenance.
6. Adjacent-source evidence is not attributed to the registered source.

### Collection invariant

1. `events` is an immutable tuple.
2. Source response order is preserved on acquisition.
3. Events are not destructively deduplicated, corrected, or overwritten.
4. An empty event tuple is allowed only when the source response itself is valid
   evidence of no returned events for the request boundary.
5. Repeated retrievals produce separate immutable evidence snapshots.

### Completeness invariant

1. Completeness defaults to `UNKNOWN`.
2. `COMPLETE` requires direct source support for the stated request scope and
   retrieval boundary.
3. Absence of a pagination token or partial-history flag does not prove
   `COMPLETE`.
4. Pagination, truncation, retention windows, access tiers, filters, and request
   bounds may require `PARTIAL`.
5. Conflicting or insufficient completeness evidence resolves to `UNKNOWN`.

### Ordering invariant

1. Ordering defaults to `UNKNOWN`.
2. Preserved response position alone supports at most `SOURCE_ORDER`.
3. `CHRONOLOGICAL` requires an explicit source guarantee or a separately
   authorized complete temporal normalization.
4. `source_sequence` remains provider-native and does not independently prove
   chronology.
5. Missing or unresolved occurrence times prevent inferred chronological order.
6. Sorting a presentation does not mutate the canonical evidence snapshot.

### Pagination and bounded-window invariant

1. `has_more=True` requires `completeness=PARTIAL`.
2. A non-empty `next_page_token` requires `completeness=PARTIAL`.
3. `has_more=False` does not independently prove `COMPLETE`.
4. Page tokens, cursors, offsets, and windows remain acquisition metadata; they
   are not shipment-event identity.
5. Combining pages requires a separately authorized deterministic assembly rule
   that preserves page provenance and source order.

### Polling and webhook invariant

1. Polling responses and webhook deliveries are separate evidence acquisitions.
2. A webhook event is not assumed to be a complete history.
3. Polling and webhook payloads are not merged by timestamp similarity alone.
4. Delivery time of a webhook does not become `occurred_at`.
5. Request and delivery correlation identifiers remain source-local.

### Freshness invariant

1. Freshness is optional at this research-contract level.
2. Freshness evaluation requires a supported `retrieved_at` and a separately
   defined evaluation context.
3. Missing freshness evidence remains `None`; it is not interpreted as stale or
   fresh.
4. Provider update cadence is not inferred from a single response.
5. Freshness does not establish completeness or chronological ordering.

## Immutability and normalization

The canonical research contract is append-only at the evidence-snapshot level.
Normalization is limited to semantics explicitly authorized by this definition:

- trimming optional strings;
- converting empty optional strings to `None`;
- uppercasing an explicitly documented country code;
- parsing timezone-aware source timestamps without changing their instant;
- freezing collections as tuples and metadata as immutable mappings in a future
  implementation.

Normalization does not authorize destructive deduplication, event replacement,
provider aliasing, timezone inference, geocoding, status taxonomy assignment, or
cross-provider identity resolution.

## Explicit non-inferences

This contract does not infer or establish:

- planned route topology or `ShippingRouteType`;
- route availability or delivery feasibility;
- legal custody or transfer of title;
- regulatory clearance or customs release;
- delivery correctness, proof of delivery, or recipient identity;
- loss, damage, delay, or financial responsibility;
- payment, settlement, duty, tax, or insurance outcome;
- provider equivalence from shared brand, corporate ownership, or carrier
  coverage;
- completeness from silence;
- chronology from array position;
- event identity from content similarity;
- actor identity from the reporting source;
- occurred time from retrieval or webhook delivery time.

## Provider compatibility consequence

This definition does not perform candidate-specific projection evaluation.
Accordingly:

- all existing candidates retain
  `canonical_projection_compatibility = unknown / None`;
- no candidate is admitted, selected, ranked, preferred, or rejected;
- no adjacent source is attributed to a registered source;
- ShipEngine v1 evidence is not attributed to ShipStation V2;
- DHL Shipment Tracking - Unified evidence is not attributed to MyDHL API;
- Korea Post EMS, TracX SmartShip, Fassto FMS, and Delivered Korea remain
  research evidence candidates under their existing classifications.

## Production and registry boundary

This research-level definition does not authorize mutation of:

- `app/services/cross_border/shipping.py`;
- `app/services/cross_border/provenance.py`;
- `app/services/cross_border/freshness.py`;
- `app/services/cross_border/external_evidence_ingress.py`;
- `app/services/cross_border/external_evidence_projection.py`;
- any production model, serializer, endpoint, registry, adapter, or projector;
- the external-evidence provider evaluation dossier.

It also does not authorize historical backfill, live provider acquisition, or
projection compatibility mutation.

## Contract authorization

CB-EA5B authorizes this document as the minimum research-level canonical
contract definition for the `observed_route_event_history` target family.

Authorized at this level:

- canonical object and value-object boundaries;
- field ownership and minimum validation semantics;
- immutable collection, completeness, ordering, pagination, temporal,
  provenance, relationship, and non-inference rules;
- use as the input to a later implementation-authorization review.

Not authorized at this level:

- production Python implementation;
- projection registry or ingress mutation;
- provider adapter or projector implementation;
- provider compatibility decisions;
- dossier mutation;
- deployment or runtime activation.

## Required implementation-authorization gate

Before production implementation, a separate gate must approve exact module
ownership, reuse of existing provenance and freshness types, runtime validation,
serialization, tests, registry effects, migration behavior, and rollback scope.

Until that gate is sealed, this document remains a research contract definition
and creates no executable production contract.
