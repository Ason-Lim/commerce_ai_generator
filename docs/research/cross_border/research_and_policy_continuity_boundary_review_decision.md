# Cross-Border Research and Policy Continuity Boundary Review Decision

## Decision identity

- Gate: `CB-MAR-2_RESEARCH_AND_POLICY_CONTINUITY_BOUNDARY_REVIEW`
- Parent review: `Cross-Border Master Authority Review`
- Decision status: `ESTABLISHED`
- Repository baseline: `1a39097cf380492016575c9d92bd24cb074fbe35`
- Evidence mode: repository evidence only
- External policy acquisition: `NOT PERFORMED`
- Runtime authority: `NONE`
- Provider-selection authority: `NONE`

## Purpose

This decision records the post-wave Cross-Border policy-continuity boundary.
It classifies only what the sealed repository establishes, distinguishes
subject-level dossier state from target-family state, and selects one bounded
candidate for the next lifecycle.

This decision does not acquire external policy evidence, amend the provider
dossier, change a canonical model, authorize an adapter or projector, rank or
select a provider, or activate production runtime behavior.

## Sealed baseline preserved

The integrated observed-route-event-history provider wave remains:

- `COMPLETE / SEALED`;
- ShipStation V2: `COMPLETE / SEALED`;
- MyDHL API observed-route-event-history: `COMPLETE / SEALED`;
- TracX SmartShip: `COMPLETE / SEALED`;
- Korea Post EMS: `STOP / DEFERRED / SEALED`.

The completion tag remains:

`cross-border-observed-route-event-history-integrated-wave-completed-v1.0`

- tag object: `b57dfdb3cb4285a000f255c118ec74a4e32e3918`;
- tag target: `1a39097cf380492016575c9d92bd24cb074fbe35`.

Nothing in this decision reopens or extends that completed lifecycle.

## Authoritative repository classification

### Established adjacent contracts

The repository establishes:

- `origin_country` and `destination_country` in the Cross-Border evaluation
  context;
- source identity and source reference through `EvidenceProvenance`;
- generic `retrieved_at` and `effective_at` provenance time;
- regulatory `jurisdiction` and bounded destination-country applicability;
- landed-cost evidence-bearing and evidence-absent states;
- the invariant that `UNKNOWN` and `UNAVAILABLE` are not zero;
- preservation of an explicitly observed numeric zero as evidence-bearing
  zero;
- `ESTIMATED` as a bounded monetary evidence state;
- a separate estimate explanation without converting it into a confidence
  contract.

These contracts are adjacent inputs. They do not by themselves establish a
shipment-specific tariff, duty, tax, customs, or legal result.

### UPS and Zonos current dossier state

The current sealed dossier records:

- `cb-ea3b1-ups-006`: `canonical_projection_compatibility = observed`;
- `cb-ea3b1-zonos-006`: `canonical_projection_compatibility = observed`.

The earlier worksheet wording that each dossier record would remain
`unknown / None` until a later exact-scope mutation describes the boundary at
the time of worksheet creation. The current dossier is authoritative because
the later mutations were completed.

These `observed` states remain documentation-level prospective compatibility.
They do not establish live-response conformance, verified charges, final
customs treatment, provider selection, or runtime authority.

### MyDHL mixed-capability boundary

The current subject-level MyDHL dossier record
`cb-ea3b1-mydhl-006` is `observed` because the bounded
`observed_route_event_history` target family was admitted and implemented.

The separate MyDHL `landed_cost_component_evidence` worksheet remains:

- target-family state: `unknown`;
- accepted value: `None`.

Therefore, subject-level `observed` must not be interpreted as universal
compatibility across all target families. MyDHL landed-cost compatibility is
not established by the observed-route-event-history result.

Any future evidence registry or admission contract must preserve target-family
identity so that one observed capability cannot silently authorize another.

### Regulatory projection state

The current sealed dossier retains `unknown / None` for
`canonical_projection_compatibility` of:

- GOV.UK Trade Tariff API;
- EU Access2Markets;
- Korea Customs Service UNI-PASS;
- USITC HTS.

Their official-source identity or broad coverage does not establish a bounded,
correlated shipment-level regulatory result. No tariff, duty, tax,
classification, customs, or legal conclusion is inferred.

## Exact policy-continuity gaps

### Repository evidence missing

The inspected repository contains no registered Cross-Border policy identity
for a United States low-value commercial-shipment rule or a dated rule change.
It contains no direct repository match for a `USD 800` default or a de minimis
policy rule.

This absence has two distinct meanings:

1. no stale automatic `USD 800` duty-free default was found in the inspected
   Cross-Border code, tests, or research documents; and
2. the current United States low-value commercial-shipment policy is not yet
   registered as repository evidence.

The second point is `MISSING`, not a factual inference about the policy itself.

### Direct contract gaps

The inspected repository does not establish direct named contracts for:

- `DDP`, `DDU`, `DAP`, or an Incoterm identity;
- policy-rule version identity;
- a policy-specific validity interval distinct from generic evidence
  provenance time;
- a policy-specific baseline and regression contract;
- policy-specific shadow evaluation.

HS or HTS concepts appear in regulatory research and provider documentation,
but the current regulatory contract explicitly does not classify HS codes or
calculate tariffs or duties. A future lifecycle must separately determine the
required classification-input identity and its evidence boundary.

Shipping-route evidence exists as a separate contract family. No automatic
binding from a route observation to a policy rule or landed-cost result is
authorized here.

### Confidence boundary

The current landed-cost contract intentionally does not expose `confidence` or
`confidence_score`. An estimate reason is an explanation, not a confidence
contract.

The request to preserve confidence is therefore a proposed future contract
question, not an already established canonical field. This decision neither
adds confidence nor infers it from source identity, estimate wording, or
provider guarantees.

## Inference and admission separation

Repository evidence and canonical admission remain separate.

- External or AI-generated research may propose a field or rule.
- A proposal does not mutate the dossier or canonical model.
- Subject-level compatibility does not authorize a different target family.
- Missing evidence remains `unknown / None` or `MISSING`, as applicable.
- Numeric zero is observed evidence only when a source explicitly supplies it.
- A rule, charge, or exemption must never be manufactured from absence.

The named external research candidates CVE-SAI, CRRN, RecVerse, SaFaRi, AP2,
DREAM, and SR-Agent were not found in the inspected repository scope. They
remain external `Research-Grounded Architecture Candidate` inputs only and
receive no admission or implementation authority from this decision.

## Next lifecycle selection

Exactly one next-lifecycle candidate is selected:

`US_LOW_VALUE_COMMERCIAL_SHIPMENT_POLICY_EVIDENCE_REGISTRATION`

Its permitted subject is limited to official, time-bound policy evidence for
United States low-value commercial shipments relevant to Cross-Border landed
cost and regulatory evaluation.

The selected lifecycle must begin with a separate read-only source-identity and
scope preflight. It must preserve:

- issuing authority;
- official source reference;
- rule identity;
- publication, effective, suspension, replacement, or validity time when
  directly established;
- shipment channel or mode scope;
- destination jurisdiction;
- value threshold only when directly established;
- applicable duty, tax, fee, entry, or exemption treatment only as directly
  stated;
- `VERIFIED`, `PARTIALLY VERIFIED`, `REPORTED`, or `MISSING` evidence status;
- distinction between source facts, project interpretation, and canonical
  admission.

## Authority granted and withheld

This decision grants only:

- selection of the named next-lifecycle candidate; and
- authority to prepare its separate read-only source-identity and scope
  preflight after this decision is committed and sealed.

This decision withholds:

- automatic lifecycle opening;
- network evidence acquisition;
- new evidence registration;
- dossier mutation;
- canonical model mutation;
- policy-rule implementation;
- landed-cost adapter or projector implementation;
- package export or registry participation;
- credential use;
- persistence or serialization;
- provider ranking or selection;
- production runtime activation.

## Decision result

- master policy-continuity classification: `ESTABLISHED`;
- integrated observed-event wave: `UNCHANGED / COMPLETE / SEALED`;
- UPS projection dossier: `OBSERVED`;
- Zonos projection dossier: `OBSERVED`;
- MyDHL subject dossier: `OBSERVED — ROUTE-EVENT-HISTORY BOUNDED`;
- MyDHL landed-cost target family: `UNKNOWN / None`;
- four regulatory projections: `UNKNOWN / None`;
- automatic `USD 800` duty-free default in inspected scope: `NOT FOUND`;
- current US low-value policy repository evidence: `MISSING`;
- trade-term contract: `MISSING`;
- policy-rule version contract: `MISSING`;
- policy-specific shadow evaluation: `MISSING`;
- next lifecycle candidate: `SELECTED / NOT OPENED`;
- repository implementation authority: `NONE`;
- production runtime authority: `NONE`.

The next permissible operation is the exact single-artifact write and
validation sequence for this decision. No external policy evidence lifecycle
may begin until this decision is separately committed, sealed, and synchronized.
