# MyDHL API Observed Route Event History Projector Authorization Boundary Decision

## Decision status

- Gate: `CB-EA5D-1B`
- Candidate: `candidate:shipping:mydhl-api`
- Evaluated product: MyDHL API Tracking, inspected version `3.3.1`
- Decision: `BOUNDED PROJECTOR PLANNING AUTHORIZED WITH TEMPORAL COMPOSITION DEFERRED`
- Projector implementation: `NOT YET AUTHORIZED`
- Package export, registry, network, and runtime authority: `DENIED`

## Purpose

This decision determines whether the retained MyDHL API candidate may proceed
from observed canonical compatibility into provider-specific projector planning.
It does not implement a projector and does not modify provider-neutral runtime
surfaces.

## Governing evidence

The decision is governed by:

1. `mydhl_api_observed_route_event_history_projection_compatibility_worksheet.md`;
2. `mydhl_api_observed_route_event_history_projection_compatibility_decision.md`;
3. the sealed provider-neutral `ObservedRouteEventHistory` contract;
4. the sealed ShipStation V2 projector as an ownership and exclusion precedent;
5. the external-evidence provider dossier and source-identity rules.

The compatibility result is a bounded strong-partial observation. It is not
implementation authority by itself.

## Candidate identity boundary

The future projector, if separately authorized, must own the fixed source
identity:

```text
candidate:shipping:mydhl-api
```

The identity must not alias DHL Shipment Tracking – Unified, another DHL API
product, ShipStation, ShipEngine, Korea Post EMS, or any adjacent source.
Provenance mismatch must fail closed.

## Module ownership boundary

Planning may target one independent provider-specific module:

```text
app/services/cross_border/mydhl_api_observed_route_event_history_projector.py
```

and one focused test module:

```text
tests/services/cross_border/test_mydhl_api_observed_route_event_history_projector.py
```

The provider-specific projector must not be exported through the
provider-neutral `app.services.cross_border` package. No shared projector
registry, provider factory, adapter registry, or runtime dispatcher is
authorized.

## Planning authority

The next planning gate may define:

- one deterministic projector function over already-acquired evidence;
- exact caller-supplied correlation and provenance requirements;
- exact accepted shipment and piece event-collection structures;
- conservative event mapping and normalization;
- scope and scope-reference rules;
- raw temporal fallback representation;
- service-area location restraint;
- fail-closed structural and minimum-content behavior;
- an exact constraint tuple; and
- an acceptance-test matrix.

Planning may not create production or test code.

## Temporal evidence boundary

The worksheet observes event `date`, `time`, and optional `GMTOffset`, but also
records unresolved exact source-format constraints across responses.

Consequently, this decision does not authorize datetime parsing or temporal
composition.

Until a later evidence or planning decision establishes exact accepted source
formats:

- `occurred_at` remains `None`;
- directly supplied non-empty temporal components may be retained only in an
  unambiguous `occurred_at_raw` representation defined by the plan;
- missing, malformed, or unsupported offsets must not trigger timezone
  inference;
- UTC, account, carrier, service-area, and location timezone assumptions are
  prohibited;
- shipment timestamps, request time, retrieval time, and evaluation time must
  not become event occurrence or recorded time; and
- `recorded_at` and `recorded_at_raw` remain absent unless separate direct
  provider evidence is established.

The planning gate must not silently introduce a parser based on examples or
common MyDHL conventions.

## Collection ownership and scope boundary

Shipment-owned and piece-owned event collections are semantically distinct.
Planning must define an input surface that makes collection ownership explicit
without guessing from event contents.

When ownership is directly established:

- shipment events may use `scope=SHIPMENT` with the shipment tracking number as
  `scope_reference`;
- piece events may use `scope=PIECE` with the piece tracking number as
  `scope_reference`; and
- response order may be retained as source order without a chronological claim.

When collection ownership is ambiguous:

- the projector must not guess shipment or piece scope;
- scope must remain `UNKNOWN` with no scope reference, or the input must fail
  closed according to one exact rule selected by the implementation plan; and
- the choice must be covered by explicit acceptance tests.

Cross-response and multi-page assembly remain unauthorized.

## Event mapping boundary

Planning may preserve only directly supported MyDHL values, including:

- provider-native `typeCode` as `provider_event_code`;
- event description as `raw_status_description`;
- raw temporal components under the deferred temporal policy;
- non-empty service-area description as location `raw_description`; and
- directly supplied remarks or source-local service-area values as restrained
  metadata when explicitly enumerated by the plan.

No normalized delivery state, stable event identity, actor, facility identity,
custody, jurisdiction, or relationship may be derived.

## Location boundary

A service area is not automatically a facility, actor, customs authority,
jurisdiction, custody holder, or physical event site.

The future plan may allow:

- non-empty service-area description as location `raw_description`; and
- source-local service-area code in event metadata.

It may not populate facility code or facility name without separate official
semantic evidence. Country, subdivision, locality, and postal code also remain
absent unless directly established.

## Event minimum-content boundary

Each projected event must contain at least one canonical minimum-content value
directly supported by the source. Planning must enumerate the accepted
alternatives.

An empty or unsupported source event must not produce an empty canonical event
or be silently skipped. The plan must require an indexed failure and atomic
projection unless a different fail-closed collection rule is separately
authorized.

## History boundary

The future bounded result must remain conservative:

- completeness: `UNKNOWN`;
- ordering: `SOURCE_ORDER` only when source array order is retained, otherwise
  `UNKNOWN`;
- chronological ordering: not claimed;
- `has_more`: `None`;
- `next_page_token`: `None`;
- freshness: `None`; and
- source record and request correlation fields: absent unless directly supplied
  under an exact owned rule.

Presence of occurrence-like components does not establish history completeness,
chronology, pagination, retention, or freshness.

## Failure behavior boundary

Planning must require fail-closed behavior for:

- wrong top-level and nested runtime types;
- missing required correlation or provenance;
- provenance source mismatch;
- ambiguous structures not covered by the exact input contract;
- wrong supported-field runtime types;
- invalid raw-temporal component structures; and
- events without supported minimum content.

Errors must not be converted into an empty successful history.

## Explicit exclusions

This authorization denies:

- projector implementation at this gate;
- datetime parsing or aware-instant construction;
- network acquisition, credentials, polling, or webhooks;
- response pagination or cross-response assembly;
- provider-neutral package export;
- ingress or projection registry mutation;
- runtime wiring, deployment, or activation;
- serialization, persistence, API, or database integration;
- canonical-model mutation;
- provider ranking or production-provider selection;
- MyDHL landed-cost projector expansion; and
- Korea Post EMS admission or implementation.

## Required next planning record

The next gate must create a read-only implementation plan and acceptance-test
matrix. It must resolve, without source inference:

1. the exact projector function signature;
2. the exact accepted shipment and piece input shapes;
3. the ambiguous-ownership rule;
4. the deterministic raw-temporal composite format;
5. the exact supported event and metadata fields;
6. the event minimum-content and atomic-failure rule;
7. the exact history correlation fields;
8. the exact constraint tuple and order;
9. package and registry exclusions; and
10. acceptance tests for every conditional branch.

The planning record must keep `occurred_at=None` unless a separate authority
establishes exact parsing formats before implementation.

## Decision

MyDHL API is authorized to proceed to bounded provider-specific projector
planning with temporal composition deferred.

This decision recognizes stronger direct event evidence than the first
ShipStation projector while preserving stricter branching controls. It creates
no executable, registry, package, network, or runtime authority.

## Next gate

The next gate is
`CB-EA5D-2_MYDHL_PROJECTOR_IMPLEMENTATION_PLAN_AND_ACCEPTANCE_MATRIX`.
