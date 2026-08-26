# USITC HTS Regulatory-Evidence Projection Compatibility Worksheet

## Document status

- Status: bounded internal observation worksheet
- Subject: `candidate:regulatory:usitc-hts`
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
USITC Harmonized Tariff Schedule candidate.

It asks only whether the currently registered documentation evidence is
sufficient to establish a bounded path into the existing canonical
`RegulatoryEvidence` contract.

The evaluation subject is the USITC HTS publication source. It is not a CBP
subject and must not be reinterpreted as one.

This worksheet does not authorize:

- API or bulk-data acquisition;
- network-client implementation;
- credential use;
- raw-payload capture;
- provider-specific parsing;
- adapter or projector implementation;
- canonical evidence construction;
- tariff or duty calculation;
- HTS classification;
- binding-ruling interpretation;
- customs filing or clearance;
- legal interpretation;
- provider registration or selection;
- runtime integration;
- verification;
- transaction execution.

## Applicable canonical target

The applicable external evidence kind is:

- `ExternalEvidenceKind.REGULATORY`

The single permitted canonical target is:

- `CanonicalProjectionTarget.REGULATORY_EVIDENCE`

The existing projection eligibility contract excludes:

- `currency_rate_evidence`;
- `shipping_route_evidence`;
- `landed_cost_component_evidence`.

Publication of tariff rates, statistical categories, duty-rate columns, or
machine-readable HTS files does not independently authorize projection into a
monetary landed-cost component.

## Registered observations

The dossier records the following bounded observations:

1. USITC publishes the Harmonized Tariff Schedule of the United States.
2. The HTS sets out United States tariff rates and statistical categories.
3. The current schedule supports search, download, and export functions.
4. Current HTS data may be exported in CSV, Excel, and JSON formats.
5. USITC identifies schedules by year and revision.
6. The USITC archive preserves earlier editions and revisions.
7. The HTS is official tariff information rather than a shipment-specific
   landed-cost estimate.
8. The HTS does not by itself determine classification or final customs
   treatment for a shipment.

The dossier retains these dimensions as `unknown` with literal `None`:

- canonical projection compatibility;
- access and security requirements;
- commercial constraints.

The registered observations create no CBP identity, relationship,
verification, acquisition authority, classification decision, or
customs-clearance capability.

## Canonical contract requirements

The canonical `RegulatoryEvidence` target contains:

- `evidence`;
- `provenance`;
- `context`;
- `observation`;
- `jurisdiction`;
- `regulatory_reference`;
- `freshness`.

The contract requires an evidence-bearing state to carry a regulatory
observation.

For an `UNKNOWN` evidence state, the contract prohibits manufacturing an
observation.

The contract does not:

- determine legal permission;
- calculate tariffs or duties;
- classify HS or HTS codes;
- retrieve live regulatory data;
- file customs declarations;
- authorize transaction execution.

## Field-level observation matrix

| Canonical requirement | Registered evidence | Observation |
|---|---|---|
| Regulatory observation | The dossier describes the HTS publication, tariff-rate and statistical-category coverage, revision model, and output formats. | No product-, tariff-line-, measure-, duty-treatment-, restriction-, or transaction-specific result is correlated with an evaluation unit. |
| Jurisdiction | The publication is the Harmonized Tariff Schedule of the United States. | United States schedule coverage is documented, but no context-bound jurisdiction field is correlated with a particular product or result. |
| Regulatory reference | The dossier preserves USITC HTS, download, export, search, and archive references. | Publication URLs and revision identities are provenance; no specific tariff line, legal note, measure, chapter provision, or result reference is registered for projection. |
| Evidence state | Several publication-level dimensions are observed. | Publication-level observations do not supply the mandatory result-level observation needed for an evidence-bearing `RegulatoryEvidence` state. |
| Provenance | USITC source identity, source type, source references, source relationship, and retrieval context are preserved. | Provenance is addressable, but provenance alone cannot construct regulatory evidence. |
| Evaluation context | The HTS generally concerns merchandise imported into the United States. | No exact product, HTS line, origin, destination, shipment, applicable program, date, or request-result correlation is registered. |
| Freshness inputs | The dossier observes year-and-revision labeling and an archive of earlier schedules. | Publication revision evidence exists, but no selected revision is correlated with a particular evaluation result or effective-time requirement. |

## Blocking gaps

### Result-level observation gap

The registered evidence describes the HTS publication and its information
surface. It does not preserve a bounded tariff-line or regulatory result
suitable for the canonical `observation` field.

A publication-level statement must not be transformed into:

- a product classification;
- an applicable tariff line;
- an applicable duty rate;
- an exemption or preference;
- a restriction or permission;
- a binding customs outcome.

### Evaluation-context gap

No exact result is correlated with:

- product identity and composition;
- candidate HTS classification;
- origin country;
- destination and import context;
- valuation facts;
- applicable program or special provision;
- schedule revision and effective date;
- shipment or transaction context.

Without this correlation, no regulatory observation can be attached to the
canonical Cross-Border evaluation context.

### Jurisdiction gap

The United States scope of the HTS is documented.

That general publication scope does not by itself establish a context-bound
jurisdiction assertion for a particular evaluation result.

### Regulatory-reference gap

The registered URLs and revision labels identify publication sources.

They do not establish a specific tariff line, chapter note, general note,
special provision, legal instrument, modification source, or binding result
reference for a particular evaluation unit.

### Temporal and freshness gap

USITC publishes revision-identified schedules and an archive.

No particular revision, effective date, or validity interval is correlated
with a specific product, tariff line, or Commerce AI evaluation result.
Revision availability therefore does not independently satisfy freshness
requirements.

### Machine-readable-format boundary

CSV, Excel, and JSON availability demonstrates exportability.

It does not establish:

- a stable acquisition contract;
- complete schema semantics;
- a field-by-field canonical mapping;
- context correlation;
- binding classification;
- final customs treatment;
- canonical projection compatibility.

Machine readability is not semantic compatibility.

### USITC and CBP authority boundary

The evaluation subject is `candidate:regulatory:usitc-hts`.

The inspected publication authority is USITC. The subject must not be renamed,
aliased, or reinterpreted as `candidate:regulatory:us-cbp-hts`.

References to customs administration or classification practice do not create:

- a CBP subject identity;
- a CBP source relationship;
- CBP verification;
- a binding classification;
- acquisition authority;
- customs-clearance capability.

### Evidence-state constraint

The existing canonical contract permits:

- `UNKNOWN` evidence with no observation; or
- an evidence-bearing state with a mandatory observation.

The registered publication-level evidence does not support manufacturing a
result-level regulatory observation. The compatible conclusion therefore
cannot advance beyond `unknown / None`.

## Non-inference rules

This worksheet does not infer:

- that a search result is a correct classification;
- that an HTS line applies to a product;
- that a stated rate is the final payable duty;
- that special, retaliatory, preferential, quota, or additional duties apply;
- that a tariff treatment is binding;
- that a customs authority will accept a classification;
- that customs clearance will be granted;
- that exported JSON constitutes an API contract;
- that USITC and CBP are the same evaluation subject;
- that publication authority creates customs-execution authority;
- that observed source coverage establishes canonical compatibility.

Publication of tariff material does not establish legal permission, binding
classification, final customs treatment, or transaction authorization.

## Minimum evidence needed for reconsideration

Reconsideration would require subject-specific evidence sufficient to:

1. identify an exact supported result surface and its schema;
2. preserve a bounded regulatory observation;
3. correlate the observation with an exact product and tariff line;
4. preserve origin, destination, valuation, and applicable-program context;
5. identify the applicable schedule revision and effective date;
6. establish context-bound jurisdiction;
7. preserve a specific regulatory reference when claimed;
8. preserve provenance and retrieval timing;
9. provide required freshness inputs when claimed;
10. distinguish publication information from binding customs treatment;
11. define acquisition and reuse boundaries separately;
12. demonstrate that projection manufactures no classification, duty, legal,
    customs, or clearance conclusion;
13. preserve USITC source identity without reinterpreting it as CBP.

These conditions support reconsideration only. They do not authorize
acquisition, implementation, verification, provider selection, or runtime use.

## Projection compatibility decision

### Target-family result

- Target family: `regulatory_evidence`
- Proposed state: `unknown`
- Proposed value: `None`

### Decision basis

The registered evidence establishes official USITC provenance, United States
HTS publication scope, revision-identified schedules, archive availability,
and search and export functions.

It does not establish a result-level regulatory observation correlated with a
complete Commerce AI evaluation context. No particular tariff line,
context-bound jurisdiction, specific regulatory reference, selected effective
revision, or transaction-level result is registered.

The availability of CSV, Excel, and JSON output does not cure these semantic
and correlation gaps.

The mandatory evidence-bearing `RegulatoryEvidence` requirements therefore
remain unsatisfied.

### Overall subject result

Because `regulatory_evidence` is the only applicable canonical target family:

- `canonical_projection_compatibility`: `unknown`
- value: `None`

No dossier mutation is proposed.

## Meaning of the conclusion

The `unknown / None` conclusion records a blocking result-shape, correlation,
regulatory-reference, and temporal-selection gap.

It is not:

- evidence that USITC HTS lacks tariff information;
- evidence that the HTS is inaccurate;
- evidence that machine-readable files are unusable;
- a provider score, grade, or comparison;
- a rejection or adoption decision;
- a tariff classification;
- a duty determination;
- a legal or customs conclusion;
- a statement about CBP authority or capability;
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
- live API or data-download operation;
- credential or network client;
- raw HTS payload;
- adapter or projector;
- canonical evidence construction;
- tariff, duty, or tax calculation;
- HTS classification;
- customs filing or clearance;
- legal interpretation;
- implementation change;
- shipment, payment, or transaction execution;
- CBP subject substitution.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The USITC HTS `canonical_projection_compatibility` record remains `unknown`
with literal `None`.

Because the worksheet proposes the same existing state and value, no later
dossier mutation is implied.
