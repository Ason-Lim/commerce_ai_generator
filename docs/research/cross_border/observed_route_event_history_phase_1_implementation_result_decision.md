# Observed Route Event History Phase 1 Implementation Result Decision

## Document status

- Gate: `CB-EA5B-8X-5B`
- Artifact type: implementation-result decision
- Target family: `observed_route_event_history`
- Decision: `PHASE-1 CANONICAL MODEL IMPLEMENTATION ACCEPTED`
- Provider projector: `NOT AUTHORIZED`
- Registry mutation: `NOT AUTHORIZED`
- Serialization or persistence: `NOT AUTHORIZED`
- Runtime activation: `NOT AUTHORIZED`
- Commit, tag, or push performed by this decision: `NO`

## Purpose

This decision records the result of the bounded Phase-1 canonical-model
implementation authorized by `CB-EA5B-8X-2` and planned by `CB-EA5B-8X-3`.

It determines whether the three authorized implementation artifacts conform to
the sealed canonical contract without extending authority into provider
projection, ingress or projection registries, serialization, persistence,
deployment, or runtime activation.

## Governing records

- canonical contract:
  `observed_route_event_history_canonical_contract_definition.md`;
- implementation ownership and reuse decision:
  `observed_route_event_history_implementation_ownership_and_reuse_decision.md`;
- Phase-1 implementation plan and acceptance-test matrix:
  `observed_route_event_history_phase_1_implementation_plan_and_acceptance_test_matrix.md`.

The governing canonical contract remains separately sealed at repository HEAD
`7dc6d3aa31280fc4f56548dd9c98d9f2a83f0725`.

## Reviewed implementation artifacts

| Artifact | Result | SHA-256 |
| --- | --- | --- |
| `app/services/cross_border/observed_route_event_history.py` | accepted | `a724aede6aa1cb4a6420672e9f5767042cda11bbc4149231b31b68884b94f905` |
| `app/services/cross_border/__init__.py` | accepted | `6736c4a1a1b212cec3bc0ba91e26fdc66b708e90035e238391a22edef04749fa` |
| `tests/services/cross_border/test_observed_route_event_history.py` | accepted | `7c125eee5d0e971b227022df90ce5dbb1d1db634ecfd72aebbff56fc944a73fa` |

The implementation changed exactly the two authorized production paths and the
one authorized focused-test path.

## Canonical type result

The implementation defines exactly the ten authorized canonical types:

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

No additional canonical event identifier, normalized delivery status, planned
route type, provider-specific type, serializer, projector, persistence model, or
runtime service was introduced.

## Ownership and reuse result

- the independent owner is
  `app/services/cross_border/observed_route_event_history.py`;
- `EvidenceProvenance` is reused from the existing provenance contract;
- history provenance remains mandatory;
- event provenance remains optional;
- `EvidenceFreshness` is reused only as an optional aggregate value;
- model construction performs no freshness evaluation;
- reporting-source identity remains separate from event-actor identity; and
- `shipping.py` remains the owner of planned-route evidence.

The module dependency audit found only the authorized standard-library imports
and the required provenance and freshness imports.

## Validation and normalization result

The accepted implementation provides deterministic construction-time behavior
for:

- trimming optional strings and converting empty optional strings to `None`;
- uppercasing an explicitly supplied country code;
- rejecting all-empty locations and actors;
- validating provider-local relationship references;
- enforcing event minimum content;
- rejecting naive datetimes without timezone inference;
- retaining raw temporal evidence without forced parsing;
- requiring history source identity, provenance, and correlation;
- copying event, relationship, and constraint collections to tuples;
- validating collection element types;
- freezing top-level metadata mappings;
- enforcing pagination evidence only with `PARTIAL` completeness; and
- preserving source order and repeated events without destructive mutation.

These behaviors remain provider-neutral and construction-local.

## Acceptance-test result

The focused test module contains one identified test function for every planned
acceptance surface from `AT-01` through `AT-32`.

Parameterized cases produced the following observational result:

- focused canonical-contract suite: `50 passed`;
- failures: `0`;
- errors: `0`.

The observational case count does not replace the identity of the 32 acceptance
surfaces and is not treated as a pre-authorized constant.

## Regression result

| Verification | Result |
| --- | --- |
| focused canonical-contract tests | `50 passed` |
| Cross-Border service tests | `573 passed` |
| full regression suite | `3809 passed` |
| compile check | `PASS` |
| package import smoke check | `PASS` |
| diff whitespace check | `PASS` |
| artifact-scope check | `PASS` |

All executed suites completed with zero failures and zero errors.

## Schema-restraint result

The result audit confirmed:

- exactly five frozen dataclass value-object or aggregate types;
- exact sealed field order for `ObservedRouteEvent`;
- exact sealed field order for `ObservedRouteEventHistory`;
- no `canonical_event_id`;
- no `normalized_status` or delivery-state output;
- no `to_dict`, `from_dict`, or persistence method;
- no shipping-route dependency;
- no ingress or projection dependency; and
- exactly ten package-level public exports.

## Artifact-scope result

The following existing files remained unchanged:

- `app/services/cross_border/shipping.py`;
- `app/services/cross_border/provenance.py`;
- `app/services/cross_border/freshness.py`;
- `app/services/cross_border/context.py`;
- `app/services/cross_border/external_evidence_ingress.py`; and
- `app/services/cross_border/external_evidence_projection.py`.

No provider, registry, migration, configuration, API, UI, ranking,
recommendation, dossier, or deployment artifact was mutated.

## Semantic boundary preserved

The accepted canonical model records source-reported shipment-event history. It
does not establish:

- planned route topology or `ShippingRouteType`;
- availability, feasibility, price, or duration;
- legal custody or regulatory clearance;
- delivery correctness or proof of delivery;
- loss, damage, delay, or financial responsibility;
- payment, settlement, duty, tax, or insurance outcome;
- cross-provider event identity;
- chronology from source position; or
- event actor identity from the reporting source.

Repeated and similar events remain separate and ordered. Construction does not
deduplicate, correct, overwrite, or supersede an event.

## Provider compatibility consequence

This implementation result does not execute or revise a provider compatibility
decision.

- existing candidate compatibility values remain unchanged;
- no candidate is admitted, selected, ranked, preferred, or rejected;
- ShipStation V2 and ShipEngine v1 remain separate evidence sources;
- MyDHL API and DHL Shipment Tracking - Unified remain separate evidence
  sources; and
- no provider-specific field mapping becomes executable runtime behavior.

## Decision

The Phase-1 provider-neutral canonical-model implementation is `ACCEPTED`.

Acceptance means only that the three authorized implementation artifacts conform
to the sealed canonical contract and acceptance matrix at the reviewed hashes.
It does not authorize any later consumer or executable projection.

## Authority not created

This decision does not authorize:

- provider adapters or projectors;
- HTTP acquisition, polling, webhooks, or pagination assembly;
- ingress evidence-kind or canonical projection-target changes;
- provider registry or dossier mutation;
- serialization, persistence, API, database, or migration work;
- normalized status or canonical identity work;
- recommendation, ranking, or UI integration;
- historical backfill;
- deployment or runtime activation; or
- commit, tag, or push by this decision itself.

## Rollback boundary

Before a later consumer is separately authorized, rollback remains limited to:

1. removing the independent model module;
2. removing the focused test module; and
3. removing only the corresponding package imports and `__all__` entries.

No rollback action may modify the existing shipping, provenance, freshness,
context, ingress, projection, provider, registry, dossier, or sealed research
contracts.

## Repository-state consequence

At this decision gate:

- repository HEAD remains
  `7dc6d3aa31280fc4f56548dd9c98d9f2a83f0725`;
- implementation and research artifacts remain uncommitted;
- staged changes remain empty;
- no tag exists for this implementation result; and
- no push has been performed.

## Required next gate

The next gate is a separate commit-sealing review. It must revalidate all six
pending paths, their hashes, the clean index, the unchanged remote baseline, and
the exact commit and annotated-tag scope before repository history is mutated.

No provider projection, registry mutation, serialization, persistence,
deployment, or runtime activation may be combined with that commit gate.
