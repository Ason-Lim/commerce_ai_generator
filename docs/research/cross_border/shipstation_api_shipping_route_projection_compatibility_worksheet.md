# ShipStation API v2 Shipping-Route Projection Compatibility Worksheet

## Worksheet identity

- Step: `CB-EA4F-2`
- Protocol: `CB-EA4A-2`
- Evaluation subject: `candidate:shipping:shipstation-api`
- Subject surface: ShipStation platform API v2
- Subject base URL: `https://api.shipstation.com/v2`
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

It does not compare ShipStation API v2 with another evaluation subject.

The evaluation subject is limited to the ShipStation platform API v2 surface.
The standalone ShipStation API, formerly ShipEngine, and the
legacy ShipStation API V1 surface at `https://ssapi.shipstation.com/` are
outside this worksheet.

It does not authorize network acquisition, credentials, raw payload storage,
an adapter, a projector, canonical evidence construction, provider
registration, scoring, ranking, recommendation, selection, runtime use,
shipment booking, label purchase, or transaction execution.

Tracking endpoints, tracking numbers, delivery events, and post-purchase
tracking-event history are outside this worksheet. The inspected canonical
target concerns prospective shipping-route evidence.

## Registered inspected sources

| source_id | source relationship | source type | source reference |
|---|---|---|---|
| `shipstation-v2-api-overview` | `subject_supplied` | `official_documentation` | https://docs.shipstation.com/api-overview |
| `shipstation-v2-getting-started` | `subject_supplied` | `official_documentation` | https://docs.shipstation.com/getting-started |
| `shipstation-v2-authentication` | `subject_supplied` | `official_documentation` | https://docs.shipstation.com/authentication |
| `shipstation-v2-rate-shopping` | `subject_supplied` | `official_documentation` | https://docs.shipstation.com/rate-shopping |
| `shipstation-v2-rate-api-reference` | `subject_supplied` | `official_documentation` | https://docs.shipstation.com/apis/openapi/rates/calculate_rates |
| `shipstation-v2-shipment-rate-api-reference` | `subject_supplied` | `official_documentation` | https://docs.shipstation.com/apis/openapi/shipments/list_shipment_rates |

These sources are supplied by the evaluation subject. Their inspection does
not establish verification, correctness, independence, trust, geographic
availability, commercial entitlement, quote accuracy, or authority.

## Documented output locator

The inspected documentation identifies:

- `POST /v2/rates` for retrieval of rate quotes using shipment details or a
  previously created `shipment_id`;
- `POST /v2/rates/estimate` for a non-exact estimate using a reduced input
  set;
- shipment address fields including `ship_from.country_code` and
  `ship_to.country_code`;
- request references including `carrier_ids`, `service_codes`,
  `package_types`, and `shipment_id`;
- rate response fields including `rate_id`, `carrier_id`, `carrier_code`,
  `service_code`, `service_type`, `shipping_amount`, `insurance_amount`,
  `confirmation_amount`, `other_amount`, `delivery_days`,
  `estimated_delivery_date`, `carrier_delivery_days`, `ship_date`,
  `guaranteed_service`, `warning_messages`, and `error_messages`;
- response correlation fields including `rate_request_id`, `shipment_id`,
  `created_at`, and `status`.

The documentation states that rate estimates are not exact quotes and may
omit insurance, fuel surcharges, customs charges, and other carrier fees.

The registered documentation does not identify a field whose documented
semantics correspond to the Commerce AI `ShippingRouteType` values
`direct_international`, `forwarder`, or `multi_leg`.

## Layer A — documented subject output shape

| Documented field | Documented meaning | Canonical relevance | Observation |
|---|---|---|---|
| `ship_from.country_code` | Shipment-origin country | `origin_country` input | Documented |
| `ship_to.country_code` | Shipment-destination country | `destination_country` input | Documented |
| `carrier_id`, `carrier_code` | Carrier references for the returned rate | `carrier_reference` input | Documented |
| `service_code`, `service_type` | Carrier service associated with the rate | Route reference or constraint input | Documented |
| `shipping_amount` | Shipment-only monetary amount | `estimated_route_cost` input | Documented |
| Monetary `currency` | Currency associated with each documented amount | `route_cost_currency` input | Documented |
| `insurance_amount` | Insurance component of the rate | Cost-detail input | Documented |
| `confirmation_amount` | Delivery-confirmation cost component | Cost-detail input | Documented |
| `other_amount`, `rate_details` | Carrier fees, surcharges, taxes, duties, brokerage, and other categorized details when present | Cost-detail or constraint input | Conditional |
| `delivery_days` | Estimated number of delivery days | `estimated_transit_days` input | Conditional estimate |
| `estimated_delivery_date` | Estimated delivery timestamp | Temporal or constraint input | Conditional estimate |
| `guaranteed_service` | Whether the service is documented as guaranteed | Estimate-semantics input | Documented field |
| `warning_messages`, `error_messages` | Rate-result warnings and errors | Constraint or unresolved-result input | Conditional |
| `rate_id`, `rate_request_id`, `shipment_id` | Rate and shipment correlation identifiers | Provenance input | Documented |
| `created_at`, `ship_date` | Documented response and shipment timestamps | Freshness candidate input | Requires temporal policy |
| No documented equivalent | Canonical route classification | `route_type` | Blocking gap |

A returned rate is bounded to the supplied shipment, carrier configuration,
service, package, account, and request context. It must not be generalized
into universal route availability.

## Layer B — Commerce AI internal envelope authority

The subject does not supply Commerce AI canonical objects.

Commerce AI retains exclusive authority for:

- assigning `ShippingRouteType`;
- assigning `ShippingAvailabilityState`;
- normalizing origin and destination countries;
- constructing `EvidenceProvenance`;
- evaluating `EvidenceFreshness`;
- constructing `ShippingRouteEvidence`;
- interpreting rate warnings, errors, estimates, and constraints;
- deciding whether any future adapter is authorized.

A documented rate result must not be copied directly into canonical route
type or availability state without a bounded and separately authorized
interpretation.

## Field-by-field canonical mapping

| Canonical requirement | Documented or internal source | Required bounded treatment | Gap status |
|---|---|---|---|
| Route type | No registered documented ShipStation v2 equivalent | A future mapping must distinguish `direct_international`, `forwarder`, and `multi_leg` without inference | Blocking |
| Origin country | `ship_from.country_code` | Normalize through Commerce AI country normalization | No blocking shape gap |
| Destination country | `ship_to.country_code` | Normalize through Commerce AI country normalization | No blocking shape gap |
| Availability state | Presence or absence of a rate within an exact request context | Requires an explicit Commerce AI state-interpretation rule; absence of a rate must not automatically mean `unavailable` | Unresolved but potentially bounded |
| Carrier reference | `carrier_id`, `carrier_code`, or documented carrier name | Preserve subject identity as a reference only | No blocking shape gap |
| Forwarder reference | No universal documented equivalent | Leave absent unless a separately inspected output explicitly identifies one | Non-blocking when route type does not require it |
| Estimated transit days | Conditional `delivery_days` | Accept only a documented non-negative integer and preserve estimate semantics | Optional |
| Estimated route cost | `shipping_amount`, with separately preserved documented components | Parse through finite non-negative decimal normalization; do not silently collapse omitted estimate charges | No blocking shape gap for documented rate results |
| Route-cost currency | Currency within documented monetary objects | Normalize consistently and require cost and currency together | No blocking shape gap |
| Route constraints | Service fields, guarantee flag, rate details, warnings, and errors | Preserve only documented constraints and estimate limitations | Conditional |
| Provenance | Registered sources plus rate, request, shipment, carrier, and service references | Construct only under separate authorization | No blocking shape gap for prospective construction |
| Freshness | `created_at`, `ship_date`, or another separately sufficient documented timestamp | Requires separate temporal-policy inspection | Optional and unresolved |

## Required transformations

A future separately authorized subject-specific adapter would require these
bounded transformations:

1. correlate the rate with its rate request and shipment;
2. obtain origin and destination countries from the documented shipment;
3. normalize country values through the Commerce AI contract;
4. preserve carrier and service identifiers as references without creating a
   canonical provider identity;
5. parse documented monetary amounts as finite non-negative decimals;
6. normalize currency and require each preserved amount and currency to occur
   together;
7. distinguish full rate quotes from reduced-input rate estimates;
8. preserve estimate omissions, warnings, errors, and guarantee semantics;
9. preserve `delivery_days` only when documented and non-negative;
10. preserve applicable service and charge details as bounded constraints;
11. construct provenance and freshness only from separately authorized inputs;
12. apply no `ShippingRouteType` until an explicit documented basis and
    bounded mapping are separately established.

These transformations are described only. They are not implemented or
executed by this worksheet.

## State and value semantic alignment

A successfully returned rate may document that one quote was produced for one
shipment, carrier configuration, service, package, account, and request
context.

That fact does not establish:

- universal availability for the origin and destination pair;
- availability for another account, carrier, parcel, service, or time;
- guaranteed transit duration;
- guaranteed final charge;
- inclusion of every surcharge, customs charge, tax, duty, or fee;
- `UNAVAILABLE` when no rate is returned;
- a canonical route type.

`ShippingAvailabilityState.UNKNOWN` must remain distinct from both
`AVAILABLE` and `UNAVAILABLE`.

Warnings, errors, unsupported destinations, absent rates, missing carrier
connections, and invalid shipment parameters require separate interpretation.
They must not be collapsed into canonical unavailability without an
authorized rule.

## Unresolved gaps and limitations

- The registered documentation does not identify a field corresponding to the
  mandatory canonical `route_type`.
- Carrier and service identity does not by itself prove whether the physical
  route is direct, forwarder-based, or multi-leg.
- A returned rate is request-specific and does not establish universal route
  availability.
- Absence of a rate does not independently establish canonical
  `unavailable`.
- Rate estimates are explicitly non-exact and may omit documented charge
  categories.
- Transit and delivery fields are conditional and do not establish a
  guaranteed duration unless the documented guarantee field says so.
- Exact temporal inputs sufficient for canonical freshness evaluation remain
  unresolved.
- Carrier connections, geographic coverage, account entitlement, plan
  entitlement, commercial terms, and rate availability remain conditional.
- No live response has been acquired or inspected under this protocol.
- No adapter behavior, normalization behavior, or error handling has been
  implemented or validated.

The missing route-type semantics prevent prospective construction of every
mandatory `ShippingRouteEvidence` invariant. This is a blocking documentation
gap under the sealed protocol.

## Protocol conclusion

### Proposed dossier state

`unknown`

### Proposed dossier observation value

`None`

### Reason outside the observation value

The registered ShipStation platform API v2 documentation identifies shipment
countries and rate-level carrier, service, cost, currency, transit estimate,
warning, error, and correlation inputs, but does not provide a documented
output field or bounded semantic basis for the mandatory Commerce AI
`ShippingRouteType`. Assigning `direct_international`, `forwarder`, or
`multi_leg` from carrier or service identity would manufacture canonical
route-type evidence.

## Meaning of the proposed conclusion

The proposed `unknown` state records a blocking documentation-shape gap for
this subject-target observation unit.

It is not:

- evidence that ShipStation lacks shipping capabilities;
- evidence that a ShipStation rate is incorrect;
- a compatibility score or grade;
- a comparison with Shippo or any other subject;
- a rejection or adoption decision;
- provider selection;
- adapter authorization;
- projector authorization;
- acquisition authority;
- runtime authority;
- verification;
- a commercial or operational assessment.

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
- shipment booking, label purchase, or transaction execution.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The ShipStation API v2 `canonical_projection_compatibility` record must remain
`unknown` with literal `None` until this worksheet is separately reviewed,
committed, and sealed.

Because this worksheet proposes the same state and value as the existing
dossier record, no later dossier mutation is implied by its creation.
