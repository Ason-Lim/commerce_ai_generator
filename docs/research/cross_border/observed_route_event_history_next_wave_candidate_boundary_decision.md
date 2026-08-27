# Observed Route Event History Next-Wave Candidate Boundary Decision

## Decision status

- Gate: `CB-EA5E-1`
- Decision type: post-first-wave completion and next-wave research boundary
- First-wave projector branch: `COMPLETE`
- Next compatibility-review candidate:
  `candidate:shipping-aggregator:tracx-smartship`
- TracX worksheet authority: `AUTHORIZED WITH POLLING-SURFACE BOUNDARY`
- Korea Post EMS worksheet authority: `DEFERRED`
- Projector implementation: `NOT AUTHORIZED`
- Dossier mutation: `NOT AUTHORIZED`
- Package, registry, network, persistence, and runtime authority: `NONE`

## Decision question

After sealing the ShipStation V2 and MyDHL API observed-route-event-history
projectors, which admitted source may proceed to the next candidate-specific
projection-compatibility worksheet without expanding production authority,
merging evidence sources, or reopening planned-route topology?

## Governing checkpoints

This decision relies on:

1. the sealed direct registered-source tracking-schema sufficiency review;
2. the sealed integrated contract-readiness review;
3. the sealed provider-neutral `ObservedRouteEventHistory` research contract;
4. the sealed Phase 1 canonical implementation;
5. the sealed first-wave ShipStation and MyDHL compatibility observations;
6. the sealed first-wave dossier compatibility mutation;
7. the sealed ShipStation V2 projector;
8. the sealed MyDHL API projector;
9. the admitted TracX SmartShip candidate record;
10. the admitted Korea Post EMS candidate record; and
11. the current external-evidence provider evaluation dossier.

This decision does not reinterpret or enlarge those checkpoints.

## First-wave completion result

The first-wave executable projector branch is complete.

Its accepted provider-specific surfaces are:

- ShipStation V2 `get_tracking_log`;
- MyDHL API Tracking.

Both projectors are isolated, deterministic transformations of already-acquired
evidence into the existing provider-neutral canonical model.

Their existence does not authorize package export, registry participation,
network acquisition, provider preference, automatic dispatch, persistence, or
runtime activation.

The first-wave dossier rows already contain their separately sealed `observed`
compatibility values. No further first-wave dossier mutation is required or
authorized by this decision.

## Planned-route exclusion

Observed route-event history and planned route topology remain distinct target
families.

This decision does not reopen the Shippo, ShipStation, EasyPost, or MyDHL
shipping-route projection worksheets. Their planned-route results remain
`unknown / None` while mandatory `ShippingRouteType` semantics remain
unresolved.

Observed events must not be used to infer planned route topology.

## TracX candidate identity

The next research subject is fixed to:

`candidate:shipping-aggregator:tracx-smartship`

The inspected registered evidence includes the official TracX TxAPI developer
guide and official SmartShip delivery-status material.

This identity must not be aliased to a destination carrier, marketplace,
fulfillment provider, ShipStation, MyDHL, Korea Post, or another aggregator.

## TracX directly observed evidence

The registered TracX evidence establishes that the polling Tracking response
contains a `tracking_history` collection with source fields covering portions
of:

- status and status code;
- a history date;
- location;
- details;
- reason;
- tracking-specific codes;
- proof-of-delivery references;
- shipment-correlation references including `shipping_no`, `ref_no`, and
  `qs_no`.

This is sufficient to authorize a candidate-specific compatibility worksheet.

It is not sufficient to declare canonical compatibility, create a projector, or
mutate the dossier.

## Polling and webhook separation

TracX polling and Delivery WebHook are separate observation surfaces.

The next worksheet is limited to the polling
`SmartShipService.Tracking` response and its `tracking_history` collection.

The worksheet must not attribute webhook-only values to polling events,
including:

- `DeliveryCompanyCode`;
- `DeliveryCompanyName`;
- webhook retry or delivery semantics;
- webhook event actor identity;
- webhook timing or ordering guarantees.

`MultiTracking` collection assembly is also outside the first worksheet unless
a later boundary decision explicitly admits it.

## Unresolved TracX semantics

The next worksheet must preserve the following as unresolved unless the direct
registered polling schema establishes them:

- stable event identity;
- stable event sequence;
- chronological ordering;
- occurrence time versus provider-recorded time;
- timezone or UTC offset;
- history completeness;
- pagination or history-window semantics;
- duplicate handling;
- correction and revision handling;
- event-level carrier or actor identity;
- retention and update latency;
- freshness;
- proof-of-delivery identity semantics.

A source `date` value must not automatically become canonical `occurred_at`.

Example ordering must not become a chronological guarantee.

## TracX worksheet authority

The next gate may create exactly one research artifact:

`docs/research/cross_border/tracx_smartship_observed_route_event_history_projection_compatibility_worksheet.md`

That worksheet may:

- inspect the registered TracX polling source;
- preserve exact source identity;
- inventory directly documented polling fields;
- compare those fields with the existing canonical contract;
- propose a bounded compatibility value;
- enumerate unresolved constraints;
- identify prohibited inference;
- recommend a later compatibility-decision gate.

The worksheet itself may not mutate the dossier or authorize implementation.

## Korea Post EMS deferral

Korea Post EMS remains an admitted research candidate.

The inspected official evidence establishes:

- contract-customer Open API availability;
- EMS internet tracking;
- a 13-character postal-item query reference;
- separate application, service-region, rate, and tracking surfaces.

It does not establish a directly inspectable reusable event-history response
schema sufficient for a compatibility worksheet equivalent to the TracX
polling worksheet.

Therefore:

- Korea Post EMS compatibility worksheet: `DEFERRED`;
- Korea Post EMS projector review: `NOT AUTHORIZED`;
- the 13-character item number remains provider-local correlation evidence only;
- event identity, actor, ordering, completeness, and cross-postal provenance
  must not be inferred.

A future Korea Post gate requires direct registered event-level response-schema
evidence or an explicit inaccessible-evidence decision.

## Candidate-selection meaning

Selecting TracX for the next research worksheet is not:

- provider ranking;
- production preference;
- recommendation;
- fallback ordering;
- runtime selection;
- provider verification;
- rejection of Korea Post EMS;
- evidence that TracX is commercially superior.

The selection applies `MINIMUM AUTHORIZED SEMANTIC BRANCHING`: TracX has a
directly registered polling event collection, while Korea Post currently lacks
equivalent event-level schema evidence.

## Explicit non-authorizations

This decision does not authorize:

- new source admission;
- adjacent-source attribution;
- live API calls or credentials;
- network acquisition;
- raw payload collection or retention;
- webhook ingestion;
- `MultiTracking` assembly;
- canonical model mutation;
- new canonical fields or enums;
- dossier mutation;
- package export;
- ingress or projection registry mutation;
- projector implementation;
- persistence, API, UI, database, deployment, or runtime activation;
- provider verification, ranking, selection, or recommendation;
- planned-route-topology inference;
- commit, tag, or push by this decision itself.

## Decision result

- first-wave projector completion: `PASS`;
- first-wave dossier state: `ALREADY SEALED`;
- planned-route family consequence: `NONE`;
- TracX source identity: `PASS`;
- TracX polling event-collection evidence: `SUFFICIENT FOR WORKSHEET`;
- TracX compatibility conclusion: `NOT YET DECIDED`;
- TracX dossier value: `unknown / None — UNCHANGED`;
- TracX projector implementation: `NOT AUTHORIZED`;
- Korea Post EMS candidate status: `PRESERVED`;
- Korea Post EMS worksheet: `DEFERRED`;
- Korea Post EMS dossier value: `unknown / None — UNCHANGED`;
- production and runtime mutation: `NONE`.

## Required next gate

The next gate is
`CB-EA5E-2_TRACX_SMARTSHIP_OBSERVED_ROUTE_EVENT_HISTORY_PROJECTION_COMPATIBILITY_WORKSHEET`.

It may create only the authorized TracX polling compatibility worksheet. A
separate read-only validation and compatibility decision must follow before any
dossier-mutation or projector-authorization request is considered.
