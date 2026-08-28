# TracX SmartShip Observed Route Event History Projector Authorization Boundary Decision

## Document status

- Gate: `CB-EA5E-10-B`
- Decision type: provider-projector implementation-authorization boundary
- Candidate: `candidate:shipping-aggregator:tracx-smartship`
- Product surface: polling `SmartShipService.Tracking`
- Source collection: polling `tracking_history`
- Canonical target: `observed_route_event_history`
- Decision:
  `BOUNDED PROJECTOR PLANNING AUTHORIZED WITH RAW-TEMPORAL-ONLY BOUNDARY`
- Projector implementation: `NOT YET AUTHORIZED`
- Test implementation: `NOT YET AUTHORIZED`
- Package export, registry, network, persistence, and runtime authority: `DENIED`
- Production mutation performed by this decision: `NO`

## Purpose

This decision determines whether the sealed TracX SmartShip polling
compatibility observation and sealed dossier record may proceed into a
provider-specific projector implementation plan and acceptance-test matrix.

It defines the maximum planning boundary. It does not create executable or test
code and does not activate any runtime surface.

## Sealed baseline

- repository HEAD and `origin/main`:
  `7b5a7298d4c55270557cabc2f9497664482936c6`;
- TracX compatibility worksheet SHA-256:
  `cea2d6bd6895eabbc7263f0e3e2dc0dc144f747ab712f02d7bcb3d484809ab2b`;
- TracX compatibility decision SHA-256:
  `c9fbf5c33105ad1cbf298ba2c02a83e28943107979af31f3272a58296aa8a17c`;
- external evidence dossier SHA-256:
  `46719fb312a1144d09b85938ddaf587ab4993cd06dea82d12dabb3eebf6a2d7a`;
- TracX dossier state:
  `canonical_projection_compatibility = observed`;
- ShipStation projector-boundary precedent:
  `261` lines,
  SHA-256
  `4c187e62e8841bd6e0eae73f32da5a838f372789e8a90b2f36c3431456f3a562`;
- MyDHL projector-boundary precedent:
  `248` lines,
  SHA-256
  `95aa832659042f46f573ee920e8e1676d0b4d313d9fdc83ff3c64a4eeca98023`;
- implementation ownership and reuse decision:
  `269` lines,
  SHA-256
  `8c619b9aeb14fa78cdb6ae10130295c2f316775aeb4f8f712f599be49fce8b6e`.

Any mismatch requires a later planning gate to stop.

## Existing production baseline

The inspected production and test artifacts are:

| Artifact | Lines | SHA-256 |
|---|---:|---|
| `app/services/cross_border/observed_route_event_history.py` | 355 | `a724aede6aa1cb4a6420672e9f5767042cda11bbc4149231b31b68884b94f905` |
| `app/services/cross_border/shipstation_v2_observed_route_event_history_projector.py` | 137 | `a77ef955523e1bd340dc5e2751f0836962435ec2e598a4c5ff0855d2d9a7096e` |
| `app/services/cross_border/mydhl_api_observed_route_event_history_projector.py` | 309 | `2c93126355ae88cbef52fa323b283dffce5b6452a2d03fbf73e4f03562cffcbb` |
| `tests/services/cross_border/test_shipstation_v2_observed_route_event_history_projector.py` | 332 | `02659367ed44f14bc1f149190eb8062ecb55c391696ec09b8004837bdeb5dd80` |
| `tests/services/cross_border/test_mydhl_api_observed_route_event_history_projector.py` | 1075 | `4fc315b4be92508bbff70cc1229e84dde831f2eda52c13cb022dcee2a07064df` |

The canonical owner remains
`app/services/cross_border/observed_route_event_history.py`.

The existing ShipStation and MyDHL projectors are precedents for structure and
fail-closed behavior. They are not evidence for TracX fields and must not be
copied as if their provider semantics applied to TracX.

## Authorization basis

Bounded planning is authorized because:

1. the candidate identity is separately admitted;
2. the polling worksheet and compatibility decision are separately sealed;
3. compatibility is accepted as `observed` with `bounded partial` strength;
4. the dossier transition to `observed` is separately authorized and sealed;
5. the mapping requires no prohibited inference;
6. the polling surface is separated from Delivery WebHook and `MultiTracking`;
7. the provider-neutral canonical owner already exists;
8. separate provider-specific projector modules are established precedent;
9. the proposed TracX projector and test paths are unoccupied; and
10. planning can remain isolated from package, registry, network, persistence,
    and runtime mutation.

## Authorized planning artifacts

The next planning gate may create exactly one research artifact:

`docs/research/cross_border/tracx_smartship_observed_route_event_history_projector_implementation_plan_and_acceptance_test_matrix.md`

That planning document may define the later possible creation of exactly these
two provider-specific artifacts:

1. `app/services/cross_border/tracx_smartship_observed_route_event_history_projector.py`;
2. `tests/services/cross_border/test_tracx_smartship_observed_route_event_history_projector.py`.

This decision does not authorize those two implementation artifacts to be
created. Their creation requires a separately validated and sealed plan followed
by another explicit implementation gate.

## Module ownership boundary

A later implementation decision may consider one independent provider-specific
projector module.

The module may own only:

- validation of an already-acquired polling `SmartShipService.Tracking`
  response;
- extraction from its polling `tracking_history` collection;
- direct provider-native field preservation;
- construction of canonical events and one immutable
  `ObservedRouteEventHistory`;
- TracX-specific limitation and constraint identifiers; and
- deterministic fail-closed behavior.

The module must not own:

- HTTP acquisition;
- authentication or credentials;
- API client construction;
- retry or rate-limit policy;
- webhook ingestion;
- `MultiTracking` assembly;
- cross-response or cross-page assembly;
- persistence or caching;
- package export;
- registry or factory dispatch;
- deployment or runtime activation.

## Reporting-source identity

The reporting source identity must be fixed to:

`candidate:shipping-aggregator:tracx-smartship`

It must not be caller-overridable.

This identity establishes only the reporting source. It does not establish the
physical carrier, carrier actor, or event-level carrier reference.

Former Qxpress naming, partner-carrier identity, and adjacent TracX surfaces
must not be silently aliased into the polling projector.

## Authorized input boundary for planning

The plan may define an input contract containing only:

- an already-acquired `SmartShipService.Tracking` response mapping;
- required response-level shipment correlation according to an exact rule
  selected by the plan from directly supported `shipping_no`, `ref_no`, and
  `qs_no` evidence;
- an existing `EvidenceProvenance` instance for the exact acquisition; and
- no caller-controlled reporting-source identity.

The plan must determine:

1. the exact accepted top-level mapping type;
2. the exact `tracking_history` collection type;
3. whether an absent, null, or empty collection is valid;
4. the deterministic correlation precedence and minimum requirement;
5. whether multiple correlation values may be preserved without inventing one
   canonical identity; and
6. the failure rule for conflicting or malformed correlation evidence.

No network client, URL, credential, session, retry configuration, webhook
payload, runtime registry, or mutable provider factory may enter the input
contract.

## Polling event mapping boundary

Planning may preserve only values directly supported by the sealed polling
surface, including:

- provider-native `status`;
- provider-native `status_code`;
- directly supported details;
- directly supported location text;
- non-empty polling `date` as unresolved raw temporal evidence;
- directly supported reason fields;
- directly supported auxiliary tracking codes; and
- proof-of-delivery references only as provider-native metadata when exact
  value and type support are present.

The plan must fix exact source-key spellings, accepted types, empty-value
handling, whitespace policy, output placement, and collision behavior before
implementation.

No case folding, status normalization, code translation, carrier inference, or
delivery-state taxonomy assignment is authorized.

## Temporal boundary

The polling `date` may be considered only for raw temporal preservation.

The plan must require:

- a supported non-empty polling `date` to map only to
  `occurred_at_raw`;
- `occurred_at=None`;
- `recorded_at=None`;
- `recorded_at_raw=None`;
- no timezone or UTC-offset inference;
- no parsing into a timezone-aware instant;
- no use of webhook `Date` formatting;
- no chronological sorting.

Array position must not be used as event identity or canonical sequence.

## Event invariant boundary

The plan must preserve the canonical minimum-content invariant.

An event may be constructed only when at least one directly supported canonical
content field is present after the exact cleaning rules are applied.

Reason fields, auxiliary tracking codes, or proof-of-delivery references stored
only as metadata must not manufacture an otherwise empty canonical event.

The plan must select one atomic failure rule under which an invalid non-empty
source entry causes the entire projection call to fail rather than being
silently dropped.

## History-level boundary

The planning record must preserve:

- completeness: `UNKNOWN`;
- ordering: `SOURCE_ORDER` only when returned array order is preserved,
  otherwise `UNKNOWN`;
- chronological ordering: not established;
- `has_more=None`;
- `next_page_token=None`;
- retention boundary: unknown;
- truncation boundary: unknown;
- duplicate and revision policy: unknown;
- freshness: `None`.

The implementation must not sort, deduplicate, merge, correct, overwrite,
supersede, or assemble source entries.

Absence of pagination evidence must not be interpreted as complete history.

## Provenance boundary

The plan must require an existing `EvidenceProvenance` instance and validate:

- exact reporting-source identity;
- evidence kind and canonical target suitability;
- immutable reuse without mutation;
- no fallback provenance construction;
- no use of retrieval time as occurrence or recorded time.

Provider-neutral provenance, context, freshness, and canonical model contracts
must be reused rather than redefined.

## Failure behavior requirements

The planning document must define deterministic failure behavior covering at
least:

- wrong top-level response type;
- wrong `tracking_history` collection type;
- wrong event-entry type;
- wrong supported-field runtime type;
- missing or malformed required response correlation;
- conflicting correlation evidence;
- invalid or mismatched provenance;
- a non-empty source event with no supported canonical minimum content;
- malformed raw temporal evidence;
- metadata collision under the selected preservation rule.

Errors must not be converted into an empty successful history.

## Acceptance-test requirements

The plan must define tests for at least:

1. minimal valid event from provider-native status;
2. minimal valid event from directly supported details;
3. location preservation without inference;
4. raw `date` preservation with all canonical instants absent;
5. response-level correlation;
6. fixed reporting-source identity;
7. source-order preservation;
8. duplicate preservation;
9. empty-history behavior;
10. invalid top-level response type;
11. invalid history collection type;
12. invalid event-entry type;
13. invalid supported-field type;
14. invalid provenance;
15. provenance source mismatch;
16. correlation absence or conflict;
17. metadata-only event rejection;
18. atomic collection failure;
19. no webhook attribution;
20. no `MultiTracking` assembly;
21. no chronological sorting;
22. completeness, pagination, and freshness conservative defaults;
23. immutable canonical result;
24. no package or registry exposure; and
25. exact authorized file scope.

Every conditional planning branch must have an acceptance test.

## Explicit exclusions

This authorization denies:

- projector implementation at this gate;
- test implementation at this gate;
- modification of the canonical model;
- package `__init__.py` export;
- ingress or projection registry mutation;
- provider factory or automatic dispatcher creation;
- live API calls or credentials;
- webhook ingestion or authentication;
- `MultiTracking` assembly;
- cross-response, cross-page, or historical assembly;
- datetime parsing or aware-instant construction;
- inferred event identity, actor, relationship, carrier, scope, or chronology;
- status taxonomy or normalized delivery-state generation;
- destructive sorting, deduplication, correction, or replacement;
- serialization, persistence, caching, API, UI, or database integration;
- provider ranking, selection, recommendation, or verification;
- Korea Post EMS consequences;
- mutation of the dossier, sealed worksheet, compatibility decision, or prior
  research artifacts;
- deployment or runtime activation;
- commit, tag, or push by this decision itself.

## Decision

- TracX bounded provider-specific projector planning:
  `AUTHORIZED WITH RAW-TEMPORAL-ONLY BOUNDARY`;
- authorized next artifact count: `ONE RESEARCH PLAN`;
- projector implementation: `NOT YET AUTHORIZED`;
- test implementation: `NOT YET AUTHORIZED`;
- canonical owner reuse: `REQUIRED`;
- provenance reuse: `REQUIRED`;
- package export: `DENIED`;
- ingress registry mutation: `DENIED`;
- projection registry mutation: `DENIED`;
- network acquisition: `DENIED`;
- persistence: `DENIED`;
- runtime activation: `DENIED`;
- production mutation performed here: `NO`.

## Required next gate

The next gate is:

`CB-EA5E-11_TRACX_PROJECTOR_IMPLEMENTATION_PLAN_AND_ACCEPTANCE_MATRIX`

It may create only the single research planning artifact named in this decision.

That plan must fix the exact symbols, input contract, source-key spellings,
cleaning rules, metadata representation, correlation rules, limitation and
constraint tuple, deterministic failure matrix, acceptance tests, authorized
file count, and verification sequence.

Only after the plan is separately validated and sealed may another authority
gate decide whether the projector and test artifacts can be created.
