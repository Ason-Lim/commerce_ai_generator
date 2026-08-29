# Observed route event history integrated wave completion decision

Decision ID: `CB-EA5E-16`

Decision type: integrated observed-route-event-history wave completion

Decision status: `WAVE COMPLETE WITH THREE SEALED IMPLEMENTATIONS AND ONE SEALED DEFERRED BRANCH`

Authority class: research completion record only

Production runtime authority: `NONE`

## Purpose

This decision records the bounded completion state of the current
`observed_route_event_history` provider research wave.

It integrates four already-sealed branch outcomes without reopening, rewriting,
ranking, selecting, or activating any provider.

The four branches are:

1. ShipStation V2;
2. MyDHL API;
3. TracX SmartShip; and
4. Korea Post EMS.

This decision creates no new evidence and changes no prior evidence state.

## Governing boundaries

This decision is subordinate to the existing provider-neutral canonical
contract, provenance contract, external-evidence dossier, provider-specific
worksheets and decisions, implementation result decisions, and annotated seals.

It also preserves the research boundary recorded in
`observed_route_event_history_next_wave_candidate_boundary_decision.md`.

That prior boundary established completion precedent for an earlier executable
projector branch. This decision does not reinterpret or enlarge that precedent.

No authority transfers from one provider branch to another.

No observed field or mapping from one provider may be attributed to another
provider by similarity, shared carrier coverage, brand relationship, or adjacent
API documentation.

## Integrated result

The current observed-route-event-history research wave is complete in the
following bounded sense:

- three provider-specific projector branches are implemented and sealed;
- one admitted provider branch is sealed as stopped and deferred;
- all four candidate identities remain distinct;
- all four dossier outcomes remain unchanged; and
- no production or runtime authority is created.

Completion means that the authorized research lifecycle for these four branch
outcomes has reached its recorded endpoint.

Completion does not mean universal provider support, production readiness,
provider equivalence, routing preference, or automatic activation.

## Branch outcome matrix

| Provider branch | Candidate identity | Canonical compatibility | Executable projector state | Integrated outcome |
| --- | --- | --- | --- | --- |
| ShipStation V2 | `candidate:shipping:shipstation-api` | `observed` | implemented and sealed | `COMPLETE / SEALED` |
| MyDHL API | `candidate:shipping-landed-cost:mydhl-api` | `observed` | implemented and sealed | `COMPLETE / SEALED` |
| TracX SmartShip | `candidate:shipping-aggregator:tracx-smartship` | `observed` | implemented and sealed | `COMPLETE / SEALED` |
| Korea Post EMS | `candidate:shipping:korea-post-ems` | `unknown / None` | not authorized and not created | `STOP / DEFERRED / SEALED` |

## ShipStation V2 branch

The ShipStation V2 branch remains bound to its registered
`get_tracking_log` surface.

Its canonical compatibility record is:

- record: `cb-ea3b1-shipstation-006`;
- field: `canonical_projection_compatibility`;
- state: `observed`.

Its provider-specific projector and focused tests are tracked and sealed.

This completion decision does not change ShipStation event semantics, mapping
rules, unresolved fields, completeness state, ordering boundary, package-export
state, registry state, or runtime state.

## MyDHL API branch

The MyDHL API branch remains bound to the inspected MyDHL Tracking surface and
its sealed evidence version.

Its canonical compatibility record is:

- record: `cb-ea3b1-mydhl-006`;
- field: `canonical_projection_compatibility`;
- state: `observed`.

Its provider-specific projector and focused tests are tracked and sealed.

This completion decision does not change MyDHL event semantics, conditional
temporal composition, raw fallback rules, unresolved fields, completeness state,
ordering boundary, package-export state, registry state, or runtime state.

## TracX SmartShip branch

The TracX SmartShip branch remains bound to polling
`SmartShipService.Tracking` and its observed `tracking_history` collection.

Its canonical compatibility record is:

- record: `cb-ea4r6-tracx-smartship-006`;
- field: `canonical_projection_compatibility`;
- state: `observed`.

Its provider-specific projector and focused tests are tracked and sealed.

The existing raw-temporal-only boundary remains effective. The polling `date`
evidence does not become a timezone-aware canonical occurrence instant.

Delivery WebHook evidence and `MultiTracking` assembly remain excluded.

This completion decision does not change TracX mapping rules, unresolved fields,
source attribution, completeness state, ordering boundary, package-export state,
registry state, or runtime state.

## Korea Post EMS branch

Korea Post EMS remains an admitted candidate.

Its exact canonical compatibility record is:

- record: `cb-ea4r2b-korea-post-ems-006`;
- field: `canonical_projection_compatibility`;
- state: `unknown`;
- accepted value: `None`.

Direct registered event-level response-schema evidence was not established.

Therefore:

- the compatibility worksheet remains absent and deferred;
- projector review remains unauthorized;
- the provider-specific projector remains absent;
- the focused projector test remains absent; and
- automatic reopening is denied.

This is a sealed `STOP / DEFERRED` outcome, not a rejection or removal of the
candidate.

Reopening requires a separately authorized review based on direct, registered,
and sealed official event-level response-schema evidence.

## Canonical and evidence preservation

The external-evidence provider evaluation dossier is not modified by this
decision.

The three `observed` records and the Korea Post EMS `unknown / None` record are
preserved exactly.

The provider-neutral canonical model is not modified.

Existing uncertainty and non-inference boundaries remain effective, including:

- no invented event time;
- no invented recorded time;
- no invented stable event identity;
- no invented event actor or relationship;
- no invented carrier reference;
- no invented completeness guarantee;
- no invented chronological ordering;
- no invented pagination or freshness semantics; and
- no cross-provider evidence attribution.

Provider-specific implementation does not promote provider-native claims into
universal canonical guarantees.

## Implementation meaning

The three implemented projectors are isolated transformations of already
acquired provider evidence into the existing provider-neutral canonical model.

Their sealed existence records research implementation completion only.

It does not authorize:

- package export;
- ingress registry participation;
- projection registry participation;
- automatic provider discovery;
- network acquisition;
- credential use;
- persistence;
- production invocation;
- runtime activation;
- provider ranking;
- provider selection;
- provider fallback routing; or
- cross-provider assembly.

No projector is declared preferred, primary, equivalent, substitutable, or
production-ready by this decision.

## Explicit non-authorities

This decision does not authorize:

1. a new provider candidate;
2. a new evidence-source registration;
3. a dossier mutation;
4. a canonical-model mutation;
5. a provider worksheet mutation;
6. a projector mutation;
7. a test mutation;
8. a package export;
9. an ingress or projection registry mutation;
10. a network or credential operation;
11. persistence or serialization integration;
12. production runtime activation;
13. provider ranking or selection;
14. Korea Post EMS reopening;
15. a new architecture candidate adoption;
16. stage, commit, tag, or push; or
17. any authority not stated expressly in this decision.

## Continuity constraints

Previously sealed artifacts remain sealed and unchanged.

External research proposals remain research-grounded architecture candidates
until they pass project-owned baseline, regression testing, shadow evaluation,
and evidence review under a separately opened lifecycle.

AI-inferred or externally proposed attributes do not become canonical evidence
through this completion decision.

No landed-cost, customs, tariff, tax, fee, shipping-route, or payment-execution
authority is created here.

## Completion determination

The integrated wave result is:

- ShipStation V2: `COMPLETE / SEALED`;
- MyDHL API: `COMPLETE / SEALED`;
- TracX SmartShip: `COMPLETE / SEALED`;
- Korea Post EMS: `STOP / DEFERRED / SEALED`;
- provider candidate preservation: `PASS`;
- canonical compatibility inventory: `PASS`;
- cross-provider identity separation: `PASS`;
- dossier mutation: `NONE`;
- implementation mutation by this decision: `NONE`;
- production runtime authority: `NONE`; and
- integrated observed-route-event-history wave: `COMPLETE`.

This completion result is bounded to the four sealed branch outcomes named in
this document.

## Required next gate

The required next gate is:

`CB-EA5E-16-D_INTEGRATED_WAVE_COMPLETION_DECISION_JOINT_READ_ONLY_VALIDATION`

That gate may inspect only this new completion decision and its sealed inputs.

It must verify:

1. exact four-branch identity;
2. exact three-implemented and one-deferred outcome counts;
3. exact canonical compatibility states;
4. Korea Post EMS candidate preservation and deferred boundary;
5. absence of dossier, code, package, registry, network, and runtime mutations;
6. absence of provider ranking or selection;
7. preservation of all sealed input identities; and
8. exactly one untracked completion-decision file.

It must perform no stage, commit, tag, push, code mutation, dossier mutation,
network operation, provider selection, or runtime activation.
