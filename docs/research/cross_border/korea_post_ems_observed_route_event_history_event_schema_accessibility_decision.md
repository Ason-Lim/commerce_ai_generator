# Korea Post EMS observed route event history event-schema accessibility decision

## Document status

- Gate: `CB-EA5E-14-C`
- Artifact type: explicit inaccessible-evidence research decision
- Decision status: `REGISTERED EVENT-LEVEL RESPONSE SCHEMA NOT ESTABLISHED`
- Candidate: `candidate:shipping:korea-post-ems`
- Canonical target: `observed_route_event_history`
- TracX SmartShip branch: `COMPLETE`
- Korea Post EMS candidate status: `ADMITTED AND PRESERVED`
- Korea Post EMS compatibility worksheet: `DEFERRED`
- Korea Post EMS projector review: `NOT AUTHORIZED`
- Dossier mutation performed: `NO`
- Network evidence acquisition performed: `NO`
- Production and runtime authority: `NONE`

## Purpose

This decision records the accessibility and sufficiency state of the registered
Korea Post EMS evidence after completion of the TracX SmartShip
observed-route-event-history branch.

It asks whether the registered and sealed official evidence establishes a
directly inspectable event-level response schema sufficient to open a
candidate-specific projection-compatibility worksheet.

It performs no evidence acquisition, worksheet creation, dossier mutation,
projector work, package publication, registry mutation, or runtime activation.

## Governing evidence

This decision is governed by the sealed:

1. direct registered-source tracking-schema sufficiency review;
2. integrated observed-route-event-history contract-readiness review;
3. next-wave candidate boundary decision;
4. external evidence provider evaluation dossier;
5. completed TracX SmartShip lifecycle and implementation seal; and
6. Evidence First and fail-closed boundaries.

Those artifacts remain unchanged and authoritative.

## Decision

The registered Korea Post EMS evidence does not establish a directly
inspectable reusable event-history response schema sufficient for a bounded
`observed_route_event_history` compatibility worksheet.

The decision is:

`NO — NOT ESTABLISHED IN THE REGISTERED EVIDENCE SET`

This does not conclude that Korea Post lacks an event schema.

It does not conclude that a schema is globally or permanently inaccessible.

## Observed official surfaces

The registered evidence establishes:

- contract-customer Open API availability;
- stated domestic and international postal-item tracking APIs;
- EMS and K-Packet application APIs;
- an official EMS internet-tracking surface;
- official service-region and rate publications;
- separate application, tracking, rate, and availability surfaces; and
- a 13-character postal-item query reference.

These establish service and query surfaces only.

They do not establish an event-level response contract.

## Correlation boundary

The 13-character item number is provider-local correlation evidence only.

It does not establish:

- globally unique canonical shipment identity;
- stable event identity or sequence;
- event actor or carrier identity;
- event-level or cross-postal provenance;
- event completeness or ordering;
- duplicate or revision semantics; or
- correction, replacement, or supersession semantics.

Events from destination postal operators, customs authorities, or other network
participants must not be attributed to Korea Post without explicit evidence.

## Missing registered schema evidence

The registered evidence does not seal documented reusable source fields for:

- event status;
- provider event code;
- event description;
- occurrence time;
- provider-recorded time;
- raw temporal representation;
- timezone or UTC offset;
- location;
- facility identity;
- event actor;
- physical carrier;
- event identity;
- event sequence;
- duplicate or revision semantics;
- pagination or truncation;
- retention or update latency;
- history completeness; or
- proof-of-delivery identity.

No undocumented provider field may be invented or mapped to a canonical field.

## Accessibility meaning

For this decision, inaccessible evidence means:

> the event-level response-schema evidence required by the sealed next-wave
> boundary is not present in the registered and sealed repository evidence set.

It does not mean:

- the provider has no schema;
- the API cannot return tracking events;
- authorized customers cannot access additional documentation;
- service credentials cannot be issued;
- production access is unavailable; or
- later evidence cannot change the result.

Exact endpoints, requests, response schemas, credentials, approval conditions,
quotas, test behavior, production entitlement, storage rights, and
redistribution rights remain unresolved.

## Source separation

The following must not be attributed to Korea Post:

- TracX polling `tracking_history`;
- TracX webhook or `MultiTracking`;
- ShipStation V2 or adjacent ShipEngine schemas;
- MyDHL or DHL Unified schemas;
- destination-postal-operator schemas;
- aggregator schemas; or
- fields assembled across multiple sources.

No adjacent or composite provider schema is accepted.

## Temporal and provenance boundary

No Korea Post event temporal field or event-level provenance field is registered
for this canonical target.

This decision does not infer timestamps, timezone, ordering, freshness,
completeness, custody, event actor, carrier identity, or facility identity.

Internet-tracking presentation order is not a canonical ordering guarantee.

## Dossier consequence

The Korea Post EMS `canonical_projection_compatibility` record remains:

- state: `unknown`;
- observation value: `None`.

The dossier is not modified.

No `observed`, `reported`, `accepted`, or rejected value is inferred.

## Authority consequence

- Korea Post EMS compatibility worksheet: `DEFERRED`;
- compatibility decision: `NOT OPEN`;
- dossier mutation: `NOT AUTHORIZED`;
- projector planning: `NOT AUTHORIZED`;
- projector implementation: `NOT AUTHORIZED`;
- package export: `NOT AUTHORIZED`;
- registry participation: `NOT AUTHORIZED`;
- network acquisition: `NOT AUTHORIZED`;
- credential use: `NOT AUTHORIZED`;
- persistence: `NOT AUTHORIZED`;
- runtime activation: `NOT AUTHORIZED`.

## Non-rejection boundary

This decision does not reject Korea Post EMS.

It does not determine commercial suitability, reliability, service quality,
coverage superiority, cost competitiveness, recommendation eligibility,
fallback priority, production preference, or general research priority.

The candidate remains admitted and preserved.

## Reversibility

A later separately authorized evidence review may revisit this result if direct
official event-level response-schema evidence becomes registered and sealed.

Any later review must preserve source identity and repeat the applicable
evidence, sufficiency, compatibility, dossier, planning, implementation, and
sealing gates.

This decision does not authorize those gates.

## Explicit exclusions

This decision does not authorize:

- browsing, scraping, or evidence acquisition;
- credential request, storage, or use;
- raw-response capture;
- worksheet creation;
- dossier or canonical mutation;
- projector or test work;
- package or registry mutation;
- serialization, persistence, caching, API, UI, or database integration;
- provider verification, ranking, recommendation, selection, or fallback;
- deployment or runtime activation;
- stage, commit, tag, or push.

## Decision result

- TracX branch completion: `PASS`;
- Korea Post candidate admission: `PRESERVED`;
- official service surfaces: `OBSERVED`;
- postal-item correlation reference: `OBSERVED`;
- direct registered event-level response schema: `NOT ESTABLISHED`;
- schema global absence claim: `DENIED`;
- provider rejection: `DENIED`;
- canonical projection compatibility: `unknown / None — UNCHANGED`;
- compatibility worksheet: `DEFERRED`;
- dossier mutation: `NOT AUTHORIZED`;
- projector work: `NOT AUTHORIZED`;
- package and registry authority: `NONE`;
- network and credential authority: `NONE`;
- production and runtime authority: `NONE`;
- mutation performed by this decision: `NO`.

## Required next gate

The next gate is:

`CB-EA5E-14-D_KOREA_POST_INACCESSIBLE_EVIDENCE_DECISION_JOINT_READ_ONLY_VALIDATION`

It must validate this decision against the sealed next-wave boundary, dossier,
direct registered-source review, integrated readiness review, and completed
TracX branch.

It must stop on an identity, scope, source-attribution, authority, or
non-inference mismatch.

It must perform no evidence acquisition, worksheet creation, dossier mutation,
projector work, test execution, stage, commit, tag, push, package mutation,
registry mutation, persistence, deployment, or runtime activation.
