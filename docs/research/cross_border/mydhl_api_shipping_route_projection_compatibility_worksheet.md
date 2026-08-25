# MyDHL API Shipping-Route Projection Compatibility Worksheet

## Worksheet identity

- Step: `CB-EA4H-2`
- Protocol: `CB-EA4A-2`
- Evaluation subject: `candidate:shipping-landed-cost:mydhl-api`
- Subject surface: DHL Express MyDHL API
- Subject base URL: `https://express.api.dhl.com/mydhlapi`
- Canonical target family: `shipping_route_evidence`
- Source relationship: `subject_supplied`
- Status: `subject-local observation worksheet`
- Runtime authority: `None`
- Acquisition authority: `None`
- Adapter authority: `None`
- Projector authority: `None`
- Verification authority: `None`
- Provider-selection authority: `None`

## Scope

This worksheet applies the sealed internal observation protocol to one
evaluation subject and one canonical target family.

It inspects only the prospective shipping-route evidence surface of the MyDHL
API. The separately documented landed-cost capability requires an independent
`landed_cost_component_evidence` worksheet.

It does not compare MyDHL API with another evaluation subject.

It does not authorize network acquisition, credentials, raw payload storage,
an adapter, a projector, canonical evidence construction, provider
registration, scoring, ranking, recommendation, selection, runtime use,
shipment creation, pickup booking, label creation, or transaction execution.

Tracking services, tracking identifiers, delivery events, proof of delivery,
and post-purchase tracking-event history are outside this worksheet.

## Registered inspected sources

| source_id | source relationship | source type | source reference |
|---|---|---|---|
| `mydhl-api-docs` | `subject_supplied` | `official_documentation` | https://developer.dhl.com/api-reference/dhl-express-mydhl-api |
| `mydhl-api-terms` | `subject_supplied` | `official_documentation` | https://developer.dhl.com/api-reference/dhl-express-mydhl-api |

These source relationships are preserved from the sealed dossier. Inspection
does not establish verification, correctness, independence, trust, quote
accuracy, entitlement, legal reusability, or operational authority.

No additional source is registered or relied upon by this worksheet.

## Documented output locator

The registered MyDHL documentation identifies:

- Rating operations that return DHL Express product capabilities, value-added
  services, estimated delivery time, and the requesting customer's DHL Express
  account rates;
- Product operations that retrieve available DHL Express products for a
  one-piece shipment;
- Address operations that validate DHL Express pickup and delivery capabilities
  at an origin and destination;
- Shipment operations that consume a selected DHL Express product and
  value-added services;
- Product and Rating Data including product name, product capability, rates,
  lead times, and estimated delivery dates or times;
- test and production environments using access credentials and Basic
  Authentication.

The registered terms state that rate, transit-time, and delivery-date
information is indicative and not guaranteed. Final values may differ based on
shipment characteristics, requested services, and packages tendered.

The registered documentation does not identify an output field or bounded
semantic rule corresponding to the Commerce AI `ShippingRouteType` values
`direct_international`, `forwarder`, or `multi_leg`.

## Layer A — documented subject output shape

| Documented subject output | Documented meaning | Canonical relevance | Observation |
|---|---|---|---|
| Origin pickup capability | Whether DHL Express has pickup capability at the supplied origin | Origin-context and availability input | Documented capability |
| Destination delivery capability | Whether DHL Express has delivery capability at the supplied destination | Destination-context and availability input | Documented capability |
| DHL Express product | Available product for the supplied shipment context | Carrier or service reference input | Documented |
| Value-added services | Services associated with a returned product | Route-constraint input | Conditional |
| DHL Express account rate | Indicative account rate for the supplied context | `estimated_route_cost` candidate input | Documented at service level |
| Estimated delivery time | Indicative delivery-time information | `estimated_transit_days` or temporal candidate input | Conditional and non-guaranteed |
| Product capability | Capability attached to the returned DHL Express product | Availability or constraint candidate input | Context-bound |
| Result and validation messages | Results of schema and business-rule validation | Constraint or unresolved-result input | Conditional |
| No documented equivalent | Canonical route classification | `route_type` | Blocking gap |

A product, capability, or rate is bounded to the applicable account, shipment,
origin, destination, package, product, service, credential, and request
context. It must not be generalized into universal route availability.

## Layer B — Commerce AI internal envelope authority

The subject does not supply Commerce AI canonical objects.

Commerce AI retains exclusive authority for:

- assigning `ShippingRouteType`;
- assigning `ShippingAvailabilityState`;
- normalizing origin and destination countries;
- interpreting pickup and delivery capability results;
- constructing `EvidenceProvenance`;
- evaluating `EvidenceFreshness`;
- constructing `ShippingRouteEvidence`;
- interpreting validation results and route constraints;
- deciding whether any future adapter is authorized.

A documented international DHL Express product or rate must not be copied
directly into a canonical route type or availability state without a bounded
and separately authorized interpretation.

## Field-by-field canonical mapping

| Canonical requirement | Documented or internal source | Required bounded treatment | Gap status |
|---|---|---|---|
| Route type | No registered documented MyDHL equivalent | A future mapping must distinguish `direct_international`, `forwarder`, and `multi_leg` without inference | Blocking |
| Origin country | Origin supplied to Rating, Product, Address, or Shipment context | Normalize only from an explicitly documented request or result association | Potentially bounded |
| Destination country | Destination supplied to Rating, Product, Address, or Shipment context | Normalize only from an explicitly documented request or result association | Potentially bounded |
| Availability state | Address capability or returned product within an exact context | Requires an explicit state-interpretation rule; failure or absence must not automatically mean `unavailable` | Unresolved but potentially bounded |
| Carrier reference | DHL Express subject and documented product association | Preserve as a subject-local reference without creating a new canonical provider identity | No blocking shape gap |
| Forwarder reference | No registered universal documented equivalent | Leave absent unless a separately inspected output explicitly identifies one | Non-blocking when route type does not require it |
| Estimated transit days | Indicative estimated delivery-time information | Preserve only when its documented form supports a bounded transformation | Optional and unresolved |
| Estimated route cost | DHL Express account rate | Requires an explicitly documented amount and associated currency | Potentially bounded |
| Route-cost currency | Currency associated with the documented account rate | Require amount and currency together | Potentially bounded |
| Route constraints | Product capability, value-added services, validation results, and indicative limitations | Preserve only documented constraints | Conditional |
| Provenance | Registered source plus account, product, shipment, and result references when documented | Construct only under separate authorization | Potentially bounded |
| Freshness | Separately sufficient documented temporal input | Requires separate temporal-policy inspection | Optional and unresolved |

## Required transformations

A future separately authorized subject-specific adapter would require these
bounded transformations:

1. correlate a documented result with its exact account and shipment context;
2. obtain origin and destination countries from the documented request-result
   relationship;
3. normalize country values through the Commerce AI contract;
4. preserve DHL Express product and service identity as references without
   manufacturing a canonical provider identity;
5. interpret pickup and delivery capability only within the exact documented
   request context;
6. parse an account rate only from a documented finite non-negative amount;
7. normalize its currency and require amount and currency together;
8. preserve delivery information as indicative and non-guaranteed;
9. preserve product capability, value-added services, and validation results as
   bounded constraints;
10. construct provenance and freshness only from separately authorized inputs;
11. apply no `ShippingRouteType` until an explicit documented basis and bounded
    mapping are separately established.

These transformations are described only. They are not implemented or
executed by this worksheet.

## State and value semantic alignment

A returned product, capability, or rate may document that DHL Express supplied
one result for one account and one shipment context.

That fact does not establish:

- universal availability for the origin and destination pair;
- availability for another account, shipment, package, product, or time;
- a guaranteed transit time or delivery date;
- a guaranteed final rate;
- inclusion of every duty, tax, customs charge, surcharge, or fee;
- `UNAVAILABLE` when no product or rate is returned;
- a canonical route type.

`ShippingAvailabilityState.UNKNOWN` must remain distinct from both `AVAILABLE`
and `UNAVAILABLE`.

An address-capability result, missing product, validation failure, credential
failure, or absent rate requires separate interpretation and must not be
collapsed into canonical availability or unavailability without an authorized
rule.

## Unresolved gaps and limitations

- The registered documentation does not identify a field corresponding to the
  mandatory canonical `route_type`.
- The description of time-definite international DHL Express shipping does not
  establish physical route topology.
- DHL Express product and service identity do not prove whether a route is
  direct, forwarder-based, or multi-leg.
- Address pickup and delivery capability does not establish route topology.
- A returned product or rate is request-specific and does not establish
  universal route availability.
- Absence of a product or rate does not independently establish canonical
  `unavailable`.
- Rate, transit-time, and delivery-date information is indicative and not
  guaranteed.
- Exact amount, currency, and temporal fields sufficient for prospective
  canonical construction remain dependent on uninspected schema detail.
- Account entitlement, credentials, product capability, geographic service,
  package characteristics, commercial terms, and final availability remain
  conditional.
- Product and Rating Data is subject to documented disclosure, storage,
  modification, and competitive-analysis restrictions.
- No live response has been acquired or inspected under this protocol.
- No adapter behavior, normalization behavior, or error handling has been
  implemented or validated.

The missing route-type semantics prevent prospective construction of every
mandatory `ShippingRouteEvidence` invariant. This is a blocking documentation
gap under the sealed protocol.

## Protocol conclusion

### Proposed target-family state

`unknown`

### Proposed target-family observation value

`None`

### Reason outside the observation value

The registered MyDHL documentation identifies international DHL Express
products, origin and destination capabilities, account rates, value-added
services, and indicative delivery inputs, but does not provide a documented
output field or bounded semantic basis for the mandatory Commerce AI
`ShippingRouteType`. Assigning `direct_international`, `forwarder`, or
`multi_leg` from international-shipping scope, DHL Express identity, product,
service, or address capability would manufacture canonical route-type
evidence.

## Mixed-capability dossier disposition

This worksheet evaluates only `shipping_route_evidence`.

The separate `landed_cost_component_evidence` observation unit remains
uninspected under this worksheet.

Therefore the existing single MyDHL
`canonical_projection_compatibility` dossier record must remain `unknown` with
literal `None`.

No target-family result from this worksheet may be generalized to the
landed-cost-component target.

## Meaning of the proposed conclusion

The proposed target-family `unknown` state records a blocking
documentation-shape gap for this subject-target observation unit.

It is not:

- evidence that MyDHL lacks shipping capabilities;
- evidence that MyDHL product or rate data is incorrect;
- a compatibility score or grade;
- a comparison with another subject;
- a rejection or adoption decision;
- provider selection;
- adapter or projector authorization;
- acquisition or runtime authority;
- verification;
- a commercial, legal, or operational assessment.

## Boundary review

This worksheet contains no:

- provider comparison;
- score, percentage, grade, weight, or rank;
- provider preference;
- recommendation or selection;
- verified state;
- runtime, acquisition, adapter, or projector authorization;
- network client, credential, or live API call;
- raw payload or HTML capture;
- implementation change;
- canonical evidence construction;
- shipment creation, pickup booking, label creation, or transaction execution.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The MyDHL API `canonical_projection_compatibility` record must remain `unknown`
with literal `None` because this shipping-route target remains blocked and the
separate landed-cost-component target remains uninspected.

No later dossier mutation is implied by creation of this worksheet.
