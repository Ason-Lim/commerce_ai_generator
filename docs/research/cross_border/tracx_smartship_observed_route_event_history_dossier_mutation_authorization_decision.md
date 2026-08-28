# TracX SmartShip observed route event history dossier-mutation authorization decision

## Document status

- Gate: `CB-EA5E-8-B`
- Artifact type: exact dossier-mutation authorization decision
- Decision status: `AUTHORIZED WITH EXACT ONE-RECORD SCOPE`
- Candidate: `candidate:shipping-aggregator:tracx-smartship`
- Canonical target: `observed_route_event_history`
- Dossier mutation performed by this document: `NO`
- Projector implementation: `NOT AUTHORIZED`
- Production and runtime authority: `NONE`

## Purpose

This decision determines whether the sealed TracX SmartShip polling
projection-compatibility observation may be transferred into its existing
`canonical_projection_compatibility` record in the external evidence provider
evaluation dossier.

It authorizes only an exact, separately validated one-record dossier mutation.
It does not modify the dossier itself.

## Sealed baseline

- repository HEAD:
  `8b2ae4f2dbd116002e9f1ca3263391d7d62eddbb`;
- repository tracking ref:
  `origin/main` at the same commit;
- dossier:
  `external_evidence_provider_evaluation_dossier.md`;
- dossier line count: `603`;
- dossier SHA-256:
  `3e3d2956ab7f44c1781febd6f24809e045461681d37feb498decd2073ec481c0`;
- TracX compatibility worksheet SHA-256:
  `cea2d6bd6895eabbc7263f0e3e2dc0dc144f747ab712f02d7bcb3d484809ab2b`;
- TracX compatibility decision SHA-256:
  `c9fbf5c33105ad1cbf298ba2c02a83e28943107979af31f3272a58296aa8a17c`;
- sealed annotated tag:
  `cross-border-tracx-smartship-observed-route-event-history-projection-compatibility-observed-v1.0`.

Any mismatch in these identities requires the later mutation gate to stop.

## Governing evidence

The authorization is governed by:

1. the sealed TracX polling compatibility worksheet;
2. the sealed TracX compatibility research decision;
3. the sealed next-wave candidate boundary;
4. the canonical `observed_route_event_history` contract;
5. the existing TracX dossier record;
6. the first-wave dossier-mutation authorization precedent; and
7. the Evidence First and fail-closed boundary.

The polling `SmartShipService.Tracking` surface, Delivery WebHook surface, and
`MultiTracking` surface remain distinct. Evidence from one surface is not
silently attributed to another.

## Authorization criteria

The exact one-record dossier mutation is authorized because all of the following
criteria are satisfied:

1. the TracX worksheet is separately validated and sealed;
2. the TracX compatibility decision is separately validated and sealed;
3. the decision accepts `canonical_projection_compatibility` as `observed`;
4. the accepted observation has strength `bounded partial`;
5. unresolved canonical fields remain absent, `None`, `UNKNOWN`, or
   provider-native evidence;
6. prohibited inference is not required;
7. source identity remains separated from adjacent products, carriers, webhook
   evidence, and `MultiTracking`;
8. the target dossier record exists exactly once as `unknown / None`;
9. existing dossier conventions support an `observed` value using
   `commerce-ai-evaluation`, `internal_research_boundary`, and a local worksheet
   reference; and
10. no model, projector, package, registry, network, persistence, production, or
    runtime mutation is required.

## Exact target

The only authorized target is:

- record ID: `cb-ea4r6-tracx-smartship-006`;
- field: `canonical_projection_compatibility`;
- current state: `unknown`;
- current value: `None`;
- current source ID: `commerce-ai-evaluation`;
- current source type: `internal_research_boundary`;
- current source reference: `CB-EA4R-6`;
- authorized replacement state: `observed`;
- source ID retained: `commerce-ai-evaluation`;
- source type retained: `internal_research_boundary`;
- authorized source reference:
  `[CB-EA5E-2 worksheet](tracx_smartship_observed_route_event_history_projection_compatibility_worksheet.md)`.

No other dossier record is authorized to change.

## Authorized replacement value

> TracX SmartShip polling `SmartShipService.Tracking` prospectively supports a
> bounded `observed_route_event_history` projection through its
> `tracking_history` collection by preserving provider-native `status`,
> `status_code`, details, directly supported location text, unresolved raw
> `date` evidence, and response-level shipment correlation within Commerce
> AI-owned history provenance. Completeness remains `UNKNOWN`; response position
> carries no chronological meaning; timezone-aware occurrence time, recorded
> time, stable event identity, actor, relationship, carrier reference,
> pagination, duplicate, revision, retention, update latency, freshness, and
> proof-of-delivery identity semantics remain absent or unresolved and are not
> inferred. Delivery WebHook evidence and `MultiTracking` assembly are excluded.

## Exact authorized replacement row

The later mutation gate may replace the existing target row with exactly:

| `cb-ea4r6-tracx-smartship-006` | `canonical_projection_compatibility` | `observed` | TracX SmartShip polling `SmartShipService.Tracking` prospectively supports a bounded `observed_route_event_history` projection through its `tracking_history` collection by preserving provider-native `status`, `status_code`, details, directly supported location text, unresolved raw `date` evidence, and response-level shipment correlation within Commerce AI-owned history provenance. Completeness remains `UNKNOWN`; response position carries no chronological meaning; timezone-aware occurrence time, recorded time, stable event identity, actor, relationship, carrier reference, pagination, duplicate, revision, retention, update latency, freshness, and proof-of-delivery identity semantics remain absent or unresolved and are not inferred. Delivery WebHook evidence and `MultiTracking` assembly are excluded. | `commerce-ai-evaluation` | `internal_research_boundary` | [CB-EA5E-2 worksheet](tracx_smartship_observed_route_event_history_projection_compatibility_worksheet.md) |

The replacement must preserve the surrounding table order and formatting.

## Required non-inference boundaries

The authorized dossier value must not be interpreted as establishing:

- complete canonical coverage;
- production or runtime readiness;
- chronological ordering;
- tracking-history completeness;
- pagination or truncation semantics;
- retention or update-latency guarantees;
- timezone or UTC-offset semantics;
- a canonical occurrence instant;
- provider recording time or response observation time;
- stable event identity;
- event-level carrier identity;
- an event actor;
- duplicate, correction, replacement, or revision semantics;
- proof-of-delivery identity or delivery correctness;
- webhook attribution;
- webhook authentication or delivery guarantees;
- `MultiTracking` assembly;
- planned-route topology;
- provider verification, ranking, selection, or recommendation; or
- Korea Post EMS compatibility consequences.

## Explicit exclusions

This authorization does not permit:

- mutation of any dossier record other than
  `cb-ea4r6-tracx-smartship-006`;
- mutation of any dimension other than
  `canonical_projection_compatibility`;
- changes to the sealed worksheet or compatibility decision;
- changes to the canonical contract;
- projector planning or implementation;
- model, adapter, serializer, or endpoint changes;
- package export or registry changes;
- live API calls or credential use;
- raw payload acquisition or retention;
- webhook ingestion;
- `MultiTracking` assembly;
- persistence, caching, API, UI, database, deployment, or activation;
- provider selection, ranking, recommendation, or verification;
- planned-route mutation;
- commit, tag, or push as part of the dossier-mutation operation.

## Validation requirements for the mutation gate

The later mutation gate must fail closed unless all of the following remain true:

1. `HEAD` and `origin/main` equal the authorized baseline;
2. the worktree is clean and the staged index is empty;
3. the dossier line count is exactly `603`;
4. the dossier SHA-256 equals the authorized baseline;
5. the sealed worksheet and compatibility-decision hashes match;
6. the target old row exists exactly once;
7. the authorized replacement row does not already exist;
8. the mutation changes exactly one table row;
9. the old row disappears exactly once;
10. the replacement row appears exactly once;
11. no other dossier content changes; and
12. no other file changes.

Commit, tag, and push must remain separate later gates.

## Authorization decision

- sealed compatibility observation: `PASS`;
- authorization criteria: `PASS`;
- exact target identity: `PASS`;
- prohibited inference required: `NO`;
- exact one-record dossier mutation: `AUTHORIZED`;
- authorized state transition:
  `unknown / None` to `observed / accepted bounded polling value`;
- mutation scope:
  `DOSSIER ONLY, EXACTLY ONE TABLE ROW`;
- source-identity separation: `REQUIRED`;
- projector planning or implementation: `NOT AUTHORIZED`;
- production and runtime mutation: `NONE`;
- dossier mutation performed by this decision: `NO`.

## Required next gate

The next gate is:

`CB-EA5E-8-C_TRACX_EXACT_DOSSIER_MUTATION`

It may perform only the exact one-row replacement authorized here.

It must stop on any baseline, hash, identity, occurrence-count, line-count, or
scope mismatch. It must leave validation, commit, annotated tag creation, and
push for later separate gates.
