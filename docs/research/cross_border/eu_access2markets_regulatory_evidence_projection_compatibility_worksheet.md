# EU Access2Markets Regulatory-Evidence Projection Compatibility Worksheet

## Document status

- Status: bounded internal observation worksheet
- Subject: `candidate:regulatory:eu-access2markets`
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
European Commission Access2Markets candidate.

It evaluates only whether the evidence already registered in the external
evidence provider evaluation dossier establishes a bounded path into the
existing canonical `RegulatoryEvidence` contract.

It does not authorize acquisition, scraping, API use, credentials, raw-payload
capture, provider parsing, adapter or projector implementation, canonical
evidence construction, classification, customs treatment, provider selection,
runtime integration, verification, or transaction execution.

## Applicable canonical target

The applicable external evidence kind is:

- `ExternalEvidenceKind.REGULATORY`

The single eligible canonical target is:

- `CanonicalProjectionTarget.REGULATORY_EVIDENCE`

The following target families are excluded:

- `currency_rate_evidence`;
- `shipping_route_evidence`;
- `landed_cost_component_evidence`.

References to tariffs, taxes, trade conditions, or customs procedures must not
be reinterpreted as monetary landed-cost-component evidence.

## Registered observations

The dossier records that Access2Markets:

- provides information concerning tariffs, taxes, rules of origin, product
  requirements, procedures, trade agreements, and statistics;
- accepts a product and export and import countries in My Trade Assistant;
- presents conditions for trade with the EU under an applicable market and
  agreement context;
- is managed by the European Commission Directorate-General for Trade and
  Economic Security;
- provides links to applicable legal texts through its rules-of-origin tools;
- describes ROSA as a self-assessment tool;
- distinguishes ROSA from Binding Origin Information, which provides written
  legal certainty;
- depends on product code, export country, import country, applicable trade
  agreement, and supplied origin facts;
- describes ROSA as free to use while leaving broader automated reuse, quota,
  and service-level terms unresolved.

The dossier retains the following as `unknown / None`:

- temporal evidence;
- canonical projection compatibility;
- access and security requirements.

The dossier expressly limits these observations to public portal functionality.
It does not establish a supported machine API, scraping permission, production
credential model, binding tariff classification, or final customs treatment
for an individual shipment.

## Canonical contract requirements

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

An evidence-bearing canonical state requires a regulatory observation.
An `UNKNOWN` state must not carry a manufactured observation.

## Field-level observation matrix

| Canonical requirement | Registered evidence | Compatibility observation |
|---|---|---|
| Regulatory observation | The dossier describes categories of information and portal functionality. | No specific product-, code-, route-, agreement-, measure-, restriction-, or procedure-bound regulatory result is registered. |
| Jurisdiction | The portal presents conditions for trade with the EU using export and import countries. | This describes an input-dependent coverage model, but does not establish the jurisdiction applicable to a particular correlated Commerce AI evaluation. |
| Regulatory reference | Applicable legal texts may be linked by rules-of-origin tools. | No specific legal text, measure, decision, commodity record, or result reference is registered for a bounded observation. |
| Evidence state | Several provider-evaluation dimensions are observed. | Those general documentation observations do not establish the mandatory canonical regulatory observation. |
| Provenance | Official European Commission sources, source identities, references, relationship, and retrieval date are preserved. | Provenance is addressable, but provenance alone cannot construct regulatory evidence. |
| Evaluation context | Product code, export country, import country, agreement, and origin facts are documented as required inputs. | Required input categories are known, but no exact request-result context is registered. |
| Freshness inputs | Temporal evidence remains `unknown / None`. | No effective date, revision time, validity interval, or result-specific freshness input is registered. |

## Blocking gaps

### Result-level observation gap

The dossier establishes that Access2Markets can present regulatory and trade
information. It does not preserve a particular regulatory result produced for
a particular input set.

A list of available information categories is not itself a canonical
regulatory observation.

### Correlated evaluation-context gap

No registered record correlates all required elements of a bounded result,
including:

- product or commodity code;
- export country;
- import country;
- origin facts;
- applicable agreement;
- query or request identity;
- returned measure, rule, requirement, or procedure;
- retrieval and effective time.

Documented prerequisites must not be treated as supplied evaluation context.

### Jurisdiction gap

The EU trade context and export/import country inputs establish a documented
coverage concept. They do not establish which jurisdiction applies to a
specific unobserved Commerce AI candidate or transaction context.

### Regulatory-reference gap

The possibility that portal tools link to legal texts does not establish a
specific reference for this observation unit.

No canonical `regulatory_reference` can be populated without a correlated
measure, decision, legal text, commodity record, or result reference.

### Temporal and freshness gap

The dossier contains no bounded result-level effective date, revision time,
validity period, or freshness relationship.

### Binding-status boundary

ROSA is described as self-assessment, while Binding Origin Information is
separately required for written legal certainty.

This distinction is useful disclosure evidence, but it does not transform
general portal documentation into a binding classification, final customs
treatment, or transaction-specific regulatory observation.

### Acquisition boundary

The registered evidence concerns public portal functionality. It does not
establish a supported machine API, scraping permission, automated reuse
permission, credential model, quota, or service-level contract.

Projection compatibility does not create acquisition authority.

## Non-inference rules

This worksheet does not infer:

- a commodity or HS classification;
- an applicable tariff, tax, preference, quota, restriction, or exemption;
- satisfaction of a rule of origin;
- legal permission to import or export;
- a binding origin or classification decision;
- final customs treatment;
- a duty or tax amount;
- automated acquisition or reuse permission;
- canonical compatibility from official-source status alone;
- absence of provider capability from absence of registered evidence.

Publication of tariff or regulatory material does not establish legal
permission, binding classification, final customs treatment, or transaction
authority.

## Minimum evidence needed for reconsideration

A later bounded observation would need to:

1. identify the exact supported result surface;
2. preserve a specific regulatory observation without legal reinterpretation;
3. correlate it with the exact product or commodity code;
4. preserve export country, import country, origin facts, and applicable
   agreement context;
5. identify the applicable jurisdiction;
6. preserve a specific regulatory or legal reference when claimed;
7. preserve provenance and retrieval timing;
8. preserve effective-time or freshness inputs when claimed;
9. distinguish self-assessment from binding treatment;
10. establish acquisition and reuse boundaries separately;
11. demonstrate that projection manufactures no classification, duty, tax,
    legal permission, or customs conclusion.

These conditions support reconsideration only. They do not authorize
implementation, acquisition, verification, selection, or runtime use.

## Projection compatibility decision

### Target-family result

- Target family: `regulatory_evidence`
- Proposed state: `unknown`
- Proposed value: `None`

### Decision basis

The registered evidence establishes substantial information coverage,
official provenance, an input-dependent geographic model, self-assessment
disclosure, and operational prerequisites.

It does not establish a result-level regulatory observation correlated with a
complete Commerce AI evaluation context. No context-bound jurisdiction,
specific regulatory reference, or temporal and freshness inputs are
registered.

The mandatory evidence-bearing `RegulatoryEvidence` requirements therefore
remain unsatisfied.

### Overall subject result

Because `regulatory_evidence` is the only applicable canonical target family:

- `canonical_projection_compatibility`: `unknown`
- value: `None`

No dossier mutation is proposed.

## Meaning of the conclusion

The `unknown / None` conclusion records a blocking result-shape, correlation,
and temporal-evidence gap.

It is not:

- evidence that Access2Markets lacks regulatory information;
- evidence that its information is inaccurate;
- a provider comparison or score;
- a rejection or adoption decision;
- a legal or customs conclusion;
- provider selection;
- adapter or projector authorization;
- acquisition or runtime authority;
- verification;
- a commercial, legal, or operational assessment.

Absence of evidence is not evidence of absence.

## Boundary review

This worksheet contains no provider comparison, score, rank, recommendation,
selection, verified state, live portal interaction, scraping, credential,
network client, raw payload, adapter, projector, canonical evidence
construction, tariff or tax calculation, classification, customs filing,
legal interpretation, implementation change, or transaction execution.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The Access2Markets `canonical_projection_compatibility` record remains
`unknown` with literal `None`.

Because the worksheet proposes the same existing state and value, no later
dossier mutation is implied.
