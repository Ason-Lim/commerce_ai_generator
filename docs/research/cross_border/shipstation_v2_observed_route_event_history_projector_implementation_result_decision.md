# ShipStation V2 Observed Route Event History Projector Implementation Result Decision

## Decision status

- Gate: `CB-EA5C-6`
- Candidate: `candidate:shipping:shipstation-api`
- Product surface: ShipStation V2 `get_tracking_log`
- Decision: `BOUNDED READ-ONLY PROJECTOR IMPLEMENTATION ACCEPTED FOR SEALING`
- Canonical model mutation: `NONE`
- Package export or registry authority: `NONE`
- Runtime activation authority: `NONE`

## Governing records

This decision is governed by:

1. `shipstation_v2_observed_route_event_history_projector_authorization_boundary_decision.md`;
2. `shipstation_v2_observed_route_event_history_projector_implementation_plan_and_acceptance_test_matrix.md`;
3. the sealed provider-neutral `ObservedRouteEventHistory` canonical contract; and
4. the sealed ShipStation V2 projection-compatibility worksheet and decision.

The implementation result does not enlarge any authority defined by those
records.

## Accepted implementation artifacts

The accepted executable implementation consists of exactly two new artifacts:

1. `app/services/cross_border/shipstation_v2_observed_route_event_history_projector.py`;
2. `tests/services/cross_border/test_shipstation_v2_observed_route_event_history_projector.py`.

No existing production, test, package, registry, model, provenance, freshness,
shipping, API, persistence, configuration, compatibility, or dossier artifact
was modified.

## Accepted executable surface

The production module exposes one provider-specific executable function:

```python
def project_shipstation_v2_tracking_log(
    response: Mapping[str, object],
    *,
    tracking_number: str,
    provenance: EvidenceProvenance,
    carrier_code: str | None = None,
) -> ObservedRouteEventHistory:
    ...
```

The function interprets one already-acquired ShipStation V2 tracking-log
response. It does not acquire evidence, issue network requests, manage
credentials, assemble pages, receive webhooks, poll providers, serialize
results, persist data, register itself, or activate runtime behavior.

## Fixed source identity result

The projector fixes its reporting source identity to:

```text
candidate:shipping:shipstation-api
```

The caller cannot override or alias this identity. Provenance whose `source_id`
does not match is rejected. ShipEngine v1, ShipStation legacy V1, MyDHL API,
Korea Post EMS, and other adjacent evidence remain separate sources.

## Accepted mapping result

The implementation preserves only the bounded source fields authorized by the
plan:

| ShipStation source field | Canonical destination |
| --- | --- |
| `status_code` | `provider_event_code` |
| `carrier_status_code` | `raw_status` |
| `carrier_status_description` | `raw_status_description` |
| `country_code` | location `country_code` |
| `company_name` | location `raw_description` only |
| `carrier_detail_code` | event metadata under the unchanged source key |

All supported strings are trimmed. Empty strings become absent. Wrong runtime
types fail closed. Unsupported source fields do not create canonical claims.

## Conservative semantic result

The projector does not infer:

- stable event identity;
- event occurrence or provider-recorded time;
- normalized delivery status;
- actor identity or role;
- facility identity or ownership;
- shipment, piece, or package scope;
- event relationships;
- chronological ordering;
- history completeness;
- pagination or truncation state; or
- provider freshness.

Response order is retained only as
`ObservedRouteEventHistoryOrdering.SOURCE_ORDER`. Completeness remains
`ObservedRouteEventHistoryCompleteness.UNKNOWN`. Pagination and freshness
remain absent.

## Collection and failure result

The accepted implementation:

- accepts a present empty list or tuple as an observed empty snapshot;
- requires the `events` key;
- preserves response order and duplicates;
- copies projected content into immutable canonical objects;
- rejects wrong structural and supported-field runtime types;
- rejects an event with no canonical minimum content using its zero-based
  source index; and
- fails the entire projection atomically when any event is invalid.

It does not silently skip invalid events or return partial output.

## Constraint disclosure result

Every projected history carries the exact ordered nine-item constraint tuple:

1. `history_completeness_not_documented`;
2. `chronological_order_not_documented`;
3. `event_occurrence_time_not_documented`;
4. `event_identity_not_documented`;
5. `provider_recorded_time_not_documented`;
6. `duplicate_and_revision_semantics_not_documented`;
7. `event_level_actor_identity_not_documented`;
8. `pagination_and_truncation_semantics_not_documented`;
9. `provider_freshness_semantics_not_documented`.

These strings disclose evidence limitations. They do not manufacture provider
semantics or runtime authority.

## Acceptance result

The focused test artifact contains one named function for each planned
acceptance surface from `AT-01` through `AT-36`.

Observed verification outputs at this gate were:

- focused projector tests: `50 passed`;
- canonical history reference tests: `50 passed`;
- combined focused and canonical tests: `100 passed`;
- all Cross-Border service tests: `623 passed`;
- full regression: `3859 passed`;
- application and test tree compile: `PASS`;
- module dependency audit: `PASS`;
- package export exclusion: `PASS`;
- ingress and projection registry exclusions: `PASS`; and
- whitespace and pending-path scope: `PASS`.

Test counts are observational outputs, not future fixed constants.

## Package and registry decision

The provider-specific function is importable only from its isolated module. It
is not exported by the provider-neutral `app.services.cross_border` package.

The following remain unchanged and unauthorized for mutation:

- `app/services/cross_border/__init__.py`;
- `app/services/cross_border/external_evidence_ingress.py`;
- `app/services/cross_border/external_evidence_projection.py`; and
- any provider, adapter, projector, or runtime registry.

The existing projection eligibility lookup remains descriptive eligibility
metadata, not an executable projector registry.

## Explicitly denied consequences

Acceptance for sealing does not authorize:

- provider network acquisition;
- credential storage or use;
- webhook or polling execution;
- pagination assembly;
- package-level export;
- ingress or projection registry mutation;
- runtime wiring or deployment;
- serialization, persistence, API, or database integration;
- production-provider selection or ranking;
- MyDHL projector implementation;
- Korea Post EMS admission or projector implementation; or
- mutation of the canonical compatibility or provider dossier record.

## Seal scope

The authorized seal candidate consists of exactly five new paths:

1. the projector authorization-boundary decision;
2. the implementation plan and acceptance-test matrix;
3. the isolated projector module;
4. the focused projector test module; and
5. this implementation-result decision.

The seal must preserve the exact verified artifact hashes, rerun relevant tests,
confirm the five-path scope, create one commit, create one annotated tag, and
push the commit and tag only after all preconditions pass.

## Final decision

The ShipStation V2 observed-route-event-history projector implementation is
accepted as a bounded, read-only, provider-specific projection surface and is
eligible for a separate sealing gate.

Its authority ends at deterministic projection of already-acquired evidence
into the existing provider-neutral canonical model. Package publication,
registry participation, evidence acquisition, and runtime activation remain
denied.

## Next gate

The next gate is `CB-EA5C-7_SHIPSTATION_PROJECTOR_COMMIT_TAG_AND_PUSH_SEAL` after
a five-path seal preflight confirms artifact integrity and repository state.
