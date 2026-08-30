# US Low-Value Commercial Shipment Policy Evidence Registration Decision

## Decision identity

- Decision gate: `CB-USLV-2_DEDICATED_POLICY_EVIDENCE_REGISTRATION_DECISION`
- Registration subject: `US_LOW_VALUE_COMMERCIAL_SHIPMENT_POLICY`
- Registration scope: `SUBJECT_LEVEL_RESEARCH_EVIDENCE_ONLY`
- Decision result: `REGISTER`
- Registration result: `REGISTERED_RESEARCH_EVIDENCE`
- Decision status: `OFFICIAL`
- Canonical admission: `NOT AUTHORIZED`

## Authority chain

This decision operates under the sealed lifecycle-opening decision:

`docs/research/cross_border/us_low_value_commercial_shipment_policy_evidence_registration_lifecycle_opening_decision.md`

The lifecycle-opening tag is:

`cross-border-us-low-value-commercial-shipment-policy-evidence-registration-lifecycle-opened-v1.0`

The exact sealed evidence input is:

`docs/research/cross_border/us_low_value_commercial_shipment_policy_official_source_evidence_record.md`

Its sealed identities are:

- evidence-record commit:
  `e0fbced6fb313df82b0587475f9957555f84f790`
- evidence-record tag object:
  `aba60f21964ec0c380539261fdaac80336141c64`
- evidence-record tag:
  `cross-border-us-low-value-commercial-shipment-policy-official-source-evidence-recorded-v1.0`
- evidence-record Git blob:
  `cf9d889be37740413db28474a84e2536b56898d8`
- evidence-record SHA-256:
  `b297ae4683c13d9c7ecc6654387bce761d7dc0da1d7807b8a71a82cc559664a6`

No unsealed or inferred evidence is registered by this decision.

## Routing decision

The exact selected routing is:

`DEDICATED_EVIDENCE_REGISTRATION_DECISION`

The alternatives are resolved as follows:

- existing provider dossier registration: `DENIED`
- dedicated evidence registration decision: `SELECTED`
- initial acquisition gate completion without registration: `INSUFFICIENT`
- additional source acquisition for the current gate: `NOT REQUIRED`

Exactly one routing option is selected.

## Routing basis

The existing
`docs/research/cross_border/external_evidence_provider_evaluation_dossier.md`
is owned by the external-provider-candidate evaluation lifecycle.

That dossier contains regulatory provider or source candidates evaluated through
provider-neutral evidence dimensions. It is not an automatically extensible
owner for every policy instrument used by Commerce AI research.

The present subject consists of time-bound official United States policy
instruments issued or published by the President and U.S. Customs and Border
Protection. It does not establish a provider candidate identity.

Automatic attribution of this subject to the provider evaluation dossier would
expand that dossier's semantic responsibility and is denied.

No existing general policy evidence registry was established by the repository
precedent review. This decision does not create one.

The sealed subject-specific evidence record and this registration decision form
the dedicated registration chain for this lifecycle.

## Registered evidence set

The following five official instruments are registered through the sealed
evidence record:

1. `Executive Order 14388`
2. `Temporary Import Surcharge Proclamation of 2026-02-20`
3. `FR Doc. 2026-12670`
4. `FR Doc. 2026-12669`
5. `FR Doc. 2026-12668`

The White House, Federal Register, and GovInfo representations identified in the
sealed evidence record remain representations of their corresponding
instruments. Multiple official representations do not create duplicate policy
instruments or duplicate facts.

Official instrument count: `5`

Registration status: `REGISTERED_RESEARCH_EVIDENCE`

## Status-preserving registration

The registration preserves the evidence status of every fact and unresolved
field in the sealed evidence record.

### VERIFIED

The following evidence classes are registered as `VERIFIED` only to the extent
directly established in the sealed official-source record:

- issuing authority;
- official instrument identity;
- publication and specified effective dates;
- postal and non-postal shipment-mode scope;
- directly stated value thresholds;
- directly stated exemption, duty, and entry treatment;
- the announced `2026-09-22` Entry Type 13 test start date; and
- the stated `2027-07-01` statutory termination date.

### PARTIALLY_VERIFIED

The bounded current-validity observation remains:

`PARTIALLY_VERIFIED`

The absence of a modification or revocation in the bounded search is not
converted into proof that no later or undiscovered instrument exists.

Time-sensitive use requires renewed official-source validation.

### REPORTED

Registered `REPORTED` facts:

`NONE`

### MISSING

The following remain explicitly `MISSING`:

- individual-product final duty;
- individual-product HTSUS classification;
- individual-product PGA requirements;
- individual-shipment entry eligibility;
- Entry Type 13 operational outcome;
- exact taxes and fees for an individual shipment; and
- a production-ready policy rule.

No missing value is inferred, defaulted, or promoted.

## Source-fact and interpretation boundary

Source facts, project interpretation, and canonical admission remain separate.

The project interpretation that the Commerce AI Generator must not use an
unconditional `$800 or less means duty free` assumption is registered as a
research interpretation grounded in the sealed official evidence.

This research interpretation is not:

- a canonical model field;
- an executable calculation rule;
- an individual-shipment customs determination;
- legal advice;
- provider selection;
- production behavior; or
- runtime activation.

## Registration effect

This decision registers the sealed official-source evidence record as the
authoritative subject-level research evidence record for this lifecycle.

Here, authoritative means authoritative within the bounded research lifecycle
and its sealed repository identity. It does not mean canonical admission,
universal legal completeness, or perpetual time validity.

The registration does not:

- mutate the external evidence provider evaluation dossier;
- create or mutate a general evidence registry;
- mutate any canonical contract;
- modify any worksheet;
- acquire additional external evidence;
- implement a parser, projector, provider, API client, or runtime rule;
- calculate a product-specific landed cost; or
- resolve any `MISSING` field.

## Downstream constraints

Any later policy model, landed-cost computation, or routing recommendation must
pass a separate authority gate.

A later gate must preserve:

- official-source provenance;
- policy-effective time;
- postal versus non-postal scope;
- HTSUS and country-of-origin dependency;
- applicable duties, taxes, fees, PGA, AD/CVD, and quota constraints;
- `PARTIALLY_VERIFIED` status where applicable; and
- every unresolved `MISSING` field until separately established.

Nothing in this decision authorizes canonical projection compatibility or
production implementation.

## Repository mutation boundary

The only repository write authorized by `CB-USLV-1K` is creation of this
decision file:

`docs/research/cross_border/us_low_value_commercial_shipment_policy_evidence_registration_decision.md`

No other repository artifact is authorized to change.

Staging, commit creation, tag creation, and push remain withheld pending a
separate explicit authority gate.

The reserved future registration tag is:

`cross-border-us-low-value-commercial-shipment-policy-evidence-registered-v1.0`

This decision does not create that tag.

## Decision result

- exact routing selection: `DEDICATED_EVIDENCE_REGISTRATION_DECISION`
- official instrument set: `REGISTERED_RESEARCH_EVIDENCE`
- evidence-record identity: `SEALED`
- `VERIFIED` facts: `REGISTERED_WITH_STATUS_PRESERVED`
- `PARTIALLY_VERIFIED` facts: `REGISTERED_WITH_STATUS_PRESERVED`
- `REPORTED` facts: `NONE`
- `MISSING` fields: `REGISTERED_AS_EXPLICIT_UNRESOLVED_STATE`
- provider dossier mutation: `NONE`
- general evidence registry creation: `NONE`
- canonical admission: `NOT AUTHORIZED`
- implementation and runtime effect: `NONE`
- lifecycle completion: `NOT PERFORMED`
- stage, commit, tag, and push: `NOT AUTHORIZED`
