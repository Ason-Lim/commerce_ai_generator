# MyDHL API Observed Route Event History Projection Compatibility Worksheet

## Document status

- Gate: `CB-EA5B-8V-2`
- Status: `candidate-specific research worksheet`
- Candidate: `candidate:shipping-landed-cost:mydhl-api`
- Product surface: DHL Express MyDHL API
- Inspected version: `3.3.1`
- Canonical target: `observed_route_event_history`
- Proposed compatibility state: `observed`
- Dossier mutation: `not authorized`
- Production implementation: `not authorized`
- Live API acquisition: `not authorized`

## Purpose

This worksheet evaluates whether directly documented MyDHL API Tracking responses
can be conservatively represented as bounded `ObservedRouteEventHistory` evidence
snapshots.

It does not establish complete route history, chronological guarantees, delivery
correctness, candidate selection, production readiness, or dossier mutation.

## Evaluation subject identity

- Registered identity: `candidate:shipping-landed-cost:mydhl-api`
- Product surface: DHL Express MyDHL API
- Inspected version: `3.3.1`
- Base URL: `https://express.api.dhl.com/mydhlapi`
- Evaluated operations:
  - `GET /shipments/{shipmentTrackingNumber}/tracking`;
  - `GET /tracking`.
- Official product reference:
  `https://developer.dhl.com/api-reference/dhl-express-mydhl-api`
- Official OpenAPI:
  `https://developer.dhl.com/sites/default/files/2026-07/dpdhl-express-api-3.3.1.yaml`

DHL Shipment Tracking - Unified is a separate API product and is not used to fill
gaps in this worksheet. ShipStation evidence is also not attributed to MyDHL API.

## Sealed research inputs

1. `observed_route_event_history_canonical_contract_definition.md`;
2. `observed_route_event_history_first_wave_projection_compatibility_review_authorization_decision.md`;
3. `direct_registered_source_tracking_schema_sufficiency_review.md`; and
4. `external_evidence_provider_evaluation_dossier.md`.

The canonical definition controls target semantics. The direct-source review
controls which MyDHL fields and behaviors are treated as observed.

## Directly observed source structure

The sealed direct-source review establishes:

- shipment-level and piece-level `events[]` collections;
- event `typeCode` and `description`;
- optional event remarks;
- separate event `date` and `time` fields;
- optional event `GMTOffset` when requested or returned;
- event `serviceArea[]` with `code` and `description`;
- shipment and piece tracking references; and
- occurred events structurally separate from `estimatedDeliveryDate`.

The sealed review does not establish:

- an independent stable event identifier;
- provider-recorded or received time;
- event-level carrier identity;
- a chronological ordering guarantee;
- complete or partial history semantics;
- duplicate, correction, replacement, or revision semantics;
- provider response freshness; or
- a deterministic cross-response assembly rule.

## Projection boundary

One successfully acquired response from one evaluated Tracking operation forms one
immutable evidence snapshot. Shipment-level and piece-level histories remain
distinct source scopes unless a future assembly rule is separately authorized.

No response is treated as complete route topology, proof of delivery, customs
clearance, legal custody, or a verified physical handoff ledger.

## History-level field mapping

| Canonical field | MyDHL evidence | Proposed projection | Finding |
|---|---|---|---|
| `reporting_source_id` | Registered candidate identity | `candidate:shipping-landed-cost:mydhl-api` | Direct evaluation-context constant |
| `provenance` | Acquisition of exact MyDHL operation and version | Commerce AI-owned mandatory acquisition provenance | Required external envelope |
| `events` | Shipment or piece `events[]` | Immutable tuple preserving returned order | Direct structural mapping |
| `carrier_reference` | DHL Express product context | Preserve direct documented provider reference when acquisition envelope supplies it | History correlation only; not event actor |
| `tracking_number` | Shipment tracking number or piece tracking number | Preserve source-local tracking reference | Direct mapping |
| `source_record_id` | No independent stable source-record identifier observed | `None` | Must not be manufactured |
| `request_correlation_id` | No separate request correlation identifier observed | `None` | Tracking number remains in its owned field |
| `completeness` | No complete or partial history indicator | `UNKNOWN` | Required conservative value |
| `ordering` | Returned array without ordering guarantee | `SOURCE_ORDER` only when response order is preserved; otherwise `UNKNOWN` | Never chronological by default |
| `has_more` | No pagination indicator established for evaluated response | `None` | No inference |
| `next_page_token` | No page token established | `None` | No inference |
| `freshness` | No provider freshness field established | `None` | Retrieval provenance is not freshness evaluation |
| `constraints` | Known semantic gaps | Immutable disclosure strings | Non-executable research metadata |
| `metadata` | Source-local response context | Immutable mapping when retained | Must not alter canonical meaning |

### Required history constraints

The bounded projection records constraints equivalent to:

- `history_completeness_not_documented`;
- `chronological_order_not_documented`;
- `stable_event_identity_not_documented`;
- `provider_recorded_time_not_documented`;
- `event_level_carrier_identity_not_documented`;
- `duplicate_and_revision_semantics_not_documented`;
- `pagination_semantics_not_documented`; and
- `provider_freshness_semantics_not_documented`.

## Event-level field mapping

| Canonical field | MyDHL evidence | Proposed projection | Finding |
|---|---|---|---|
| `provider_event_id` | No independent stable event identifier | `None` | Array position and content hash prohibited |
| `provider_event_code` | Event `typeCode` | Preserve trimmed provider-native value | Direct mapping |
| `raw_status` | Event `typeCode` | `None` by default to avoid duplicating code semantics | May remain metadata if distinct source field exists |
| `raw_status_description` | Event `description` | Preserve trimmed source value | Direct mapping |
| `occurred_at` | Event `date`, `time`, optional `GMTOffset` | Construct only when all required components produce a timezone-aware instant | Conditional direct composition |
| `occurred_at_raw` | Source date/time/offset components | Preserve an unambiguous source-local composite when canonical instant cannot be formed | No timezone inference |
| `recorded_at` | No recorded or received instant observed | `None` | Must not copy occurrence or retrieval time |
| `recorded_at_raw` | No recorded-time field observed | `None` | No raw recorded value established |
| `location` | `serviceArea[].code` and `description` | Bounded raw location object; source code retained without facility inference | Partial structural mapping |
| `actor` | No event-level actor field established | `None` | MyDHL reporting source is not default event actor |
| `scope` | Shipment-level or piece-level event collection | `SHIPMENT` or `PIECE` only when collection ownership is explicit | Direct structural scope |
| `scope_reference` | Shipment or piece tracking number | Preserve corresponding source-local reference | Direct when scope is supported |
| `source_sequence` | No provider-native sequence value observed | `None` | Array position is not a sequence value |
| `relationships` | No duplicate, correction, or supersession relation observed | `()` | Omit unresolved relations |
| `provenance` | No event-specific provenance established | `None` | Mandatory history provenance remains authoritative |
| `metadata` | Remarks and unprojected service-area values | Immutable source-local mapping | No canonical status or identity inference |

## Temporal composition rule

`occurred_at` may be populated only when:

1. event `date` is present and parseable under the exact documented format;
2. event `time` is present and parseable under the exact documented format;
3. event `GMTOffset` is present and parseable as the documented offset;
4. the three components describe one event occurrence instant; and
5. composition preserves that instant without location- or account-based timezone
   inference.

When these conditions pass, the composed value is a timezone-aware ISO-8601
instant. The original components remain recoverable in source metadata.

When date or time exists but the offset is absent, malformed, or semantically
unresolved:

- `occurred_at = None`;
- the directly supplied components may be preserved in `occurred_at_raw` as one
  source-local composite;
- no UTC, local timezone, carrier timezone, or location timezone is assumed; and
- the event remains valid when another minimum-content field is present.

`shipmentTimestamp`, request time, retrieval time, and evaluation time do not
become event `occurred_at` or `recorded_at`.

## Location subprojection

| Canonical location field | MyDHL evidence | Proposed value |
|---|---|---|
| `country_code` | Not established in the sealed event matrix | `None` |
| `subdivision_code` | Not observed | `None` |
| `locality` | Not observed | `None` |
| `postal_code` | Not observed | `None` |
| `facility_code` | `serviceArea[].code` | `None` unless official semantics explicitly establish a facility code |
| `facility_name` | `serviceArea[].description` | `None` unless official semantics explicitly establish a facility name |
| `raw_description` | `serviceArea[].description` | Preserve non-empty description without facility or actor inference |

The service-area code may remain source-local location metadata. A service area is
not automatically a facility, actor, customs authority, jurisdiction, custody
holder, or physical event site.

## Scope subprojection

Shipment-level and piece-level event collections are structurally distinct.
Accordingly:

- shipment-owned `events[]` may use `scope=SHIPMENT` with the shipment tracking
  number as `scope_reference`;
- piece-owned `events[]` may use `scope=PIECE` with the piece tracking number as
  `scope_reference`; and
- ambiguous collection ownership resolves to `scope=UNKNOWN` and
  `scope_reference=None`.

Piece and package are not treated as aliases.

## Event minimum-content check

An event is projectable when at least one non-empty directly supported value can
populate:

- `provider_event_code` from `typeCode`;
- `raw_status_description` from `description`;
- `occurred_at` or `occurred_at_raw` from supported temporal components; or
- `location` from a non-empty service-area description.

An empty source element cannot produce an empty canonical event.

## Completeness, ordering, and pagination finding

- Completeness: `UNKNOWN`.
- Ordering: `SOURCE_ORDER` only as preservation of the returned array;
  otherwise `UNKNOWN`.
- Chronological ordering: not supported by a source guarantee.
- Temporal values do not independently authorize sorting.
- `has_more`: `None`.
- `next_page_token`: `None`.
- Multi-page or cross-response assembly: not authorized.

The presence of occurrence timestamps does not prove chronological response order
or complete history.

## Provenance, actor, and correlation finding

The canonical history correlation invariant can be satisfied by the directly
supplied shipment or piece tracking number.

Mandatory history provenance must identify the exact MyDHL product, inspected
version, operation, retrieval context, and source reference. It is supplied by the
Commerce AI acquisition boundary in any future separately authorized
implementation.

DHL Express product identity at history level does not automatically populate an
event actor. No event-level carrier, facility, customs authority, handler, or
custodian is inferred.

## Identity, relationship, and normalization finding

- Stable event identity: unresolved; `provider_event_id=None`.
- Provider event code: `typeCode` remains provider-native.
- Description: preserved without normalized delivery-state assignment.
- Remarks: retained as metadata when directly supplied.
- Duplicate relationship: not established.
- Correction relationship: not established.
- Supersession relationship: not established.
- Destructive deduplication or replacement: prohibited.
- Cross-retrieval assembly: not authorized.
- Cross-provider identity resolution: prohibited.

## Canonical invariant checks

| Invariant | Result | Basis |
|---|---|---|
| Non-empty reporting source | `pass` | Fixed registered candidate identity |
| At least one history correlation reference | `pass` | Shipment or piece tracking number |
| Mandatory history provenance | `pass prospectively` | Commerce AI acquisition envelope required |
| Immutable event collection | `pass prospectively` | Response array can be frozen without semantic change |
| Event minimum content | `pass conditionally` | Supported code, description, time, or location required |
| Timezone-aware `occurred_at` | `pass conditionally` | Requires date, time, and documented GMT offset |
| Unresolved temporal preservation | `pass` | Raw composite used without timezone inference |
| Location minimum content | `pass conditionally` | Location omitted when raw description is empty |
| Actor minimum content | `not applicable` | Actor omitted |
| Scope ownership | `pass conditionally` | Shipment or piece collection ownership must be explicit |
| Relationship reference | `not applicable` | Relationships omitted |
| Completeness rules | `pass` | `UNKNOWN` with no inference |
| Ordering rules | `pass` | Source order only; no chronological claim |
| Pagination rules | `pass` | Pagination fields remain `None` |
| Non-destructive collection rules | `pass prospectively` | No deduplication or overwrite authorized |
| Source identity separation | `pass` | DHL Unified and ShipStation evidence excluded |

`pass prospectively` is a research mapping result, not implementation or runtime
verification.

## Unresolved requirements

The following remain unresolved:

1. stable provider event identity;
2. behavior when `GMTOffset` is omitted or malformed;
3. exact source format constraints for temporal composition in every response;
4. provider-recorded or received time;
5. event-level actor and carrier identity;
6. chronological ordering guarantee;
7. complete or partial history semantics;
8. pagination, truncation, and retention behavior;
9. duplicate, correction, replacement, and revision semantics;
10. provider response retrieval time and freshness policy;
11. deterministic assembly across repeated retrievals; and
12. whether all service-area codes have stable location semantics.

These gaps prevent claims of complete coverage, guaranteed chronology, stable
event identity, event-level custody, or freshness. They do not prevent a bounded
projection that preserves directly supported values and explicit unknowns.

## Compatibility proposal

Proposed result:

- `canonical_projection_compatibility`: `observed`;
- projection scope: bounded MyDHL API Tracking response snapshot;
- compatibility strength: `strong partial`;
- completeness: `UNKNOWN`;
- ordering: `SOURCE_ORDER` when response order is preserved, otherwise `UNKNOWN`;
- temporal projection: conditional timezone-aware occurrence instant with raw
  fallback;
- scope projection: shipment or piece when directly supported;
- source identity: MyDHL API version `3.3.1` only;
- production readiness: not established.

Proposed observation value:

> MyDHL API Tracking in inspected version `3.3.1` prospectively supports a
> bounded `observed_route_event_history` projection through shipment- and
> piece-level `events[]`, provider-native `typeCode` and description, conditional
> composition of event `date`, `time`, and `GMTOffset` into a timezone-aware
> occurrence instant with raw fallback, service-area location evidence, and
> shipment or piece tracking correlation within Commerce AI-owned history
> provenance. Completeness remains `UNKNOWN`; response order is not chronological
> by default; stable event identity, recorded time, event actor, duplicate,
> revision, pagination, assembly, and freshness semantics remain absent or
> unresolved and are not inferred.

This worksheet is a research proposal only. Dossier record
`cb-ea3b1-mydhl-006` remains `unknown / None` until an exact dossier-mutation gate
is separately authorized and sealed.

## Boundary result

- direct field mapping: `PASS WITH EXPLICIT GAPS`;
- canonical invariants: `PASS FOR BOUNDED STRONG-PARTIAL PROJECTION`;
- prohibited inference required: `NO`;
- DHL Unified attribution: `NONE`;
- ShipStation attribution: `NONE`;
- candidate admission or selection: `NOT AUTHORIZED`;
- production implementation: `NOT AUTHORIZED`;
- dossier mutation: `NOT AUTHORIZED`;
- current dossier compatibility: `unknown / None — UNCHANGED`;
- worksheet proposed compatibility: `observed`.

## Required next gate

The worksheet must undergo separate read-only validation and a research decision.
No dossier record may change before those gates are sealed.
