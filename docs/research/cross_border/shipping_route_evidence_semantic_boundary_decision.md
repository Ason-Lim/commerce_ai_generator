# Shipping-Route Evidence Semantic Boundary Decision

## Document status

- Status: research architecture decision
- Decision ID: `CB-EA4P`
- Decision date: `2026-08-26`
- Scope: canonical shipping-route evidence semantics
- Authority: research-only
- Production model mutation: not authorized
- Dossier mutation: none
- Provider decision mutation: none

## Decision question

Should Commerce AI distinguish:

1. `planned_route_topology`; and
2. `observed_route_event_history`

when evaluating external shipping evidence?

## Decision

Yes. The two concepts are semantically distinct and must not be represented as
though they were interchangeable evidence.

The distinction is established as a research semantic boundary only.

This decision does not add a production enum, dataclass field, canonical target
family, adapter, provider mapping, registry entry, score, rank, recommendation,
selection rule, or runtime behavior.

## Existing canonical contract finding

The existing `ShippingRouteEvidence` contract contains:

- `route_type`;
- `origin_country`;
- `destination_country`;
- `availability_state`;
- `carrier_reference`;
- `forwarder_reference`;
- `estimated_transit_days`;
- `estimated_route_cost`;
- `route_cost_currency`;
- `constraints`;
- `provenance`;
- `freshness`.

The contract contains planned or prospective signals such as availability,
estimated transit time, estimated cost, currency, and constraints.

It does not contain an explicit discriminator between planned and observed
evidence.

It also does not contain event-history fields such as:

- tracking identifier;
- event identifier;
- event sequence;
- event status;
- occurrence timestamp;
- scan timestamp;
- facility;
- event location;
- actual carrier movement;
- delivery-event history.

The current production contract is therefore a
`planned_route_topology` candidate in semantic intent. This statement is a
research interpretation and does not rename the production class or target
family.

## ShippingRouteType boundary

`ShippingRouteType` currently contains:

- `direct_international`;
- `forwarder`;
- `multi_leg`.

These values describe provider-independent route structure.

They do not describe:

- whether evidence is planned or observed;
- whether a route event actually occurred;
- whether a quote became a shipment;
- whether a carrier scan was recorded;
- whether delivery was completed.

The planned-versus-observed distinction must not be encoded by adding temporal
or evidentiary meaning to the existing route-structure values.

## Planned-route-topology semantic unit

`planned_route_topology` means prospective evidence about an offered,
available, quoted, estimated, or intended shipping route.

Candidate material may include:

- origin and destination;
- route structure;
- carrier or forwarder reference;
- service reference;
- availability;
- estimated transit duration;
- estimated route cost and currency;
- service and route constraints;
- quote or request correlation;
- provenance and freshness.

Planned topology evidence does not prove that shipment movement occurred.

A quoted carrier or service identity does not independently establish
`direct_international`, `forwarder`, or `multi_leg`.

## Observed-route-event-history semantic unit

`observed_route_event_history` means evidence of actual shipment-related events
reported as having occurred.

A future canonical contract candidate would require bounded consideration of:

- tracking or shipment correlation identity;
- event identity or stable sequence;
- event status or provider event code;
- occurrence or scan timestamp;
- location or facility when supplied;
- carrier reference;
- event ordering;
- provenance;
- freshness;
- unknown, unavailable, and incomplete-history boundaries.

A tracking event does not independently establish legal custody, regulatory
clearance, delivery correctness, loss responsibility, or final settlement.

No such production canonical contract is currently present in the inspected
cross-border model.

## Orthogonal semantic axes

The following axes are independent:

| Axis | Example values | Meaning |
|---|---|---|
| Evidence semantics | planned topology / observed event history | Whether evidence describes a prospective route or occurred events |
| Route structure | direct international / forwarder / multi-leg | How the route is structurally classified |
| Availability | available / unavailable / unknown | Whether a planned route is available |
| Event status | future contract candidate | What an observed shipment event reports |
| Evidence authority | observed / verified boundary | Strength and authority of the supporting evidence |

One axis must not be inferred solely from another.

## Existing provider worksheet effect

The inspected shipping-route worksheets are:

- Shippo API;
- ShipStation API v2;
- EasyPost API;
- MyDHL API.

They evaluate rating, shipment, service, cost, transit estimate, and related
planned-route material.

They explicitly exclude tracking-event history from their observation units.

Each worksheet identifies a blocking gap: the inspected provider documentation
does not supply a bounded semantic basis for the mandatory canonical
`ShippingRouteType`.

This semantic-boundary decision does not remove that gap.

Therefore the existing proposed results remain:

- `canonical_projection_compatibility`: `unknown`;
- value: `None`.

No existing provider worksheet or dossier record is reinterpreted or mutated by
this decision.

## MyDHL subject identity note

The registered MyDHL subject identity is:

- `candidate:shipping-landed-cost:mydhl-api`

This hybrid identity has both shipping-route and landed-cost-component
applicable target-family worksheets.

A supported result for one target family must not cause another applicable
target family to become observed.

## Canonical target-family decision

This document does not create new target families.

For current protocol application:

- `shipping_route_evidence` remains the existing canonical target family;
- its production contract remains unchanged;
- `planned_route_topology` is a research semantic lens;
- `observed_route_event_history` is a separate future canonical-contract
  candidate.

A future architecture decision must determine whether to:

1. clarify the existing `ShippingRouteEvidence` documentation as planned-route
   evidence;
2. add an explicit semantic discriminator;
3. introduce a separate observed-event-history evidence contract;
4. introduce a separate canonical target family;
5. define compatibility and migration behavior.

No option is authorized for implementation by this document.

## Required future gates

Before any production change, a separately authorized architecture gate must
define:

1. canonical names and ownership;
2. precise planned-route invariants;
3. precise observed-event invariants;
4. event identity and ordering rules;
5. timestamp and timezone rules;
6. location and facility normalization boundaries;
7. unknown, unavailable, partial-history, and out-of-order behavior;
8. provenance and freshness requirements;
9. compatibility with existing `ShippingRouteEvidence`;
10. adapter and provider-mapping authority;
11. regression and migration requirements;
12. dossier and observation-protocol consequences.

## Prohibited inferences

This decision prohibits:

- treating a quote as an occurred shipment event;
- treating a tracking event as a planned route offer;
- assigning `ShippingRouteType` from carrier identity alone;
- assigning route structure from international origin and destination alone;
- manufacturing missing route legs;
- manufacturing missing tracking events;
- treating missing history as delivery failure;
- treating an event timestamp as route freshness without policy;
- changing provider compatibility records solely because this boundary exists.

## Authority boundary

This decision does not authorize:

- production code changes;
- canonical model changes;
- provider adapter implementation;
- API acquisition or credentials;
- live tracking;
- shipment booking;
- warehouse execution;
- carrier selection;
- provider ranking;
- provider verification;
- recommendation activation;
- dossier mutation.

## Final conclusion

The semantic split is necessary.

The existing `ShippingRouteEvidence` contract is best understood, at the
research level, as a planned-route-topology candidate.

Observed route-event history is not represented by the current canonical
contract and requires a separate future architecture decision before
implementation.

Existing Shippo, ShipStation, EasyPost, and MyDHL shipping-route projection
results remain `unknown / None` because their mandatory route-type semantics
gap remains unresolved.
