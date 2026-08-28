# TracX SmartShip Observed Route Event History Projection Compatibility Worksheet

## Document status

- Gate: `CB-EA5E-2`
- Artifact type: candidate-specific research compatibility worksheet
- Candidate source identity:
  `candidate:shipping-aggregator:tracx-smartship`
- Evaluated operation: polling `SmartShipService.Tracking`
- Evaluated collection: polling `tracking_history`
- Delivery WebHook: excluded
- `MultiTracking`: excluded
- Dossier mutation: not authorized
- Projector implementation: not authorized
- Production or runtime mutation: not authorized

This worksheet is a research proposal. It does not change the current
provider-evaluation dossier value, authorize an implementation, or activate a
provider.

## Purpose

This worksheet evaluates whether the directly registered TracX SmartShip
polling Tracking evidence can be projected into the canonical
`observed_route_event_history` family without manufacturing identity, time,
actor, completeness, ordering, or planned-route semantics.

The evaluation is deliberately limited to a bounded partial projection. It
does not evaluate live credentials, live API behavior, webhook delivery,
`MultiTracking` assembly, commercial superiority, or production readiness.

## Evaluation subject identity

| Property | Value |
|---|---|
| Candidate identity | `candidate:shipping-aggregator:tracx-smartship` |
| Reporting-source role | Cross-border shipping aggregator candidate |
| Publisher observed in registered evidence | TracX Logis |
| Polling operation | `SmartShipService.Tracking` |
| Polling event collection | `tracking_history` |
| Dossier compatibility row | `cb-ea4r6-tracx-smartship-006` |
| Current dossier state | `unknown` |
| Current dossier value | `None` |
| Worksheet proposal | `observed` |
| Implementation authority | None |

TracX Logis is the reporting-source candidate. It must not automatically
become the physical carrier or event actor.

## Sealed research inputs

This worksheet is governed by:

1. the canonical `observed_route_event_history` contract definition;
2. the sealed TracX SmartShip candidate-admission evidence;
3. the sealed next-wave candidate boundary decision;
4. the current provider-evaluation dossier;
5. the polling-versus-webhook separation rule.

Adjacent provider evidence is not imported.

## Authorized evidence surface

The authorized source surface is exactly:

- the polling `SmartShipService.Tracking` response;
- its `tracking_history` collection;
- polling response correlation fields established in registered evidence;
- polling event-field categories established in registered evidence.

The following are outside this worksheet:

- `MultiTracking` collection assembly;
- Delivery WebHook payload projection;
- webhook-only `PackingNo`;
- webhook-only `TrackingNo`;
- webhook-only `RefOrderNo`;
- webhook-only `DeliveryCompanyCode`;
- webhook-only `DeliveryCompanyName`;
- webhook delivery, retry, authentication, timing, or ordering semantics;
- Korea Post EMS;
- planned-route topology;
- live API acquisition.

Webhook carrier identity must not be copied onto polling history entries.

## Directly observed polling structure

Registered official evidence establishes that:

- `SmartShipService.Tracking` returns a `tracking_history` collection;
- polling history entries contain status evidence;
- polling history entries contain status-code evidence;
- polling history entries contain `date`;
- polling history entries contain location evidence;
- polling history entries contain details and reason evidence;
- polling history entries contain tracking-specific codes;
- polling history entries contain proof-of-delivery references;
- the Tracking response contains correlation fields including
  `shipping_no`, `ref_no`, and `qs_no`.

The registered evidence does not establish:

- stable event identity;
- stable provider event sequence;
- chronological ordering;
- complete-history semantics;
- pagination or truncation semantics;
- duplicate, correction, or revision semantics;
- retention or update-latency semantics;
- event occurrence versus provider-recorded-time meaning;
- timezone or UTC offset;
- response observation time;
- event-level physical-carrier identity;
- webhook equivalence;
- proof-of-delivery identity or delivery-correctness semantics.

## Projection boundary

A compatible projection must satisfy all of the following:

1. preserve provider-native status evidence without normalization;
2. preserve unresolved temporal evidence as raw source evidence;
3. preserve location only at directly supported strength;
4. keep polling and webhook acquisitions separate;
5. preserve response entries without deduplication or destructive merging;
6. disclose completeness and ordering gaps;
7. avoid globally unique identity claims;
8. avoid event actor inference;
9. avoid planned-route inference;
10. reject events with no supported canonical minimum content.

## History-level field mapping

| Canonical field | TracX polling evidence | Proposed projection | Finding |
|---|---|---|---|
| `reporting_source_id` | Fixed candidate identity | `candidate:shipping-aggregator:tracx-smartship` | Direct |
| `provenance` | Mandatory Commerce AI acquisition provenance | Required provenance object | Prospective requirement |
| `events` | `tracking_history` entries | Immutable event tuple preserving returned entries | Direct collection boundary |
| `carrier_reference` | No polling event-level carrier identity established | `None` | No webhook attribution |
| `tracking_number` | `shipping_no`, `ref_no`, and `qs_no` are correlation candidates | Populate only from the explicitly selected acquisition correlation | No inferred priority |
| `source_record_id` | No globally stable source-record identity established | `None` unless a direct contract later establishes one | Conservative |
| `request_correlation_id` | Polling correlation values may be retained | Populate only when request ownership is explicit | Conditional |
| `completeness` | Complete or partial history semantics not documented | `UNKNOWN` | Required conservative value |
| `ordering` | Returned collection position without chronological guarantee | `SOURCE_ORDER` only when response order is preserved; otherwise `UNKNOWN` | Never chronological by default |
| `has_more` | Pagination indicator not established | `None` | No inference |
| `next_page_token` | Page token not established | `None` | No inference |
| `freshness` | Provider freshness field not established | `None` | Retrieval is not freshness evaluation |
| `constraints` | Known semantic gaps | Immutable disclosure strings | Research-level disclosure |
| `metadata` | Additional source-local correlations | Immutable mapping where retained | Must not change canonical meaning |

No canonical preference among `shipping_no`, `ref_no`, and `qs_no` is inferred.
A caller or later acquisition contract must identify the owned tracking
correlation explicitly.

## Required history constraints

A future bounded projection would disclose constraints equivalent to:

- `history_completeness_not_documented`;
- `chronological_order_not_documented`;
- `stable_event_identity_not_documented`;
- `stable_event_sequence_not_documented`;
- `provider_recorded_time_not_documented`;
- `event_level_actor_identity_not_documented`;
- `event_level_carrier_identity_not_documented`;
- `duplicate_and_revision_semantics_not_documented`;
- `pagination_and_truncation_semantics_not_documented`;
- `retention_and_update_latency_not_documented`;
- `temporal_format_and_timezone_unresolved`;
- `proof_of_delivery_identity_semantics_unresolved`;
- `polling_webhook_surface_separation_required`.

These are worksheet-level semantic requirements. This worksheet does not
authorize an exact implementation constraint tuple.

## Event-level field mapping

| Canonical field | TracX polling evidence | Proposed projection | Finding |
|---|---|---|---|
| `provider_event_id` | Stable event identifier not established | `None` | Must not manufacture identity |
| `provider_event_code` | Status-code and tracking-specific-code evidence exists | Preserve one directly designated provider code without combining unrelated codes | Conditional |
| `raw_status` | Provider-native status evidence exists | Preserve trimmed non-empty source status | Direct |
| `raw_status_description` | Details and reason evidence exists | Preserve a directly descriptive value without synthesizing a sentence | Conditional |
| `occurred_at` | `date` lacks timezone and occurrence-time guarantee | `None` | Canonical datetime prohibited |
| `occurred_at_raw` | Polling `date` is described as history-change date | Preserve the non-empty raw `date` value | Direct raw preservation |
| `recorded_at` | Provider-recorded instant not established | `None` | No inference |
| `recorded_at_raw` | Separate recorded-time field not established | `None` | No field reassignment |
| `location` | Polling location evidence exists | Raw description only when non-empty | Bounded |
| `actor` | Polling event-level actor not established | `None` | Reporting source is not actor |
| `scope` | Event ownership scope not directly established | `UNKNOWN` | No shipment/package inference |
| `scope_reference` | Event scope reference not established | `None` | No correlation promotion |
| `source_sequence` | Stable provider-native sequence not established | `None` | Array index is not identity |
| `relationships` | Duplicate, correction, and supersession relations not established | Empty tuple | No similarity inference |
| `provenance` | Event-specific provenance not separately established | `None` or the same directly supported provenance only if later authorized | No manufacture |
| `metadata` | Reason, additional codes, and POD references may be source-local | Preserve separately and immutably when non-empty | No semantic promotion |

A tracking-specific code must not be merged with a status code into a
manufactured canonical identifier. When multiple code roles are present, their
source roles remain distinct.

Details and reason values must not be concatenated into a new provider
statement. A value may populate `raw_status_description` only when its direct
source role is descriptive; other non-empty values remain metadata.

## Temporal finding

The polling `date` value is described as a history-change date, but the
registered contract does not establish:

- timezone;
- UTC offset;
- whether the value denotes physical event occurrence;
- whether the value denotes provider recording;
- whether the value denotes response retrieval;
- whether all entries use one stable format.

Therefore:

- `occurred_at` remains `None`;
- `recorded_at` remains `None`;
- `recorded_at_raw` remains `None`;
- a non-empty polling `date` may be preserved as `occurred_at_raw`;
- no timezone is inferred from location, account, carrier, request time, or
  webhook documentation;
- no chronological sorting is authorized.

The webhook `Date` format is adjacent-surface evidence and does not establish
the polling `date` format.

## Location subprojection

| Canonical location field | Polling evidence | Proposed value |
|---|---|---|
| `raw_description` | Non-empty polling location value | Preserve directly |
| `country_code` | Not separately established | `None` |
| `subdivision` | Not separately established | `None` |
| `locality` | Not separately established | `None` |
| `postal_code` | Not separately established | `None` |
| `facility_reference` | Not separately established | `None` |
| `facility_name` | Not separately established | `None` |

The source location value does not prove custody, jurisdiction, customs
clearance, carrier identity, or physical facility ownership.

An empty or unsupported location value produces no location object.

## Proof-of-delivery reference finding

Polling proof-of-delivery references may be retained only as source-local
metadata when their exact source role and non-empty value are directly
available.

They do not establish:

- successful delivery;
- delivery correctness;
- recipient identity;
- signature identity;
- legal proof;
- financial liability;
- event identity.

No binary delivered state is inferred from the presence of a POD reference.

## Event minimum-content check

A projected event must contain at least one supported non-empty canonical
content value, such as:

- provider event code;
- raw status;
- directly descriptive status text;
- raw polling `date`;
- raw location description.

Metadata-only content is insufficient.

A reason, tracking-specific auxiliary code, or POD reference retained only as
metadata must not create an otherwise empty canonical event.

If any source entry cannot satisfy minimum content, a future projection must
fail closed for the evaluated collection rather than return a partial
canonical history.

## Completeness, ordering, and pagination finding

- Completeness: `UNKNOWN`.
- Ordering: `SOURCE_ORDER` only when returned array position is preserved.
- Chronological ordering: not established.
- `has_more`: `None`.
- `next_page_token`: `None`.
- Retention boundary: unknown.
- Truncation boundary: unknown.
- Duplicate policy: unknown.
- Revision policy: unknown.

Preserving array order does not prove chronological order. Absence of a page
token does not prove complete history.

No sorting, deduplication, correction, overwriting, or cross-acquisition merge
is authorized.

## Provenance and correlation finding

History provenance remains mandatory.

The provenance source identity is fixed to
`candidate:shipping-aggregator:tracx-smartship`.

The polling correlations `shipping_no`, `ref_no`, and `qs_no` remain
provider-local. They do not become globally unique canonical shipment
identity, and their mutual precedence is not inferred.

The reporting source is not automatically:

- the physical carrier;
- the event actor;
- the location owner;
- the delivery company for each event.

Webhook-only delivery-company fields remain excluded.

## Polling and webhook separation check

| Rule | Finding | Reason |
|---|---|---|
| Polling response evaluated independently | `pass` | Worksheet is limited to `SmartShipService.Tracking` |
| `tracking_history` retained as polling collection | `pass` | Direct registered polling evidence |
| Webhook fields copied to polling events | `none` | Explicitly prohibited |
| Webhook carrier identity inferred for polling | `none` | Event-level polling carrier identity unresolved |
| Webhook `Date` format applied to polling `date` | `none` | Separate observation surfaces |
| Webhook delivery treated as complete history | `none` | Webhook excluded |
| `MultiTracking` assembly performed | `none` | Outside authorized boundary |

## Identity, relationship, and normalization finding

The worksheet does not authorize:

- a manufactured canonical event identifier;
- content hashes as event identity;
- array indexes as provider event identity;
- normalized provider-independent status;
- carrier attribution from aggregator identity;
- duplicate relationships from similar content;
- correction or supersession relationships;
- planned-route topology;
- provider selection or ranking.

Provider-native statuses and codes remain provider-local evidence.

## Canonical invariant checks

| Canonical invariant | Finding | Basis |
|---|---|---|
| Non-empty reporting source | `pass` | Fixed candidate identity |
| At least one history correlation | `pass conditionally` | Explicit acquisition-owned correlation required |
| Mandatory history provenance | `pass prospectively` | Acquisition envelope remains required |
| Immutable event collection | `pass prospectively` | Polling array can be frozen without semantic change |
| Event minimum content | `pass conditionally` | Supported code, status, description, raw date, or location required |
| Timezone-aware `occurred_at` | `not populated` | Timezone and occurrence meaning unresolved |
| Unresolved temporal preservation | `pass` | Polling `date` remains raw |
| Location minimum content | `pass conditionally` | Empty location produces no object |
| Actor minimum content | `not applicable` | Actor omitted |
| Scope ownership | `unresolved` | Scope remains `UNKNOWN` |
| Relationship references | `not applicable` | Relationships omitted |
| Completeness rules | `pass` | `UNKNOWN`; no inference |
| Ordering rules | `pass` | Source order only when preserved |
| Pagination rules | `pass` | Pagination fields remain `None` |
| Non-destructive history | `pass prospectively` | No deduplication or overwrite |
| Polling/webhook separation | `pass` | Webhook evidence excluded |
| Planned-route separation | `pass` | No route topology projection |
| Source identity separation | `pass` | Aggregator is not physical carrier by default |

## Unresolved requirements

The following remain unresolved:

1. exact polling field-key spellings and type/cardinality constraints beyond
   the registered evidence categories;
2. stable provider event identity;
3. stable provider event sequence;
4. chronological ordering guarantee;
5. complete or partial history semantics;
6. pagination, truncation, and retention behavior;
7. duplicate, correction, and revision semantics;
8. polling `date` format, timezone, and temporal ownership;
9. provider-recorded and response-observation time;
10. event-level carrier and actor identity;
11. correlation-field precedence and identity ownership;
12. details-versus-reason descriptive roles;
13. status-code versus tracking-specific-code precedence;
14. POD reference identity and lifecycle;
15. provider update latency and freshness;
16. live response drift from the registered publication.

These gaps do not require prohibited inference for the bounded projection
described here. They must remain constraints or `None`.

## Compatibility proposal

Direct polling event-history evidence can support a bounded partial canonical
projection when all of the following are enforced:

- fixed TracX SmartShip candidate source identity;
- explicit acquisition-owned history correlation;
- immutable preservation of polling `tracking_history` entries;
- provider-native status and code preservation;
- raw-only preservation of polling `date`;
- raw-only location preservation;
- no event actor or physical-carrier inference;
- `UNKNOWN` completeness;
- source order without chronological meaning;
- no pagination inference;
- no deduplication or relationship inference;
- polling/webhook separation;
- fail-closed minimum-content validation;
- immutable disclosure of unresolved constraints.

Accordingly, this worksheet proposes:

- compatibility state: `observed`;
- compatibility value: bounded polling projection with explicit unresolved
  semantics and no webhook attribution.

This proposal does not mutate dossier record
`cb-ea4r6-tracx-smartship-006`.

That dossier record remains `unknown / None` until a separately authorized
compatibility decision and exact dossier-mutation gate approve a replacement.

## Boundary result

- directly observed polling collection: `PASS`;
- direct field mapping: `PASS WITH EXPLICIT GAPS`;
- canonical invariants: `PASS FOR BOUNDED PARTIAL PROJECTION`;
- prohibited inference required: `NO`;
- webhook attribution: `NONE`;
- `MultiTracking` assembly: `NONE`;
- planned-route consequence: `NONE`;
- dossier mutation: `NONE`;
- projector implementation: `NOT AUTHORIZED`;
- production or runtime mutation: `NONE`;
- current dossier compatibility: `unknown / None — UNCHANGED`;
- worksheet proposed compatibility: `observed`.

## Required next gate

The next gate is:

`CB-EA5E-3_TRACX_SMARTSHIP_OBSERVED_ROUTE_EVENT_HISTORY_PROJECTION_COMPATIBILITY_VALIDATION`

It must perform a read-only validation of this worksheet against the sealed
canonical contract, TracX admission evidence, current dossier, and next-wave
boundary decision.

Only after that validation may a separate compatibility decision consider
whether the worksheet proposal is supportable.

This worksheet does not authorize dossier mutation, projector implementation,
package export, registry mutation, network acquisition, credentials use,
persistence, runtime activation, commit, tag, or push.
