# Zonos API Landed-Cost-Component Projection Compatibility Worksheet

## Document status

- Status: bounded internal observation worksheet
- Subject: `candidate:landed-cost:zonos-api`
- External evidence kind: `landed_cost`
- Canonical target family: `landed_cost_component_evidence`
- Observation stage: documentation-only
- Evidence relationship: `subject_supplied`
- Observation date: `2026-08-26`
- Proposed compatibility state: `observed`
- Proposed compatibility value: subject-specific prospective mapping
- Dossier mutation: proposed only after separate exact-scope authorization

## Purpose

This worksheet applies the internal canonical projection compatibility
observation protocol to the prospective landed-cost-component surface of the
Zonos Landed Cost API.

It asks whether the documented output shape supports a bounded prospective
mapping into `LandedCostComponentEvidence`.

It does not authorize API acquisition, credentials, payload capture,
implementation, provider registration, selection, verification, ranking,
production use, tariff calculation, customs determination, order creation, or
transaction execution.

## Applicable canonical target

The applicable external evidence kind is:

- `ExternalEvidenceKind.LANDED_COST`

The single permitted canonical target is:

- `CanonicalProjectionTarget.LANDED_COST_COMPONENT_EVIDENCE`

The following target families are excluded:

- `currency_rate_evidence`;
- `shipping_route_evidence`;
- `regulatory_evidence`.

## Registered evidence

The dossier records that Zonos:

1. calculates and breaks down duties, taxes, and import-related fees;
2. documents landed-cost calculation coverage for international shipments;
3. preserves item-level duty descriptions and HS-code-source information;
4. distinguishes approximate and conditionally guaranteed calculations;
5. requires parties or locations, item and monetary data, destination
   information, shipping cost, and landed-cost configuration;
6. requires an account, API key, and documented version header for REST use.

The dossier retains temporal and commercial constraints as `unknown / None`.

Those unresolved dimensions do not independently block a documentation-only
output-shape observation, but they continue to block acquisition, entitlement,
production, and verification conclusions.

## Inspected documented output shape

The official Zonos GraphQL landed-cost guide documents a
`landedCostCalculateWorkflow` result containing:

- a result `id`;
- `duties` entries with `amount`, `currency`, and `note`;
- `taxes` entries with `amount`, `currency`, and `note`;
- `fees` entries with `amount`, `currency`, and `note`.

The documented request workflow correlates the result with:

- origin and destination parties or locations;
- item identity and amount;
- item currency;
- quantity;
- country of origin;
- HS-code input or Zonos classification behavior;
- shipping service and amount;
- landed-cost calculation method;
- end-use context;
- tariff-rate preference.

The documentation describes the result as a landed-cost quote or calculation.
A guarantee configuration does not convert the resulting monetary evidence
into a customs determination or universally final charge.

## Canonical target requirements

`LandedCostComponentEvidence` requires:

- non-empty component identity;
- `LandedCostComponentState`;
- non-negative amount and currency for evidence-bearing states;
- no amount or currency for evidence-absent states;
- provenance when claimed;
- evaluation context when claimed;
- estimate reason when applicable.

The canonical component vocabulary is intentionally open. Provider-specific
component names remain permitted, but must not be declared canonical without
a separate justified mapping.

## Field-level mapping

| Zonos field or relationship | Canonical interpretation | Boundary |
|---|---|---|
| `duties[].amount` | `amount` for component `duty` | Parse as a non-negative decimal; do not calculate or infer a missing value. |
| `duties[].currency` | `currency` for component `duty` | Normalize only under Commerce AI currency rules. |
| `duties[].note` | Candidate `estimate_reason` or provenance-adjacent note | Preserve only when semantically applicable; do not turn it into legal status. |
| `taxes[].amount` | `amount` for component `tax` | Parse as a non-negative decimal; do not infer tax applicability beyond the response. |
| `taxes[].currency` | `currency` for component `tax` | Normalize only under Commerce AI currency rules. |
| `taxes[].note` | Candidate `estimate_reason` or provenance-adjacent note | Preserve without legal reinterpretation. |
| `fees[].amount` | `amount` for provider-specific component `fees` | Do not silently map to `customs_fee`, `service_fee`, or another canonical subtype. |
| `fees[].currency` | `currency` for provider-specific component `fees` | Normalize only under Commerce AI currency rules. |
| `fees[].note` | Candidate `estimate_reason` or provider note | Preserve without inventing a fee category. |
| Result `id` and official source identity | Provenance correlation material | Commerce AI owns the canonical provenance envelope. |
| Request parties, items, origin, destination, shipping, and configuration | Evaluation-context correlation material | Commerce AI owns and validates the canonical evaluation-context envelope. |
| Quote or calculation semantics | `LandedCostComponentState.ESTIMATED` | Guaranteed workflow must not be mapped to `KNOWN` solely from marketing or workflow terminology. |

## Component-identity decision

The following mappings are supported prospectively:

- Zonos `duties` → canonical `duty`;
- Zonos `taxes` → canonical `tax`.

The Zonos `fees` collection is preserved prospectively as the provider-specific component identity `fees`.

This worksheet does not establish that every fee entry is:

- `customs_fee`;
- `service_fee`;
- `payment_fee`;
- `surcharge`;
- any other canonical subtype.

A more specific fee mapping requires entry-level documented semantics and a
separate mapping justification.

## State decision

The prospective component state is:

- `LandedCostComponentState.ESTIMATED`

This state reflects the documented quote and calculation semantics.

The following are prohibited:

- mapping a guaranteed workflow directly to `KNOWN`;
- mapping a zero amount to `NOT_APPLICABLE`;
- treating `UNKNOWN` or `UNAVAILABLE` as zero;
- deriving absent duty, tax, or fee amounts;
- converting a Zonos calculation into a customs determination.

A documented numeric zero remains evidence-bearing zero only when it is
actually present in the correlated response.

## Provenance and context envelope

The subject output may support prospective canonical construction only when
Commerce AI separately supplies and validates:

- subject identity;
- official source identity and reference;
- retrieval time;
- response or result correlation identity;
- origin and destination;
- product and item correlation;
- currency;
- applicable shipping and calculation inputs;
- evaluation purpose and context.

The provider output does not own the canonical envelope.

The prospective mapping therefore combines:

1. documented Zonos output fields; and
2. Commerce AI-owned provenance and evaluation-context authority.

## Estimate and guarantee boundary

Zonos distinguishes approximate and conditionally guaranteed calculations.

This worksheet does not infer:

- that every response is guaranteed;
- that a guarantee applies to a prospective Commerce AI request;
- that a guarantee makes an amount legally final;
- that customs will accept the underlying classification;
- that actual charges cannot differ outside applicable guarantee terms;
- that Commerce AI has contractual entitlement to the guarantee.

When a documented response-specific reason is available, it may be preserved
as `estimate_reason`. No generic guarantee assertion is manufactured.

## Operational and commercial boundary

The documentation-only compatibility observation does not establish:

- Commerce AI account eligibility;
- pricing;
- contractual entitlement;
- production quotas or service levels;
- storage, reuse, or display permission;
- permitted comparison or competitive-analysis use;
- guarantee eligibility;
- production availability;
- verified accuracy.

The dossier's commercial-constraint record remains `unknown / None`.

## Minimum projection conditions

A future authorized projector would have to:

1. accept only a correlated Zonos landed-cost result;
2. preserve the exact result and request relationship;
3. parse each documented amount without recomputation;
4. preserve the documented currency;
5. map `duties` only to `duty`;
6. map `taxes` only to `tax`;
7. preserve `fees` as provider-specific unless a narrower mapping is justified;
8. use `ESTIMATED` rather than `KNOWN` by default;
9. preserve numeric zero as zero;
10. preserve provenance through a Commerce AI-owned envelope;
11. preserve evaluation context through a Commerce AI-owned envelope;
12. reject negative or missing evidence-bearing amounts;
13. manufacture no duty, tax, fee, classification, legal, or customs result;
14. keep acquisition, credentials, entitlement, and verification outside the
    projection decision.

These conditions establish prospective compatibility only. They do not
authorize implementation.

## Projection compatibility decision

### Target-family result

- Target family: `landed_cost_component_evidence`
- Proposed state: `observed`
- Proposed value: Zonos `duties`, `taxes`, and `fees` entries prospectively
  support component-level projection through documented `amount`, `currency`,
  and `note` fields; `duties` maps to `duty`, `taxes` maps to `tax`, and
  `fees` remains provider-specific, with `ESTIMATED` state and Commerce
  AI-owned provenance and evaluation-context envelopes.

### Decision basis

The inspected official documentation identifies an explicit component
breakdown rather than only a total landed-cost estimate.

The documented `duties`, `taxes`, and `fees` result collections expose
component-level monetary values and currency. The request workflow supplies
the contextual inputs needed to correlate those results with a bounded
evaluation unit.

The canonical contract permits open provider-specific component identities,
so `fees` can remain provider-specific without manufacturing a canonical fee
subtype.

All prospective monetary components remain `ESTIMATED`. Guarantee language
does not independently authorize `KNOWN`.

### Overall subject result

Because `landed_cost_component_evidence` is the only applicable canonical
target family:

- `canonical_projection_compatibility`: `observed`
- value: subject-specific prospective component mapping

A later dossier mutation is proposed, but only through a separate authorized
exact-scope step.

## Meaning of the conclusion

The `observed` conclusion means only that the documented Zonos result shape
supports a prospective, bounded mapping into the existing canonical
landed-cost-component contract.

It is not:

- verification of a Zonos response;
- evidence of actual Commerce AI entitlement;
- provider adoption or selection;
- a score, grade, weight, or rank;
- a provider comparison;
- implementation or runtime authorization;
- credential or acquisition authority;
- a guarantee determination;
- tariff or duty verification;
- HS-code verification;
- customs or legal advice;
- a transaction or order authorization.

## Boundary review

This worksheet contains no live API call, credential, raw payload, adapter,
projector, runtime integration, provider comparison, score, ranking,
recommendation, selection, verified state, tariff calculation, classification,
customs filing, legal interpretation, order creation, or transaction
execution.

## Dossier mutation boundary

This worksheet does not mutate the dossier.

The dossier record remains `unknown / None` until a separate exact-scope
mutation is authorized and performed.

The proposed later mutation is limited to
`cb-ea3b1-zonos-006` and must preserve the existing subject identity, record
count, source relationships, and all other dossier records.
