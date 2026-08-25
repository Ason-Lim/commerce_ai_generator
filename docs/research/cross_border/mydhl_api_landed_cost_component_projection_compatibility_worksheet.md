# MyDHL API Landed-Cost-Component Projection Compatibility Worksheet

## Worksheet identity

- Step: `CB-EA4I-2`
- Protocol: `CB-EA4A-2`
- Evaluation subject: `candidate:shipping-landed-cost:mydhl-api`
- Subject surface: DHL Express MyDHL API
- Subject base URL: `https://express.api.dhl.com/mydhlapi`
- Canonical target family: `landed_cost_component_evidence`
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

It inspects only the prospective landed-cost-component evidence surface of the
MyDHL API.

The MyDHL `shipping_route_evidence` observation is recorded separately in the
sealed MyDHL shipping-route worksheet and is not generalized into this target.

It does not compare MyDHL API with another evaluation subject.

It does not authorize network acquisition, credentials, raw payload storage,
an adapter, a projector, canonical evidence construction, provider
registration, scoring, ranking, recommendation, selection, runtime use,
customs classification, shipment creation, payment, or transaction execution.

## Registered inspected sources

| source_id | source relationship | source type | source reference |
|---|---|---|---|
| `mydhl-api-docs` | `subject_supplied` | `official_documentation` | https://developer.dhl.com/api-reference/dhl-express-mydhl-api |
| `mydhl-api-terms` | `subject_supplied` | `official_documentation` | https://developer.dhl.com/api-reference/dhl-express-mydhl-api |

These source relationships are preserved from the sealed dossier. Inspection
does not establish verification, correctness, independence, quote accuracy,
legal authority, entitlement, storage permission, display permission, or
operational readiness.

No additional source is registered or relied upon by this worksheet.

## Documented output locator

The registered MyDHL documentation identifies:

- a Landed Cost service that returns an estimated landed cost including duties
  and taxes;
- landed cost as total costs associated with shipping a product from one
  location to another;
- estimated transportation charges and customs duties as included concepts;
- freight and insurance as shipment values that the customer may be responsible
  for supplying;
- item and customs inputs, including HS codes, as prerequisites;
- time-sensitive results that may change;
- additional legal restrictions applicable to Landed Cost data.

The registered documentation describes a service-level estimate and included
cost concepts.

It does not expose, within the registered inspected surface, a bounded response
schema that identifies each returned component, its individual amount and
currency, and its component-specific evidence state.

A prose statement that a total includes duties and taxes does not establish
that the response exposes separate `duty` and `tax` component amounts.

## Layer A — documented subject output shape

| Documented subject output or concept | Documented meaning | Canonical relevance | Observation |
|---|---|---|---|
| Estimated landed cost | Estimated total cost associated with the supplied shipment | Aggregate context only | Documented service concept |
| Duties and taxes | Cost categories described as included in the estimate | `duty` and `tax` candidates | No registered component-level output shape |
| Transportation charges | Transportation cost concept included in landed cost | `international_shipping` or `shipping` candidate | No registered component-level output shape |
| Freight supplied by customer | Shipment value used as a calculation input | Shipping-cost input context | Must not be treated as provider output |
| Insurance supplied by customer | Shipment value used as a calculation input | `insurance` input context | Must not be treated as provider output |
| Item catalogue and customs data | Product and HS-code inputs | Evaluation-context and constraint inputs | Documented prerequisites |
| Time-sensitive estimated result | Estimate may change frequently | `ESTIMATED` and estimate-reason candidate | Documented limitation |
| No documented equivalent | Component-specific returned identity | `component` | Blocking gap |
| No documented equivalent | Component-specific returned amount | `amount` | Blocking gap |
| No documented equivalent | Component-specific returned currency | `currency` | Blocking gap |
| No documented equivalent | Component-specific canonical state | `state` | Requires internal interpretation |

The inspected description of included concepts must not be converted into a
component breakdown unless the registered output shape explicitly exposes that
breakdown.

Customer-provided freight or insurance values must not be represented as
provider-observed component amounts.

## Layer B — Commerce AI internal envelope authority

The subject does not supply Commerce AI canonical objects.

Commerce AI retains exclusive authority for:

- assigning canonical landed-cost component identities;
- assigning `LandedCostComponentState`;
- distinguishing provider output from customer-supplied inputs;
- parsing and validating monetary amounts;
- normalizing currency;
- constructing `EvidenceProvenance`;
- attaching `CrossBorderEvaluationContext`;
- recording an estimate reason;
- constructing `LandedCostComponentEvidence`;
- deciding whether any future adapter is authorized.

Commerce AI must not manufacture a component identity, amount, currency, or
state from an aggregate estimate or general service description.

## Field-by-field canonical mapping

| Canonical requirement | Documented or internal source | Required bounded treatment | Gap status |
|---|---|---|---|
| Component identity | Included cost concepts are described, but no registered returned component identifier is exposed | Map only an explicitly returned provider component through a separately justified canonical mapping | Blocking |
| Component state | Service is described as estimated | `ESTIMATED` may be considered only after a specific returned component is identified with amount and currency | Blocked by component shape |
| Amount | Estimated total is described; no registered component-level amount field is exposed | Do not decompose or allocate the total | Blocking |
| Currency | No registered component-level currency association is exposed | Require currency together with each evidence-bearing component amount | Blocking |
| Provenance | Registered MyDHL source and future result identifiers when documented | Construct only under separate authorization | Potentially bounded |
| Evaluation context | Shipment, item, origin, destination, and customs inputs | Attach only from an explicitly correlated request-result context | Potentially bounded |
| Estimate reason | MyDHL states that Landed Cost is estimated, input-dependent, time-sensitive, and subject to change | Preserve only as a bounded reason after a component observation becomes constructible | Potentially bounded |
| Evidence-absent state | No component-level output does not prove `UNAVAILABLE` or `NOT_APPLICABLE` | Preserve uncertainty without zero or synthetic state | Unresolved |

## Canonical component vocabulary review

The current canonical vocabulary includes:

- `item_price`;
- `origin_shipping`;
- `international_shipping`;
- `shipping`;
- `forwarding`;
- `consolidation`;
- `insurance`;
- `duty`;
- `tax`;
- `customs_fee`;
- `payment_fee`;
- `payment_fx_fee`;
- `service_fee`;
- `surcharge`;
- `discount`.

The registered MyDHL description does not justify assigning any of these
canonical identities to an output value without a documented component-level
response field and a separately bounded mapping.

The wording "duties and taxes" must not be silently split into two monetary
components. Transportation charges must not be assigned to `shipping` or
`international_shipping` without documented component semantics.

## Required transformations

A future separately authorized subject-specific adapter would require these
bounded transformations:

1. correlate the landed-cost response with its exact shipment, item, origin,
   destination, and customs-input context;
2. identify each component from an explicitly documented returned field;
3. distinguish customer-provided freight and insurance inputs from MyDHL
   output observations;
4. preserve provider-specific component names before any canonical mapping;
5. justify each provider-to-canonical component mapping separately;
6. parse each component amount as a finite non-negative decimal;
7. normalize its associated currency and require amount and currency together;
8. assign `ESTIMATED` only where component identity, amount, currency, and
   estimate semantics are all supported;
9. preserve time-sensitive and input-dependent estimate limitations in
   `estimate_reason`;
10. construct provenance and context only from separately authorized inputs;
11. never decompose an aggregate total into components without an explicitly
    documented output breakdown;
12. never replace an unsupported component with zero, false, empty text,
    `UNAVAILABLE`, or `NOT_APPLICABLE`.

These transformations are described only. They are not implemented or
executed by this worksheet.

## State and value semantic alignment

Evidence-bearing states are:

- `KNOWN`;
- `ESTIMATED`;
- `DERIVED`.

Each evidence-bearing state requires both amount and currency.

Evidence-absent states are:

- `UNKNOWN`;
- `UNAVAILABLE`;
- `NOT_APPLICABLE`.

Each evidence-absent state requires both amount and currency to be absent.

The service-level statement that MyDHL returns an estimated landed cost does
not by itself support `ESTIMATED` component evidence. A specific component
identity, amount, currency, and request-result association must first be
documented.

Absence of an exposed component must not be interpreted as a zero amount,
`UNAVAILABLE`, or `NOT_APPLICABLE`.

## Unresolved gaps and limitations

- The registered inspected surface does not expose a component-level response
  schema.
- No returned component identifier is established.
- No component-level amount and currency association is established.
- The documentation does not establish whether duties and taxes are returned
  separately, combined, or only represented in a total.
- Transportation, freight, insurance, customs, surcharge, and other cost
  concepts cannot be mapped to canonical components without output-level
  semantics.
- Customer-provided freight and insurance are inputs and must not be
  misrepresented as provider observations.
- A total estimate must not be decomposed or proportionally allocated.
- Exact provenance and freshness inputs remain unresolved.
- HS codes and other customs data are input requirements and do not establish
  correct classification or final customs treatment.
- Estimates are time-sensitive, input-dependent, and not authoritative final
  charges.
- Commercial restrictions may constrain storage, modification, disclosure,
  analysis, reuse, and display.
- No live response has been acquired or inspected under this protocol.
- No adapter behavior, normalization behavior, or error handling has been
  implemented or validated.

The missing component-level identity, amount, and currency semantics prevent
prospective construction of the mandatory `LandedCostComponentEvidence`
invariants. This is a blocking documentation-shape gap under the sealed
protocol.

## Protocol conclusion

### Proposed target-family state

`unknown`

### Proposed target-family observation value

`None`

### Reason outside the observation value

The registered MyDHL documentation describes an estimated landed-cost service
and included cost concepts, but it does not expose within the inspected surface
a bounded component-level response shape containing component identity,
individual amount, associated currency, and component-specific state.

Decomposing a total or interpreting included-concept prose as separate
canonical `duty`, `tax`, `shipping`, `international_shipping`, or `insurance`
evidence would manufacture canonical component evidence.

## Mixed-capability dossier disposition

The MyDHL `shipping_route_evidence` worksheet concluded `unknown` with literal
`None`.

This worksheet also concludes `unknown` with literal `None` for
`landed_cost_component_evidence`.

Because both applicable target-family observations remain unknown, the existing
single MyDHL `canonical_projection_compatibility` dossier record remains
`unknown` with literal `None`.

No dossier mutation is proposed.

## Meaning of the proposed conclusion

The proposed target-family `unknown` state records a blocking
documentation-shape gap for this subject-target observation unit.

It is not:

- evidence that MyDHL lacks a landed-cost service;
- evidence that a MyDHL estimate is incorrect;
- a compatibility score or grade;
- a comparison with another subject;
- a customs classification or legal conclusion;
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
- component allocation or total decomposition;
- implementation change;
- canonical evidence construction;
- customs classification;
- shipment, payment, or transaction execution.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The MyDHL API `canonical_projection_compatibility` record remains `unknown`
with literal `None`.

Because both applicable target-family worksheets propose the same existing
state and value, no later dossier mutation is implied by this worksheet.
