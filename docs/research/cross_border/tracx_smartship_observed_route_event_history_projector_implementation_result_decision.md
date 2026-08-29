# TracX SmartShip observed route event history projector implementation result decision

## Document status

- Gate: `CB-EA5E-13-D`
- Artifact type: projector implementation result decision
- Candidate: `candidate:shipping-aggregator:tracx-smartship`
- Evaluated surface: polling `SmartShipService.Tracking` / `tracking_history` only
- Decision status: `BOUNDED READ-ONLY PROJECTOR IMPLEMENTATION ACCEPTED FOR SEALING WITH RAW-TEMPORAL-ONLY BOUNDARY`
- Projector implementation performed before this decision: `YES`
- Focused test implementation performed before this decision: `YES`
- Package export performed: `NO`
- Registry mutation performed: `NO`
- Network or credential integration performed: `NO`
- Persistence or runtime activation performed: `NO`

## Purpose

This decision records the result of the separately authorized and validated
TracX SmartShip observed-route-event-history projector implementation.

It determines whether the exact two implementation artifacts may proceed to a
separate sealing workflow together with this result decision.

This document does not expand implementation authority, modify either
implementation artifact, execute tests, stage files, create a commit, create a
tag, push refs, publish a package symbol, mutate a registry, or activate a
runtime path.

## Governing sealed evidence

This decision is governed by the already tracked and sealed:

1. TracX SmartShip projection-compatibility worksheet;
2. TracX SmartShip projection-compatibility decision;
3. external evidence provider evaluation dossier record;
4. projector-planning authorization-boundary decision;
5. projector implementation plan and acceptance-test matrix; and
6. projector implementation authorization decision.

Those records remain authoritative for evidence attribution, accepted source
keys, canonical destinations, prohibited inference, temporal handling, failure
behavior, and negative production authority.

They are not pending implementation artifacts and must not be recounted in the
later pending seal.

## Accepted executable implementation

The accepted implementation consists of exactly:

1. `app/services/cross_border/tracx_smartship_observed_route_event_history_projector.py`;
2. `tests/services/cross_border/test_tracx_smartship_observed_route_event_history_projector.py`.

No existing tracked file was modified.

No third executable, package, registry, adapter, client, serializer,
persistence, configuration, endpoint, or runtime artifact was created.

## Exact artifact identities

The accepted projector identity is:

- line count: `218`;
- SHA-256: `7f8b85465286d63e579dddcefc9358321127fb44d4f354e48272a22cdf1e2250`.

The accepted focused-test identity is:

- line count: `541`;
- SHA-256: `173152720ac31369bf52ccfb3e23a40f14c50d90abcf5843fc907914b80806aa`.

Any later mismatch in path, line count, or SHA-256 must stop the sealing
workflow.

## Exact public surface

The projector module exposes exactly one public function:

```python
def project_tracx_smartship_tracking_history(
    response: Mapping[str, object],
    *,
    correlation_key: str,
    correlation_value: str,
    provenance: EvidenceProvenance,
) -> ObservedRouteEventHistory:
    ...
```

Private constants and helpers support only deterministic validation,
normalization, canonical construction, and atomic failure.

No public provider client, adapter, serializer, factory, dispatcher, protocol,
class, dataclass, or additional projection function is accepted.

## Fixed reporting-source identity

The reporting source is fixed to:

`candidate:shipping-aggregator:tracx-smartship`

It is not caller-overridable.

It is not interpreted as a physical carrier, carrier actor, custody actor,
event-level carrier reference, or adjacent TracX product.

The exact caller-supplied `EvidenceProvenance` object is reused, and its
`source_id` must equal the fixed reporting-source identity.

## Polling and correlation boundary

The accepted input is the polling `SmartShipService.Tracking` response only.

The accepted source collection is `tracking_history`.

The acquisition-owned correlation keys are exactly:

1. `shipping_no`;
2. `ref_no`;
3. `qs_no`.

The caller selects exactly one key and supplies the expected value.

The selected non-empty source value becomes the canonical tracking number only
after exact normalized matching.

Other recognized non-empty correlations remain separate history metadata.

No precedence, alias, global identity, or equivalence among the three
correlation keys is inferred.

Delivery WebHook attribution is absent.

`MultiTracking` input or assembly is absent.

## Exact event-key boundary

The implementation recognizes exactly five event keys:

1. `status`;
2. `status_code`;
3. `details`;
4. `location`;
5. `date`.

Reason fields, auxiliary tracking codes, proof-of-delivery references, and
unknown keys remain deferred or ignored.

They do not become canonical fields, metadata, descriptions, identities, or
provenance.

No unregistered provider key is invented.

## Exact canonical mapping

| Source key | Canonical destination | Accepted rule |
| --- | --- | --- |
| `status_code` | `provider_event_code` | optional trimmed provider-native string |
| `status` | `raw_status` | optional trimmed provider-native string |
| `details` | `raw_status_description` | optional trimmed provider-native string |
| `location` | `ObservedRouteEventLocation` | raw-description-only location |
| `date` | `occurred_at_raw` | optional non-empty raw temporal string |

The implementation reuses the existing provider-neutral canonical
observed-route-event-history classes.

No parallel history, event, location, provenance, scope, completeness, or
ordering model was created.

## Raw-temporal-only boundary

A non-empty polling `date` may populate only `occurred_at_raw`.

The implementation fixes:

- `occurred_at=None`;
- `recorded_at=None`;
- `recorded_at_raw=None`;
- completeness to `UNKNOWN`;
- ordering to `SOURCE_ORDER`;
- pagination fields to `None`;
- freshness to `None`.

It performs no datetime parsing, timezone inference, UTC-offset inference,
aware-datetime construction, chronological sorting, or webhook temporal
attribution.

Source order is preserved without claiming chronological order.

## Exact ordered constraint tuple

The accepted history emits exactly this ordered thirteen-item tuple:

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

Constraint order is part of the accepted contract.

No payload value dynamically removes, renames, reorders, or adds a constraint.

## Collection and failure behavior

The accepted implementation is deterministic and atomic.

Wrong top-level, collection, event, supported-field, correlation, or provenance
runtime types raise `TypeError`.

Missing or mismatched required correlation, invalid provenance source identity,
or a non-empty event lacking supported canonical minimum content raises
`ValueError`.

No partially projected history is returned after any validation or canonical
construction failure.

Valid source event order and repeated entries are preserved without sorting or
deduplication.

Later mutation of the input response cannot mutate the returned canonical
history, event tuple, location object, constraints, or metadata.

## Acceptance result

The implementation was validated before this decision with these observational
results:

- focused TracX acceptance tests: `70 passed`;
- canonical observed-route-event-history tests: `50 passed`;
- focused plus canonical combined tests: `120 passed`;
- all Cross-Border service tests: `792 passed`;
- full repository regression: `4028 passed`;
- compile check: `PASS`;
- dependency audit: `PASS`;
- package and registry audit: `PASS`;
- whitespace audit: `PASS`;
- exact two-file implementation scope audit: `PASS`.

These counts are observations from the validated repository state.

They are not future fixed test-count requirements and do not authorize an
inference that later suites must produce identical counts.

Acceptance requirements remain semantic, identity-bound, and fail closed.

## Package and registry decision

The projector is importable only from its isolated provider module.

It is not exported by `app.services.cross_border`.

The provider-neutral package initializer is unchanged.

Ingress and projection registries are unchanged.

Descriptive dossier compatibility and planning metadata are not executable
registry participation.

No adapter, provider client, dispatcher, selection surface, or runtime wiring
was added.

## Explicitly denied consequences

Acceptance for sealing does not authorize:

- package export;
- ingress or projection registry mutation;
- provider client or network acquisition;
- credential use;
- polling execution or scheduling;
- Delivery WebHook ingestion or attribution;
- `MultiTracking` assembly;
- datetime parsing or timezone inference;
- persistence, serialization, API, UI, or database integration;
- provider verification, selection, ranking, recommendation, or fallback;
- dossier, compatibility, canonical model, or provenance mutation;
- production deployment or runtime activation.

Production and runtime authority remain `NONE`.

## Pending seal scope

The prospective pending seal consists of exactly three new paths:

1. `app/services/cross_border/tracx_smartship_observed_route_event_history_projector.py`;
2. `tests/services/cross_border/test_tracx_smartship_observed_route_event_history_projector.py`;
3. `docs/research/cross_border/tracx_smartship_observed_route_event_history_projector_implementation_result_decision.md`.

The earlier boundary decision, plan, and implementation authorization decision
are already tracked and sealed.

They are excluded from this pending three-file count.

No fourth pending file is authorized.

## Final decision

The exact TracX SmartShip polling projector and focused acceptance test are
accepted as a bounded, deterministic, read-only, provider-specific canonical
projection surface with a raw-temporal-only boundary.

They are eligible for a separate exact three-file sealing review.

Authority ends at deterministic projection of already acquired polling
`tracking_history` evidence into the existing provider-neutral canonical model.

Package publication, registry participation, network acquisition, credentials,
webhook ingestion, `MultiTracking` assembly, temporal interpretation,
persistence, provider selection, recommendation, deployment, and runtime
activation remain denied.

## Required next gate

The next gate is:

`CB-EA5E-13-E_TRACX_IMPLEMENTATION_RESULT_JOINT_READ_ONLY_VALIDATION`

It must validate this result decision jointly against the two exact
implementation artifacts, all governing sealed evidence, the accepted test
results, package and registry non-mutation, and the exact prospective
three-file seal scope.

It must perform no implementation edit, test execution, stage, commit, tag,
push, package mutation, registry mutation, network operation, persistence, or
runtime activation.
