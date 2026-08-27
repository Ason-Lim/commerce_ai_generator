# Observed Route Event History Implementation Ownership and Reuse Decision

## Document status

- Gate: `CB-EA5B-8X-2`
- Artifact type: implementation-authorization architecture decision
- Status: `PHASE-1 CANONICAL MODEL IMPLEMENTATION AUTHORIZED`
- Provider projector implementation: `NOT AUTHORIZED`
- Runtime activation: `NOT AUTHORIZED`
- Production mutation performed by this decision: `NO`

## Purpose

This decision assigns exact production ownership for the sealed
`observed_route_event_history` canonical contract and defines the bounded first
implementation phase.

It resolves module ownership, reuse of provenance and freshness contracts, public
exports, validation ownership, test ownership, serialization scope, registry
effects, migration behavior, and rollback scope before production code changes.

## Sealed baseline

- repository HEAD: `7dc6d3aa31280fc4f56548dd9c98d9f2a83f0725`;
- canonical contract SHA-256:
  `b112e77bc991801e76a898695c74b9f3c9aa9870ad9f11da20deb6a6469c6975`;
- target-family ownership decision SHA-256:
  `c2c2f399d57617acd7bb541df501913a3dc000f9a283d769b89de16bf70cc104`;
- first-wave dossier SHA-256:
  `3e3d2956ab7f44c1781febd6f24809e045461681d37feb498decd2073ec481c0`.

ShipStation V2 and MyDHL API each have a separately sealed `observed`
compatibility observation. Those observations establish research sufficiency for
bounded projections; they do not authorize provider-specific runtime projection.

## Inspected production baseline

The ownership review inspected these exact production artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `app/services/cross_border/shipping.py` | `33bdf2fdc98b9cee3892cbba377904e1f9b011ba4093ca57ec0a0cb659c59f93` |
| `app/services/cross_border/provenance.py` | `2a5a34d5574d8a37c35cb63384e3d6364fae11d09f454d743483d4c1473196a3` |
| `app/services/cross_border/freshness.py` | `63b55ad93e38d1691297ff72ede57c0cc2a450fb065128023c9ef179b1b608ea` |
| `app/services/cross_border/context.py` | `681256bd6464576396d323185c8b146f6ed7223487906f1ac769556bb19276f7` |
| `app/services/cross_border/external_evidence_ingress.py` | `809a9ce73ce64843e02a5b97c76209d7acb01e6bf1b061d621cd874c3753af36` |
| `app/services/cross_border/external_evidence_projection.py` | `f6d949c2598100f023d82808a57abde6f536799fcdc62196ec528cd017b97deb` |
| `app/services/cross_border/__init__.py` | `748269e16faf8fd15506fec59407fc20eef3aff6c8025822738b6d4882aa80b7` |

No production `ObservedRouteEvent*` type or
`OBSERVED_ROUTE_EVENT_HISTORY` projection target exists at this baseline.

## Target-family ownership decision

The canonical model will be owned by a new independent module:

`app/services/cross_border/observed_route_event_history.py`

This module owns only provider-neutral immutable canonical value objects,
normalization, and construction-time validation for observed shipment-event
history evidence.

It does not own planned route topology, provider acquisition, provider schema
interpretation, projection execution, ranking, recommendation, persistence, or
network activity.

## Shipping boundary

`app/services/cross_border/shipping.py` remains the exclusive owner of:

- `ShippingRouteType`;
- `ShippingAvailabilityState`; and
- `ShippingRouteEvidence`.

Those types express planned-route and availability evidence. They must not be
extended with observed-event history fields, enums, relationships, timestamps, or
collections.

Phase 1 authorizes no mutation of `shipping.py`.

## Authorized canonical types

The new module may implement exactly these sealed types:

- `ObservedRouteEventHistoryCompleteness`;
- `ObservedRouteEventHistoryOrdering`;
- `ObservedRouteEventScope`;
- `ObservedRouteEventActorRole`;
- `ObservedRouteEventRelationshipType`;
- `ObservedRouteEventLocation`;
- `ObservedRouteEventActor`;
- `ObservedRouteEventRelationship`;
- `ObservedRouteEvent`;
- `ObservedRouteEventHistory`.

The enum members, fields, defaults, collection types, and semantic distinctions
must match the sealed canonical contract. No provider-independent normalized
status or manufactured canonical event identifier may be added.

## Provenance reuse decision

`EvidenceProvenance` from `app/services/cross_border/provenance.py` is the required
provenance type.

- `ObservedRouteEvent.provenance` remains optional;
- `ObservedRouteEventHistory.provenance` is required; and
- `reporting_source_id` remains distinct from event actor identity.

No duplicate provenance class, provider-specific provenance subtype, or automatic
actor derivation is authorized.

Phase 1 authorizes no mutation of `provenance.py`.

## Freshness reuse decision

`EvidenceFreshness` from `app/services/cross_border/freshness.py` is the authorized
optional aggregate freshness type.

Freshness may be attached only when already evaluated under the existing
freshness contract. Construction of an event history does not independently
classify evidence as fresh or stale.

Missing freshness remains `None`. Phase 1 authorizes no mutation of
`freshness.py` or `context.py`.

## Validation ownership

The new module owns deterministic construction-time validation and conservative
normalization matching the sealed contract, including:

- trimming optional strings and converting empty optional strings to `None`;
- uppercasing an explicitly supplied country code without inferring one;
- requiring at least one populated location field when a location exists;
- requiring actor reference or actor name when an actor exists;
- requiring a non-empty provider-local related-event reference;
- requiring each event to satisfy the sealed minimum-content invariant;
- requiring non-empty `reporting_source_id`;
- validating tuple element types;
- enforcing pagination and completeness invariants;
- preserving source order unless stronger ordering is explicitly supported;
- rejecting naive `datetime` values without inferring a timezone;
- preserving raw temporal values when a timezone-aware instant is unavailable;
- copying collections to tuples; and
- freezing metadata as immutable mappings without deep provider interpretation.

Validation must raise deterministic `TypeError` or `ValueError` consistent with
existing Cross-Border canonical contracts.

## Public export decision

Phase 1 authorizes `app/services/cross_border/__init__.py` to import and expose the
ten authorized canonical types through its existing explicit `__all__` pattern.

No provider-specific symbol, factory, parser, projector, registry entry, or runtime
service may be exported.

## Test ownership

The required test owner is:

`tests/services/cross_border/test_observed_route_event_history.py`

The test suite must cover:

- every enum value;
- immutable dataclass behavior;
- normalization of optional strings;
- location and actor minimum-content rules;
- relationship validation and provider-local preservation;
- event minimum-content alternatives;
- timezone-aware and raw temporal handling;
- rejection of naive datetimes;
- tuple conversion and type rejection;
- immutable metadata behavior;
- required history provenance and reporting source;
- completeness, ordering, pagination, and bounded-window invariants;
- freshness reuse without implicit evaluation;
- absence of planned-route inference;
- absence of normalized status and canonical event ID; and
- package-level public exports.

Existing provenance, freshness, shipping, ingress, and projection tests must remain
passing.

## Serialization decision

Phase 1 authorizes no new `to_dict`, `from_dict`, JSON schema, API response model,
database serializer, or wire-format contract.

The canonical objects may use standard immutable Python values only. A later gate
must separately define datetime encoding, enum encoding, immutable mapping
encoding, backward compatibility, and public API stability before serialization is
introduced.

## Ingress and projection decision

Phase 1 does not add an `ExternalEvidenceKind` member, a
`CanonicalProjectionTarget` member, or a `projection_target_for` mapping.

It does not create an executable projector. ShipStation and MyDHL field mappings
remain sealed research observations rather than runtime adapters.

Accordingly, Phase 1 authorizes no mutation of:

- `external_evidence_ingress.py`;
- `external_evidence_projection.py`;
- their current tests; or
- any provider registry.

## Migration behavior

No database table, SQL migration, persisted schema, configuration registry, YAML
registry, API endpoint, or historical backfill is required or authorized for the
Phase-1 canonical model implementation.

The implementation is additive at the Python contract and package-export level.

## Rollback scope

Before any later consumer is authorized, Phase 1 can be rolled back by:

1. removing `observed_route_event_history.py`;
2. removing `test_observed_route_event_history.py`; and
3. removing only the corresponding imports and `__all__` entries from
   `app/services/cross_border/__init__.py`.

Rollback must not modify shipping, provenance, freshness, context, ingress,
projection, provider, registry, dossier, or research artifacts.

## Explicit prohibitions

This decision does not authorize:

- provider adapters or projectors for ShipStation, MyDHL, or any adjacent source;
- HTTP requests, credentials, polling, webhooks, pagination assembly, or backfill;
- inference of chronology from response position;
- inference of event time from retrieval or webhook-delivery time;
- inferred actors, relationships, scopes, locations, or stable event identities;
- destructive deduplication, replacement, aliasing, or cross-provider identity
  resolution;
- status taxonomy assignment or normalized delivery-state generation;
- freshness evaluation during model construction;
- ingress or projection registry changes;
- serialization, persistence, API endpoint, recommendation, ranking, or UI changes;
- database or configuration migration;
- deployment or runtime activation; or
- mutation of sealed research artifacts or dossier records.

## Authorization result

- independent production owner: `observed_route_event_history.py`;
- canonical model implementation: `AUTHORIZED FOR PHASE 1`;
- authorized production files: new model module and package `__init__.py` only;
- authorized test file: new focused canonical-contract test module only;
- provenance reuse: `REQUIRED`;
- freshness reuse: `AUTHORIZED AS OPTIONAL AGGREGATE VALUE`;
- shipping mutation: `NOT AUTHORIZED`;
- ingress or projection registry mutation: `NOT AUTHORIZED`;
- provider projector implementation: `NOT AUTHORIZED`;
- serialization or persistence: `NOT AUTHORIZED`;
- migration: `NONE`;
- runtime activation: `NOT AUTHORIZED`;
- production mutation performed here: `NO`.

## Required next gate

The next gate is `CB-EA5B-8X-3`, a read-only implementation plan and acceptance-test
matrix. Only after that matrix is validated may a separate gate create the three
authorized implementation artifacts and modify the package exports.
