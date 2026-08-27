# ShipStation V2 Observed Route Event History Projector Implementation Plan and Acceptance-Test Matrix

## Document status

- Gate: `CB-EA5C-2B`
- Candidate: `candidate:shipping:shipstation-api`
- Product surface: ShipStation V2 `get_tracking_log`
- Status: `READ-ONLY IMPLEMENTATION PLAN DEFINED`
- Projector implementation performed: `NO`
- Test implementation performed: `NO`
- Registry, runtime, commit, tag, or push mutation: `NONE`

## Governing boundary

This plan is governed by
`shipstation_v2_observed_route_event_history_projector_authorization_boundary_decision.md`.
It converts that boundary and the sealed compatibility worksheet into an exact
implementation sequence. It does not authorize implementation until a separate
write gate validates this plan.

## Authorized later artifacts

A later implementation gate may create exactly two files:

1. `app/services/cross_border/shipstation_v2_observed_route_event_history_projector.py`;
2. `tests/services/cross_border/test_shipstation_v2_observed_route_event_history_projector.py`.

No existing file may be modified. In particular, package exports, canonical
models, ingress, projection eligibility, registries, provenance, freshness,
shipping, dossier, API, persistence, and configuration artifacts remain
unchanged.

## Exact executable surface

The production module defines one non-private executable symbol:

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

No input dataclass, provider client, adapter registry, factory, serializer, or
additional public function is authorized.

Private constants and helpers may be defined only for deterministic validation,
normalization, location construction, and event construction.

## Fixed source identity

The module owns the private constant:

```python
_REPORTING_SOURCE_ID = "candidate:shipping:shipstation-api"
```

The caller cannot override this identity. `provenance.source_id` must equal the
fixed identity after existing provenance normalization. A mismatch raises
`ValueError`. ShipEngine v1, ShipStation legacy V1, and adjacent-source evidence
are rejected rather than aliased.

## Input validation

- `response` must be a `Mapping`; otherwise raise `TypeError`.
- `tracking_number` must be a string that remains non-empty after trimming;
  otherwise raise `TypeError` or `ValueError` respectively.
- `carrier_code` must be a string or `None`; empty strings normalize to `None`.
- `provenance` must be an `EvidenceProvenance`; otherwise raise `TypeError`.
- provenance source identity mismatch raises `ValueError`.
- `response` must contain an `events` key; absence raises `ValueError`.
- `response["events"]` must be a list or tuple; otherwise raise `TypeError`.
- every event element must be a `Mapping`; otherwise raise `TypeError`.

A present empty list or tuple is a valid empty response snapshot. Missing
`events` is not treated as equivalent to an observed empty collection.

## Source string normalization

Supported source strings are trimmed and empty strings normalize to `None`.
Wrong source-field runtime types raise `TypeError`; they are not stringified.

No source value is parsed as a datetime, geocoded, interpreted as a canonical
status, or used to manufacture identity.

## Exact history projection

The result is constructed with:

```python
ObservedRouteEventHistory(
    reporting_source_id=_REPORTING_SOURCE_ID,
    provenance=provenance,
    events=projected_events,
    carrier_reference=normalized_carrier_code,
    tracking_number=normalized_tracking_number,
    source_record_id=None,
    request_correlation_id=None,
    completeness=ObservedRouteEventHistoryCompleteness.UNKNOWN,
    ordering=ObservedRouteEventHistoryOrdering.SOURCE_ORDER,
    has_more=None,
    next_page_token=None,
    freshness=None,
    constraints=_CONSTRAINTS,
    metadata={},
)
```

Response order is preserved. `SOURCE_ORDER` carries no chronological meaning.

## Exact constraint tuple

The private immutable tuple is fixed in this order:

```python
_CONSTRAINTS = (
    "history_completeness_not_documented",
    "chronological_order_not_documented",
    "event_occurrence_time_not_documented",
    "event_identity_not_documented",
    "provider_recorded_time_not_documented",
    "duplicate_and_revision_semantics_not_documented",
    "event_level_actor_identity_not_documented",
    "pagination_and_truncation_semantics_not_documented",
    "provider_freshness_semantics_not_documented",
)
```

Seven identifiers reuse the sealed worksheet spelling. The plan explicitly adds
`provider_recorded_time_not_documented` and
`pagination_and_truncation_semantics_not_documented` to disclose two boundary
requirements that the worksheet describes without dedicated constraint labels.
These strings are disclosure only.

## Exact event projection

For each source event mapping:

- `status_code` maps to `provider_event_code`;
- `carrier_status_code` maps to `raw_status`;
- `carrier_status_description` maps to `raw_status_description`;
- `country_code` maps to location `country_code` when non-empty;
- `company_name` maps only to location `raw_description` when non-empty; and
- `carrier_detail_code` maps to event metadata under the unchanged key
  `carrier_detail_code` when non-empty.

All supported values use conservative string normalization. No other source
field is retained in Phase 1 of the projector.

The canonical event is constructed without passing inferred values, leaving
event ID, temporal fields, actor, scope reference, source sequence,
relationships, and event provenance at their sealed conservative defaults.

## Location construction

Create `ObservedRouteEventLocation` only when normalized `country_code` or
`company_name` is non-empty.

- country code is supplied to the canonical location contract, which owns its
  authorized uppercasing;
- company name is supplied only as `raw_description`;
- facility code, facility name, locality, subdivision, and postal code remain
  absent; and
- company name never becomes an actor or facility owner.

## Event minimum-content failure

After supported-field normalization and optional location construction, a source
event must provide at least one canonical minimum-content value.

If a non-empty source event lacks all supported content, raise `ValueError` with
its zero-based source index. Do not skip it, create an empty event, derive content
from an unsupported field, or continue with a partial output.

Projection is atomic: any invalid element fails the entire call.

## Collection behavior

- input list or tuple order is preserved;
- repeated and equal event mappings produce repeated canonical events;
- no sorting, deduplication, correction, replacement, or relationship creation
  occurs;
- the canonical model freezes the output collection; and
- later input mutation cannot change the canonical result.

## Error matrix

| Condition | Result |
| --- | --- |
| response is not a mapping | `TypeError` |
| tracking number has wrong type | `TypeError` |
| tracking number is empty after trimming | `ValueError` |
| carrier code has wrong type | `TypeError` |
| provenance has wrong type | `TypeError` |
| provenance source ID differs | `ValueError` |
| events key missing | `ValueError` |
| events value is not list or tuple | `TypeError` |
| event element is not a mapping | `TypeError` |
| supported event field has wrong type | `TypeError` |
| event has no supported minimum content | `ValueError` |

No error is converted into an empty successful history.

## Acceptance-test matrix

| ID | Surface | Required acceptance |
| --- | --- | --- |
| `AT-01` | function signature | exact name, arguments, keyword-only boundary, and return type |
| `AT-02` | fixed source | result uses the registered ShipStation V2 identity |
| `AT-03` | source separation | mismatched provenance and adjacent-source identity are rejected |
| `AT-04` | response type | mapping accepted; non-mapping rejected |
| `AT-05` | tracking correlation | trimmed tracking number retained; empty and wrong types rejected |
| `AT-06` | carrier correlation | trimmed value retained; empty becomes `None`; wrong type rejected |
| `AT-07` | provenance | exact existing instance retained; wrong type rejected |
| `AT-08` | events presence | explicit events key required |
| `AT-09` | events collection | list and tuple accepted; other values rejected |
| `AT-10` | empty response | present empty collection creates valid empty history |
| `AT-11` | event element type | mappings accepted; non-mappings rejected |
| `AT-12` | provider event code | `status_code` trims and maps directly |
| `AT-13` | raw status | `carrier_status_code` trims and maps directly |
| `AT-14` | raw description | carrier description trims and maps directly |
| `AT-15` | country location | country code maps and canonical uppercasing applies |
| `AT-16` | company location | company name maps only to raw description |
| `AT-17` | location omission | location omitted when supported location fields are empty |
| `AT-18` | detail metadata | non-empty detail code retained under its source key |
| `AT-19` | metadata restraint | unsupported fields do not create canonical claims |
| `AT-20` | minimum content | each supported alternative independently projects |
| `AT-21` | empty event | unsupported or empty event fails with indexed `ValueError` |
| `AT-22` | supported field types | wrong string-field types raise `TypeError` |
| `AT-23` | event defaults | identity, times, actor, scope reference, sequence, relations, provenance absent |
| `AT-24` | conservative history | completeness unknown, source order, no pagination, no freshness |
| `AT-25` | constraints | exact nine-item tuple and order preserved |
| `AT-26` | source order | response event order retained without chronological claim |
| `AT-27` | duplicates | repeated events remain separate |
| `AT-28` | input isolation | later input mutation cannot alter canonical output |
| `AT-29` | atomic failure | one invalid event prevents partial output |
| `AT-30` | no network | module has no HTTP, credential, polling, or webhook dependency |
| `AT-31` | no registry | ingress and projection contracts remain unchanged |
| `AT-32` | no package export | projector absent from package-level imports and `__all__` |
| `AT-33` | no serialization | no serializer, persistence, API, or database surface |
| `AT-34` | canonical reuse | output and nested objects use existing canonical classes |
| `AT-35` | immutable result | canonical event tuple and metadata remain immutable |
| `AT-36` | no inference | no time, identity, actor, facility, scope, relationship, completeness, or chronology inference |

## Implementation sequence

1. Create the isolated module and authorized imports.
2. Define the fixed source identity and exact constraint tuple.
3. Implement private source-string and structural validators.
4. Implement private location projection.
5. Implement indexed event projection with fail-closed minimum-content handling.
6. Implement the single public projection function.
7. Create the focused test module covering `AT-01` through `AT-36`.
8. Run focused, Cross-Border, full-regression, compile, import-boundary, and
   artifact-scope verification.

## Verification requirements

- focused projector tests: zero failures and errors;
- existing observed-history canonical tests: zero failures and errors;
- all Cross-Border service tests: zero failures and errors;
- full regression: zero failures and errors;
- compile checks: pass;
- diff whitespace checks: pass;
- module dependency audit: pass;
- only the two implementation files plus this plan and its governing pending
  decision may exist as pending paths; and
- HEAD and origin/main remain unchanged until a separate sealing gate.

Test counts are observational outputs and are not pre-authorized constants.

## Explicit exclusions

No implementation gate based on this plan may modify existing production or test
files, export the projector, register a target, execute network acquisition,
assemble pages or webhooks, mutate compatibility or dossier state, implement
MyDHL or Korea Post EMS, serialize or persist results, deploy, activate runtime,
or select a production provider.

## Gate result

- exact executable surface: `DEFINED`;
- exact mapping and constraints: `DEFINED`;
- failure behavior: `DEFINED`;
- acceptance surfaces: `AT-01` through `AT-36`;
- authorized later implementation artifact count: `2`;
- projector implementation performed: `NO`;
- registry and package mutation: `DENIED`; and
- next gate: separate two-file implementation authorization and write preflight.
