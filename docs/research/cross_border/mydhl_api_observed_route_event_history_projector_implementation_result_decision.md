# MyDHL API Observed Route Event History Projector Implementation Result Decision

## Decision status

- Gate: `CB-EA5D-5`
- Candidate: `candidate:shipping:mydhl-api`
- Product surface: MyDHL API tracking-event response
- Decision: `BOUNDED READ-ONLY PROJECTOR IMPLEMENTATION ACCEPTED FOR SEALING WITH TEMPORAL COMPOSITION DEFERRED`
- Canonical model mutation: `NONE`
- Package export or registry authority: `NONE`
- Network acquisition authority: `NONE`
- Runtime activation authority: `NONE`
- Datetime composition authority: `NONE`

## Governing records

This decision is governed by the MyDHL projector authorization-boundary
decision, the implementation plan and acceptance-test matrix, the sealed
provider-neutral `ObservedRouteEventHistory` contract, the sealed MyDHL
projection-compatibility records, and the registered source identity
`candidate:shipping:mydhl-api`.

This implementation result does not enlarge authority defined by those records.
Unresolved provider semantics remain raw, constrained, absent, or fail closed.

## Accepted implementation artifacts

The accepted executable implementation consists of exactly two new artifacts:

1. `app/services/cross_border/mydhl_api_observed_route_event_history_projector.py`;
2. `tests/services/cross_border/test_mydhl_api_observed_route_event_history_projector.py`.

No existing production, test, package, registry, canonical model, provenance,
freshness, API, UI, persistence, configuration, compatibility, or dossier
artifact was modified.

## Accepted executable surface

The isolated module exposes exactly one provider-specific function:

`project_mydhl_api_tracking_events(response, *, tracking_number, collection_scope, provenance) -> ObservedRouteEventHistory`

It accepts a top-level mapping containing an `events` list or tuple. Every event
must be a mapping. The tracking number is required and normalized. Only
`SHIPMENT` and `PIECE` scopes are accepted.

The function projects already-acquired evidence only. It does not acquire
evidence, use credentials, issue network requests, receive webhooks, poll
providers, assemble pages, persist data, register itself, export itself through
the provider-neutral package, or activate runtime behavior.

## Fixed source identity result

The reporting source identity is fixed to
`candidate:shipping:mydhl-api`.

Caller provenance with a different `source_id` fails closed. MyDHL API, DHL
Shipment Tracking Unified, other DHL products, aggregators, Korea Post EMS, and
other adjacent sources remain separate evidence identities.

## Accepted mapping result

The bounded mappings are:

- `typeCode` to `provider_event_code`;
- `description` to `raw_status_description`;
- `date`, `time`, and `GMTOffset` to `occurred_at_raw` only;
- sole `serviceArea.description` to location `raw_description` only;
- sole `serviceArea.code` to metadata `service_area_code`;
- normalized `remarks` list or tuple to immutable metadata `remarks`;
- normalized tracking number to event `scope_reference` and history
  `tracking_number`;
- accepted collection scope to event `scope`.

Strings are trimmed and empty strings become absent. Unknown keys do not create
canonical fields or metadata. Service-area code and remarks are metadata only
and do not satisfy event minimum content.

Source order and duplicate occurrences are preserved. Invalid events fail the
whole projection atomically. Events are not sorted, deduplicated, or silently
filtered.

## Temporal deferral result

The projector does not parse, normalize, combine, or infer canonical datetimes.

`occurred_at` always remains `None`.

When temporal evidence exists, `occurred_at_raw` uses this length-prefixed
representation:

`date:<length>:<value>|time:<length>:<value>|GMTOffset:<length>:<value>`

Missing normalized components use length `-1`. If every temporal component is
absent or empty, `occurred_at_raw` remains `None`.

This representation preserves raw source evidence; it is not datetime
composition.

## Conservative semantic result

The projector does not infer canonical event identity, stable provider
sequence, chronological ordering, canonical occurrence time, provider recorded
time, actor or facility identity, geographic semantics, event relationships,
history completeness, pagination, truncation, freshness, planned route
topology, delivery outcome, provider verification, provider selection, ranking,
or fallback.

History completeness remains `UNKNOWN`. Ordering remains `SOURCE_ORDER`.
Pagination and freshness remain absent.

## Constraint disclosure result

Every projected history carries this exact ordered ten-item tuple:

1. `history_completeness_not_documented`;
2. `chronological_order_not_documented`;
3. `stable_event_identity_not_documented`;
4. `provider_recorded_time_not_documented`;
5. `event_level_actor_identity_not_documented`;
6. `duplicate_and_revision_semantics_not_documented`;
7. `pagination_and_truncation_semantics_not_documented`;
8. `provider_freshness_semantics_not_documented`;
9. `temporal_format_constraints_unresolved`;
10. `service_area_semantics_partially_unresolved`.

These constraints disclose evidence limitations. They create no additional
provider semantics or authority.

## Acceptance result

The focused test module contains one named function corresponding semantically
to each authoritative row from `AT-01` through `AT-48`.

Observed verification outputs were:

- focused MyDHL projector tests: `99 passed`;
- canonical history tests: `50 passed`;
- ShipStation V2 precedent tests: `50 passed`;
- combined observed-history tests: `199 passed`;
- Cross-Border service tests: `722 passed`;
- full repository regression: `3958 passed`;
- compilation and dependency audits: `PASS`;
- function and public-surface audits: `PASS`;
- package, registry, network, persistence, and runtime exclusions: `PASS`;
- exact pending-path scope: `PASS`.

Test counts are observational results, not future fixed constants.

Verified executable identities are:

- projector SHA-256:
  `2c93126355ae88cbef52fa323b283dffce5b6452a2d03fbf73e4f03562cffcbb`;
- focused test SHA-256:
  `4fc315b4be92508bbff70cc1229e84dde831f2eda52c13cb022dcee2a07064df`.

## Package and registry decision

The function is importable only from its isolated provider module. It is not
exported by `app.services.cross_border`.

Package export, ingress registry, projection registry, API, UI, runtime,
selection, ranking, and adapter surfaces remain unchanged and unauthorized.
Descriptive projection-eligibility metadata is not an executable registry.

## Explicitly denied consequences

Acceptance for sealing does not authorize:

- network acquisition or credential use;
- webhook, polling, or pagination execution;
- datetime parsing or temporal composition;
- package export or registry mutation;
- runtime wiring or deployment;
- serialization, persistence, API, UI, or database integration;
- provider verification, selection, ranking, or fallback;
- planned-route-topology inference;
- adjacent-source evidence attribution;
- DHL Shipment Tracking Unified admission or implementation;
- Korea Post EMS admission or implementation;
- canonical model, compatibility record, or dossier mutation; or
- recommendation authority.

## Seal scope

The authorized seal candidate consists of exactly five new paths:

1. the authorization-boundary decision;
2. the implementation plan and acceptance-test matrix;
3. the isolated MyDHL projector module;
4. the focused MyDHL test module;
5. this implementation-result decision.

A separate seal preflight must preserve verified hashes, validate this decision,
rerun relevant tests, confirm the exact five-path scope, and authorize commit,
annotated tag, and push only after all preconditions pass.

## Final decision

The MyDHL API observed-route-event-history projector is accepted as a bounded,
read-only, provider-specific projection surface with temporal composition
explicitly deferred. It is eligible for a separate sealing gate.

Its authority ends at deterministic projection of already-acquired MyDHL API
tracking-event evidence into the existing provider-neutral canonical model.
Package publication, registry participation, evidence acquisition, datetime
composition, provider verification, provider selection, ranking, persistence,
and runtime activation remain denied.

## Next gate

The next gate is
`CB-EA5D-6_MYDHL_PROJECTOR_COMMIT_TAG_AND_PUSH_SEAL` after an exact five-path
seal preflight confirms artifact integrity, decision integrity, tests, and
repository state.
