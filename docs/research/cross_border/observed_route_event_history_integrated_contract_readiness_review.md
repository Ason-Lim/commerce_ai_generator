# Observed Route Event History Integrated Contract Readiness Review

## Document status

- Status: `research architecture readiness decision`
- Review ID: `CB-EA4Q-2I-3`
- Sealing gate: `CB-EA4Q-2I-4`
- Review date: `2026-08-26`
- Scope: integrated readiness for a future `observed_route_event_history`
  contract
- Authority: `research-only`
- Production model mutation: `not authorized`
- Canonical contract mutation: `not authorized`
- Dossier mutation: `none`
- Provider decision mutation: `none`
- New subject admission: `not authorized`

## Review question

Do the internal cross-border canonical precedents and the bounded external
tracking, shipment, fulfillment, and order evidence provide sufficient
readiness to:

1. define the observed-event problem;
2. begin a conservative architecture-contract design;
3. establish a canonical contract; or
4. implement production projection and runtime behavior?

These four readiness questions are evaluated separately.

## Predecessor decisions

This review depends on:

- `shipping_route_evidence_semantic_boundary_decision.md`;
- `direct_registered_source_tracking_schema_sufficiency_review.md`;
- the sealed candidate observations in
  `external_evidence_provider_evaluation_dossier.md`;
- the existing internal `EvidenceProvenance`, `EvidenceFreshness`,
  `ShippingRouteEvidence`, and `ShippingRouteType` contracts.

No independent repository artifact named `CB-EA4Q-2` was found during the
read-only inventory. The applicable internal precedents are therefore bounded
to the inspected semantic-boundary document and existing canonical model
contracts. Conversation-only or unstored findings are not treated as a
separately sealed repository authority.

## Exact subject identities

This review preserves the following registered subject identities:

| Subject identity | Bounded role |
|---|---|
| `candidate:shipping:shipstation-api` | Direct tracking-event schema precedent |
| `candidate:shipping-landed-cost:mydhl-api` | Direct tracking-event and temporal/location schema precedent |
| `candidate:shipping-aggregator:tracx-smartship` | Polling event-history and separate webhook precedent |
| `candidate:shipping:korea-post-ems` | Official postal tracking and item-correlation precedent |
| `candidate:fulfillment-aggregator:fassto-fms` | Fulfillment and shipment-status snapshot precedent |
| `candidate:shipping-aggregator:delivered-korea` | Order, shipment, carrier-request, and tracking-surface precedent |

These identities must not be flattened into a common `candidate:shipping:*`
namespace.

Their different subject roles remain material to provenance and semantic
interpretation.

## Evidence-boundary rule

This is a contract-requirement coverage review, not a cross-provider projection.

Evidence from multiple sources may demonstrate that a contract concern exists.
It must not be combined to assert that one provider supplies fields or
semantics documented only by another provider.

An aggregate coverage finding does not create:

- source identity equivalence;
- aliases;
- event-level provenance;
- payload compatibility;
- provider interoperability;
- canonical projection compatibility.

## Source-role findings

### ShipStation V2

The registered `get_tracking_log` source directly establishes:

- an `events[]` collection;
- provider or carrier status-code fields;
- status descriptions;
- carrier and tracking correlation;
- portions of event-location structure.

It does not directly establish event occurrence-time semantics, event offset,
provider-recording time, chronological ordering, history completeness,
duplicate or revision semantics, or evidence freshness.

### MyDHL API

The registered Tracking schema directly establishes:

- shipment-level and piece-level `events[]`;
- `typeCode` and `description`;
- `date`, `time`, and optional `GMTOffset`;
- structured `serviceArea`;
- shipment and piece tracking identifiers;
- structural separation of occurred events and `estimatedDeliveryDate`.

It does not directly establish a stable event identifier, provider-recording
time, ordering guarantees, history completeness, duplicate or revision
semantics, or retrieval freshness.

### TracX SmartShip

The registered source directly establishes:

- polling `tracking_history`;
- status and tracking-specific codes;
- date, location, details, and reason fields;
- shipment-correlation references;
- a separate Delivery WebHook contract;
- delivery-company identity in the webhook contract.

The polling and webhook surfaces remain separate. Webhook carrier identity must
not be attributed to each polling history entry without direct source support.

The source does not establish timezone, occurrence-time versus recording-time
meaning, ordering, completeness, pagination, duplicate handling, retention,
update latency, or webhook retry behavior.

### Korea Post EMS

The registered official surfaces establish:

- domestic and international postal-item tracking capability;
- EMS internet tracking;
- a 13-character postal-item query and correlation reference;
- separate EMS application, service-region, and rate surfaces.

They do not establish a public event-level response schema, event source
identity across postal operators, event timestamp semantics, ordering,
completeness, or production acquisition conditions.

### Fassto FMS

The registered source establishes:

- fulfillment and shipment-status snapshots;
- `invoiceNo`, `ordNo`, `slipNo`, `parcelCd`, and `parcelNm`;
- temporal fields including `ordDt`, `packDt`, and `updTime`;
- fulfillment work-state values.

These are not automatically carrier route events.

The public schema does not expose a carrier-event-history array or establish
the original carrier or downstream tracking provider as event-level source.

### Delivered Korea

The registered source establishes:

- Global Checkout order queries;
- Global Ship order registration;
- order and shipment correlation;
- requested carrier and domestic shipping-number fields;
- a public Global Tracking surface.

The public developer documentation does not expose a tracking-event endpoint,
event-history array, shipment-status webhook, event actor, ordered history, or
reusable tracking-response schema.

## Integrated requirement-coverage matrix

| Contract requirement | Integrated evidence | Readiness |
|---|---|---|
| Event collection | ShipStation, MyDHL, TracX | `covered` |
| Shipment or tracking correlation | Present across sources at provider-local scope | `covered_with_boundary` |
| Provider-native event code or status | ShipStation, MyDHL, TracX | `covered` |
| Status description or details | ShipStation, MyDHL, TracX | `covered` |
| Event occurrence time | Directly structured by MyDHL; TracX supplies an unresolved history-change date | `partial` |
| Timezone or UTC offset | Directly structured by MyDHL | `partial` |
| Event location or facility | MyDHL and TracX; ShipStation partial | `covered_structurally` |
| Event-level carrier or actor | Limited webhook evidence only | `insufficient` |
| Stable event identity | No sufficient direct source | `gap` |
| Stable event sequence | No sufficient direct source | `gap` |
| Occurred time versus recorded time | No sufficient direct distinction | `gap` |
| Retrieval or observation time | No sufficient provider response contract | `gap` |
| Ordering guarantee | No sufficient direct source | `gap` |
| Out-of-order semantics | No sufficient direct source | `gap` |
| Complete or partial-history state | No sufficient direct source | `gap` |
| Pagination or history window | No sufficient common contract | `gap` |
| Duplicate semantics | No sufficient direct source | `gap` |
| Correction or revision semantics | No sufficient direct source | `gap` |
| Estimated versus occurred distinction | Directly structured by MyDHL | `partial` |
| Event-level provenance | Incomplete and source-specific | `gap` |
| Event-history freshness policy | Existing general precedent only | `gap` |

## Internal provenance precedent

The existing `EvidenceProvenance` contract provides:

- `source_id`;
- `source_type`;
- `record_id`;
- `source_reference`;
- `retrieved_at`;
- `effective_at`;
- `metadata`.

This envelope is reusable as a bounded source and record-provenance precedent.

Its fields do not automatically mean:

- `effective_at` equals an event occurrence time;
- `retrieved_at` equals a carrier recording time;
- response-level provenance equals event-level provenance;
- an aggregator is the original actor for each downstream carrier event.

A future event-history contract must explicitly distinguish the reporting
source, source record, event actor when known, and event occurrence semantics.

## Internal freshness precedent

The existing `EvidenceFreshness` contract evaluates:

`effective_at -> retrieved_at -> unknown`

This vocabulary and unknown-state behavior are reusable precedents.

The existing time-selection rule is not automatically sufficient for event
history because:

- event occurrence age is not necessarily evidence freshness;
- provider recording time may differ from occurrence time;
- retrieval time measures observation of the response;
- history may be incomplete even when recently retrieved;
- an old event may be valid within a fresh response.

A separately authorized event-history freshness policy is required.

## Current shipping-contract boundary

`ShippingRouteEvidence` and `ShippingRouteType` remain planned-route contracts.

They must not be reused to represent:

- an event-history container;
- event status;
- event sequence;
- an occurred shipment;
- tracking completeness;
- event actor or custody.

This review does not rename or mutate those production contracts.

## Prohibited cross-source constructions

This review prohibits:

- applying MyDHL `GMTOffset` to a TracX timestamp;
- applying TracX webhook carrier identity to polling history entries;
- treating Fassto `updTime` as carrier event occurrence or recording time;
- treating Delivered Korea's requested carrier as the actual event actor;
- treating a Korea Post item number as globally unique canonical identity;
- using an adjacent ShipEngine or DHL Unified schema as direct evidence;
- treating example order as an ordering guarantee;
- treating an event collection as complete history;
- manufacturing missing event identity, sequence, timestamps, or provenance;
- composing fields from different sources into a fictional complete provider
  schema.

## Readiness decisions

### Problem-definition readiness

`PASS`

The inspected sources sufficiently demonstrate the practical need for event
collections, native event status, temporal evidence, location, correlation,
provenance, freshness, and explicit unknown or incomplete boundaries.

### Architecture-contract design readiness

`CONDITIONALLY_READY`

A conservative architecture-contract design may begin if it explicitly permits:

- provider-local correlation identity;
- absent stable event identity;
- unknown timezone;
- unknown provider-recording time;
- unordered or out-of-order history;
- unknown or partial completeness;
- unresolved duplicate and revision behavior;
- separation of event actor and reporting source;
- separation of occurred, recorded, retrieved, and evaluated times.

### Canonical-contract establishment readiness

`NOT_READY`

The following architecture decisions remain unresolved:

1. canonical owner and target-family name;
2. event identity and composite-key policy;
3. ordering and tie-breaking policy;
4. partial-history representation;
5. duplicate, correction, and revision handling;
6. occurred, recorded, retrieved, and evaluated-time semantics;
7. event actor and reporting-source provenance;
8. compatibility and migration behavior;
9. provider mapping and adapter authority;
10. validation and regression requirements.

### Production implementation readiness

`DENIED`

No production model, enum, target family, adapter, projector, provider mapping,
selection rule, acquisition behavior, or runtime integration is authorized.

## Projection consequence

Every reviewed candidate retains:

- `canonical_projection_compatibility`: `unknown`;
- canonical projection value: `None`.

Structural precedent does not constitute canonical projection compatibility.

## Final decision

The integrated evidence is sufficient to define the problem and conditionally
begin a conservative architecture-contract design.

It is not sufficient to establish a canonical contract or authorize production
implementation.

Therefore:

- bounded source reading: `pass`;
- exact subject identity preservation: `pass`;
- cross-provider attribution: `denied`;
- problem-definition readiness: `pass`;
- architecture-contract design readiness: `conditionally_ready`;
- canonical-contract establishment readiness: `not_ready`;
- production implementation: `denied`;
- canonical projection compatibility: `unknown`;
- canonical projection value: `None`;
- dossier mutation: `none`;
- production mutation: `none`.

## Required next architecture gate

Before any canonical or production change, a separately authorized architecture
gate must decide:

1. whether `observed_route_event_history` becomes a distinct canonical target
   family or another explicitly bounded structure;
2. contract ownership and naming;
3. event and history invariants;
4. identity, ordering, completeness, and revision rules;
5. temporal semantics;
6. event actor and reporting-source provenance;
7. freshness and observation semantics;
8. compatibility and migration behavior;
9. provider-mapping authority;
10. regression and operational safeguards.

This document does not make those architecture decisions.
