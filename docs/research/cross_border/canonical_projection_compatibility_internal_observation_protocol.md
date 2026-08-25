# Canonical Projection Compatibility Internal Observation Protocol

## Document identity

- Protocol: `CB-EA4A-2`
- Status: `research protocol only`
- Runtime authority: `None`
- Acquisition authority: `None`
- Provider-selection authority: `None`
- Adapter authority: `None`
- Projector authority: `None`
- Verification authority: `None`

## Purpose

This protocol defines a bounded internal observation procedure for the
`canonical_projection_compatibility` dimension in the external evidence
provider evaluation dossier.

The procedure compares no evaluation subjects with one another. It examines
one opaque evaluation subject and one canonical target family at a time.

Its only purpose is to determine whether inspected subject documentation
provides enough output-shape evidence to record a subject-local observation
about prospective interpretation into an existing Commerce AI canonical
evidence contract.

## Existing canonical target families

The protocol is limited to these existing target families:

1. `currency_rate_evidence`
2. `shipping_route_evidence`
3. `regulatory_evidence`
4. `landed_cost_component_evidence`

The mapping from external evidence kind to target family remains owned by
`external_evidence_projection.py`.

This protocol does not change that mapping and does not execute projection.

## Non-negotiable authority boundary

This protocol does not authorize:

- network access or live provider calls;
- credentials, authentication, or account use;
- raw response or payload storage;
- HTML capture or scraping;
- provider-specific adapters;
- generic projectors;
- canonical evidence construction;
- provider registration or canonical provider identity;
- scoring, weighting, ranking, comparison, recommendation, or selection;
- runtime consumption;
- transaction execution;
- independent verification of subject-supplied claims.

A protocol observation is not evidence that a provider is correct, reliable,
independent, commercially available, legally reusable, operationally ready,
or suitable for adoption.

## Observation unit

The observation unit is:

`evaluation subject × canonical target family`

Each unit must be inspected independently.

A subject that documents more than one evidence kind must have a separate
observation worksheet for each applicable canonical target family. Evidence
for one target family must not be generalized to another target family.

## Evidence sources

Only sources already registered in the sealed external provider evaluation
dossier may be used during the initial protocol application.

A source must remain associated with its recorded source relationship.

`subject_supplied` evidence remains subject-supplied. Its use in this
protocol does not establish verification, correctness, independence, trust,
or authority.

If additional sources are required, they must be separately authorized and
registered before use.

## Two-layer inspection model

Every observation must distinguish two layers.

### Layer A — documented subject output shape

This layer records only fields, values, identifiers, state indicators,
references, and timestamps explicitly documented by the evaluation subject.

No undocumented field may be inferred or manufactured.

### Layer B — Commerce AI internal envelope authority

Commerce AI retains authority for:

- `CrossBorderEvidence`;
- `EvidenceState`;
- `EvidenceProvenance`;
- `CrossBorderEvaluationContext`;
- `EvidenceFreshness`;
- canonical target construction;
- bounded normalization;
- canonical state interpretation.

A provider does not become compatible merely because Commerce AI could
manufacture missing envelope data.

Internal envelope fields may be satisfied only when their required inputs
are traceable to inspected documentation or to an explicitly identified
Commerce AI evaluation context.

## Common inspection requirements

Each worksheet must record:

- `subject_ref`;
- `target_family`;
- inspected `source_id`;
- inspected `source_reference`;
- source relationship;
- documented output locator;
- documented subject fields;
- required canonical fields;
- field-by-field evidence mapping;
- required transformations;
- unresolved gaps;
- state/value semantic alignment;
- provenance input availability;
- temporal input availability;
- context input availability;
- conclusion state;
- conclusion value.

Required transformations must be described, but no transformation may be
implemented or executed under this protocol.

## Target-family requirements

### Currency-rate evidence

The canonical target requires evidence sufficient to address:

- base currency;
- quote currency;
- positive finite rate;
- evidence state;
- provenance;
- evaluation context;
- freshness inputs when claimed.

The documented rate direction must be unambiguous:

`1 base_currency = rate quote_currency`

An inverse rate must not be assumed without a separately authorized
transformation rule.

### Shipping-route evidence

The canonical target requires evidence sufficient to address:

- route type;
- origin country;
- destination country;
- availability state;
- carrier or forwarder reference when applicable;
- estimated transit days when claimed;
- estimated route cost and its currency when claimed;
- route constraints;
- provenance when claimed;
- freshness inputs when claimed.

A documented price without a documented currency cannot support a route-cost
mapping.

A rate result does not by itself establish universal route availability.

### Regulatory evidence

The canonical target requires evidence sufficient to address:

- regulatory observation;
- jurisdiction when claimed;
- regulatory reference when claimed;
- evidence state;
- provenance;
- evaluation context;
- freshness inputs when claimed.

Publication of tariff or regulatory material does not establish legal
permission, binding classification, final customs treatment, or transaction
authority.

### Landed-cost-component evidence

The canonical target requires evidence sufficient to address:

- component identity;
- component state;
- amount and currency for evidence-bearing states;
- absence of amount and currency for evidence-absent states;
- provenance when claimed;
- evaluation context when claimed;
- estimate reason when applicable.

A total landed-cost estimate must not be decomposed into components unless
the inspected documentation explicitly exposes the component breakdown.

Provider-specific component names may be recorded as documented, but they
must not be declared canonical without a separately justified component
mapping.

## State and value rules

The existing dossier evidence-state vocabulary remains authoritative.

### Observed conclusion

The existing `canonical_projection_compatibility` record may become
`observed` only when all of the following are true:

1. the applicable canonical target family is unambiguous;
2. the inspected documentation identifies the relevant output shape;
3. every mandatory target invariant has documented support or an explicitly
   identified Commerce AI internal-envelope source;
4. state and value semantics do not require manufacturing evidence;
5. every required transformation is bounded and explicitly described;
6. unresolved gaps do not prevent prospective canonical construction;
7. the observation remains subject-local and non-comparative.

An observed conclusion value must be factual prose identifying:

- the target family;
- the documented shape support;
- required bounded transformations;
- remaining non-blocking limitations.

It must not use adoption language or claim runtime readiness.

### Unknown conclusion

The record must remain:

- state: `unknown`
- observation value: `None`

when any required condition is unsupported, ambiguous, contradictory, or
dependent on uninspected documentation.

The reason for remaining unknown must be recorded outside the observation
value.

Unknown must not be replaced with zero, false, empty text, an assumed field,
or a synthetic compatibility result.

## Prohibited conclusion vocabulary

The protocol must not produce:

- compatibility scores;
- percentages;
- grades;
- weights;
- ranks;
- provider ordering;
- winner or preferred-provider labels;
- adoption recommendations;
- production-ready labels;
- verified labels;
- generic compatibility claims across multiple targets.

Terms such as `best`, `better`, `preferred`, `recommended`, `selected`,
`approved provider`, and `production ready` are prohibited.

## Mixed-capability subjects

When one evaluation subject documents multiple evidence kinds, each target
family must be inspected separately.

A supported observation for one target family must not cause another target
family to become observed.

The existing single dossier dimension record may change from `unknown` only
when its observation value can enumerate every inspected target-family
result without hiding an unresolved applicable target.

Otherwise the existing record remains `unknown` with literal `None`.

## Verification boundary

Protocol application may produce an `observed` record only.

It cannot produce `verified`.

Independent verification requires a separate authorization, separate
evidence sources, and a separate verification protocol.

## Required artifacts for protocol application

A future authorized application step must produce:

1. one subject-local worksheet per applicable target family;
2. source citations tied to the sealed source register;
3. a field-by-field canonical mapping;
4. an explicit unresolved-gap list;
5. a proposed dossier record state and value;
6. a boundary review confirming absence of scoring and selection;
7. tests or deterministic checks for dossier count and state preservation.

These artifacts remain research documentation and must not be imported by
runtime packages.

## Deferred work

This protocol does not authorize its application to the eleven evaluation
subjects.

Protocol application, dossier mutation, adapter design, acquisition runtime,
independent verification, provider assessment, and provider selection each
require separate authorization.
