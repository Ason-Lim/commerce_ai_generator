# Shippo API Shipping-Route Projection Compatibility Worksheet

## Worksheet identity

- Step: `CB-EA4E-2`
- Protocol: `CB-EA4A-2`
- Evaluation subject: `candidate:shipping:shippo-api`
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

It does not compare Shippo API with another evaluation subject.

It does not authorize network acquisition, credentials, raw payload storage,
an adapter, a projector, canonical evidence construction, provider
registration, scoring, ranking, recommendation, selection, runtime use,
shipment booking, label purchase, or transaction execution.

Tracking-event history is outside this worksheet. The inspected canonical
target concerns prospective shipping-route evidence, not post-purchase
package-tracking evidence.

## Registered inspected sources

| source_id | source relationship | source type | source reference |
|---|---|---|---|
| `shippo-api-overview` | `subject_supplied` | `official_documentation` | https://docs.goshippo.com/api-reference/overview |
| `shippo-shipment-api-reference` | `subject_supplied` | `official_documentation` | https://docs.goshippo.com/api-reference/shipments/create-a-new-shipment |
| `shippo-rate-api-reference` | `subject_supplied` | `official_documentation` | https://docs.goshippo.com/api-reference/rates/retrieve-a-rate |

These sources are supplied by the evaluation subject. Their inspection does
not establish verification, correctness, independence, trust, geographic
availability, commercial entitlement, quote accuracy, or authority.

## Documented output locator

The inspected documentation identifies:

- `POST /shipments` for creation of a shipment object from sender,
  recipient, parcel, and optional carrier-account inputs;
- `GET /rates/{RateId}` for retrieval of an existing rate object;
- shipment address fields including `address_from.country` and
  `address_to.country`;
- rate fields including `provider`, `servicelevel`, `amount`, `currency`,
  `estimated_days`, `duration_terms`, `messages`, `carrier_account`,
  `shipment`, and `test`.

The rate documentation describes `estimated_days` as an estimated average
provided for the applicable service level rather than a guaranteed transit
time.

The documentation does not identify a field whose semantics correspond to
the Commerce AI `ShippingRouteType` values `direct_international`,
`forwarder`, or `multi_leg`.

## Layer A — documented subject output shape

| Documented field | Documented meaning | Canonical relevance | Observation |
|---|---|---|---|
| `address_from.country` | Sender-address country | `origin_country` input | Documented |
| `address_to.country` | Recipient-address country | `destination_country` input | Documented |
| `provider` | Carrier offering the rate | `carrier_reference` input | Documented |
| `servicelevel` | Service-level details for the rate | Route constraint or reference input | Documented |
| `amount` | Rate amount | `estimated_route_cost` input | Documented |
| `currency` | Currency associated with the rate amount | `route_cost_currency` input | Documented |
| `estimated_days` | Estimated average transit duration | `estimated_transit_days` input | Optional and non-guaranteed |
| `duration_terms` | Clarification of transit-time terms | Route-constraint input | Optional |
| `messages` | Carrier or rate-result messages | Route-constraint or unresolved-result input | Conditional |
| `carrier_account` | Carrier account used to retrieve the rate | Additional provenance input | Documented |
| `shipment` | Shipment object associated with the rate | Correlation and provenance input | Documented |
| `test` | Test-mode indicator | Provenance-context input | Documented |
| No documented equivalent | Canonical route classification | `route_type` | Blocking gap |

A returned rate is bounded to the shipment, carrier account, service level,
and request context represented by the documented objects. It must not be
generalized into universal route availability.

## Layer B — Commerce AI internal envelope authority

The subject does not supply Commerce AI canonical objects.

Commerce AI retains exclusive authority for:

- assigning `ShippingRouteType`;
- assigning `ShippingAvailabilityState`;
- normalizing origin and destination countries;
- constructing `EvidenceProvenance`;
- evaluating `EvidenceFreshness`;
- constructing `ShippingRouteEvidence`;
- interpreting provider messages and route constraints;
- deciding whether any future adapter is authorized.

A documented rate result must not be copied directly into canonical route
type or availability state without a bounded and separately authorized
interpretation.

## Field-by-field canonical mapping

| Canonical requirement | Documented or internal source | Required bounded treatment | Gap status |
|---|---|---|---|
| Route type | No registered documented Shippo equivalent | A future mapping must distinguish `direct_international`, `forwarder`, and `multi_leg` without inference | Blocking |
| Origin country | `address_from.country` | Normalize through Commerce AI country normalization | No blocking shape gap |
| Destination country | `address_to.country` | Normalize through Commerce AI country normalization | No blocking shape gap |
| Availability state | Presence or absence of a rate within an exact request context | Requires an explicit Commerce AI state-interpretation rule; absence of a rate must not automatically mean `unavailable` | Unresolved but potentially bounded |
| Carrier reference | `provider`, with optional `carrier_account` correlation | Preserve subject identity as a reference only | No blocking shape gap |
| Forwarder reference | No universal documented equivalent | Leave absent unless a separately inspected output explicitly identifies one | Non-blocking when route type does not require it |
| Estimated transit days | Optional `estimated_days` | Accept only a documented non-negative integer and preserve its non-guaranteed estimate status | Optional |
| Estimated route cost | `amount` | Parse through Commerce AI finite non-negative decimal normalization | No blocking shape gap for documented rate results |
| Route-cost currency | `currency` | Normalize consistently and require it whenever cost is present | No blocking shape gap for documented rate results |
| Route constraints | `servicelevel`, `duration_terms`, and applicable `messages` | Preserve only documented constraints; do not infer missing carrier conditions | Conditional |
| Provenance | Registered sources plus shipment, rate, carrier-account, and test references when present | Construct only under separate authorization | No blocking shape gap for prospective construction |
| Freshness | Rate `object_created` or other documented temporal input when applicable | Requires separate temporal-policy inspection; must not be manufactured | Optional and unresolved |

## Required transformations

A future separately authorized subject-specific adapter would require these
bounded transformations:

1. correlate the documented rate with its shipment object;
2. obtain origin and destination countries from the documented shipment
   addresses;
3. normalize country values through the Commerce AI contract;
4. preserve `provider` as a carrier reference without creating a canonical
   provider identity;
5. parse `amount` as a finite non-negative decimal;
6. normalize `currency` and require cost and currency to occur together;
7. preserve `estimated_days` only when documented and non-negative;
8. preserve the documented estimate and non-guarantee semantics;
9. preserve applicable service-level terms and messages as bounded route
   constraints;
10. construct provenance and freshness only from separately authorized
    inputs;
11. apply no `ShippingRouteType` until an explicit documented basis and
    bounded mapping are separately established.

These transformations are described only. They are not implemented or
executed by this worksheet.

## State and value semantic alignment

A successfully returned rate may document that one rate was produced for one
shipment, carrier account, and service level in one request context.

That fact does not establish:

- universal availability for the origin and destination pair;
- availability for another account, carrier, parcel, service, or time;
- guaranteed transit duration;
- guaranteed final charge;
- `UNAVAILABLE` when no rate is returned;
- a canonical route type.

`ShippingAvailabilityState.UNKNOWN` must remain distinct from both
`AVAILABLE` and `UNAVAILABLE`.

Carrier messages, request failures, absent rates, and unsupported service
conditions require separate interpretation. They must not be collapsed into
canonical unavailability without an authorized rule.

## Unresolved gaps and limitations

- The registered documentation does not identify a field corresponding to
  the mandatory canonical `route_type`.
- Carrier and service-level identity does not by itself prove whether the
  physical route is direct, forwarder-based, or multi-leg.
- A returned rate is request-specific and does not establish universal route
  availability.
- Absence of a rate does not independently establish canonical
  `unavailable`.
- `estimated_days` is optional and explicitly non-guaranteed.
- Exact temporal inputs sufficient for canonical freshness evaluation remain
  unresolved.
- Carrier-specific constraints, geographic coverage, account entitlement,
  commercial terms, and rate availability remain conditional.
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

The registered Shippo documentation identifies shipment countries and
rate-level carrier, service, cost, currency, and optional transit inputs, but
does not provide a documented output field or bounded semantic basis for the
mandatory Commerce AI `ShippingRouteType`. Assigning
`direct_international`, `forwarder`, or `multi_leg` from carrier or service
identity would manufacture canonical route-type evidence.

## Meaning of the proposed conclusion

The proposed `unknown` state records a blocking documentation-shape gap for
this subject-target observation unit.

It is not:

- evidence that Shippo lacks shipping capabilities;
- evidence that a Shippo rate is incorrect;
- a compatibility score or grade;
- a provider comparison;
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

The Shippo API `canonical_projection_compatibility` record must remain
`unknown` with literal `None` until this worksheet is separately reviewed,
committed, and sealed.

Because this worksheet proposes the same state and value as the existing
dossier record, no later dossier mutation is implied by its creation.
