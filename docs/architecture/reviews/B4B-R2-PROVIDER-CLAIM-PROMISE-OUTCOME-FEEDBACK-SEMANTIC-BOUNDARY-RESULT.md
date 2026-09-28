# B4B-R2 — Provider Claim / Promise / Outcome / Feedback Semantic Boundary Result

## 1. Research Identity and Baseline

Research stream:

`B4-B — Logistics Provider Evidence, SLA & Choice Architecture`

Research stage:

`B4B-R2 — Provider Claim vs Promised SLA vs Observed Performance vs Customer Feedback`

Repository baseline:

`6c71fe2083a96fa5bacdcae3cc00bd0bca641420`

Research mode:

`BOUNDED_SEMANTIC_RESEARCH`

R2 establishes semantic boundaries among:

- Provider Claim
- Promised SLA
- Observed Outcome
- Outcome Attribution
- Customer Provider Feedback
- Provider Performance Evidence

It does not establish production schemas, performance methodology,
provider scoring, ranking, recommendation, selection, or implementation
authority.

---

## 2. R1 Sealed Input

R2 begins from the sealed B4B-R1 result:

`B4B_R1_EXISTING_PROVIDER_SLA_FEEDBACK_EVIDENCE_INVENTORY_ESTABLISHED`

R1 artifact:

`docs/architecture/reviews/B4B-R1-EXISTING-PROVIDER-SLA-FEEDBACK-EVIDENCE-INVENTORY-RESULT.md`

R1 SHA-256:

`d7ee4918d20ef7dec1398fc68bb3bdc553644b82c3f247a175b6a93d6d603809`

The following R1 boundaries remain authoritative:

`Provider Claim != Promised SLA`

`Promised SLA != Observed Outcome`

`Observed Outcome != Provider Performance`

`Provider Performance != Customer Feedback`

`Product Review != Logistics Provider Feedback`

`Performance Evidence != Recommendation`

R2 does not reopen R1.

---

## 3. Exact Selected-Source Boundary

R2 reviewed:

- `app/services/cross_border/shipping.py`
- `app/services/cross_border/observed_route_event_history.py`
- `app/services/cross_border/external_evidence_provider_subject.py`
- `app/services/cross_border/external_evidence_provider_source_relationship.py`
- `app/services/cross_border/external_evidence_provider_evidence.py`
- `app/services/cross_border/external_evidence_provider_evidence_collection.py`
- `app/services/cross_border/external_evidence_provider_dimension_evidence.py`
- `app/services/cross_border/external_evidence_provider_evaluation.py`
- `app/services/cross_border/freshness.py`
- `app/services/cross_border/evidence.py`

Relevant existing tests were used as negative-boundary evidence.

The selected-source boundary does not establish global repository absence
for concepts not found within this scope.

---

## 4. C1 — Provider Claim Boundary

A Provider Claim is a source-attributed assertion concerning a provider,
service, capability, coverage, condition, or other bounded subject.

Existing provider-evaluation evidence supplies reusable foundations for:

- opaque evaluation-subject correlation;
- source-to-subject relationship;
- provenance;
- canonical evidence state;
- source-specific evidence preservation;
- multiple evidence items without forced reconciliation.

Existing source relationships include a subject-supplied relationship and
an internal-observation relationship.

Those relationships do not establish truth, correctness, trust, quality,
score, rank, recommendation, selection, or acquisition authority.

Therefore:

`Provider Claim = Source-Attributed Assertion`

`Provider Claim != Verified Fact`

`Provider Claim != Proven Capability`

`Provider Claim != Promised SLA`

`Provider Claim != Provider Performance`

R2 determination:

`C1_PROVIDER_CLAIM_BOUNDARY = ESTABLISHED`

`C1_EXISTING_FOUNDATION = PARTIAL_REUSABLE`

---

## 5. C2 — Promised SLA Boundary

A Promised SLA is semantically distinct from an estimate.

Existing `ShippingRouteEvidence` preserves:

`estimated_transit_days`

but the exact selected-source review did not establish a canonical
provider-authored or contractually binding SLA/promise/guarantee contract.

Therefore:

`Estimated Transit != Promised SLA`

`Estimated Delivery != Guaranteed Delivery`

`Provider Claim != Contractual Commitment`

A future Promised SLA evidence contract should preserve, where applicable:

- promise issuer/source;
- provider/evaluation-subject correlation;
- service scope;
- promise terms;
- issued/effective time;
- validity/expiry;
- geography;
- pickup/delivery conditions;
- exclusions/exceptions;
- guarantee indicator;
- shipment/request/service correlation;
- provenance.

R2 does not define the production schema for those obligations.

R2 determination:

`C2_PROMISED_SLA_BOUNDARY = ESTABLISHED`

`C2_EXISTING_CANONICAL_CONTRACT = NOT_ESTABLISHED`

<!-- B4B-R2-CHUNK-1-COMPLETE -->

---

## 6. C3 — Observed Outcome Boundary

Existing `ObservedRouteEvent` and `ObservedRouteEventHistory` provide a
strong reusable evidence foundation.

Reusable semantics include:

- reporting source;
- provenance;
- carrier reference;
- tracking number;
- source record reference;
- request correlation reference;
- raw status;
- raw status description;
- occurred time;
- recorded time;
- actor;
- event scope;
- scope reference;
- location;
- event relationships;
- completeness;
- ordering;
- pagination evidence;
- freshness.

These contracts preserve source-reported operational evidence.

They do not by themselves establish normalized delivery state,
provider responsibility, SLA compliance, or provider performance.

Therefore:

`Observed Event != Normalized Delivery State`

`Observed Outcome != Provider Performance`

R2 determination:

`C3_OBSERVED_OUTCOME_BOUNDARY = ESTABLISHED`

`C3_EXISTING_FOUNDATION = STRONG_REUSABLE`

---

## 7. C3-A — Outcome Attribution Boundary

Existing observed-event actor roles include:

- CARRIER
- POSTAL_OPERATOR
- CUSTOMS_AUTHORITY
- FULFILLMENT_PROVIDER
- SHIPPING_AGGREGATOR
- TRACKING_PROVIDER
- FACILITY
- UNKNOWN

This actor separation prevents an observed event from being silently
attributed to a carrier/provider.

A future attribution decision should preserve:

- observed event;
- reporting source;
- actor/reference where supplied;
- actor role where supplied;
- event scope;
- event time;
- location where available;
- provenance;
- attribution evidence;
- attribution uncertainty.

R2 preserves:

`Delay Observed != Carrier Caused Delay`

`Damage Observed != Carrier Caused Damage`

`Delivery Failure != Provider Failure`

`Customs Delay != Carrier SLA Failure`

`Unknown Actor != Provider Actor`

`Observed Outcome != Attribution`

`Attribution != Liability`

R2 does not establish causal-responsibility or liability policy.

R2 determination:

`C3A_ATTRIBUTION_BOUNDARY = ESTABLISHED`

`C3A_ATTRIBUTION_POLICY = UNRESOLVED`

---

## 8. C4 — Customer Provider Feedback Boundary

The selected provider evidence sources did not establish a canonical
logistics-provider-specific customer feedback contract.

Product Recommendation currently contains product rating/review signals.

Those signals are not logistics-provider feedback.

A future provider-feedback evidence class should preserve, where applicable:

- feedback source/customer reference;
- provider/evaluation-subject correlation;
- reported time;
- feedback content/category;
- provenance;
- shipment/service correlation;
- tracking/request correlation;
- experience time;
- structured rating where supplied;
- complaint category;
- satisfaction category;
- supporting artifact;
- verification state;
- uncertainty.

R2 preserves:

`Product Review != Logistics Provider Feedback`

`Customer Feedback != Observed Operational Fact`

`Customer Feedback != SLA Compliance`

`Customer Feedback != Provider Performance`

R2 determination:

`C4_CUSTOMER_FEEDBACK_BOUNDARY = ESTABLISHED`

`C4_EXISTING_PROVIDER_FEEDBACK_CONTRACT = NOT_ESTABLISHED`

<!-- B4B-R2-CHUNK-2-COMPLETE -->

---

## 9. C5 — Provider Performance Evidence Boundary

Provider Performance Evidence is a derived evidence concept.

It must not be equated with one raw event, one provider claim, one SLA,
or one customer review.

Candidate derivation context includes:

- provider/evaluation subject;
- exact performance dimension;
- eligible observation definition;
- observation count;
- observation window;
- service/geographic/unit scope where material;
- source/provenance;
- qualifying observed outcomes;
- exclusions;
- attribution state;
- completeness;
- freshness;
- coverage;
- uncertainty;
- derivation lineage;
- correction/supersession lineage.

The selected source review did not establish canonical provider-performance
methodology, sample-size threshold, observation-window threshold, coverage
threshold, SLA-compliance calculation, or aggregation methodology.

R2 preserves:

`Observed Outcome != Provider Performance`

`Customer Feedback != Provider Performance`

`Performance Evidence != Provider Quality Judgment`

`Performance Evidence != Provider Score`

`Performance Evidence != Provider Rank`

`Performance Evidence != Provider Recommendation`

`Performance Evidence != Provider Selection`

R2 determination:

`C5_PROVIDER_PERFORMANCE_EVIDENCE_BOUNDARY = ESTABLISHED`

`C5_NATURE = DERIVED_EVIDENCE`

---

## 10. Minimum Evidence Obligations

### C1 Provider Claim

Minimum semantic obligations:

- evaluation-subject reference;
- claim source;
- source relationship;
- bounded assertion;
- provenance.

Where material:

- effective time;
- retrieved time;
- geographic/service scope;
- validity;
- supporting source artifact;
- uncertainty.

### C2 Promised SLA

Minimum semantic obligations:

- promise issuer/source;
- subject/provider correlation;
- exact service scope;
- promise terms;
- issued/effective time;
- provenance.

Where material:

- validity/expiry;
- geography;
- conditions;
- exclusions;
- guarantee state;
- request/shipment/service correlation.

### C3 Observed Outcome

Reuse existing observed-event semantics wherever compatible:

- reporting source;
- provenance;
- raw event;
- occurred/recorded time;
- actor;
- scope;
- correlation;
- location;
- relationships;
- completeness;
- freshness.

### C3-A Attribution

Attribution requires explicit evidence beyond outcome existence.

Preserve:

- actor/reference;
- actor role;
- attribution source;
- attribution basis;
- uncertainty.

### C4 Customer Provider Feedback

Preserve:

- feedback source;
- provider/evaluation-subject correlation;
- reported time;
- content/category;
- provenance;
- related shipment/service where available;
- verification state;
- uncertainty.

### C5 Provider Performance Evidence

Preserve:

- performance subject;
- performance dimension;
- eligible observation population;
- observation count;
- observation window;
- scope;
- source/provenance;
- outcome basis;
- exclusions;
- attribution state;
- completeness;
- freshness;
- coverage;
- uncertainty;
- derivation lineage.

R2 does not establish numeric sufficiency thresholds.

---

## 11. Cold-Start Boundary

A new provider may have:

- provider claims;
- capability evidence;
- SLA commitments;
- certification or service evidence;

while having little or no:

- observed history;
- customer feedback;
- derived performance evidence.

Therefore:

`No Historical Evidence != Poor Provider`

`Small Sample != Poor Performance`

`Small Sample != Proven Good Performance`

`Strong SLA != Proven Performance`

`Provider Claim != Proven Capability`

Cold-start uncertainty must remain visible rather than being converted into
a negative or positive performance judgment.

<!-- B4B-R2-CHUNK-3-COMPLETE -->

---

## 12. R2 Core Invariants

R2 establishes:

`Provider Claim != Verified Fact`

`Provider Claim != Promised SLA`

`Estimated Transit != Promised SLA`

`Promised SLA != Observed Outcome`

`Observed Outcome != Attribution`

`Attribution != Liability`

`Observed Outcome != Provider Performance`

`Customer Feedback != Observed Operational Fact`

`Customer Feedback != SLA Compliance`

`Customer Feedback != Provider Performance`

`Performance Evidence != Provider Quality Judgment`

`Performance Evidence != Provider Score`

`Performance Evidence != Provider Rank`

`Performance Evidence != Provider Recommendation`

`Performance Evidence != Provider Selection`

`Missing Evidence != Negative Evidence`

`Small Sample != Poor Performance`

`Small Sample != Proven Good Performance`

---

## 13. R2-U1–U12 Unresolved Dependency Register

### R2-U1 — Provider Claim Exact Content / Schema

Status:

`UNRESOLVED`

Re-entry:

Minimum Architecture Candidate or explicit Provider Claim contract research.

### R2-U2 — SLA Exact Terms / Schema

Status:

`UNRESOLVED`

Re-entry:

Promised-SLA contract research.

### R2-U3 — Promise-to-Outcome Eligibility Rules

Status:

`UNRESOLVED`

Re-entry:

Correlation and eligibility research.

### R2-U4 — Outcome Attribution Policy

Status:

`UNRESOLVED`

Re-entry:

Actor/cause attribution evidence research.

### R2-U5 — Observation Population Definition

Status:

`UNRESOLVED`

Re-entry:

Provider-performance methodology research.

### R2-U6 — Minimum Sample Threshold

Status:

`UNRESOLVED`

Re-entry:

Empirical/statistical methodology research.

### R2-U7 — Observation-Window Threshold

Status:

`UNRESOLVED`

Re-entry:

Provider-performance methodology research.

### R2-U8 — Coverage Sufficiency Threshold

Status:

`UNRESOLVED`

Re-entry:

Evidence-sufficiency methodology research.

### R2-U9 — SLA Compliance Calculation

Status:

`UNRESOLVED`

Re-entry:

Promised SLA and observed-outcome contracts sufficiently established.

### R2-U10 — Provider Feedback Verification

Status:

`UNRESOLVED`

Re-entry:

Provider-specific customer-feedback research.

### R2-U11 — Performance Aggregation Methodology

Status:

`UNRESOLVED`

Re-entry:

R2-U3 through R2-U9 sufficiently resolved.

### R2-U12 — Performance-to-Recommendation Bridge

Status:

`OUT_OF_SCOPE`

Re-entry:

Future Recommendation integration research.

---

## 14. Evidence-Triggered Re-entry Conditions

R2 semantic boundaries should not be reopened merely because another
provider API or data source is discovered.

Re-entry should be triggered by material evidence such as:

- explicit Provider Claim contract candidate;
- explicit SLA/guarantee/commitment contract candidate;
- new operational outcome evidence requiring incompatible semantics;
- causal-attribution model candidate;
- provider-specific customer-feedback contract candidate;
- performance methodology candidate;
- empirical sample/window/coverage methodology;
- future Recommendation integration requirement.

---

## 15. Explicit Non-Claims

This result does NOT establish:

- canonical provider legal identity;
- production Provider Claim schema;
- production SLA schema;
- SLA compliance methodology;
- causal provider responsibility;
- liability;
- minimum sample threshold;
- observation-window threshold;
- coverage sufficiency threshold;
- provider-feedback verification policy;
- provider-performance aggregation methodology;
- provider quality judgment;
- provider score;
- provider rank;
- provider recommendation;
- provider selection;
- production schema;
- implementation authority.

It does not reopen B4-A.

It does not resolve MA-2026-040 U1-U7.

It does not reopen B4B-R1.

---

## 16. R2 Completion Determination

`B4B_R2_WAVE1 = COMPLETE`

`B4B_R2_WAVE2 = COMPLETE`

`B4B_R2_WAVE3 = COMPLETE`

`B4B_R2_WAVE4 = COMPLETE`

`C1_PROVIDER_CLAIM_BOUNDARY = ESTABLISHED`

`C1_EXISTING_FOUNDATION = PARTIAL_REUSABLE`

`C2_PROMISED_SLA_BOUNDARY = ESTABLISHED`

`C2_EXISTING_CANONICAL_CONTRACT = NOT_ESTABLISHED`

`C3_OBSERVED_OUTCOME_BOUNDARY = ESTABLISHED`

`C3_EXISTING_FOUNDATION = STRONG_REUSABLE`

`C3A_ATTRIBUTION_BOUNDARY = ESTABLISHED`

`C3A_ATTRIBUTION_POLICY = UNRESOLVED`

`C4_CUSTOMER_FEEDBACK_BOUNDARY = ESTABLISHED`

`C4_EXISTING_PROVIDER_FEEDBACK_CONTRACT = NOT_ESTABLISHED`

`C5_PROVIDER_PERFORMANCE_EVIDENCE_BOUNDARY = ESTABLISHED`

`C5_NATURE = DERIVED_EVIDENCE`

`R2_U1_TO_U11 = PRESERVED_UNRESOLVED`

`R2_U12 = OUT_OF_SCOPE`

`PROVIDER_SCORE = OUT_OF_SCOPE`

`PROVIDER_RANK = OUT_OF_SCOPE`

`PROVIDER_RECOMMENDATION = OUT_OF_SCOPE`

`PROVIDER_SELECTION = OUT_OF_SCOPE`

`PRODUCTION_SCHEMA = NOT_ESTABLISHED`

`IMPLEMENTATION_AUTHORITY = NONE`

R2 disposition:

`B4B_R2_PROVIDER_CLAIM_PROMISE_OUTCOME_FEEDBACK_SEMANTIC_BOUNDARIES_ESTABLISHED_WITH_PRESERVED_METHODOLOGY_DEPENDENCIES`

---

## 17. Next Research Gate

Next research gate:

`B4B-R3 — SLA & Operational Performance Model`

R3 begins from the R1 and R2 sealed evidence boundaries.

R3 may investigate:

- SLA evidence vocabulary;
- promise-to-outcome eligibility;
- observation population;
- observation window;
- performance dimensions;
- evidence sufficiency;
- uncertainty;
- cold-start treatment.

R3 must not silently establish:

- provider scoring;
- provider ranking;
- provider recommendation;
- provider selection;
- production schema;
- implementation authority.

R3 must preserve:

`Claim != Promise`

`Promise != Outcome`

`Outcome != Attribution`

`Outcome != Performance`

`Feedback != Operational Fact`

`Performance Evidence != Recommendation`

<!-- B4B-R2-CHUNK-4-COMPLETE -->
