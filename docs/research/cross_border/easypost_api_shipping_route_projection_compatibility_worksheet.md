# EasyPost API Shipping-Route Projection Compatibility Worksheet

## Worksheet identity

- Step: `CB-EA4G-2`
- Protocol: `CB-EA4A-2`
- Evaluation subject: `candidate:shipping:easypost-api`
- Subject surface: EasyPost API documentation
- Subject base URL: `https://api.easypost.com/v2`
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

It does not compare EasyPost API with another evaluation subject.

It does not authorize network acquisition, credentials, raw payload storage,
an adapter, a projector, canonical evidence construction, provider
registration, scoring, ranking, recommendation, selection, runtime use,
shipment booking, label purchase, or transaction execution.

Tracking endpoints, tracker objects, tracking codes, delivery events, and
post-purchase tracking-event history are outside this worksheet. The inspected
canonical target concerns prospective shipping-route evidence.

## Registered inspected sources

| source_id | source relationship | source type | source reference |
|---|---|---|---|
| `easypost-rate-docs` | `subject_supplied` | `official_documentation` | https://docs.easypost.com/docs/shipments/rates |
| `easypost-parcel-and-message-docs` | `subject_supplied` | `official_documentation` | https://docs.easypost.com/docs/parcels; https://docs.easypost.com/docs/shipments/messages |
| `easypost-carrier-docs` | `subject_supplied` | `official_documentation` | https://www.easypost.com/carriers/usps-guide; https://docs.easypost.com/docs/carrier-accounts |

These sources are supplied by the evaluation subject. Their inspection does
not establish verification, correctness, independence, trust, geographic
availability, commercial entitlement, quote accuracy, or authority.

No additional source is registered or relied upon by this worksheet.

## Documented output locator

The inspected documentation identifies:

- shipment rating using a shipment containing `to_address`, `from_address`,
  parcel, and optional carrier-account inputs;
- address fields including `from_address.country` and `to_address.country`;
- rate fields including `id`, `mode`, `service`, `carrier`,
  `carrier_account_id`, `shipment_id`, `rate`, `currency`, `retail_rate`,
  `retail_currency`, `list_rate`, `list_currency`, `delivery_days`,
  `delivery_date`, `delivery_date_guaranteed`, `billing_type`, `created_at`,
  and `updated_at`;
- `POST /shipments/:id/rerate` for regeneration of shipment rates;
- message fields including `carrier`, `type`, `message`, and
  `carrier_account_id`;
- carrier-account fields that identify the carrier credentials and account
  used for rating.

The documentation distinguishes the actual quoted rate from retail and list
rates and identifies the currency associated with each documented amount.

The registered documentation does not identify a field whose documented
semantics correspond to the Commerce AI `ShippingRouteType` values
`direct_international`, `forwarder`, or `multi_leg`.

## Layer A — documented subject output shape

| Documented field | Documented meaning | Canonical relevance | Observation |
|---|---|---|---|
| `from_address.country` | Shipment-origin address country | `origin_country` input | Documented |
| `to_address.country` | Shipment-destination address country | `destination_country` input | Documented |
| `carrier` | Carrier associated with the rate | `carrier_reference` input | Documented |
| `carrier_account_id` | Carrier account used to generate the rate | Carrier correlation and provenance input | Documented |
| `service` | Carrier service level associated with the rate | Route reference or constraint input | Documented |
| `shipment_id` | Shipment associated with the rate | Correlation and provenance input | Documented |
| `rate` | Actual quoted rate for the service | `estimated_route_cost` input | Documented |
| `currency` | Currency associated with `rate` | `route_cost_currency` input | Documented |
| `retail_rate`, `retail_currency` | Retail rate and its currency | Alternative documented price context | Conditional |
| `list_rate`, `list_currency` | List rate and its currency | Alternative documented price context | Conditional |
| `delivery_days` | Delivery days for the service | `estimated_transit_days` input | Conditional |
| `delivery_date` | Documented delivery date when present | Temporal or constraint input | Conditional |
| `delivery_date_guaranteed` | Whether the delivery window is guaranteed | Estimate-semantics input | Documented field |
| `created_at`, `updated_at` | Rate timestamps | Freshness candidate input | Requires temporal policy |
| `mode` | Test or production mode | Provenance-context input | Documented |
| Message `carrier`, `type`, `message`, `carrier_account_id` | Carrier-supplied rating failure details | Constraint or unresolved-result input | Conditional |
| Parcel weight and dimensions | Shipment rating inputs with carrier-specific requirements | Request-context and constraint input | Conditional |
| No documented equivalent | Canonical route classification | `route_type` | Blocking gap |

A returned rate is bounded to the supplied shipment, addresses, parcel,
carrier account, service, mode, and request context. It must not be generalized
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
- interpreting rate messages, failures, estimates, and constraints;
- deciding whether any future adapter is authorized.

A documented rate result must not be copied directly into canonical route type
or availability state without a bounded and separately authorized
interpretation.

## Field-by-field canonical mapping

| Canonical requirement | Documented or internal source | Required bounded treatment | Gap status |
|---|---|---|---|
| Route type | No registered documented EasyPost equivalent | A future mapping must distinguish `direct_international`, `forwarder`, and `multi_leg` without inference | Blocking |
| Origin country | `from_address.country` | Normalize through Commerce AI country normalization | No blocking shape gap |
| Destination country | `to_address.country` | Normalize through Commerce AI country normalization | No blocking shape gap |
| Availability state | Presence or absence of a rate within an exact request context | Requires an explicit Commerce AI state-interpretation rule; absence of a rate must not automatically mean `unavailable` | Unresolved but potentially bounded |
| Carrier reference | `carrier`, with `carrier_account_id` correlation | Preserve subject identity as a reference only | No blocking shape gap |
| Forwarder reference | No universal documented equivalent | Leave absent unless a separately inspected output explicitly identifies one | Non-blocking when route type does not require it |
| Estimated transit days | Conditional `delivery_days` | Accept only a documented non-negative integer and preserve guarantee semantics separately | Optional |
| Estimated route cost | `rate` | Parse through Commerce AI finite non-negative decimal normalization | No blocking shape gap for documented rate results |
| Route-cost currency | `currency` | Normalize consistently and require it whenever `rate` is preserved | No blocking shape gap for documented rate results |
| Route constraints | `service`, delivery fields, mode, parcel requirements, and applicable messages | Preserve only documented constraints and do not infer missing carrier conditions | Conditional |
| Provenance | Registered sources plus rate, shipment, carrier-account, service, and mode references | Construct only under separate authorization | No blocking shape gap for prospective construction |
| Freshness | `created_at`, `updated_at`, or another separately sufficient documented timestamp | Requires separate temporal-policy inspection | Optional and unresolved |

## Required transformations

A future separately authorized subject-specific adapter would require these
bounded transformations:

1. correlate each documented rate with its shipment and carrier account;
2. obtain origin and destination countries from the documented shipment
   addresses;
3. normalize country values through the Commerce AI contract;
4. preserve carrier, carrier-account, and service identifiers as references
   without creating a canonical provider identity;
5. distinguish `rate` from `retail_rate` and `list_rate`;
6. parse a preserved monetary amount as a finite non-negative decimal;
7. normalize its corresponding currency and require amount and currency to
   occur together;
8. preserve `delivery_days` only when documented and non-negative;
9. preserve `delivery_date_guaranteed` without manufacturing a guarantee;
10. preserve applicable service, parcel, mode, and carrier-message details as
    bounded constraints;
11. construct provenance and freshness only from separately authorized inputs;
12. apply no `ShippingRouteType` until an explicit documented basis and bounded
    mapping are separately established.

These transformations are described only. They are not implemented or
executed by this worksheet.

## State and value semantic alignment

A successfully returned rate may document that one rate was produced for one
shipment, carrier account, carrier, service, parcel, mode, and request context.

That fact does not establish:

- universal availability for the origin and destination pair;
- availability for another account, carrier, parcel, service, mode, or time;
- guaranteed transit duration unless the documented guarantee field says so;
- guaranteed final charge;
- inclusion of customs duties, taxes, insurance, or other amounts not included
  in the documented rate;
- `UNAVAILABLE` when no rate is returned;
- a canonical route type.

`ShippingAvailabilityState.UNKNOWN` must remain distinct from both `AVAILABLE`
and `UNAVAILABLE`.

Carrier messages, authentication failures, request failures, absent rates,
unsupported services, and invalid shipment or parcel inputs require separate
interpretation. They must not be collapsed into canonical unavailability
without an authorized rule.

## Unresolved gaps and limitations

- The registered documentation does not identify a field corresponding to the
  mandatory canonical `route_type`.
- Origin and destination countries do not by themselves prove whether the
  physical route is direct, forwarder-based, or multi-leg.
- Carrier, carrier-account, and service identity do not independently establish
  route topology.
- A returned rate is request-specific and does not establish universal route
  availability.
- Absence of a rate does not independently establish canonical `unavailable`.
- Delivery fields may be absent, and guarantee semantics must be preserved.
- Exact temporal inputs sufficient for canonical freshness evaluation remain
  unresolved.
- Parcel requirements, carrier integrations, geographic coverage, credentials,
  account entitlement, production mode, commercial terms, and rate
  availability remain conditional.
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

The registered EasyPost documentation identifies shipment countries and
rate-level carrier, carrier-account, service, cost, currency, delivery,
message, mode, and correlation inputs, but does not provide a documented
output field or bounded semantic basis for the mandatory Commerce AI
`ShippingRouteType`. Assigning `direct_international`, `forwarder`, or
`multi_leg` from address countries, carrier, carrier-account, or service
identity would manufacture canonical route-type evidence.

## Meaning of the proposed conclusion

The proposed `unknown` state records a blocking documentation-shape gap for
this subject-target observation unit.

It is not:

- evidence that EasyPost lacks shipping capabilities;
- evidence that an EasyPost rate is incorrect;
- a compatibility score or grade;
- a comparison with Shippo, ShipStation, or any other subject;
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

The EasyPost API `canonical_projection_compatibility` record must remain
`unknown` with literal `None` until this worksheet is separately reviewed,
committed, and sealed.

Because this worksheet proposes the same state and value as the existing
dossier record, no later dossier mutation is implied by its creation.
