# IPR-EXPERIENCE-2026-001

## Integration Verification Request

**Project:** Commerce AI Generator
**Architecture Program:** MA-2026-033
**Architecture:** Experience Architecture
**Verification Authority:** 99 Integration Verification Authority
**Document Type:** Integration Verification Request
**Document ID:** IPR-EXPERIENCE-2026-001
**Status:** REQUESTED

---

# 1. Request Purpose

This document formally requests independent Integration Verification for
MA-2026-033 Experience Architecture.

The Master Architecture lifecycle has completed.

The purpose of this request is to verify that the approved canonical
architecture is correctly integrated into the repository and runtime
execution paths without reopening architecture ownership or redesigning
approved semantics.

---

# 2. Governing Architecture Chain

The governing architecture lifecycle is:

```text
ADA-MA-2026-033-EXPERIENCE-ARCHITECTURE
        ->
AVCR-MA-2026-033-EXPERIENCE-ARCHITECTURE
        ->
MACR-MA-2026-033-EXPERIENCE-ARCHITECTURE
        ->
DHN-MA-2026-033-EXPERIENCE-ARCHITECTURE
        ->
99 Integration Verification Authority
```

All preceding architecture governance stages are complete.

---

# 3. Architecture Verification Approval

Architecture Verification Completion Review:

```text
AVCR-MA-2026-033-EXPERIENCE-ARCHITECTURE
```

Decision:

```text
APPROVED
```

Authoritative commit:

```text
58c5e2fd4eb481ba3c6f86f5df968d14cd92a13f
```

Completion tag:

```text
avcr-ma-2026-033-experience-architecture-approved-v1.0
```

The completion tag was verified against the remote repository.

---

# 4. Master Architecture Completion Approval

Master Architecture Completion Review:

```text
MACR-MA-2026-033-EXPERIENCE-ARCHITECTURE
```

Decision:

```text
APPROVED
```

Authoritative commit:

```text
403d7b4f12e6f1b9b35027ffe643e0db085a39e2
```

Completion tag:

```text
macr-ma-2026-033-experience-architecture-approved-v1.0
```

The completion tag was verified against the remote repository.

---

# 5. Design Handoff Approval

Design Handoff Notice:

```text
DHN-MA-2026-033-EXPERIENCE-ARCHITECTURE
```

Handoff status:

```text
APPROVED
```

Authoritative commit:

```text
d426599150b9cec447f62ad8135036be44e1bc58
```

Completion tag:

```text
dhn-ma-2026-033-experience-architecture-handoff-approved-v1.0
```

The DHN completion tag was verified against the remote repository.

---

# 6. Implementation Verification Baseline

The completed implementation baseline is:

```text
5639628621c6e6d5bab63a73e7d0ced712f11362
```

The baseline is sealed by:

```text
ma-2026-033-phase2h-complete-v1.0
```

Subsequent AVCR, MACR, and DHN commits are architecture governance
documentation commits and do not reopen the implementation lifecycle.

---

# 7. Canonical Experience Architecture

The canonical Experience Architecture is established under:

```text
app/services/experience/
```

Primary boundaries include:

```text
comparison.py
revisit.py
tracking.py
```

Integration Verification should confirm that these modules are
importable, operational, and correctly consumed by their intended
runtime and presentation paths.

---

# 8. Preference Canonical Authority

Canonical Preference authority is established under:

```text
app/services/preference/
```

Expected canonical components include:

```text
__init__.py
models.py
policy.py
service.py
store.py
```

Integration Verification should confirm:

* canonical import resolution,
* canonical service ownership,
* policy ownership,
* consumer integration,
* absence of superseded production ownership.

---

# 9. Session Context Canonical Authority

Canonical Session Context authority is established under:

```text
app/services/session_context/
```

Expected canonical components include:

```text
__init__.py
models.py
policy.py
service.py
store.py
```

Integration Verification should independently confirm:

* canonical read authority,
* canonical write authority,
* canonical policy authority,
* analytics consumer integration,
* main runtime consumer integration,
* absence of retired legacy authority.

---

# 10. Generator Canonical Execution

Generator execution is expected to resolve through canonical
Recommendation authority.

Relevant components include:

```text
app/services/generator_service.py
app/services/generator_compatibility.py
app/services/recommendation/provider.py
```

Integration Verification should confirm that compatibility behavior does
not reclaim canonical Recommendation execution ownership.

---

# 11. Recommendation Canonical Authorities

The relevant canonical Recommendation authorities are:

```text
app/services/recommendation/provider.py
app/services/recommendation/scoring.py
app/services/recommendation/ranking.py
app/services/recommendation/deduplication.py
app/services/recommendation/platform_normalization.py
```

Integration Verification should confirm:

1. RecommendationProvider is the execution/orchestration authority.
2. Canonical scoring resolves through Recommendation scoring.
3. Canonical ranking resolves through Recommendation ranking.
4. Candidate deduplication resolves through canonical Recommendation
   deduplication.
5. Platform normalization resolves through canonical Recommendation
   platform normalization.

---

# 12. Retired Legacy Responsibilities

The following legacy Recommendation support responsibilities were
retired during MA-2026-033:

```text
Legacy AI Ranking Engine V8

Legacy Deduplication Engine V8.1
Legacy Deduplication Engine V8.2
Legacy Deduplication Engine V8.3

Legacy Platform Normalizer V8.4
```

Integration Verification should confirm that these retired authorities
are absent from active production execution paths.

Historical test assertions or documentation references must not be
treated as active runtime consumers.

---

# 13. Active Compatibility Surfaces

The architecture closure review classified the following as active
compatibility or presentation surfaces:

```text
recommendation_score_v8
recommendation_story_engine_v61
recommendation_compare_engine_v62
```

These are not unresolved Class A architecture blockers.

Integration Verification should confirm that these surfaces do not
replace the approved canonical Recommendation execution authority.

---

# 14. Adjacent Authority Protection

Integration Verification must preserve adjacent architecture
boundaries.

## Recommendation Engine

Recommendation semantics remain under Recommendation authority.

## Marketplace Core

Marketplace normalization and marketplace-level deduplication remain
independent from Experience ownership.

## Market Intelligence

Market collection and market evidence remain outside Experience semantic
ownership.

## Food Intelligence / Food Knowledge

Food Intelligence and Food Knowledge remain independent canonical
authorities.

The integration review must validate these boundaries rather than merge
or redesign them.

---

# 15. Required Integration Verification Scope

The requested Integration Verification scope includes:

## A. Registration and Import Resolution

Verify that canonical Experience, Preference, Session Context,
Generator, and Recommendation authorities import successfully and
resolve to the intended implementations.

## B. Runtime Execution

Verify representative runtime execution paths through:

* Experience comparison,
* Experience revisit,
* Experience tracking composition,
* Preference consumption,
* Session Context consumption,
* Generator execution,
* RecommendationProvider execution.

## C. Result Contract Verification

Verify that canonical result contracts and compatibility boundaries
remain consistent with approved runtime behavior.

## D. Canonical Authority Resolution

Verify that runtime consumers resolve the canonical authority rather
than retired legacy implementations.

## E. Legacy Retirement Verification

Verify absence of retired legacy Recommendation support modules from
active production execution paths.

## F. Adjacent Boundary Verification

Verify that Marketplace Core, Market Intelligence, and Food Intelligence
authorities remain independently owned.

## G. Regression Verification

Execute the approved major regression suites.

## H. Repository Integrity

Verify compile integrity, diff integrity, repository status, and
authoritative baseline consistency.

---

# 16. Expected Regression Baseline

Architecture verification previously confirmed:

```text
Experience                39 passed
Preference                33 passed
Session Context            27 passed
Generator                   28 passed
Recommendation + Market   418 passed
```

Integration Verification should independently rerun the relevant suites.

A changed test count does not automatically constitute failure if the
change is explained by subsequently added verification tests.

Any functional regression or architecture ownership conflict must be
reported.

---

# 17. Minimum Verification Commands

The Integration Verification Authority is requested to independently
execute at minimum:

```text
python -m pytest -q tests/services/experience
python -m pytest -q tests/services/preference
python -m pytest -q tests/services/session_context
python -m pytest -q tests/services/generator
python -m pytest -q tests/services/recommendation tests/services/market

python -m compileall -q app tests

git diff --check
git status --short
```

Additional independent probes are authorized where necessary to verify
runtime authority resolution.

---

# 18. Verification Baseline Chain

The authoritative chain submitted for verification is:

```text
Implementation Baseline
5639628621c6e6d5bab63a73e7d0ced712f11362

AVCR
58c5e2fd4eb481ba3c6f86f5df968d14cd92a13f

MACR
403d7b4f12e6f1b9b35027ffe643e0db085a39e2

DHN
d426599150b9cec447f62ad8135036be44e1bc58
```

Current repository main at handoff should resolve to the DHN-approved
state or a later authorized verification-document-only state.

---

# 19. Verification Evidence Requested

The 99 Integration Verification Authority is requested to return
independent evidence covering:

```text
IPR
Integration Verification Request

IPS
Integration Preparation / Scope confirmation

IRC
Integration Registration / Canonical authority confirmation

IRR
Integration Runtime Review

IRG
Integration Regression Gate

IVC
Integration Verification Completion
```

Equivalent evidence records may be used where the current Integration
Verification process defines a more specific canonical document set.

---

# 20. Integration Verification Decision Requested

The requested final decision is one of:

```text
PASS
PASS WITH OBSERVATIONS
FAIL
```

A PASS decision should confirm that MA-2026-033 is correctly integrated
without reopening Master Architecture implementation.

A PASS WITH OBSERVATIONS decision should distinguish non-blocking
architecture observations from integration defects.

A FAIL decision should identify the exact violated canonical contract,
runtime path, regression, or ownership boundary.

---

# 21. Architecture Reopening Rule

Integration Verification must not modify architecture merely to make a
verification test pass.

If an architecture-level defect is discovered, verification should:

```text
Detect
    ->
Record Evidence
    ->
Classify
    ->
Return to Architecture Governance
```

rather than silently redesigning canonical authority.

---

# 22. Submission Decision

```text
INTEGRATION VERIFICATION REQUEST

Architecture Program:
MA-2026-033

Architecture:
Experience Architecture

Request Status:
SUBMITTED

Architecture Verification:
APPROVED

Master Architecture Completion:
APPROVED

Design Handoff:
APPROVED

Class A Closure Blockers:
0

Implementation Reopening Required:
NO

Destination:
99 Integration Verification Authority

Independent Integration Verification:
REQUESTED
```

---

# 23. Requested Next Action

99 Integration Verification Authority is requested to begin independent
verification of MA-2026-033 Experience Architecture using this IPR, the
approved DHN, the approved MACR, and the approved AVCR as governing
evidence.

No additional implementation work is authorized by this request.

---

**Document ID:** IPR-EXPERIENCE-2026-001
**Architecture Program:** MA-2026-033
**Architecture:** Experience Architecture
**Request Status:** SUBMITTED
**Destination:** 99 Integration Verification Authority
