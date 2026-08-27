# MyDHL API observed route event history projector implementation plan and acceptance-test matrix

## Decision status

- Gate: `CB-EA5D-2B`
- Candidate: `candidate:shipping:mydhl-api`
- Inspected product: MyDHL API Tracking, version `3.3.1`
- Authority: `PROJECTOR IMPLEMENTATION PLANNING COMPLETE`
- Projector implementation: `NOT YET AUTHORIZED`
- Test implementation: `NOT YET AUTHORIZED`
- Datetime composition: `DEFERRED`
- Package export, registry mutation, network acquisition, and runtime activation: `DENIED`

This document converts the sealed authorization boundary into an exact, reviewable
implementation plan. It does not create production or test code and does not expand
provider evidence.

## Authorized later implementation artifacts

Only these two later implementation artifacts may be created after a separate write
preflight:

1. `app/services/cross_border/mydhl_api_observed_route_event_history_projector.py`
2. `tests/services/cross_border/test_mydhl_api_observed_route_event_history_projector.py`

Authorized later implementation artifact count: `2`.

The provider-neutral `app.services.cross_border` package `__all__`, ingress registry,
projection registry, canonical model, provenance model, network clients, webhooks,
polling, persistence, and runtime wiring remain outside authority.

## Module ownership and public surface

The provider-specific module owns exactly one public function:

```python
def project_mydhl_api_tracking_events(
    response: Mapping[str, object],
    *,
    tracking_number: str,
    collection_scope: ObservedRouteEventScope,
    provenance: EvidenceProvenance,
) -> ObservedRouteEventHistory:
    ...
```

No overload, async variant, network wrapper, registry adapter, package re-export, or
provider-selection function is authorized.

## Input contract

- `response` must be a runtime `Mapping`; otherwise raise `TypeError`.
- `tracking_number` must be a runtime `str`, is trimmed, and must remain non-empty;
  wrong runtime type raises `TypeError`, and empty-after-trimming raises `ValueError`.
- `collection_scope` must be an `ObservedRouteEventScope`; wrong runtime type raises
  `TypeError`.
- Only `ObservedRouteEventScope.SHIPMENT` and
  `ObservedRouteEventScope.PIECE` are accepted. `PACKAGE` and `UNKNOWN` raise
  `ValueError`. Ambiguous collection ownership therefore fails closed.
- `provenance` must be an `EvidenceProvenance`; wrong runtime type raises
  `TypeError`.
- `response` must contain an `events` key. Missing `events` raises `ValueError`.
- `events` must be a list or tuple. A present empty list or tuple is a valid empty
  response snapshot. Any other runtime type, including `None`, raises `TypeError`.
- Every event must be a runtime `Mapping`; one invalid element fails the entire call.
- Projection is atomic: no partial history is returned after any validation or
  canonical-construction failure.

The function reads an already-acquired response snapshot. It performs no I/O.

## Normalization primitives

All directly supported scalar source values use one common optional-string rule:

1. absent or `None` becomes `None`;
2. a present non-string runtime value raises `TypeError`;
3. a string is trimmed with `str.strip()`;
4. an empty-after-trimming string becomes `None`; and
5. a non-empty trimmed string is preserved verbatim otherwise.

No case folding, status normalization, code translation, timezone inference,
identifier synthesis, array-position identity, or content hashing is authorized.

## Explicit scope projection

The caller-supplied `collection_scope` is authoritative only because the caller must
already know which source collection owns `events`.

- `SHIPMENT` produces `scope=SHIPMENT` and the trimmed shipment tracking number as
  `scope_reference` for every event.
- `PIECE` produces `scope=PIECE` and the trimmed piece tracking number as
  `scope_reference` for every event.
- `PACKAGE` is not an alias for `PIECE`.
- `UNKNOWN` cannot silently preserve ambiguous ownership; it fails closed.

The projector does not inspect surrounding response fields to guess collection
ownership.

## Event field mapping

| Canonical field | Exact source input | Planned value |
|---|---|---|
| `provider_event_id` | none established | `None` |
| `provider_event_code` | `typeCode` | optional-string normalized value |
| `raw_status` | none independently established | `None` |
| `raw_status_description` | `description` | optional-string normalized value |
| `occurred_at` | deferred date/time/offset composition | always `None` |
| `occurred_at_raw` | `date`, `time`, `GMTOffset` | length-prefixed composite defined below |
| `recorded_at` | none established | `None` |
| `recorded_at_raw` | none established | `None` |
| `location` | `serviceArea` | bounded raw location rule defined below |
| `actor` | none established | `None` |
| `scope` | explicit function argument | `SHIPMENT` or `PIECE` |
| `scope_reference` | explicit `tracking_number` | trimmed value |
| `source_sequence` | none established | `None` |
| `relationships` | none established | `()` |
| `provenance` | no event-specific evidence | `None` |
| `metadata` | `remarks`, service-area code | immutable source-local mapping |

Unknown event keys are ignored. They do not become canonical fields or generic
metadata automatically.

## Deferred temporal composition and raw composite

This phase performs no date, time, or offset parsing. `occurred_at` is always `None`.
Each of `date`, `time`, and `GMTOffset` is independently normalized by the optional-
string rule.

When all three normalized components are `None`, `occurred_at_raw` is `None`.
Otherwise it is the following deterministic, unambiguous composite in fixed order:

```text
date:<length>:<value>|time:<length>:<value>|GMTOffset:<length>:<value>
```

For a missing normalized component, `<length>` is `-1` and `<value>` is empty. Length
is the Python character count of the normalized string, not a byte count. Examples:

```text
date:10:2026-08-27|time:8:13:04:05|GMTOffset:6:+09:00
date:10:2026-08-27|time:-1:|GMTOffset:-1:
```

This format preserves component boundaries even when values contain `|` or `:`. It
does not assert that any value is syntactically or semantically valid. Source
temporal values are not duplicated into metadata.

## Service-area rule

The event key `serviceArea`, when present and non-`None`, must be a list or tuple.
Any other runtime type raises `TypeError`.

- zero elements produce `location=None` and no service-area metadata;
- exactly one element is accepted and must be a runtime `Mapping`;
- more than one element raises `ValueError` because selection semantics are not
  established; and
- an invalid sole element raises `TypeError`.

For the sole service-area mapping:

- `description` uses the optional-string rule;
- `code` uses the optional-string rule;
- a non-empty description creates `ObservedRouteEventLocation` with only
  `raw_description` populated;
- `code` never populates `facility_code`, country, subdivision, locality, postal
  code, actor, or scope;
- a non-empty code is retained in event metadata under exact key
  `service_area_code`; and
- an empty mapping or one whose code and description normalize to `None` contributes
  no event minimum content.

## Remarks and metadata

The event key `remarks`, when present, must be a list or tuple; any other runtime
type raises `TypeError`. Every element must be a runtime string; one invalid element
raises `TypeError`. Each string is trimmed and empty results are discarded while
source order and duplicates are preserved.

When at least one normalized remark remains, event metadata contains exact key
`remarks` with a tuple of strings. Remarks are metadata only and do not satisfy the
canonical event minimum-content rule.

The only authorized metadata keys are:

1. `service_area_code`, when non-empty; and
2. `remarks`, when at least one normalized remark remains.

The mapping is immutable through canonical construction. Metadata does not populate
status, event identity, actor, location facility semantics, or relationships.

## Event minimum content and atomic failure

An event is projectable only when at least one of these canonical values is present:

- non-empty `provider_event_code`;
- non-empty `raw_status_description`;
- non-empty `occurred_at_raw`; or
- `location` created from a non-empty service-area description.

Tracking correlation, scope, service-area code alone, remarks alone, and other
metadata do not satisfy minimum content. A non-empty source event that has no
authorized canonical minimum-content value raises `ValueError`; it must not be
silently removed. An empty source mapping also raises `ValueError`.

One invalid event fails the entire projection. No filtering, destructive
deduplication, replacement, merging, sorting, or cross-response assembly occurs.

## History construction

The result uses:

- `reporting_source_id="candidate:shipping:mydhl-api"`;
- the trimmed `tracking_number` in the canonical tracking correlation field;
- the caller-supplied `provenance` as mandatory history provenance;
- projected events as an immutable tuple in exact source order;
- `completeness=ObservedRouteEventHistoryCompleteness.UNKNOWN`;
- `ordering=ObservedRouteEventHistoryOrdering.SOURCE_ORDER`;
- `has_more=None`;
- `next_page_token=None`; and
- the exact constraint tuple below.

An empty `events` collection produces a valid empty history with the same metadata.
Occurrence components never authorize chronological sorting.

## Exact constraint tuple

The history constraints must equal this ordered tuple exactly:

```python
(
    "history_completeness_not_documented",
    "chronological_order_not_documented",
    "stable_event_identity_not_documented",
    "provider_recorded_time_not_documented",
    "event_level_actor_identity_not_documented",
    "duplicate_and_revision_semantics_not_documented",
    "pagination_and_truncation_semantics_not_documented",
    "provider_freshness_semantics_not_documented",
    "temporal_format_constraints_unresolved",
    "service_area_semantics_partially_unresolved",
)
```

Constraint order is part of the planned contract. The projector adds no constraints
from provider payload values and removes none when optional values happen to exist.

## Failure taxonomy

Raise `TypeError` for wrong runtime kinds: top-level response, scalar source fields,
scope enum, provenance, events collection, event element, service-area collection or
element, remarks collection or element.

Raise `ValueError` for structurally or semantically unsupported values: empty
tracking correlation, missing `events`, unsupported scope value, more than one
service-area element, or an event lacking canonical minimum content.

Canonical constructor exceptions propagate unchanged. The projector does not catch
and convert them into partial output.

## Implementation sequence

1. Verify the exact sealed research and canonical-model hashes.
2. Create only the provider-specific projector module and focused test module.
3. Implement private normalization, raw-temporal, service-area, remarks, and event
   projection helpers.
4. Implement the single public projection function.
5. Run the acceptance matrix, canonical-model tests, Cross-Border regression, and
   full regression.
6. Verify package export, registry, network, persistence, and runtime exclusion.
7. Create a separate implementation-result decision before any commit or tag.

## Acceptance-test matrix

| ID | Acceptance behavior |
|---|---|
| `AT-01` | A minimal mapping with `events=[]` returns a valid empty history. |
| `AT-02` | A tuple-valued empty `events` collection is accepted. |
| `AT-03` | Wrong top-level response runtime type raises `TypeError`. |
| `AT-04` | Missing `events` raises `ValueError`. |
| `AT-05` | `events=None` or another non-list/tuple raises `TypeError`. |
| `AT-06` | A wrong event-element runtime type raises `TypeError`. |
| `AT-07` | Wrong tracking-number runtime type raises `TypeError`. |
| `AT-08` | Tracking number is trimmed and empty-after-trimming raises `ValueError`. |
| `AT-09` | Wrong collection-scope runtime type raises `TypeError`. |
| `AT-10` | `SHIPMENT` is accepted and projected with the tracking reference. |
| `AT-11` | `PIECE` is accepted and projected with the tracking reference. |
| `AT-12` | `PACKAGE` is rejected with `ValueError`; piece/package aliasing is absent. |
| `AT-13` | `UNKNOWN` is rejected with `ValueError`; ambiguous scope fails closed. |
| `AT-14` | Wrong provenance runtime type raises `TypeError`. |
| `AT-15` | `typeCode` is trimmed into `provider_event_code`. |
| `AT-16` | `description` is trimmed into `raw_status_description`. |
| `AT-17` | Wrong `typeCode` or `description` runtime type raises `TypeError`. |
| `AT-18` | `raw_status`, identity, sequence, relationships, actor, and event provenance remain absent. |
| `AT-19` | `occurred_at` remains `None` even with all three temporal components. |
| `AT-20` | Complete temporal components produce the exact length-prefixed raw composite. |
| `AT-21` | Partial temporal components encode missing values with length `-1`. |
| `AT-22` | Delimiters inside temporal values remain unambiguous through length prefixes. |
| `AT-23` | Wrong temporal-component runtime type raises `TypeError`. |
| `AT-24` | Missing or empty temporal components produce `occurred_at_raw=None`. |
| `AT-25` | Absent, `None`, or empty `serviceArea` produces no location. |
| `AT-26` | Wrong service-area collection runtime type raises `TypeError`. |
| `AT-27` | More than one service-area element raises `ValueError`. |
| `AT-28` | Wrong sole service-area element runtime type raises `TypeError`. |
| `AT-29` | Sole non-empty description creates raw-description-only location. |
| `AT-30` | Service-area code is metadata only and does not create facility semantics. |
| `AT-31` | Wrong service-area code or description runtime type raises `TypeError`. |
| `AT-32` | Wrong remarks collection or element runtime type raises `TypeError`. |
| `AT-33` | Remarks are trimmed, empty entries discarded, and order and duplicates preserved. |
| `AT-34` | Only `service_area_code` and `remarks` may appear as metadata keys. |
| `AT-35` | Code-only or remarks-only events fail canonical minimum content with `ValueError`. |
| `AT-36` | Empty mapping and whitespace-only supported content raise `ValueError`. |
| `AT-37` | Any invalid element makes a multi-event projection fail atomically. |
| `AT-38` | Valid events preserve exact source order without sorting or deduplication. |
| `AT-39` | Reporting source identity equals `candidate:shipping:mydhl-api`. |
| `AT-40` | Completeness is `UNKNOWN` and ordering is `SOURCE_ORDER`. |
| `AT-41` | Pagination fields remain `None`. |
| `AT-42` | The exact ten-item ordered constraint tuple is emitted. |
| `AT-43` | History provenance is the exact caller-supplied value. |
| `AT-44` | History and event collections and metadata satisfy canonical immutability. |
| `AT-45` | Unknown event keys do not become fields or metadata. |
| `AT-46` | Direct module import exposes exactly one public function. |
| `AT-47` | Provider-neutral package export remains absent. |
| `AT-48` | Network, webhook, polling, registry, persistence, and runtime dependencies remain absent. |

Test counts are observational outputs, not pre-authorized constants. The focused file
must contain exactly one named test function for every `AT-01` through `AT-48`, but
parameterization may produce a larger observed pytest case count.

## Static file-scope acceptance

After later implementation, the pending implementation scope must contain only the
two research documents plus the two authorized implementation artifacts until a
separate result decision is created. Existing provider-neutral, registry, canonical,
provenance, ingress, projection, shipping, context, and freshness files must remain
unchanged.

Static inspection must confirm:

- exactly one public projector function;
- no `requests`, `httpx`, `urllib`, `boto3`, webhook, or polling dependency;
- no import of ingress or projection registries;
- no package `__all__` mutation;
- no serialization or persistence surface; and
- no runtime activation.

## Verification matrix

| Verification | Required result |
|---|---|
| Focused acceptance tests | all collected cases pass |
| Canonical observed-route-event-history tests | all pass |
| Focused plus canonical combined run | all pass |
| Cross-Border suite | all pass |
| Full repository suite | all pass |
| Python compilation | pass |
| Whitespace checks | pass |
| Authorized-path inventory | exact |
| Existing-file mutation | none |
| Package/registry/network/runtime surface | absent |

## Explicit non-authorizations

This plan does not authorize:

- datetime parsing or `occurred_at` composition;
- interpreting `GMTOffset`, date, or time syntax;
- service-area selection from multiple elements;
- facility, actor, custody, jurisdiction, or carrier inference;
- event identity synthesis;
- chronological sorting, pagination, history assembly, deduplication, or revision
  handling;
- package export or shared-registry mutation;
- network acquisition, webhook handling, polling, persistence, or serialization;
- runtime activation, provider ranking, or production provider selection;
- MyDHL compatibility or dossier mutation; or
- commit, tag, or push.

## Required next gate

The next gate is `CB-EA5D-3_MYDHL_PROJECTOR_IMPLEMENTATION_WRITE_PREFLIGHT`.
It must re-verify both research documents, the canonical types and constructors, the
ShipStation independent-module precedent, exact authorized paths, and all forbidden
mutation surfaces before production or test code is written.
