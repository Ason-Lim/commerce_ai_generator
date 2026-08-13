# Provider Selection Verification Request

## IPS-SEAFOOD-2026-001

**Title**

Independent Provider Selection Verification Request for the Seafood Knowledge Domain

---

# Document Identity

| Item | Value |
|---|---|
| Document ID | IPS-SEAFOOD-2026-001 |
| Requesting Authority | Seafood Domain Development |
| Receiving Authority | 99_Integration Verification Authority |
| Project | Commerce AI Generator |
| Domain | 20_Seafood |
| Verification Phase | Sprint 3 |
| Verification Type | Provider Selection Verification |
| Status | OFFICIAL REQUEST |

---

# 1. Purpose

This document officially requests independent Provider Selection Verification for the Seafood Knowledge Domain.

The preceding Provider Registration Verification has completed under:

~~~text
IPR-SEAFOOD-2026-001
~~~

with the official decision:

~~~text
PASS WITH ARCHITECTURE OBSERVATION
~~~

The recognized non-blocking observation is:

~~~text
AO-SEAFOOD-2026-001
Historical Provider Membership Expectation Drift
~~~

The purpose of this IPS phase is to independently determine whether the shared Food Knowledge runtime selects the Seafood provider correctly for supported Seafood product names while preserving provider selection behavior for existing domains.

This request does not assert the outcome of the IPS verification.

---

# 2. Governing Evidence

The requested verification follows the current Sprint 3 evidence chain:

~~~text
ADA-MA-2026-019-SEAFOOD
        ↓
Seafood Domain Implementation
        ↓
IVR-SEAFOOD-2026-001
        ↓
IPR-SEAFOOD-2026-001
        ↓
Provider Registration Verification
PASS WITH ARCHITECTURE OBSERVATION
        ↓
IPS-SEAFOOD-2026-001
~~~

Relevant principles include:

- Evidence First Principle
- Progressive Maturity Model
- Sprint 3 Domain Completion Governance
- Shared Food Knowledge Registry Contract
- Provider Selection Preservation
- Independent Integration Verification

---

# 3. Verification Scope

The independent IPS verification is requested to cover:

1. Seafood provider selection
2. Direct Food Knowledge Registry resolution
3. Shared resolver selection
4. Agreement between direct and shared provider resolution
5. Supported Seafood alias selection
6. Representative legacy-domain selection preservation
7. Undeclared Seafood alias boundary preservation
8. Seafood domain regression safety
9. Compilation safety

The verification is specifically concerned with provider selection behavior.

Result Contract Verification and later integration phases remain outside the decision scope of this request.

---

# 4. Seafood Positive Selection Cases

The following representative product names are requested as positive Seafood provider-selection cases:

~~~text
노르웨이 연어
고등어
참치
새우
꽃게
전복
오징어
~~~

For each case, independent verification should evaluate both:

~~~text
resolve_food_provider(...)
~~~

and:

~~~text
resolve_knowledge_provider(...)
~~~

Expected provider:

~~~text
seafood
~~~

The direct registry resolver and shared resolver should agree on the selected provider.

---

# 5. Legacy Provider Selection Preservation

Provider selection for representative pre-existing domains must remain unchanged.

Requested representative cases include:

| Product | Expected Provider |
|---|---|
| 고당도 사과 | fruit |
| 양배추 | vegetable |
| 브리 치즈 | cheese |
| 예가체프 원두 | coffee |
| 프랑스 레드 와인 | wine |
| 제주 녹차 | tea |
| 엑스트라 버진 올리브 오일 | olive_oil |
| 바질 | herb_spice |
| 한우 등심 | beef |
| 프리미엄 도퍼 어린양 프렌치랙 | lamb |
| 토종닭 | chicken |
| 훈제오리 | duck |

For each representative product, the direct provider resolver and shared resolver should select the same expected pre-existing provider.

Seafood registration must not capture unrelated products belonging to existing domains.

---

# 6. Undeclared Seafood Alias Boundary

The preceding IPR verification established that the following names are not currently declared positive aliases of `SeafoodKnowledgeProvider`:

~~~text
광어
넙치
~~~

Related examples include:

~~~text
광어
국산 광어
광어회
넙치
국산 넙치
~~~

These cases must not be treated as positive Seafood assertions during the current IPS verification.

The requested boundary assertion is:

~~~text
Seafood provider must not be selected
solely on the assumption that these
undeclared aliases belong to the current
Seafood provider contract.
~~~

This boundary requirement preserves the actual runtime contract verified during IPR.

Failure to select Seafood for these undeclared aliases must not, by itself, be classified as a Seafood implementation defect.

Expansion of the Seafood alias contract remains outside this IPS verification scope.

---

# 7. Direct and Shared Resolver Agreement

For every positive Seafood case and representative legacy case, verification should compare:

~~~text
Direct Resolver
resolve_food_provider(...)

Shared Resolver
resolve_knowledge_provider(...)
~~~

The requested invariant is:

~~~text
DIRECT PROVIDER
==
SHARED PROVIDER
==
EXPECTED PROVIDER
~~~

Any disagreement must be independently investigated before an IPS PASS decision is issued.

---

# 8. Compilation and Domain Safety

The IPS verification should also confirm that provider-selection behavior is not accompanied by compilation or Seafood-domain regression failures.

Requested safety checks:

~~~text
python -m compileall -q app
~~~

and:

~~~text
pytest tests/services/food/knowledge/seafood -q
~~~

These checks provide supporting evidence only.

The final IPS decision remains the responsibility of 99_Integration Verification Authority.

---

# 9. Architecture Observation Preservation

The existing Architecture Observation remains:

~~~text
AO-SEAFOOD-2026-001
Historical Provider Membership Expectation Drift
~~~

Its IPR classification is:

~~~text
NON-BLOCKING
~~~

The IPS verification should not automatically propagate historical provider-membership expectation failures into a provider-selection failure.

If new provider-selection defects are observed, they must be separately identified and attributed based on runtime evidence.

---

# 10. Requested Verification Matrix

99_Integration Verification Authority is requested to independently determine the following:

| Verification Item | Requested Verification |
|---|---|
| Supported Seafood Provider Selection | VERIFY |
| Direct Resolver Selection | VERIFY |
| Shared Resolver Selection | VERIFY |
| Direct / Shared Agreement | VERIFY |
| Legacy Provider Selection Preservation | VERIFY |
| Undeclared Alias Boundary | VERIFY |
| Seafood Domain Regression Safety | VERIFY |
| Compilation Safety | VERIFY |
| New Blocking Selection Defect | DETERMINE |

No PASS result is asserted by this request document.

---

# 11. Requested Evidence

The IPS verification report should record independently reproduced evidence sufficient to determine:

~~~text
SUPPORTED SEAFOOD SELECTION
PASS / FAIL

DIRECT / SHARED RESOLVER AGREEMENT
PASS / FAIL

LEGACY SELECTION PRESERVATION
PASS / FAIL

UNDECLARED ALIAS BOUNDARY
PASS / FAIL

COMPILATION
PASS / FAIL

SEAFOOD DOMAIN REGRESSION
PASS / FAIL

BLOCKING PROVIDER SELECTION DEFECT
YES / NO
~~~

Any unexpected behavior should be attributed before the final decision.

---

# 12. Requested Decision

99_Integration Verification Authority is requested to issue one of the following evidence-based decisions:

~~~text
PASS

PASS WITH ARCHITECTURE OBSERVATION

REQUIRES REMEDIATION

FAIL
~~~

The decision must be based on independently reproduced provider-selection evidence.

This request itself does not predetermine the decision.

---

# 13. Next Stage

If Provider Selection Verification succeeds, the Seafood Domain may proceed to:

~~~text
IRC-SEAFOOD-2026-001
Result Contract Verification
~~~

The expected Sprint 3 Integration Verification sequence remains:

~~~text
IPR
↓
IPS
↓
IRC
↓
IRR
↓
IRG
↓
IVC
~~~

Advancement to IRC requires an official IPS decision from 99_Integration Verification Authority.

---

# 14. Official Request

The Seafood Domain formally requests independent execution of:

~~~text
IPS-SEAFOOD-2026-001
Provider Selection Verification
~~~

The request is limited to verification of provider-selection behavior and associated preservation requirements.

No claim of Result Contract Verification, Runtime Routing Verification, Cross-domain Regression Completion, Integration Verification Completion, or Master Architecture approval is made by this document.

---

**Requested By**

**Seafood Domain Development**

Commerce AI Generator

~~~text
INDEPENDENT PROVIDER SELECTION
VERIFICATION REQUESTED

IPS-SEAFOOD-2026-001
~~~
