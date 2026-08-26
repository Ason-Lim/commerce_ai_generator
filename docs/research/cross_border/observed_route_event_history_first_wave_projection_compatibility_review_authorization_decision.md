# Observed Route Event History First-Wave Projection Compatibility Review Authorization Decision

## Document status

- Gate: `CB-EA5B-8T-3`
- Status: `research review authorization decision`
- Decision scope: first-wave candidate-specific projection compatibility review
- Canonical target family: `observed_route_event_history`
- Authorized candidates:
  - `candidate:shipping:shipstation-api`;
  - `candidate:shipping-landed-cost:mydhl-api`.
- Production implementation: `not authorized`
- Dossier mutation: `not authorized`
- Compatibility mutation: `not performed`

## Purpose

This decision determines whether the two directly reviewed registered sources may
enter candidate-specific research evaluation against the sealed
`observed_route_event_history` canonical contract.

It authorizes evaluation work only. It does not decide that either candidate is
compatible, incompatible, sufficient, admitted, selected, ranked, preferred, or
production-ready.

## Sealed inputs

The authorization relies on these sealed research inputs:

1. `observed_route_event_history_canonical_contract_definition.md`;
2. `observed_route_event_history_target_family_ownership_decision.md`;
3. `observed_route_event_history_integrated_contract_readiness_review.md`;
4. `direct_registered_source_tracking_schema_sufficiency_review.md`;
5. `external_evidence_provider_evaluation_dossier.md`.

The sealed canonical definition is authoritative for target semantics. Provider
documentation remains authoritative only for the fields and behaviors explicitly
documented by each provider.

## Evaluation subjects

### ShipStation V2

- Candidate identity: `candidate:shipping:shipstation-api`
- Product surface: ShipStation platform API V2
- Base URL: `https://api.shipstation.com/v2`
- Evaluated operation: V2 `get_tracking_log`

ShipStation API formerly ShipEngine v1 and legacy ShipStation V1 are outside this
subject. Their evidence must not be attributed to ShipStation V2.

### MyDHL API

- Candidate identity: `candidate:shipping-landed-cost:mydhl-api`
- Product surface: DHL Express MyDHL API
- Inspected version: `3.3.1`
- Base URL: `https://express.api.dhl.com/mydhlapi`
- Evaluated operations:
  - `GET /shipments/{shipmentTrackingNumber}/tracking`;
  - `GET /tracking`.

DHL Shipment Tracking - Unified is outside this subject. Its evidence must not be
attributed to MyDHL API.

## Governing distinction

Canonical contract sufficiency and candidate projection compatibility are
different questions.

- `canonical contract sufficiency` asks whether a provider schema can establish
  the canonical rules themselves;
- `candidate projection compatibility` asks whether directly documented provider
  values can be conservatively represented within the already established
  canonical rules without prohibited inference.

The sealed direct-source review found both provider schemas insufficient to
establish the complete canonical contract. That finding does not independently
prove incompatibility with a canonical contract that explicitly represents
partial history, unknown ordering, optional fields, source-native values, and
unresolved semantics.

Conversely, structural similarity does not prove compatibility. Each mapping must
be evaluated field by field against canonical validation, provenance, temporal,
ordering, completeness, relationship, pagination, and non-inference rules.

## Authorized evaluation questions

For each candidate, the review may determine:

1. whether a provider response can form one bounded
   `ObservedRouteEventHistory` evidence snapshot;
2. which provider fields can populate canonical fields directly;
3. which canonical fields must remain `None`, empty, provider-native, or unknown;
4. whether completeness must be `PARTIAL` or `UNKNOWN`;
5. whether ordering must be `SOURCE_ORDER` or `UNKNOWN` rather than chronological;
6. whether occurrence time is directly supported and timezone-aware;
7. whether recorded, retrieved, and evaluated times have distinct evidence;
8. whether provider event identifiers, shipment references, and source-record
   references are directly available;
9. whether location, actor, and relationship objects can be populated without
   inference;
10. whether pagination, polling, webhook, duplication, correction, and revision
    semantics require explicit unresolved findings;
11. whether any required canonical invariant makes a bounded projection
    incompatible; and
12. what additional evidence would be required to resolve an unknown result.

## Required output discipline

Each candidate must receive a separate worksheet. A worksheet must contain:

- exact candidate identity, product surface, version, base URL, and operation;
- exact official source references used;
- a provider-field-to-canonical-field matrix;
- direct, partial, absent, and prohibited-inference findings;
- canonical invariant checks;
- completeness, ordering, pagination, temporal, provenance, relationship, and
  freshness findings;
- explicit unresolved gaps;
- an independently stated proposed compatibility result; and
- confirmation that no production or dossier mutation was performed.

The permitted proposed results are:

- `observed` with a bounded projection statement;
- `unknown / None` with unresolved requirements;
- `incompatible` with the exact violated invariant.

A worksheet result is a research proposal only. It does not mutate the dossier
unless a later dossier-mutation gate separately authorizes the exact record change.

## Candidate order

The first-wave review order is:

1. `candidate:shipping:shipstation-api`;
2. `candidate:shipping-landed-cost:mydhl-api`.

ShipStation V2 is evaluated first to test the weakest directly reviewed temporal
structure against the canonical contract's partial and unknown semantics. MyDHL
API follows with its stronger occurrence-time, GMT-offset, and structured-location
evidence.

The sequence does not rank or prefer either provider.

## Excluded candidates and sources

This decision does not authorize evaluation of:

- ShipStation API formerly ShipEngine v1;
- legacy ShipStation V1;
- DHL Shipment Tracking - Unified;
- Shippo tracking schemas;
- EasyPost tracking schemas;
- TracX SmartShip;
- Korea Post EMS;
- Fassto FMS;
- Delivered Korea; or
- any unregistered or newly discovered source.

Those subjects require their own direct-evidence and authorization gates. Shared
brand, carrier coverage, response similarity, redirect behavior, partnership, or
corporate ownership does not merge source identities.

## Explicit prohibitions

The authorized review must not:

- infer chronological order from array position;
- infer completeness from silence, end-of-array, or `has_more=False` alone;
- infer occurrence time from retrieval or webhook-delivery time;
- infer timezone or UTC offset from location;
- infer stable event identity from content similarity;
- infer event-level carrier or actor identity from the reporting API alone;
- map provider status codes into a canonical status taxonomy that is not defined;
- destructively deduplicate or replace events;
- merge polling and webhook records without a separately authorized assembly rule;
- attribute adjacent-source evidence to a registered candidate;
- perform live API calls, credential use, historical backfill, or runtime testing;
- modify production code, registries, adapters, projectors, or serializers; or
- mutate the provider evaluation dossier.

## Authorization decision

The first-wave candidate-specific projection compatibility review is
`AUTHORIZED` for:

1. ShipStation V2 `get_tracking_log`; and
2. MyDHL API Tracking operations in inspected version `3.3.1`.

Authorization is limited to separate research worksheets evaluated against the
sealed `observed_route_event_history` canonical contract.

At this gate:

- source-identity separation: `PASS`;
- direct-schema evidence availability: `PASS`;
- candidate-specific review authorization: `AUTHORIZED`;
- adjacent-source attribution: `DENIED`;
- candidate admission or selection: `NOT AUTHORIZED`;
- compatibility decision: `NOT PERFORMED`;
- dossier mutation: `NOT AUTHORIZED`;
- production implementation: `NOT AUTHORIZED`;
- existing `canonical_projection_compatibility = unknown / None`: `UNCHANGED`.

## Required next gate

The next gate is `CB-EA5B-8U`, beginning with a ShipStation V2 candidate-specific
projection compatibility worksheet. The worksheet must remain separate from the
MyDHL worksheet and must preserve all source-identity and non-inference boundaries
defined here.
