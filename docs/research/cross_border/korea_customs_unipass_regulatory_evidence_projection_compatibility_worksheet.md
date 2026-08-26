# Korea Customs UNI-PASS Regulatory-Evidence Projection Compatibility Worksheet

## Document status

- Status: bounded internal observation worksheet
- Subject: `candidate:regulatory:korea-customs-unipass`
- External evidence kind: `regulatory`
- Canonical target family: `regulatory_evidence`
- Observation stage: documentation-only
- Evidence relationship: `subject_supplied`
- Observation date: `2026-08-26`
- Proposed compatibility state: `unknown`
- Proposed compatibility value: `None`
- Dossier mutation: none

## Purpose

This worksheet applies the internal canonical projection compatibility
observation protocol to the prospective regulatory-evidence surface of the
Korea Customs Service UNI-PASS candidate.

It asks only whether the evidence already registered in the external evidence
provider evaluation dossier establishes a bounded path into the canonical
`RegulatoryEvidence` contract.

It does not authorize:

- portal or API acquisition;
- credentials or account access;
- raw-payload capture;
- provider-specific parsing;
- adapter or projector implementation;
- canonical evidence construction;
- tariff or duty calculation;
- customs valuation;
- HS-code classification;
- declaration or application filing;
- provider registration or selection;
- runtime integration;
- verification;
- transaction execution.

## Applicable canonical target

The applicable external evidence kind is:

- `ExternalEvidenceKind.REGULATORY`

The single eligible canonical target is:

- `CanonicalProjectionTarget.REGULATORY_EVIDENCE`

The following target families are excluded:

- `currency_rate_evidence`;
- `shipping_route_evidence`;
- `landed_cost_component_evidence`.

References to tariff treatment, customs valuation, refunds, or other monetary
concepts do not authorize projection into landed-cost-component evidence.

## Registered observations

The dossier records that UNI-PASS:

- exposes Korean customs-administration workflows;
- covers export and import declarations;
- covers tariff treatment and customs valuation;
- covers cargo and special-clearance workflows;
- covers tariff-classification workflows;
- covers refunds and FTA origin procedures;
- represents procedures for goods entering, leaving, or moving through the
  Korean customs system;
- is an official Korea Customs Service system;
- organizes information by named workflow and document type;
- separates customs work into declarations, applications, approvals,
  corrections, certificates, and status workflows.

The dossier retains the following as `unknown / None`:

- temporal evidence;
- estimate-status disclosure;
- canonical projection compatibility;
- access and security requirements;
- commercial constraints.

The dossier further states that the inspected portal does not establish:

- a general machine API contract;
- credential entitlement;
- automated reuse permission;
- service levels;
- canonical projection;
- acquisition-runtime authority.

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

An evidence-bearing state requires a regulatory observation. An `UNKNOWN`
state must not carry a manufactured observation.

## Field-level observation matrix

| Canonical requirement | Registered evidence | Compatibility observation |
|---|---|---|
| Regulatory observation | The dossier identifies customs-administration workflow categories. | No specific declaration, application, classification, approval, certificate, status, tariff treatment, or customs result is registered. |
| Jurisdiction | The portal represents Korean customs procedures. | Korea is a documented service and procedure scope, but no jurisdiction is attached to a particular correlated evaluation result. |
| Regulatory reference | Workflows and document types are described generally. | No specific legal provision, declaration, application, certificate, classification decision, measure, or result reference is registered. |
| Evidence state | Several provider-evaluation dimensions are observed. | General portal and workflow observations do not satisfy the mandatory canonical regulatory-observation field. |
| Provenance | Official Korea Customs Service identity, source reference, relationship, and retrieval date are preserved. | Provenance is addressable, but provenance alone cannot construct regulatory evidence. |
| Evaluation context | Goods entering, leaving, or moving through the Korean customs system are within the described scope. | No exact product, shipment, origin, destination, procedure, filing, or request-result context is registered. |
| Freshness inputs | Temporal evidence is `unknown / None`. | No effective date, revision time, validity interval, or result-specific freshness input is registered. |

## Blocking gaps

### Result-level observation gap

The registered evidence establishes the existence and organization of customs
workflows. It does not preserve a particular regulatory condition or outcome
returned for a particular product, shipment, declaration, or application.

A workflow name must not be reinterpreted as a canonical regulatory result.

### Evaluation-context gap

No registered observation correlates:

- product or commodity identity;
- commodity or HS code;
- origin and destination;
- shipment or cargo identity;
- import, export, or transit procedure;
- declaration or application identity;
- applicable date;
- returned condition, status, approval, classification, or treatment.

The general scope of a government customs system does not substitute for
bounded evaluation context.

### Jurisdiction gap

Korean customs jurisdiction is strongly indicated as the portal's institutional
scope. However, the canonical field must remain tied to a particular
regulatory observation and evaluation context.

No such result-level correlation is registered.

### Regulatory-reference gap

The dossier contains no specific:

- statute or regulation;
- customs notice or measure;
- declaration or application;
- approval or correction;
- certificate;
- tariff-classification decision;
- status or result identifier.

The portal root URL is provenance material, not a result-level regulatory
reference.

### Temporal and freshness gap

No effective time, revision timestamp, validity period, decision date, filing
date, or result-specific retrieval relationship is registered.

### Workflow-state boundary

UNI-PASS separates customs activity into workflow-specific declarations,
applications, approvals, corrections, certificates, and status processes.

This structure weighs against treating portal availability as one
unconditional regulatory result.

### Acquisition boundary

Portal availability and electronic customs workflows do not establish:

- a supported general machine API;
- credentials or entitlement;
- automated acquisition or reuse permission;
- production quotas;
- service-level guarantees;
- runtime authorization.

Projection compatibility cannot create those authorities.

## Non-inference rules

This worksheet does not infer:

- an HS or commodity classification;
- a tariff, duty, tax, or customs value;
- an applicable restriction, exemption, or preference;
- declaration acceptance or customs clearance;
- approval, certificate, or filing status;
- regulatory permission;
- a binding customs decision;
- automated acquisition or reuse permission;
- canonical compatibility from official-source identity alone;
- absence of provider capability from absence of registered evidence.

Published customs information and portal workflows do not establish binding
classification, final customs treatment, filing authority, or transaction
authority.

## Minimum evidence needed for reconsideration

A later bounded observation would need to:

1. identify the exact supported result surface;
2. preserve a specific regulatory observation;
3. correlate it with the exact product, shipment, or filing context;
4. preserve applicable origin, destination, and procedure;
5. establish context-bound jurisdiction;
6. preserve a specific regulatory or result reference when claimed;
7. preserve provenance and retrieval timing;
8. preserve effective-time or freshness inputs when claimed;
9. distinguish information, application, approval, and binding-decision states;
10. establish acquisition and reuse boundaries separately;
11. demonstrate that projection manufactures no classification, duty, tax,
    permission, clearance, or legal conclusion.

These conditions support reconsideration only. They do not authorize
acquisition, implementation, verification, selection, or runtime use.

## Projection compatibility decision

### Target-family result

- Target family: `regulatory_evidence`
- Proposed state: `unknown`
- Proposed value: `None`

### Decision basis

The registered evidence establishes official provenance, Korean customs-system
scope, and named customs workflow categories.

It does not establish a result-level regulatory observation correlated with a
complete Commerce AI evaluation context. No specific regulatory reference or
temporal and freshness inputs are registered. The documented jurisdictional
scope is not attached to a particular observation.

The mandatory evidence-bearing `RegulatoryEvidence` requirements therefore
remain unsatisfied.

### Overall subject result

Because `regulatory_evidence` is the only applicable canonical target family:

- `canonical_projection_compatibility`: `unknown`
- value: `None`

No dossier mutation is proposed.

## Meaning of the conclusion

The `unknown / None` conclusion records a blocking result-shape, correlation,
reference, and temporal-evidence gap.

It is not:

- evidence that UNI-PASS lacks customs information or workflows;
- evidence that UNI-PASS information is inaccurate;
- a provider comparison or score;
- a rejection or adoption decision;
- a tariff classification or legal conclusion;
- a customs-clearance decision;
- provider selection;
- adapter or projector authorization;
- acquisition or runtime authority;
- verification;
- a commercial, legal, or operational assessment.

Absence of evidence is not evidence of absence.

## Boundary review

This worksheet contains no provider comparison, score, rank, recommendation,
selection, verified state, portal interaction, live API call, credential,
network client, raw payload, adapter, projector, canonical evidence
construction, tariff or duty calculation, customs valuation, classification,
filing, legal interpretation, implementation change, or transaction execution.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The Korea Customs UNI-PASS `canonical_projection_compatibility` record remains
`unknown` with literal `None`.

Because the worksheet proposes the same existing state and value, no later
dossier mutation is implied.
