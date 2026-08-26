# ShipStation V2 Observed Route Event History Projection Compatibility Worksheet

## Document status

- Gate: `CB-EA5B-8U-2`
- Status: `candidate-specific research worksheet`
- Candidate: `candidate:shipping:shipstation-api`
- Canonical target: `observed_route_event_history`
- Proposed compatibility state: `observed`
- Dossier mutation: `not authorized`
- Production implementation: `not authorized`
- Live API acquisition: `not authorized`

## Purpose

This worksheet evaluates whether the directly documented ShipStation V2
`get_tracking_log` response can be conservatively represented as one bounded
`ObservedRouteEventHistory` evidence snapshot.

The worksheet does not establish that ShipStation V2 supplies a complete route
history. It does not authorize candidate admission, provider selection, ranking,
runtime acquisition, implementation, or dossier mutation.

## Evaluation subject identity

- Product surface: ShipStation platform API V2
- Base URL: `https://api.shipstation.com/v2`
- Operation: `get_tracking_log`
- Official reference:
  `https://docs.shipstation.com/apis/openapi/tracking/get_tracking_log`
- Registered identity: `candidate:shipping:shipstation-api`

ShipStation API formerly ShipEngine v1 and legacy ShipStation V1 are separate
source identities. Their documentation is not used to fill gaps in this worksheet.

## Sealed research inputs

1. `observed_route_event_history_canonical_contract_definition.md`;
2. `observed_route_event_history_first_wave_projection_compatibility_review_authorization_decision.md`;
3. `direct_registered_source_tracking_schema_sufficiency_review.md`; and
4. `external_evidence_provider_evaluation_dossier.md`.

The canonical definition controls target semantics. The sealed direct-source
review controls which ShipStation V2 fields and behaviors are treated as observed.

## Directly observed source structure

The sealed source review establishes:

- `events[]` as events occurring during the lifetime of a tracking number;
- `events[].status_code`;
- `events[].carrier_status_code`;
- `events[].carrier_detail_code`;
- `events[].carrier_status_description`;
- event-location components including `country_code` and `company_name`;
- request correlation through `carrier_code` and `tracking_number`; and
- actual-delivery information structurally separate from the event collection.

The sealed source review does not establish:

- a stable provider event identifier;
- an event occurrence timestamp;
- an event timezone or UTC offset;
- a provider-recorded or received timestamp;
- chronological ordering;
- complete or partial history semantics;
- duplicate, correction, replacement, or revision semantics;
- response pagination semantics for the evaluated operation;
- a retrieval timestamp supplied by the provider response; or
- evidence freshness semantics.

## Projection boundary

One successfully acquired `get_tracking_log` response may be treated as one
immutable evidence snapshot. The response is not treated as a mutable shipment
state, complete route topology, verified delivery history, or cross-provider event
ledger.

The projection preserves source response order and source-native values. It does
not sort, deduplicate, merge, enrich, geocode, infer timestamps, normalize delivery
status, or manufacture identity.

## History-level field mapping

| Canonical field | ShipStation V2 evidence | Proposed projection | Finding |
|---|---|---|---|
| `reporting_source_id` | Registered candidate identity | `candidate:shipping:shipstation-api` | Direct evaluation-context constant |
| `provenance` | Acquisition of the evaluated V2 operation | Commerce AI-owned mandatory acquisition provenance | Required external envelope; not copied from an event |
| `events` | `events[]` | Immutable tuple preserving response order | Direct structural mapping |
| `carrier_reference` | Request `carrier_code` | Preserve trimmed provider value | Direct when supplied |
| `tracking_number` | Request `tracking_number` | Preserve trimmed provider value | Direct when supplied |
| `source_record_id` | No independent source record identifier observed | `None` | Must not be manufactured |
| `request_correlation_id` | No separate request identifier observed | `None` | Tracking number remains in its owned field |
| `completeness` | No completeness or partial-history contract observed | `UNKNOWN` | Required conservative value |
| `ordering` | Response array position, without ordering guarantee | `SOURCE_ORDER` only when response order is preserved; otherwise `UNKNOWN` | No chronological meaning |
| `has_more` | Not observed | `None` | No pagination inference |
| `next_page_token` | Not observed | `None` | No pagination inference |
| `freshness` | No provider freshness field observed | `None` | Retrieval provenance does not itself establish freshness evaluation |
| `constraints` | Known semantic gaps | Immutable constraint strings | Research-level disclosure |
| `metadata` | Source-local noncanonical response context | Immutable mapping where retained | Must not change canonical meaning |

### Required history constraints

The bounded projection records constraints equivalent to:

- `history_completeness_not_documented`;
- `chronological_order_not_documented`;
- `event_occurrence_time_not_documented`;
- `event_identity_not_documented`;
- `duplicate_and_revision_semantics_not_documented`;
- `event_level_actor_identity_not_documented`; and
- `provider_freshness_semantics_not_documented`.

Constraint text is disclosure metadata. It is not a normalized status taxonomy or
an executable validation policy.

## Event-level field mapping

| Canonical field | ShipStation V2 evidence | Proposed projection | Finding |
|---|---|---|---|
| `provider_event_id` | No independent stable event identifier observed | `None` | Array position and hashes prohibited |
| `provider_event_code` | `events[].status_code` | Preserve trimmed value | Direct provider-native code |
| `raw_status` | `events[].carrier_status_code` | Preserve trimmed value when supplied | Carrier-native value; no canonical status meaning |
| `raw_status_description` | `events[].carrier_status_description` | Preserve trimmed value | Direct description |
| `occurred_at` | No event occurrence instant observed | `None` | Must not infer from array order or other timestamps |
| `occurred_at_raw` | No event occurrence-time field observed | `None` | No raw temporal value established |
| `recorded_at` | No recorded or received instant observed | `None` | Must not copy retrieval time |
| `recorded_at_raw` | No recorded-time field observed | `None` | No raw temporal value established |
| `location` | Event `country_code` and `company_name` | Bounded location object only from non-empty direct fields | Partial structural mapping |
| `actor` | No event-level actor identity observed | `None` | Reporting API and request carrier are not default event actors |
| `scope` | No event scope semantics observed | `UNKNOWN` | Shipment request does not force event scope |
| `scope_reference` | No event-owned scope reference observed | `None` | Tracking number remains history correlation |
| `source_sequence` | No provider-native sequence value observed | `None` | Array position must not become identity or sequence |
| `relationships` | No duplicate, correction, or supersession semantics observed | `()` | Omit unresolved relationships |
| `provenance` | No event-specific acquisition provenance observed | `None` | History provenance remains mandatory |
| `metadata` | `carrier_detail_code` and other preserved source-native fields | Immutable source-local mapping | Does not establish canonical identity or status |

### Location subprojection

| Canonical location field | Source evidence | Proposed value |
|---|---|---|
| `country_code` | `events[].country_code` | Uppercase only when documented as a country code |
| `subdivision_code` | Not observed | `None` |
| `locality` | Not observed | `None` |
| `postal_code` | Not observed | `None` |
| `facility_code` | Not observed | `None` |
| `facility_name` | `events[].company_name` | `None` unless the source documentation explicitly establishes facility semantics |
| `raw_description` | `events[].company_name` | Preserve here when non-empty and semantic role remains ambiguous |

A location object is omitted when all supported values are absent or empty.
`company_name` is not promoted to actor identity or facility ownership.

## Event minimum-content check

An event is projectable when at least one directly supplied non-empty value can
populate:

- `provider_event_code` from `status_code`;
- `raw_status` from `carrier_status_code`;
- `raw_status_description` from `carrier_status_description`; or
- `location` from directly supported location evidence.

An empty provider event cannot produce an empty canonical event. It must remain an
unprojectable source element recorded as an evaluation gap rather than a
manufactured event.

## Temporal finding

ShipStation V2 temporal compatibility is bounded as follows:

- `occurred_at = None`;
- `occurred_at_raw = None`;
- `recorded_at = None`;
- `recorded_at_raw = None`;
- no timezone or UTC offset is inferred;
- no chronological sorting is authorized; and
- acquisition `retrieved_at`, when captured by mandatory history provenance, does
  not become event time.

The absence of event time does not invalidate a non-empty canonical event because
the event contract permits provider-native code, status, description, location, or
actor evidence as minimum content.

## Completeness, ordering, and pagination finding

- Completeness: `UNKNOWN`.
- Ordering: `SOURCE_ORDER` only as preservation of returned array position;
  otherwise `UNKNOWN`.
- Chronological ordering: not supported.
- `has_more`: `None`.
- `next_page_token`: `None`.
- Multi-page assembly: not authorized.

An absent pagination indicator does not prove complete history. Preserved array
position does not prove chronology.

## Provenance and correlation finding

The history can satisfy the canonical correlation invariant with directly supplied
request `tracking_number` and, when present, `carrier_code` as
`carrier_reference`.

Mandatory history provenance must be supplied by the Commerce AI acquisition
boundary and must identify the exact registered source, V2 operation, retrieval
context, and source reference. This does not authorize a live call in this
worksheet and does not convert evaluation time into provider evidence.

No event-level carrier, custodian, facility owner, postal operator, or physical
handler is inferred from history-level correlation.

## Identity, relationship, and normalization finding

- Stable event identity: unresolved; `provider_event_id=None`.
- Provider code: `status_code` may remain provider-native.
- Carrier code: `carrier_status_code` may remain a raw status value.
- Detail code: `carrier_detail_code` may remain source-local metadata.
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
| At least one history correlation reference | `pass` | Request tracking number; carrier code when supplied |
| Mandatory history provenance | `pass prospectively` | Commerce AI acquisition envelope is required |
| Immutable event collection | `pass prospectively` | Response array can be frozen without semantic change |
| Event minimum content | `pass conditionally` | At least one supported status, description, or location value required |
| Timezone-aware canonical datetime | `not applicable` | No canonical event datetime is populated |
| Location minimum content | `pass conditionally` | Location omitted when no supported non-empty field exists |
| Actor minimum content | `not applicable` | Actor omitted |
| Relationship reference | `not applicable` | Relationships omitted |
| Completeness rules | `pass` | `UNKNOWN`; no completeness inference |
| Ordering rules | `pass` | Response order preserved without chronological claim |
| Pagination rules | `pass` | Pagination fields remain `None`; no completeness inference |
| Non-destructive collection rules | `pass prospectively` | No deduplication, correction, or overwrite authorized |
| Source identity separation | `pass` | ShipEngine v1 and legacy V1 evidence excluded |

`pass prospectively` means that a future authorized implementation could satisfy
the invariant using the stated envelope or immutable representation. It is not an
implementation authorization or runtime verification result.

## Unresolved requirements

The following remain unresolved and are not required to be manufactured for the
bounded projection:

1. stable provider event identity;
2. event occurrence time and timezone;
3. provider-recorded or received time;
4. event-level actor and carrier identity;
5. event scope and scope reference;
6. chronological ordering guarantee;
7. complete or partial history semantics;
8. pagination or truncation behavior;
9. duplicate, correction, replacement, and revision semantics;
10. provider-supplied response retrieval time;
11. provider update cadence and freshness policy; and
12. deterministic assembly across repeated retrievals, polling, or webhooks.

These gaps prevent claims of complete canonical coverage, chronology, event
identity, freshness, or verified route history. They do not prevent preservation
of the directly supported bounded event snapshot.

## Compatibility proposal

Proposed result:

- `canonical_projection_compatibility`: `observed`;
- projection scope: bounded ShipStation V2 `get_tracking_log` response snapshot;
- compatibility strength: `partial`;
- completeness: `UNKNOWN`;
- ordering: `SOURCE_ORDER` when response order is preserved, otherwise `UNKNOWN`;
- temporal projection: absent at event level;
- source identity: ShipStation platform API V2 only;
- production readiness: not established.

Proposed observation value:

> ShipStation V2 `get_tracking_log` prospectively supports a bounded
> `observed_route_event_history` projection by preserving its `events[]`
> collection, provider- and carrier-native status fields, status description,
> directly supported location evidence, and request carrier and tracking
> correlation within Commerce AI-owned history provenance. Completeness remains
> `UNKNOWN`; response position carries no chronological meaning; event occurrence,
> recorded time, stable identity, actor, relationship, duplicate, revision,
> pagination, and freshness semantics remain absent or unresolved and are not
> inferred.

This is a worksheet proposal only. The existing dossier record
`cb-ea3b1-shipstation-006` remains `unknown / None` until a separately authorized
dossier-mutation gate evaluates and approves the exact replacement value.

## Boundary result

- direct field mapping: `PASS WITH EXPLICIT GAPS`;
- canonical invariants: `PASS FOR BOUNDED PARTIAL PROJECTION`;
- prohibited inference required: `NO`;
- adjacent-source attribution: `NONE`;
- candidate admission or selection: `NOT AUTHORIZED`;
- production implementation: `NOT AUTHORIZED`;
- dossier mutation: `NOT AUTHORIZED`;
- current dossier compatibility value: `unknown / None — UNCHANGED`;
- worksheet proposed compatibility: `observed`.

## Required next gate

The worksheet must undergo a separate read-only validation and research decision
gate. No dossier record may change until that decision is sealed and an exact
dossier-mutation gate is separately authorized.
