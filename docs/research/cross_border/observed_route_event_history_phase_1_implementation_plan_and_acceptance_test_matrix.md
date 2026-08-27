# Observed Route Event History Phase 1 Implementation Plan and Acceptance-Test Matrix

## Decision identity

- gate: `CB-EA5B-8X-3`;
- target family: `observed_route_event_history`;
- governing canonical contract: `observed_route_event_history_canonical_contract_definition.md`;
- governing authorization: `observed_route_event_history_implementation_ownership_and_reuse_decision.md`;
- implementation phase: `PHASE 1 CANONICAL MODEL ONLY`;
- production implementation performed by this record: `NO`.

This record converts the sealed canonical contract and implementation-ownership
decision into an executable implementation sequence and acceptance-test matrix.
It does not create, modify, import, register, serialize, persist, or activate the
canonical model.

## Authorized outcome

The later implementation gate may create a provider-neutral immutable canonical
model for observed shipment-event history evidence. The implementation must not
interpret a provider payload, infer planned route topology, normalize delivery
status, manufacture event identity, or activate a runtime projection.

The only authorized implementation artifacts are:

1. new `app/services/cross_border/observed_route_event_history.py`;
2. modified `app/services/cross_border/__init__.py`; and
3. new `tests/services/cross_border/test_observed_route_event_history.py`.

No other production, test, research, configuration, migration, or deployment file
is authorized for mutation by the Phase 1 implementation gate.

## Exact type inventory

The new model module may define and publicly expose exactly these canonical types:

1. `ObservedRouteEventHistoryCompleteness`;
2. `ObservedRouteEventHistoryOrdering`;
3. `ObservedRouteEventScope`;
4. `ObservedRouteEventActorRole`;
5. `ObservedRouteEventRelationshipType`;
6. `ObservedRouteEventLocation`;
7. `ObservedRouteEventActor`;
8. `ObservedRouteEventRelationship`;
9. `ObservedRouteEvent`; and
10. `ObservedRouteEventHistory`.

No provider-independent normalized status enum, canonical event identifier,
planned-route type, provider adapter, projector, serializer, or persistence model
may be added.

## Required type reuse

- `EvidenceProvenance` must be imported from `provenance.py`.
- `ObservedRouteEvent.provenance` must remain optional.
- `ObservedRouteEventHistory.provenance` must be required.
- `EvidenceFreshness` may be imported from `freshness.py` only as the optional
  aggregate `freshness` value.
- Construction must not evaluate or classify freshness.
- `reporting_source_id` must remain distinct from event actor identity.

`provenance.py`, `freshness.py`, and `context.py` must remain byte-for-byte
unchanged during the implementation gate.

## Implementation sequence

### Step 1 — module skeleton and imports

Create the independent module with standard-library imports for immutable
dataclasses, timezone-aware datetime validation, enums, immutable mappings, and
typing. Import only the existing provenance and freshness value objects required
by the contract.

The module must not import `shipping.py`, ingress, projection, provider clients,
API models, database models, recommendation services, or UI modules.

### Step 2 — sealed enums

Implement the five sealed enums with exactly the names and values defined by the
canonical contract. Defaults must remain:

- completeness: `UNKNOWN`;
- ordering: `UNKNOWN`;
- event scope: `UNKNOWN`; and
- actor role: `UNKNOWN`.

The relationship enum has only `DUPLICATE_OF`, `CORRECTS`, and `SUPERSEDES`.

### Step 3 — conservative normalization helpers

Implement private deterministic helpers sufficient to:

- require the expected runtime type where the existing module convention does;
- trim optional strings;
- normalize empty optional strings to `None`;
- uppercase an explicitly supplied country code;
- reject naive datetime values;
- copy iterable collections to tuples;
- validate every tuple element type; and
- freeze top-level metadata as an immutable mapping.

Helpers must not geocode, parse ambiguous codes, infer timezones, sort events,
deduplicate events, derive actors, classify freshness, or interpret provider
metadata.

### Step 4 — leaf value objects

Implement frozen `ObservedRouteEventLocation`, `ObservedRouteEventActor`, and
`ObservedRouteEventRelationship` dataclasses.

Location construction must reject a location whose normalized fields are all
`None`. Actor construction must reject an actor without a normalized reference or
name. Relationship construction must require an allowed relationship enum and a
non-empty normalized provider-local related-event reference.

### Step 5 — individual event

Implement frozen `ObservedRouteEvent` with the exact sealed field order, types,
defaults, and collection types.

Construction must:

- normalize its optional strings conservatively;
- require timezone-aware `occurred_at` and `recorded_at` when supplied;
- preserve unresolved temporal evidence only in the raw fields;
- retain `occurred_at` and `recorded_at` as separate concepts;
- require correct location, actor, relationship, and provenance element types;
- preserve relationship order while copying relationships to a tuple;
- freeze top-level metadata;
- enforce the event minimum-content invariant; and
- permit an event with no provider event ID when other minimum content exists.

Construction must not create a canonical ID, normalized status, inferred scope,
actor, location, relationship, or timestamp.

### Step 6 — history aggregate

Implement frozen `ObservedRouteEventHistory` with the exact sealed field order,
types, defaults, and collection types.

Construction must:

- require a non-empty normalized `reporting_source_id`;
- require an existing `EvidenceProvenance` instance;
- require at least one non-empty normalized source-local correlation reference;
- preserve event order while copying events to a tuple;
- validate all event elements;
- copy constraints to a tuple and validate their string elements;
- normalize empty constraint strings consistently with the sealed decision;
- freeze top-level metadata;
- accept `freshness=None`;
- accept an existing `EvidenceFreshness` without re-evaluation;
- enforce `has_more=True` implies `PARTIAL`; and
- enforce a non-empty `next_page_token` implies `PARTIAL`.

`has_more=False` must not change completeness to `COMPLETE`. Empty events must be
representable as a source response snapshot when the other history invariants are
satisfied.

### Step 7 — public exports

Update only `app/services/cross_border/__init__.py` to import and expose the ten
canonical types using the package's existing public-export convention.

Do not add an ingress evidence kind, projection target, projection mapping,
provider registration, runtime factory, API route, serializer, or database hook.

### Step 8 — focused canonical-contract tests

Create only `tests/services/cross_border/test_observed_route_event_history.py`.
Tests must exercise the acceptance matrix below and must not use network access,
provider fixtures, credentials, persistence, or runtime registry mutation.

### Step 9 — verification

Run the focused test module, the existing cross-border service test directory,
the full regression suite, and compile checks. Confirm that only the three
authorized implementation artifacts changed in addition to the two uncommitted
research records created by gates `CB-EA5B-8X-2` and `CB-EA5B-8X-3`.

## Acceptance-test matrix

| ID | Contract surface | Positive acceptance | Negative or boundary acceptance |
|---|---|---|---|
| `AT-01` | enum vocabulary | all five enums expose exactly the sealed values | no normalized status or extra relationship member exists |
| `AT-02` | enum defaults | completeness, ordering, scope, and actor role default to `UNKNOWN` | defaults do not imply complete, chronological, or shipment scope |
| `AT-03` | location normalization | strings trim; country code uppercases; raw and structured values may coexist | all-empty location is rejected; no geocoding or semantic inference occurs |
| `AT-04` | actor invariant | reference-only and name-only actors are valid | all-empty actor is rejected; reporting source is not auto-assigned |
| `AT-05` | relationship invariant | each sealed relationship with a non-empty reference is valid | empty reference and wrong relationship type are rejected |
| `AT-06` | event minimum content | every permitted minimum-content field can independently support an event | an otherwise empty event is rejected |
| `AT-07` | provider identity | provider IDs and codes are trimmed and preserved | missing ID remains `None`; no hash or source position becomes identity |
| `AT-08` | raw status | raw code and description remain distinct and preserved | description is not promoted to code and no delivery state is generated |
| `AT-09` | aware occurred time | aware `occurred_at` is accepted and preserved | naive `occurred_at` is rejected; timezone is not inferred |
| `AT-10` | aware recorded time | aware `recorded_at` is accepted and preserved | naive `recorded_at` is rejected; it is not copied from occurred time |
| `AT-11` | raw temporal evidence | raw occurred and recorded values can independently satisfy minimum content | raw values are not parsed into inferred instants |
| `AT-12` | event nested types | valid location, actor, relationships, and provenance are retained | wrong nested or tuple element types are rejected |
| `AT-13` | event tuple immutability | relationship input is copied to a tuple in source order | input mutation cannot mutate the stored tuple; no deduplication occurs |
| `AT-14` | event metadata | input mapping is copied to an immutable top-level mapping | top-level assignment and later input-dict mutation cannot change stored metadata |
| `AT-15` | reporting source | non-empty `reporting_source_id` trims and remains separate from actor | empty source ID is rejected and does not populate actor fields |
| `AT-16` | history provenance | existing `EvidenceProvenance` is required and retained | missing or wrong provenance type is rejected |
| `AT-17` | history correlation | each of the four correlation references can independently satisfy the invariant | all four absent or empty is rejected |
| `AT-18` | event collection | events are copied to an immutable tuple and source order is retained | wrong event elements are rejected; duplicates are not removed |
| `AT-19` | empty history | empty event tuple is representable with valid source, provenance, and correlation | emptiness does not imply completeness |
| `AT-20` | completeness | explicit enum values are preserved | missing pagination evidence does not auto-promote `UNKNOWN` to `COMPLETE` |
| `AT-21` | ordering | `SOURCE_ORDER` and supported explicit values are preserved | construction never sorts or upgrades ordering to `CHRONOLOGICAL` |
| `AT-22` | pagination `has_more` | `has_more=True` with `PARTIAL` is accepted | `has_more=True` with `UNKNOWN` or `COMPLETE` is rejected |
| `AT-23` | pagination token | non-empty token with `PARTIAL` is accepted | non-empty token with `UNKNOWN` or `COMPLETE` is rejected; empty token becomes `None` |
| `AT-24` | `has_more=False` | false is preserved with any otherwise valid completeness | false does not prove or create `COMPLETE` |
| `AT-25` | freshness reuse | `None` and an existing `EvidenceFreshness` are accepted | wrong type is rejected; construction performs no freshness evaluation |
| `AT-26` | constraints | constraint input is normalized, validated, and copied to a tuple | wrong element types are rejected and input mutation has no effect |
| `AT-27` | history metadata | input mapping is copied to an immutable top-level mapping | top-level assignment and later input-dict mutation cannot change stored metadata |
| `AT-28` | frozen dataclasses | all five value-object and aggregate dataclasses reject field reassignment | no mutable list remains in canonical collection fields |
| `AT-29` | public exports | all ten sealed types import from `app.services.cross_border` | no unrelated registry or provider symbol is added |
| `AT-30` | planned-route separation | canonical history constructs without `ShippingRouteEvidence` | no planned route, route type, price, duration, or availability field exists |
| `AT-31` | schema restraint | field names and defaults match the canonical contract | no canonical event ID, normalized status, serializer, or persistence method exists |
| `AT-32` | source preservation | repeated and similar events remain separate and ordered | construction does not correct, overwrite, supersede, or destructively deduplicate |

## Static file-scope acceptance

Before tests run, the implementation gate must prove that the only production and
focused-test paths changed are:

- `app/services/cross_border/observed_route_event_history.py`;
- `app/services/cross_border/__init__.py`; and
- `tests/services/cross_border/test_observed_route_event_history.py`.

The following files must remain unchanged:

- `app/services/cross_border/shipping.py`;
- `app/services/cross_border/provenance.py`;
- `app/services/cross_border/freshness.py`;
- `app/services/cross_border/context.py`;
- `app/services/cross_border/external_evidence_ingress.py`; and
- `app/services/cross_border/external_evidence_projection.py`.

No migration, schema, configuration, API, UI, ranking, recommendation, or provider
adapter file may change.

## Verification matrix

| Verification | Required result |
|---|---|
| focused canonical test module | all tests pass |
| `tests/services/cross_border` | all tests pass |
| full regression suite | all tests pass |
| compile check for new module and focused test | pass |
| package import smoke check | all ten public types import successfully |
| diff check | no whitespace error |
| artifact-scope check | only authorized paths plus the two research records are present |
| repository history | HEAD remains unchanged until a separate commit gate |
| remote state | no push or tag until separately authorized |

Test counts are observational outputs, not pre-authorized constants. A passing
result requires zero failures and zero errors; it does not require manufacturing a
predetermined count.

## Explicit exclusions

Phase 1 implementation must not perform or introduce:

- HTTP requests, credentials, polling, webhooks, pagination assembly, or backfill;
- provider payload parsing or ShipStation/MyDHL runtime adapters;
- inference of chronology from source position;
- inference of event time from retrieval or webhook-delivery time;
- inferred actors, relationships, scopes, locations, or identities;
- destructive deduplication, correction, replacement, or cross-provider matching;
- normalized status or delivery-state generation;
- freshness evaluation during construction;
- changes to shipping, provenance, freshness, context, ingress, or projection;
- serialization, persistence, API endpoints, ranking, recommendation, or UI work;
- database, schema, configuration, or deployment migration; or
- runtime activation.

## Failure and rollback rule

If an implementation acceptance fails, stop before commit, tag, push, registry
mutation, or runtime activation. The implementation gate may modify only its three
authorized implementation artifacts. The two research records must not be altered
to conceal a failed implementation.

Because Phase 1 creates no persistence or runtime registration, rollback before a
commit consists only of removing or correcting the three explicitly authorized
implementation artifacts while preserving the research record and sealed
baseline. No production rollback command is authorized by this planning record.

## Gate decision

- implementation plan: `DEFINED`;
- acceptance-test matrix: `DEFINED`;
- exact canonical type inventory: `LOCKED`;
- provenance reuse: `REQUIRED`;
- freshness reuse: `OPTIONAL AGGREGATE VALUE ONLY`;
- planned-route separation: `REQUIRED`;
- provider projector: `NOT AUTHORIZED`;
- serialization and persistence: `NOT AUTHORIZED`;
- registry mutation: `NOT AUTHORIZED`;
- runtime activation: `NOT AUTHORIZED`;
- implementation performed: `NO`.

The next gate is `CB-EA5B-8X-4`, which may create the three authorized
implementation artifacts and run the defined verification matrix. It may not
commit, tag, push, register, serialize, persist, deploy, or activate the model.
