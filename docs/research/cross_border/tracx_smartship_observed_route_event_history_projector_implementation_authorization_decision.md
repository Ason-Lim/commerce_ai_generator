# TracX SmartShip observed route event history projector implementation authorization decision

## Document status

- Gate: `CB-EA5E-12-B`
- Artifact type: exact two-file projector implementation authorization decision
- Decision status: `AUTHORIZED WITH EXACT TWO-FILE SCOPE`
- Candidate: `candidate:shipping-aggregator:tracx-smartship`
- Product surface: polling `SmartShipService.Tracking`
- Source collection: polling `tracking_history`
- Canonical target: `observed_route_event_history`
- Projector implementation authority: `AUTHORIZED`
- Test implementation authority: `AUTHORIZED`
- Projector implementation performed: `NO`
- Test implementation performed: `NO`
- Package, registry, network, persistence, and runtime authority: `DENIED`
- Production and runtime authority: `NONE`

## Purpose

This decision determines whether the sealed TracX SmartShip projector plan may
advance to a later exact two-file implementation write gate.

It authorizes only the two new files named in this decision and only the
contract fixed by the sealed plan.

This decision creates no projector code, test code, package export, registry
entry, network acquisition, persistence, deployment, or runtime activation.

## Governing sealed evidence

This decision is governed by:

1. `tracx_smartship_observed_route_event_history_projection_compatibility_worksheet.md`;
2. `tracx_smartship_observed_route_event_history_projection_compatibility_decision.md`;
3. `tracx_smartship_observed_route_event_history_dossier_mutation_authorization_decision.md`;
4. `external_evidence_provider_evaluation_dossier.md`;
5. `tracx_smartship_observed_route_event_history_projector_authorization_boundary_decision.md`;
6. `tracx_smartship_observed_route_event_history_projector_implementation_plan_and_acceptance_test_matrix.md`;
7. `observed_route_event_history_implementation_ownership_and_reuse_decision.md`;
8. the existing canonical `observed_route_event_history` implementation;
9. the existing `EvidenceProvenance` contract; and
10. the implemented ShipStation V2 and MyDHL projector precedents.

## Authorization criteria

The authorization criteria are satisfied because:

1. the TracX compatibility observation is sealed;
2. the exact dossier mutation is sealed as `observed`;
3. the projector-planning boundary is sealed;
4. the implementation plan is validated, committed, tagged, and pushed;
5. the plan fixes exactly one public projector function;
6. the plan fixes exactly two later implementation artifacts;
7. reporting-source identity and acquisition-owned correlation are fixed;
8. exactly five source event keys are recognized;
9. raw temporal preservation is fixed without datetime inference;
10. existing canonical and provenance owners are reused;
11. the thirteen-item constraint tuple is fixed;
12. acceptance surfaces `AT-01` through `AT-48` are complete;
13. implemented provider precedents remain intact;
14. no TracX projector or focused test currently exists; and
15. no existing-file, package, registry, network, persistence, production, or
    runtime mutation is required.

## Exact authorized artifacts

A later implementation write gate may create exactly these two files:

1. `app/services/cross_border/tracx_smartship_observed_route_event_history_projector.py`
2. `tests/services/cross_border/test_tracx_smartship_observed_route_event_history_projector.py`

Both files must be new.

No existing file may be modified.

No third file, alternate path, package export, registry entry, adapter, factory,
dispatcher, serializer, endpoint, database, or configuration artifact is
authorized.

## Exact public projector surface

The projector module may expose exactly one public function:

```python
def project_tracx_smartship_tracking_history(
    response: object,
    *,
    correlation_key: str,
    correlation_value: str,
    provenance: EvidenceProvenance,
) -> ObservedRouteEventHistory:
    ...
````

Private constants and helpers are permitted only for deterministic validation,
normalization, canonical construction, and atomic failure.

No additional public function, class, dataclass, protocol, adapter, provider
client, serializer, factory, or dispatcher is authorized.

## Fixed reporting-source identity

The reporting source must be exactly:

`candidate:shipping-aggregator:tracx-smartship`

It must not be caller-overridable.

It must not be interpreted as a physical carrier, carrier actor, custody actor,
event-level carrier reference, or adjacent product identity.

The exact caller-supplied `EvidenceProvenance` instance must be reused unchanged.
Its `source_id` must equal the fixed reporting source.

## Exact response and correlation boundary

The input is the polling `SmartShipService.Tracking` response only.

The authorized event collection is `tracking_history`.

Delivery WebHook attribution is denied.

`MultiTracking` assembly is denied.

The authorized acquisition-owned correlation keys are exactly:

1. `shipping_no`;
2. `ref_no`; and
3. `qs_no`.

The caller must select one key and its expected value.

The selected source value must match `correlation_value`.

Multiple non-empty correlation fields remain separate. No precedence, alias,
global identity, or equivalence may be inferred.

## Exact recognized event keys

The implementation may recognize exactly:

1. `status`;
2. `status_code`;
3. `details`;
4. `location`; and
5. `date`.

Unknown and deferred keys must be ignored. They must not leak into canonical
metadata, descriptions, identity fields, or provenance.

## Exact canonical mapping

| Source key    | Canonical destination        | Rule                                    |
| ------------- | ---------------------------- | --------------------------------------- |
| `status_code` | `provider_event_code`        | optional trimmed provider-native string |
| `status`      | `raw_status`                 | optional trimmed provider-native string |
| `details`     | `raw_status_description`     | optional trimmed provider-native string |
| `location`    | `ObservedRouteEventLocation` | raw-description-only location           |
| `date`        | `occurred_at_raw`            | optional non-empty raw temporal string  |

The implementation must reuse existing canonical classes.

No parallel event-history, event, location, provenance, scope, completeness, or
ordering model is authorized.

## Temporal boundary

A non-empty polling `date` may populate only `occurred_at_raw`.

The following values remain fixed:

* `occurred_at=None`;
* `recorded_at=None`;
* `recorded_at_raw=None`;
* completeness `UNKNOWN`; and
* ordering `SOURCE_ORDER`.

The implementation must perform:

* no datetime parsing;
* no timezone or UTC-offset inference;
* no aware-datetime construction;
* no chronological sorting;
* no webhook temporal attribution; and
* no claim that source position represents chronology.

## Deferred and prohibited inference

The implementation must not recognize, preserve, or invent exact source-key
spellings for:

* reason fields;
* auxiliary tracking codes; or
* proof-of-delivery references.

Those fields remain deferred.

The implementation must not infer stable event identity, stable sequence, actor,
custody, physical carrier, relationships, duplicate or revision semantics,
pagination completeness, retention, update latency, freshness,
proof-of-delivery identity, or normalized delivery state.

## Exact ordered constraint tuple

The implementation must emit exactly this ordered tuple:

1. `history_completeness_not_documented`
2. `chronological_order_not_documented`
3. `stable_event_identity_not_documented`
4. `stable_event_sequence_not_documented`
5. `provider_recorded_time_not_documented`
6. `event_level_actor_identity_not_documented`
7. `event_level_carrier_identity_not_documented`
8. `duplicate_and_revision_semantics_not_documented`
9. `pagination_and_truncation_semantics_not_documented`
10. `retention_and_update_latency_not_documented`
11. `temporal_format_and_timezone_unresolved`
12. `proof_of_delivery_identity_semantics_unresolved`
13. `polling_webhook_surface_separation_required`

No constraint may be removed, renamed, reordered, or supplemented.

## Failure and collection behavior

Projection must be atomic.

Wrong top-level, collection, event, supported-field, correlation, or provenance
runtime types must raise `TypeError`.

Missing or mismatched required correlation, invalid provenance source identity,
or a non-empty event without supported canonical minimum content must raise
`ValueError`.

No partial history may be returned after validation or canonical-construction
failure.

Source event order must be preserved without a chronological claim.

Repeated source entries must remain separate.

Sorting, deduplication, merging, correction, supersession, and replacement are
not authorized.

## Focused-test authority

The focused test file must implement acceptance surfaces `AT-01` through
`AT-48` from the sealed plan.

The tests must prove:

* the exact public signature;
* fixed reporting-source identity;
* the exact correlation boundary;
* response and collection validation;
* exact event mappings;
* raw-temporal-only behavior;
* deferred-key non-leakage;
* canonical and provenance reuse;
* exact constraint order;
* source-order and duplicate preservation;
* input/output immutability;
* atomic failure;
* no package export;
* no registry dependency;
* no network, credentials, webhook, serialization, persistence, API, UI,
  database, deployment, or runtime surface; and
* exactly one public projector function.

Tests may import the projector only through its explicit provider-specific
module.

## Explicit exclusions

This authorization does not permit:

* modification of any existing file;
* package-level export or `__all__` mutation;
* ingress or projection registry mutation;
* provider factory or dispatcher creation;
* HTTP acquisition, credentials, retries, rate limiting, or scheduling;
* webhook ingestion or authentication;
* Delivery WebHook attribution;
* `MultiTracking` assembly;
* cross-response, cross-page, or historical assembly;
* canonical or provenance model mutation;
* dossier or sealed research mutation;
* date parsing or timezone inference;
* normalized status or delivery-state generation;
* serialization, persistence, caching, migration, API, UI, or database work;
* provider verification, ranking, selection, or recommendation;
* Korea Post EMS consequences;
* deployment or runtime activation; or
* production authority.

## Authorized later write-gate behavior

A later exact implementation write gate may:

1. create the exact projector file;
2. create the exact focused test file; and
3. perform no other repository mutation.

That gate must verify all sealed identities and both path absences before
creation.

It must leave both created files untracked and perform no stage, commit, tag,
push, package mutation, registry mutation, deployment, or runtime activation.

Creation, joint validation, commit, annotated tag creation, and push remain
separate gates.

## Authorization decision

* sealed projector plan: `PASS`;
* authorization criteria: `PASS`;
* exact projector path: `AUTHORIZED`;
* exact focused-test path: `AUTHORIZED`;
* exact implementation artifact count: `TWO`;
* existing-file modification: `DENIED`;
* canonical and provenance reuse: `REQUIRED`;
* source-identity separation: `REQUIRED`;
* raw-temporal-only boundary: `REQUIRED`;
* exact constraints: `THIRTEEN`;
* acceptance surfaces: `AT-01` through `AT-48`;
* package and registry mutation: `DENIED`;
* network and persistence mutation: `DENIED`;
* production and runtime mutation: `NONE`;
* implementation performed by this decision: `NO`.

## Required next gate

The next gate is:

`CB-EA5E-12-C_TRACX_PROJECTOR_IMPLEMENTATION_AUTHORIZATION_DECISION_JOINT_READ_ONLY_VALIDATION`

It must validate this decision against the sealed plan, planning boundary,
dossier, canonical owner, provenance contract, and implemented provider
precedents.

It must perform no projector creation, test creation, stage, commit, tag, push,
package mutation, registry mutation, deployment, or runtime activation.
