# GOV.UK Trade Tariff API Regulatory-Evidence Projection Compatibility Worksheet

## Document status

- Status: bounded internal observation worksheet
- Subject: `candidate:regulatory:govuk-trade-tariff-api`
- External evidence kind: `regulatory`
- Canonical target family: `regulatory_evidence`
- Observation stage: documentation-only
- Evidence relationship: `subject_supplied`
- Observation date: `2026-08-25`
- Proposed compatibility state: `unknown`
- Proposed compatibility value: `None`
- Dossier mutation: none

## Purpose

This worksheet applies the internal canonical projection compatibility
observation protocol to the prospective regulatory-evidence surface of the
GOV.UK Trade Tariff API candidate.

It asks only whether the currently registered documentation evidence is
sufficient to establish a bounded path into the existing canonical
`RegulatoryEvidence` contract.

It does not authorize:

- API acquisition;
- network-client implementation;
- credential use;
- raw-payload capture;
- provider-specific parsing;
- adapter or projector implementation;
- canonical evidence construction;
- tariff or duty calculation;
- HS-code or commodity-code classification;
- customs filing;
- legal interpretation;
- provider registration or selection;
- runtime integration;
- verification;
- transaction execution.

## Governing contracts

The applicable external evidence kind is:

- `ExternalEvidenceKind.REGULATORY`

The single permitted canonical target is:

- `CanonicalProjectionTarget.REGULATORY_EVIDENCE`

The existing projection eligibility contract excludes the following target
families for this observation unit:

- `currency_rate_evidence`;
- `shipping_route_evidence`;
- `landed_cost_component_evidence`.

References to tariffs, duties, taxes, customs measures, commodity codes, or
trade measures do not independently authorize projection into a monetary
landed-cost component.

## Registered subject evidence

The evaluation dossier currently records the following bounded observations:

1. The official service endpoint identifies a UK Trade Tariff API and redirects
   users to its documentation service.
2. The evidence endpoint is hosted under the official UK government Trade
   Tariff service domain.

The dossier retains the following dimensions as `unknown` with literal
`None`:

- geographic coverage;
- temporal evidence;
- estimate-status disclosure;
- canonical projection compatibility;
- operational constraints;
- access and security requirements;
- commercial constraints.

The dossier also states that the inspected endpoint does not, by itself,
establish:

- complete dataset scope;
- revision behavior;
- production access terms;
- reuse permission;
- service levels;
- suitability for automated Commerce AI acquisition.

## Canonical target requirements

The canonical `RegulatoryEvidence` target requires evidence sufficient to
address:

- regulatory observation;
- jurisdiction when claimed;
- regulatory reference when claimed;
- evidence state;
- provenance;
- evaluation context;
- freshness inputs when claimed.

Its bounded fields are:

- `evidence`;
- `provenance`;
- `context`;
- `observation`;
- `jurisdiction`;
- `regulatory_reference`;
- `freshness`.

For an `UNKNOWN` evidence state, the canonical contract prohibits
manufacturing a regulatory observation.

For an evidence-bearing state, a regulatory observation is mandatory.

The contract does not determine legal permission, calculate tariffs or duties,
classify HS codes, retrieve live regulatory data, file customs declarations,
or authorize transaction execution.

## Field-level observation matrix

| Canonical requirement | Registered evidence | Observation |
|---|---|---|
| Regulatory observation | The registered text identifies an API service and official documentation endpoint. | No bounded product-, commodity-, measure-, restriction-, tariff-, or procedure-specific regulatory observation is established. |
| Jurisdiction | The source identity and domain are associated with the official UK Trade Tariff service. | The applicable jurisdiction for a particular evaluation context is not established. The service name or domain must not be silently converted into a context-bound jurisdiction assertion. |
| Regulatory reference | The dossier preserves the official service URL. | A service URL is provenance material, but no bounded regulation, measure, commodity, legal instrument, or result reference is registered. |
| Evidence state | The dossier records service identity and provenance observations. | Those observations do not provide the mandatory regulatory observation required for an evidence-bearing `RegulatoryEvidence` state. |
| Provenance | Source ID, source type, source reference, relationship, and retrieval date are available in the dossier. | Provenance is partially addressable, but provenance alone cannot construct regulatory evidence. |
| Evaluation context | No correlated product, commodity code, origin, destination, shipment, or query-result context is registered. | Mandatory bounded evaluation context is absent. |
| Freshness inputs | Temporal evidence is `unknown / None`. | No effective time, revision time, validity interval, or bounded freshness input is registered. |

## Blocking gaps

### Regulatory observation gap

The registered evidence describes the identity of the API service. It does not
preserve a bounded regulatory condition or result suitable for the canonical
`observation` field.

An API identity statement must not be reinterpreted as a tariff rule,
restriction, measure, classification, legal permission, or customs outcome.

### Evaluation-context gap

No exact request-result relationship is registered for:

- product or commodity identity;
- commodity or classification code;
- origin country;
- destination country;
- applicable date;
- procedure or trade flow;
- regulatory measure or result.

Without that correlation, a regulatory observation cannot be attached to the
canonical Cross-Border evaluation context.

### Jurisdiction gap

The official UK service identity is useful provenance. It does not, by itself,
establish that a particular regulatory observation applies to a particular
Commerce AI evaluation context.

No jurisdiction value should be manufactured from the provider name, hostname,
or subject category.

### Regulatory-reference gap

The service root URL does not identify a particular legal provision,
commodity record, measure, tariff result, restriction, or regulatory decision.

The canonical `regulatory_reference` field therefore cannot be populated from
the registered evidence.

### Temporal and freshness gap

The registered dossier contains no bounded effective date, revision timestamp,
validity interval, or result-specific retrieval relationship sufficient to
support claimed freshness inputs.

### Evidence-state constraint

The canonical contract permits `UNKNOWN` evidence without an observation, but
prohibits `UNKNOWN` evidence from carrying a manufactured observation.

Because the registered material lacks a bounded regulatory observation, an
evidence-bearing canonical state cannot be proposed.

## Non-inference rules

This worksheet does not infer any of the following:

- that a product has a particular commodity or HS code;
- that a tariff measure applies;
- that a duty or tax amount is payable;
- that a restriction, prohibition, quota, preference, or exemption applies;
- that a published measure is legally binding for a specific transaction;
- that customs clearance will be granted;
- that the service permits automated acquisition or reuse;
- that an official source is automatically compatible with the Commerce AI
  canonical evidence contract;
- that absence of registered evidence means absence of provider capability.

Publication of tariff or regulatory information does not establish legal
permission, binding classification, final customs treatment, or transaction
authority.

## Minimum evidence needed for reconsideration

A later bounded observation would need evidence sufficient to:

1. identify the exact documented API resource or response surface;
2. preserve a specific regulatory observation without legal reinterpretation;
3. correlate that observation with its exact request and evaluation context;
4. establish whether and how jurisdiction is represented;
5. preserve a bounded regulatory reference when one is claimed;
6. preserve source provenance and retrieval timing;
7. identify effective-time or freshness inputs when claimed;
8. distinguish published information from binding classification or final
   customs treatment;
9. document access, reuse, and operational boundaries separately from
   projection compatibility;
10. demonstrate that no tariff, duty, tax, classification, or legal conclusion
    is manufactured during projection.

These conditions would support reconsideration only. They would not authorize
acquisition, implementation, provider selection, verification, or runtime use.

## Projection compatibility decision

### Target-family result

- Target family: `regulatory_evidence`
- Proposed state: `unknown`
- Proposed value: `None`

### Decision basis

The registered documentation establishes an official UK Trade Tariff API
service identity and traceable official source.

It does not establish the mandatory bounded regulatory observation or
evaluation context required for an evidence-bearing `RegulatoryEvidence`
instance. Jurisdiction, regulatory reference, and freshness inputs are also
not established at the required context-bound level.

The documentation-only observation therefore cannot establish canonical
projection compatibility.

### Overall subject result

Because `regulatory_evidence` is the only applicable canonical target family,
the overall prospective result for this subject remains:

- `canonical_projection_compatibility`: `unknown`
- value: `None`

No dossier mutation is proposed.

## Meaning of the conclusion

The `unknown / None` conclusion records a blocking evidence-shape and
correlation gap for this subject-target observation unit.

It is not:

- evidence that the GOV.UK Trade Tariff API lacks regulatory information;
- evidence that the service is inaccurate;
- a compatibility score or grade;
- a provider comparison;
- a legal conclusion;
- a tariff classification;
- a customs decision;
- a rejection or adoption decision;
- provider selection;
- adapter or projector authorization;
- acquisition or runtime authority;
- verification;
- a commercial, legal, or operational assessment.

Absence of evidence is not evidence of absence.

## Boundary review

This worksheet contains no:

- provider comparison;
- score, percentage, grade, weight, or rank;
- provider preference;
- recommendation or selection;
- verified state;
- live API call;
- credential or network client;
- raw provider payload;
- adapter or projector;
- canonical evidence construction;
- tariff, duty, or tax calculation;
- HS-code or commodity-code classification;
- customs filing;
- legal interpretation;
- implementation change;
- shipment, payment, or transaction execution.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The GOV.UK Trade Tariff API `canonical_projection_compatibility` record remains
`unknown` with literal `None`.

Because the target-family worksheet proposes the same existing state and
value, no later dossier mutation is implied by this worksheet.
