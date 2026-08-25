# Canonical Projection Compatibility Protocol Application Review

## Review identity

- Step: `CB-EA4D-1`
- Reviewed protocol: `CB-EA4A-2`
- Review type: `non-comparative application consistency review`
- Reviewed target family: `currency_rate_evidence`
- Runtime authority: `None`
- Acquisition authority: `None`
- Adapter authority: `None`
- Projector authority: `None`
- Verification authority: `None`
- Provider-selection authority: `None`
- Protocol-mutation authority: `None`
- Dossier-mutation authority: `None`

## Purpose

This review examines whether the sealed canonical projection compatibility
observation protocol was applied consistently in two independently authorized
subject-local worksheets.

The review evaluates the protocol application method. It does not evaluate,
rank, compare, recommend, approve, reject, or select an evaluation subject.

A difference between subject-local conclusions is considered only to determine
whether the protocol responded consistently to different documented evidence
conditions.

## Sealed reviewed artifacts

| artifact | sealed identity |
|---|---|
| Internal observation protocol | `265eafad06133a87656771eabe5143d160afb7988f482bbc3ad0cf00d85555ee` |
| Frankfurter v2 worksheet | `522358ced30e0676f6d90e7a4024ec6f9854cd377cd41ffc8a4990cc63aae6ad` |
| ECB Data API worksheet | `c313fb4aa97d5e5304e45b9d60e6ee8a82f489a42128ede9ffbbc1ea4b0fef7c` |
| External provider evaluation dossier | `cf539cbea42d2a93906e1dae8d0a4021c6e7eb6f7cfcd62745b7c7cb024b0aa7` |

The sealed artifacts remain authoritative for their own scopes. This review
does not replace or amend them.

## Review boundaries

This review contains no:

- provider comparison;
- compatibility score;
- weight;
- rank;
- provider preference;
- recommendation;
- selection;
- verification;
- runtime authorization;
- acquisition authorization;
- adapter authorization;
- projector authorization;
- network client;
- credential;
- live data call;
- raw payload storage;
- runtime import;
- package-level public export.

The review remains research documentation only.

## Review method

The review inspected the following protocol controls:

1. observation-unit isolation;
2. sealed-source registration;
3. preservation of source relationship;
4. separation of documented subject output from Commerce AI envelope
   authority;
5. field-by-field mapping to the canonical target;
6. preservation of rate direction;
7. mandatory positive finite rate support;
8. evidence-state semantic separation;
9. provenance, context, and temporal-input handling;
10. unresolved-gap classification;
11. observed-versus-unknown decision rules;
12. verification, runtime, and provider-selection boundaries;
13. dossier count and state preservation.

Each worksheet was evaluated against those controls independently.

## Observation-unit isolation review

The protocol defines the observation unit as:

`evaluation subject × canonical target family`

Both reviewed worksheets used one subject and the same single canonical target
family, `currency_rate_evidence`.

Neither worksheet generalized its conclusion to another subject or another
target family.

Conclusion:

`PASS`

## Registered-source and relationship review

Each worksheet cited only sources registered in the sealed dossier at the time
of its authorized application.

Each source retained the relationship:

`subject_supplied`

Neither worksheet treated subject-supplied material as independent
verification, correctness, trust, entitlement, or authority.

Conclusion:

`PASS`

## Two-layer authority review

Both worksheets distinguished:

- Layer A: documented subject output shape;
- Layer B: Commerce AI internal envelope authority.

Both retained Commerce AI authority over:

- `CurrencyPair`;
- `CrossBorderEvidence`;
- `EvidenceState`;
- `EvidenceProvenance`;
- `CrossBorderEvaluationContext`;
- `EvidenceFreshness`;
- `CurrencyRateEvidence`.

Neither worksheet treated a subject field as authorization to construct
canonical evidence or assign runtime evidence state.

Conclusion:

`PASS`

## Currency-direction review

The canonical direction remains:

`1 base_currency = rate quote_currency`

The Frankfurter worksheet preserved the documented `base` and `quote`
direction without inversion.

The ECB worksheet did not copy the ordered SDMX key positionally. It mapped:

- `CURRENCY_DENOM` to `base_currency`;
- `CURRENCY` to `quote_currency`;
- `OBS_VALUE` to the prospective rate value.

It preserved the documented semantic direction:

`1 CURRENCY_DENOM = OBS_VALUE CURRENCY`

Neither worksheet assumed or calculated an inverse rate.

Conclusion:

`PASS`

## Positive finite invariant review

The canonical `CurrencyRateEvidence` contract rejects:

- zero;
- negative values;
- `NaN`;
- positive or negative infinity;
- invalid decimal values.

The protocol therefore correctly requires documented support for a positive
finite rate before an evidence-bearing prospective construction can support an
`observed` compatibility conclusion.

One subject-local worksheet recorded explicit documented support for a
positive numeric rate.

The other subject-local worksheet recorded a documented rate-value field but
no registered documentation establishing the mandatory positive finite
constraint across applicable documented outputs.

The protocol produced different subject-local conclusions because the
documented invariant support differed. It did not produce the difference from
a provider score, preference, comparison, or selection rule.

A sample positive value does not establish a universal output constraint.

Ordinary domain expectations about exchange rates do not replace inspected
documentation.

Commerce AI decimal validation may reject an invalid future input, but that
validation does not establish a missing subject documentation guarantee.

Conclusion:

`PASS — retain the positive finite requirement`

## Evidence-state semantic review

Both worksheets retained `EvidenceState` as Commerce AI internal authority.

The ECB worksheet explicitly separated `OBS_STATUS`, a statistical
observation-status attribute, from Commerce AI `EvidenceState`.

No subject field was copied directly into canonical evidence state.

Conclusion:

`PASS`

## Provenance and evaluation-context review

Both worksheets identified prospective provenance inputs without constructing
runtime provenance.

Both retained `CrossBorderEvaluationContext` as an independently supplied
Commerce AI evaluation input.

Neither worksheet manufactured evaluation context from a subject response.

Conclusion:

`PASS`

## Temporal and freshness review

Both worksheets identified date or period information but did not manufacture
a timezone-aware timestamp.

Both left freshness absent or unknown because the inspected temporal evidence
did not independently support the existing freshness evaluator.

Freshness is optional in `CurrencyRateEvidence`; its unresolved status was
therefore treated as non-blocking where all mandatory invariants otherwise had
documented support.

Conclusion:

`PASS`

## Observed decision-rule review

The protocol permits an `observed` conclusion only when:

- the target family is unambiguous;
- the relevant output shape is documented;
- every mandatory invariant has documented or authorized internal-envelope
  support;
- state and value semantics do not manufacture evidence;
- transformations are bounded;
- unresolved gaps do not block prospective canonical construction;
- the conclusion remains subject-local and non-comparative.

The worksheet proposing `observed` documented each mandatory rate-shape
invariant and classified freshness as an optional unresolved limitation.

Its proposed value remained factual, bounded, subject-local, non-comparative,
and free of adoption or runtime-readiness language.

Conclusion:

`PASS`

## Unknown decision-rule review

The protocol requires:

- state: `unknown`;
- observation value: `None`;

when any required condition is unsupported, ambiguous, contradictory, or
dependent on uninspected documentation.

The worksheet proposing `unknown` identified the blocking documentation gap
outside the observation value and preserved literal `None`.

It did not replace unknown with zero, false, empty text, a sample-derived
assumption, or a synthetic compatibility result.

Conclusion:

`PASS`

## Verification-boundary review

Neither application produced or proposed `verified`.

Both retained:

- Verification authority: `None`;
- Runtime authority: `None`;
- Acquisition authority: `None`;
- Adapter authority: `None`;
- Projector authority: `None`;
- Provider-selection authority: `None`.

Conclusion:

`PASS`

## Dossier preservation review

The sealed dossier contains:

- evaluation subjects: `11`;
- canonical dimensions per subject: `9`;
- total evidence records: `99`;
- observed records: `59`;
- unknown records: `40`;
- verified records: `0`;
- canonical projection compatibility records: `11`;
- compatibility observed: `1`;
- compatibility unknown: `10`;
- compatibility verified: `0`.

The ECB compatibility record remains:

- state: `unknown`;
- observation value: `None`.

This review does not authorize a dossier mutation.

Conclusion:

`PASS`

## Protocol consistency finding

The protocol demonstrated consistent decision behavior across a simple
documented output shape and a more complex SDMX documentation shape.

The different subject-local conclusions are traceable to whether the
registered inspected documentation supported every mandatory canonical
invariant.

The difference is not evidence of provider quality, accuracy, trust,
preference, suitability, or selection.

Overall finding:

`APPLICATION CONSISTENCY OBSERVED`

This phrase describes the reviewed method only. It is not a verification state
and must not be projected into the external provider evaluation dossier.

## Positive finite requirement decision

Decision:

`RETAIN`

Rationale:

- it is an enforced canonical invariant;
- relaxing it would permit a documented field name to stand in for required
  value semantics;
- runtime rejection cannot substitute for documentation sufficiency;
- examples cannot establish a universal constraint;
- retaining it preserves the distinction between prospective construction and
  manufacturing evidence.

This review creates no new transformation rule and no runtime behavior.

## Protocol revision decision

Decision:

`NO REVISION REQUIRED`

The sealed protocol already distinguishes:

- mandatory from optional inputs;
- documented subject shape from internal envelope authority;
- observed from unknown;
- observation from verification;
- research conclusions from runtime and provider-selection authority.

A future clarification may be separately proposed if repeated applications
show ambiguity about what qualifies as documented value-domain support.

This review does not authorize or implement that clarification.

## Dossier mutation decision

Decision:

`NO MUTATION`

The existing dossier states and counts remain unchanged.

The Frankfurter record remains the single observed compatibility record.

The ECB record remains `unknown` with literal `None`.

This statement preserves existing sealed state. It does not compare, prefer, or
select either evaluation subject.

## Next architecture gate

Further subject application remains separately authorized per observation
unit.

Before another application:

1. confirm that the subject sources are already registered;
2. identify the applicable canonical target family;
3. inspect mandatory target invariants;
4. create one subject-local worksheet;
5. preserve source relationship and authority boundaries;
6. keep the dossier unchanged until a worksheet is reviewed, committed, and
   sealed;
7. authorize any later dossier mutation separately.

No adapter, projector, acquisition runtime, provider scoring, comparison, or
selection follows from this review.

## Final boundary statement

This review establishes only that the sealed protocol behaved consistently in
the two reviewed subject-local applications.

It does not establish:

- subject equivalence;
- subject superiority;
- provider compatibility verification;
- provider quality;
- provider accuracy;
- provider trust;
- provider adoption;
- provider recommendation;
- provider selection;
- production readiness;
- runtime authority.
