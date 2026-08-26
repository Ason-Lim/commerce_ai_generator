# Observed Route Event History Target-Family Ownership Decision

## Document status

- Status: `research architecture decision`
- Decision ID: `CB-EA5A-2`
- Decision date: `2026-08-26`
- Scope: target-family separation, identifier, and ownership
- Authority: `architecture-level only`
- Concrete canonical schema authority: `not granted`
- Production model mutation: `not authorized`
- Projection registry mutation: `not authorized`
- Ingress mutation: `not authorized`
- Dossier mutation: `none`
- Provider decision mutation: `none`

## Decision question

Should observed shipment-event history be represented by:

1. an extension of `shipping_route_evidence`;
2. a subordinate structure within the same canonical target family; or
3. an independent canonical target family?

If independent, which layer owns its canonical semantics?

## Preconditions

The following predecessor findings are preserved:

- `planned_route_topology` and `observed_route_event_history` are distinct
  evidence semantics;
- `ShippingRouteEvidence` and `ShippingRouteType` currently express planned
  route structure and prospective evidence;
- direct registered tracking sources provide partial event-history structure;
- integrated evidence is sufficient for problem definition and conditional
  architecture design;
- integrated evidence is not sufficient to establish a concrete canonical
  contract or authorize production implementation;
- all evaluated provider projections remain `unknown` with value `None`.

## Options considered

### Option 1 — Extend `ShippingRouteEvidence`

Decision: `denied`.

`ShippingRouteEvidence` contains prospective route, availability, estimate,
cost, constraint, provenance, and freshness semantics.

Observed event history has materially different invariants:

- occurred-event reporting;
- event and shipment correlation;
- provider-native status;
- occurrence and observation times;
- event ordering;
- history completeness;
- duplicate and revision behavior;
- event-level provenance.

Adding those concerns to `ShippingRouteEvidence` would collapse planned and
observed evidence into one contract and give existing route fields meanings
they do not currently possess.

### Option 2 — Add an observed-history structure within
`shipping_route_evidence`

Decision: `denied`.

A subordinate structure within the same target family would still couple:

- projection compatibility;
- provider admission;
- provenance evaluation;
- freshness evaluation;
- partial-history state;
- lifecycle and acquisition behavior.

A provider may support planned route evidence without tracking history, or
tracking history without a sufficient planned-route classification.

The two evidence families therefore require independently observable
compatibility and independently governed lifecycle behavior.

### Option 3 — Independent canonical target family

Decision: `authorized_at_architecture_level`.

The reserved target-family identifier is:

`observed_route_event_history`

This identifier represents evidence of shipment-related events reported as
having occurred.

It does not represent:

- a planned route offer;
- route availability;
- a rate or quote;
- `ShippingRouteType`;
- legal custody;
- regulatory clearance;
- delivery correctness;
- loss responsibility;
- final settlement.

## Ownership decision

The canonical semantics of `observed_route_event_history` are owned by the
Commerce AI Cross-Border Evidence Layer.

Ownership is not assigned to:

- a carrier;
- a shipping aggregator;
- a fulfillment provider;
- a tracking vendor;
- the Provider Registry;
- the Category Registry;
- `ShippingRouteEvidence`;
- `ShippingRouteType`;
- a provider-specific adapter.

Provider contracts remain source-local observations.

Commerce AI retains authority to define canonical identity, time, ordering,
completeness, provenance, freshness, validation, and unknown-state behavior
through later separately authorized gates.

## Relationship to existing target families

`shipping_route_evidence` and `observed_route_event_history` are independent
canonical target families.

Their relationship is bounded as follows:

| Concern | `shipping_route_evidence` | `observed_route_event_history` |
|---|---|---|
| Primary meaning | Planned or prospective route evidence | Reported occurred-event history |
| Route structure | `direct_international`, `forwarder`, `multi_leg` | Not inferred |
| Availability | Planned-route availability | Not inferred from event existence |
| Estimates | Transit and route-cost estimates | Must remain distinct from occurred events |
| Main correlation | Route, quote, carrier, service, request | Shipment, tracking record, event |
| Temporal concern | Estimate and evidence freshness | Occurred, recorded, retrieved, evaluated |
| Completeness | Optional planned evidence fields | Explicit unknown or partial-history concern |
| Ordering | Not an event-sequence contract | Requires a separately defined policy |

The existence of an object in either family does not require an object in the
other family.

A shared provider, tracking reference, shipment reference, or carrier reference
does not merge the objects or transfer semantic authority between them.

## Provenance ownership boundary

The existing `EvidenceProvenance` contract is a reusable internal precedent for
source and record traceability.

A future observed-history contract may reuse or compose that precedent only
after separately deciding:

- history-response provenance;
- event-level provenance;
- reporting source;
- original event actor when known;
- downstream carrier or postal-operator identity;
- source-record correlation;
- retrieved and effective time meanings.

`effective_at` must not automatically become event `occurred_at`.

`retrieved_at` must not be interpreted as provider-recorded time.

An aggregator or tracking provider must not automatically be recorded as the
original event actor.

## Freshness ownership boundary

The existing `EvidenceFreshnessState` vocabulary is a reusable precedent.

The existing generic time-selection rule does not automatically define
event-history freshness.

A later contract gate must distinguish:

- event occurrence age;
- provider recording delay;
- response retrieval time;
- evaluation time;
- response freshness;
- history completeness.

A recently retrieved response can contain old valid events or incomplete
history. Event age and evidence freshness must remain separable.

## Registry and projection boundary

This architecture decision reserves a target-family identifier but does not
register it in production.

It does not modify:

- `external_evidence_ingress.py`;
- `external_evidence_projection.py`;
- provider or source registries;
- canonical projection compatibility;
- candidate admission;
- provider selection;
- runtime acquisition.

No provider is automatically applicable to the reserved target family.

Applicability and compatibility require future subject-specific authorization
and observation.

## Concrete contract boundary

This decision does not establish:

- a Python class or dataclass;
- an enum;
- canonical fields;
- required or optional cardinality;
- event identity;
- a composite key;
- event ordering;
- a tie-breaker;
- duplicate handling;
- correction or revision behavior;
- partial-history representation;
- timestamp parsing or normalization;
- location normalization;
- event-status normalization;
- adapter or projector behavior;
- migration or regression rules.

These remain mandatory subjects of a later contract-definition gate.

## Compatibility consequence

Every currently evaluated provider retains:

- `canonical_projection_compatibility`: `unknown`;
- canonical projection value: `None`.

The architecture-level reservation of a target family does not constitute
provider applicability, compatibility, or projection evidence.

## Decision

The following architecture direction is established:

- `shipping_route_evidence` remains the planned-route target family;
- `observed_route_event_history` is reserved as an independent target-family
  identifier;
- its canonical semantics are owned by the Commerce AI Cross-Border Evidence
  Layer;
- provider schemas remain source-local;
- canonical schema establishment remains unauthorized;
- production registration and implementation remain unauthorized.

## Gate result

- semantic separation: `pass`;
- independent lifecycle requirement: `pass`;
- independent provenance requirement: `pass`;
- independent freshness-policy requirement: `pass`;
- target-family identifier: `reserved`;
- independent target-family architecture: `authorized`;
- concrete canonical schema: `not_yet_authorized`;
- production registration: `denied`;
- provider projection: `denied`;
- canonical projection compatibility: `unknown`;
- canonical projection value: `None`;
- dossier mutation: `none`;
- production mutation: `none`.

## Required next gate

A separately authorized contract-definition gate must decide:

1. history and event object boundaries;
2. event identity and composite-key policy;
3. event sequence and ordering policy;
4. complete, partial, and unknown-history states;
5. duplicate, correction, and revision handling;
6. occurred, recorded, retrieved, and evaluated-time semantics;
7. timezone and offset requirements;
8. event location and actor representation;
9. history-response and event-level provenance;
10. freshness semantics;
11. compatibility and migration behavior;
12. validation, adapter, projection, and regression authority.

Until that gate is completed, no canonical or production contract exists.
