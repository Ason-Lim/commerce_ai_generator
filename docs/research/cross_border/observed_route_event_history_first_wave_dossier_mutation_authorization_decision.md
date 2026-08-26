# First-wave observed route event history dossier mutation authorization decision

## Document status

- Gate: `CB-EA5B-8W-2`
- Artifact type: exact dossier-mutation authorization decision
- Decision status: `AUTHORIZED WITH EXACT TWO-RECORD SCOPE`
- Dossier mutation performed by this document: `NO`
- Production implementation: `NOT AUTHORIZED`

## Purpose

This decision determines whether the two sealed first-wave
`observed_route_event_history` compatibility observations may be transferred into
their existing canonical-projection-compatibility records in the external evidence
provider evaluation dossier.

It authorizes only an exact, separately validated dossier mutation. It does not
itself modify the dossier.

## Sealed baseline

- repository HEAD: `82099963fe7672d88e30b495339222f18a40afd6`;
- current dossier SHA-256:
  `41848176d4c6555949af6d82db19baf550fcc1e29f34a292257fa459adc088b4`;
- current ShipStation record: `cb-ea3b1-shipstation-006`, state `unknown`, value
  `None`;
- current MyDHL record: `cb-ea3b1-mydhl-006`, state `unknown`, value `None`.

The worktree was clean and synchronized with `origin/main` when the authorization
preflight was performed.

## Sealed research inputs

### ShipStation V2

- worksheet:
  `shipstation_v2_observed_route_event_history_projection_compatibility_worksheet.md`;
- worksheet SHA-256:
  `8b71dbed9d7ef30c792dd614f54c36ad7b445c1b7a732b6b16ab7fd6e30df0c4`;
- decision:
  `shipstation_v2_observed_route_event_history_projection_compatibility_decision.md`;
- decision SHA-256:
  `07a811052f25b0b4e41d9a115e2109c171e540bb9883ac55b6e6006b0a40a160`;
- sealed result: `ACCEPTED AS BOUNDED PARTIAL PROJECTION OBSERVATION`;
- accepted compatibility: `observed`.

### MyDHL API

- worksheet:
  `mydhl_api_observed_route_event_history_projection_compatibility_worksheet.md`;
- worksheet SHA-256:
  `f8449e31119c15027c7bda43e684c43dc2987958d7928926f5af54e059602b1f`;
- decision:
  `mydhl_api_observed_route_event_history_projection_compatibility_decision.md`;
- decision SHA-256:
  `eab576eba9ce46fb589c040f573d50810ab81b79428f1f9a948a2d12e1c3febb`;
- sealed result: `ACCEPTED AS BOUNDED STRONG-PARTIAL PROJECTION OBSERVATION`;
- accepted compatibility: `observed`.

## Governing distinction

An `observed` compatibility state records that inspected, source-specific evidence
supports a bounded prospective projection into the sealed canonical contract. It
does not mean complete field coverage, production readiness, provider admission,
provider selection, live acquisition authorization, or runtime activation.

The two records remain independent. ShipStation evidence cannot fill a MyDHL gap,
and MyDHL evidence cannot fill a ShipStation gap.

## Authorization criteria

A dossier mutation is authorized only because all of the following are satisfied:

1. each candidate has a separately sealed worksheet;
2. each worksheet has a separately sealed research decision;
3. each decision accepts compatibility as `observed`;
4. each accepted observation preserves unresolved canonical fields as absent,
   `None`, `UNKNOWN`, or provider-native evidence;
5. neither result requires prohibited inference;
6. source identity remains separated from adjacent products and versions;
7. the target dossier records exist exactly once and remain `unknown / None`;
8. existing dossier conventions support `observed` compatibility records using
   `commerce-ai-evaluation`, `internal_research_boundary`, and a local worksheet
   reference; and
9. no production or registry mutation is required.

## Exact ShipStation mutation authorization

The following existing record is the only authorized ShipStation target:

- record ID: `cb-ea3b1-shipstation-006`;
- field: `canonical_projection_compatibility`;
- current state: `unknown`;
- current value: `None`;
- authorized replacement state: `observed`;
- source ID retained: `commerce-ai-evaluation`;
- source type retained: `internal_research_boundary`;
- authorized source reference:
  `[CB-EA5B-8U worksheet](shipstation_v2_observed_route_event_history_projection_compatibility_worksheet.md)`.

Authorized replacement value:

> ShipStation V2 `get_tracking_log` prospectively supports a bounded
> `observed_route_event_history` projection by preserving its `events[]`
> collection, provider- and carrier-native status fields, status description,
> directly supported location evidence, and request carrier and tracking
> correlation within Commerce AI-owned history provenance. Completeness remains
> `UNKNOWN`; response position carries no chronological meaning; event occurrence,
> recorded time, stable identity, actor, relationship, duplicate, revision,
> pagination, and freshness semantics remain absent or unresolved and are not
> inferred.

No other ShipStation record or narrative paragraph is authorized to change.

## Exact MyDHL mutation authorization

The following existing record is the only authorized MyDHL target:

- record ID: `cb-ea3b1-mydhl-006`;
- field: `canonical_projection_compatibility`;
- current state: `unknown`;
- current value: `None`;
- authorized replacement state: `observed`;
- source ID retained: `commerce-ai-evaluation`;
- source type retained: `internal_research_boundary`;
- authorized source reference:
  `[CB-EA5B-8V worksheet](mydhl_api_observed_route_event_history_projection_compatibility_worksheet.md)`.

Authorized replacement value:

> MyDHL API Tracking in inspected version `3.3.1` prospectively supports a
> bounded `observed_route_event_history` projection through shipment- and
> piece-level `events[]`, provider-native `typeCode` and description, conditional
> composition of event `date`, `time`, and `GMTOffset` into a timezone-aware
> occurrence instant with raw fallback, service-area location evidence, and
> shipment or piece tracking correlation within Commerce AI-owned history
> provenance. Completeness remains `UNKNOWN`; response order is not chronological
> by default; stable event identity, recorded time, event actor, duplicate,
> revision, pagination, assembly, and freshness semantics remain absent or
> unresolved and are not inferred.

No other MyDHL record or narrative paragraph is authorized to change.

## Required mutation mechanics

The subsequent mutation gate must:

1. start from the exact sealed HEAD and dossier SHA-256 stated above;
2. replace exactly the two identified Markdown table rows;
3. preserve every other dossier byte;
4. use the accepted observation values verbatim as single table-cell values;
5. change each target state from `unknown` to `observed`;
6. preserve the source ID and source type;
7. use the authorized local worksheet reference for each candidate;
8. verify that each target record still occurs exactly once;
9. verify that the old `unknown / None` form occurs zero times for both target
   record IDs;
10. verify that the resulting diff contains only the dossier and exactly two
    changed lines; and
11. perform a separate read-only final validation before any commit.

If any precondition differs, the mutation must stop without attempting a partial
update.

## Explicit prohibitions

This authorization does not permit:

- changing any dossier record other than `cb-ea3b1-shipstation-006` and
  `cb-ea3b1-mydhl-006`;
- changing candidate admission, selection, ranking, preference, or verification;
- attributing ShipStation API formerly ShipEngine v1 or legacy ShipStation V1
  evidence to ShipStation platform API V2;
- attributing DHL Shipment Tracking - Unified evidence to MyDHL API;
- converting `UNKNOWN` completeness into `COMPLETE` or `PARTIAL`;
- inventing chronology, timestamps, stable event identity, actors, relationships,
  pagination, freshness, duplicate, revision, or assembly semantics;
- changing the canonical contract, worksheets, or research decisions;
- production model, adapter, projector, serializer, registry, or endpoint changes;
- live API calls, credentials, historical backfill, deployment, or activation; or
- commit, tag, or push as part of the dossier-mutation operation itself.

## Authorization decision

- exact two-record dossier mutation: `AUTHORIZED`;
- ShipStation state transition: `unknown / None` to `observed / accepted value`;
- MyDHL state transition: `unknown / None` to `observed / accepted value`;
- source-identity separation: `REQUIRED`;
- mutation scope: `DOSSIER ONLY, EXACTLY TWO TABLE ROWS`;
- candidate admission or selection: `NOT AUTHORIZED`;
- production implementation: `NOT AUTHORIZED`;
- dossier mutation performed here: `NO`.

## Required next gate

The next gate is `CB-EA5B-8W-3`, which may perform the exact two-row dossier
mutation defined here. It must stop on any baseline, hash, identity, line-count,
or replacement-count mismatch and must leave commit, tag, and push for later
separate gates.
