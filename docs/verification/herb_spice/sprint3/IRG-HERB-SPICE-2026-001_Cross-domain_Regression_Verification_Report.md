# Cross-domain Regression Verification Report

## IRG-HERB-SPICE-2026-001

| Item | Value |
|---|---|
| Document ID | IRG-HERB-SPICE-2026-001 |
| Title | Herb & Spice Knowledge Domain Cross-domain Regression Verification Report |
| Project | Commerce AI Generator |
| Sprint | Sprint 3 |
| Domain | 15_Herb & Spice |
| Verification Authority | 99_Integration Verification Authority |
| Architecture Authority | 00_1 Master Architecture |
| Status | OFFICIAL |
| Verification Result | PASS WITH ARCHITECTURE OBSERVATION |
| Verification Date | 2026-08-06 |

---

# 1. Purpose

This report records the independent Cross-domain Regression Verification performed for the Herb & Spice Knowledge Domain.

The purpose of this verification is to determine whether integration of `HerbSpiceKnowledgeProvider` introduced any new regression into:

- the shared Provider portfolio;
- Provider resolution;
- shared runtime behavior;
- `FoodKnowledgeResult`;
- import safety;
- compilation safety;
- previously approved Food Knowledge Domains.

This report distinguishes verified Herb & Spice integration behavior from pre-existing shared runtime observations.

---

# 2. Governing References

- IVR-HERB-SPICE-2026-001
- IPR-HERB-SPICE-2026-001
- IPS-HERB-SPICE-2026-001
- IRC-HERB-SPICE-2026-001
- IRR-HERB-SPICE-2026-001
- IRG-HERB-SPICE-2026-001 Cross-domain Regression Verification Request
- ADA-MA-2026-016-HERB-SPICE
- APR-MA-2026-001 Revision 1
- AAR-MA-2026-001
- MAN-2026-003
- ARN-MA-2026-001 Revision 1
- SED-2026-001 Sprint 3 Domain Completion Directive
- Commerce AI Generator Architecture Handbook v1.1
- Evidence First Principle
- Progressive Maturity Model
- Pre-Herb & Spice comparison baseline commit `651a603`

---

# 3. Entry Conditions

The following verification phases were completed before final IRG execution:

~~~text
IPR PASS

IPS PASS

IRC PASS

IRR PASS
~~~

The IRG Request was submitted before IRR completion, but remained pending until the IRR Verification Report was issued.

Following official IRR completion, all IRG entry conditions were satisfied.

---

# 4. Verification Scope

Independent Cross-domain Regression Verification covered:

- Provider portfolio preservation;
- Provider identifier uniqueness;
- deterministic Provider ordering;
- canonical Provider resolution;
- Herb & Spice Provider resolution;
- shared `FoodKnowledgeResult` compatibility;
- import safety;
- compilation safety;
- full Food Knowledge regression;
- comparison with the pre-Herb & Spice baseline;
- regression attribution;
- Architecture Observation classification.

---

# 5. Provider Portfolio Preservation

The expected Provider portfolio was:

~~~text
fruit
cheese
coffee
wine
tea
olive_oil
herb_spice
venison
goat
beef
lamb
chicken
duck
~~~

The actual Provider portfolio was identical.

Independent execution produced:

~~~text
UNIQUE=True
MATCH=True
PORTFOLIO_PASS=True
~~~

Verification confirmed:

- all expected Providers are present;
- `herb_spice` is present in the approved position;
- Provider identifiers remain unique;
- Provider order remains deterministic;
- no existing Provider was removed.

## Result

~~~text
PASS
~~~

---

# 6. Canonical Provider Resolution

Representative canonical products were independently resolved through the shared runtime.

| Product | Expected Provider | Result |
|---|---|---|
| 고당도 사과 | fruit | PASS |
| 브리 치즈 | cheese | PASS |
| 예가체프 원두 | coffee | PASS |
| 프랑스 레드 와인 | wine | PASS |
| 제주 녹차 | tea | PASS |
| 엑스트라 버진 올리브 오일 | olive_oil | PASS |
| 바질 | herb_spice | PASS |
| 한우 등심 | beef | PASS |
| 프리미엄 도퍼 어린양 프렌치랙 | lamb | PASS |
| 토종닭 | chicken | PASS |
| 훈제오리 | duck | PASS |

Independent execution produced:

~~~text
CANONICAL_PROVIDER_RESOLUTION_PASS=True
~~~

No canonical Provider-resolution regression attributable to Herb & Spice was identified.

## Result

~~~text
PASS
~~~

---

# 7. Shared Result Contract Preservation

The following representative products were analyzed through the shared runtime:

- 바질
- 후추
- 올리브 오일
- 브리 치즈
- 예가체프 원두

Each execution returned:

~~~text
FoodKnowledgeResult
~~~

Independent execution produced:

~~~text
RESULT_CONTRACT_PASS=True
~~~

The shared result contract remained preserved across Herb & Spice and previously approved domains.

## Result

~~~text
PASS
~~~

---

# 8. Import Safety

The following shared runtime modules were independently imported:

~~~text
app.services.food.category_registry
app.services.food.knowledge.registry
app.services.food.resolver
~~~

Independent execution produced:

~~~text
IMPORT_REGRESSION_PASS=True
~~~

No import error, circular-import failure, or runtime initialization failure was identified.

## Result

~~~text
PASS
~~~

---

# 9. Compilation Safety

Application compilation was independently executed.

~~~text
python -m compileall -q app
compile_exit_code=0
~~~

## Result

~~~text
PASS
~~~

---

# 10. Full Food Knowledge Regression

The full Food Knowledge regression suite was independently executed.

~~~text
pytest tests/services/food/knowledge -q
~~~

Execution result:

~~~text
1638 passed
0 failed
~~~

No test regression was identified.

## Result

~~~text
PASS
~~~

---

# 11. Pre-Herb & Spice Baseline Comparison

A detached Git worktree was created from the pre-Herb & Spice baseline:

~~~text
Commit:
651a603c62f742f3a002f2094c4a408b44865072

Short Commit:
651a603
~~~

The following ambiguous shared Resolver cases were evaluated:

~~~text
사슴 안심
Expected Provider=venison

보어 염소 갈비
Expected Provider=goat
~~~

Baseline execution produced:

~~~text
사슴 안심
Category Registry=beef
Provider Registry=venison
Shared Resolver=beef
Shared Routing Pass=False

보어 염소 갈비
Category Registry=beef
Provider Registry=goat
Shared Resolver=beef
Shared Routing Pass=False

PRE_HERB_SPICE_SHARED_ROUTING_PASS=False
~~~

The same routing behavior therefore existed before Herb & Spice integration.

---

# 12. Architecture Observation

The following Architecture Observation is recorded.

## Observation ID

~~~text
AO-MA-2026-016-HERB-SPICE-001
~~~

## Description

Generic Beef aliases such as:

~~~text
안심
갈비
~~~

may be resolved by the Category Registry before more domain-specific Venison or Goat Provider matching is applied.

## Verified Classification

~~~text
PRE-EXISTING

SHARED RUNTIME OBSERVATION

NOT ATTRIBUTABLE TO HERB & SPICE
~~~

## Blocking Status

~~~text
NON-BLOCKING
~~~

## Disposition

The observation shall be preserved for future architecture evaluation.

No Category Registry redesign, Resolver redesign, or Alias Resolution redesign is authorized by this report.

Future evaluation may be conducted under the separately planned Sprint 4 Alias Resolution Layer work.

---

# 13. Regression Attribution

The independent evidence supports the following conclusions:

- the Herb & Spice Provider portfolio entry is correct;
- canonical Provider resolution remains preserved;
- the shared result contract remains preserved;
- import and compilation safety remain preserved;
- the complete Food Knowledge test suite passes;
- the identified Venison and Goat ambiguity existed before Herb & Spice integration;
- no new regression attributable to Herb & Spice was identified.

The observed shared routing ambiguity shall not be classified as a Herb & Spice implementation defect.

---

# 14. Verification Matrix

| Verification Item | Result |
|---|---|
| Provider Portfolio Preservation | PASS |
| Provider Identifier Uniqueness | PASS |
| Deterministic Provider Order | PASS |
| Herb & Spice Provider Presence | PASS |
| Canonical Provider Resolution | PASS |
| Shared Result Contract | PASS |
| Import Safety | PASS |
| Compilation Safety | PASS |
| Full Food Knowledge Regression | PASS |
| New Regression Attributable to Herb & Spice | NOT FOUND |
| Venison/Goat Shared Resolver Ambiguity | PRE-EXISTING OBSERVATION |
| Architecture Observation Blocking Status | NON-BLOCKING |

---

# 15. Independent Evidence Summary

~~~text
PORTFOLIO_PASS=True

CANONICAL_PROVIDER_RESOLUTION_PASS=True

RESULT_CONTRACT_PASS=True

IMPORT_REGRESSION_PASS=True

compile_exit_code=0

1638 passed

IRG_EXECUTION_PASS=True
~~~

---

# 16. Findings

## Verified Facts

- The expected Provider portfolio matches the actual Provider portfolio.
- Provider category identifiers remain unique.
- Herb & Spice is registered in the approved Provider order.
- All verified canonical product cases resolve to their expected Providers.
- Herb & Spice canonical products resolve to `herb_spice`.
- Shared runtime analysis returns `FoodKnowledgeResult`.
- Shared runtime modules import successfully.
- Application compilation completed with exit code `0`.
- Full Food Knowledge regression completed with `1638 passed`.
- The Venison and Goat shared-routing ambiguity existed before Herb & Spice integration.
- Baseline commit `651a603` reproduced the same ambiguity.
- No new regression attributable to Herb & Spice was identified.

## Assumptions

~~~text
NONE
~~~

This report does not rely on unverified assumptions for its final decision.

---

# 17. Official Decision

## Review Result

~~~text
PASS WITH ARCHITECTURE OBSERVATION
~~~

## Phase Status

~~~text
CROSS-DOMAIN REGRESSION VERIFIED
~~~

## Regression Attribution

~~~text
NO NEW REGRESSION

ATTRIBUTABLE TO

HERB & SPICE
~~~

## Architecture Observation

~~~text
AO-MA-2026-016-HERB-SPICE-001

PRE-EXISTING

NON-BLOCKING
~~~

## Next Phase

~~~text
IVC-HERB-SPICE-2026-001

Integration Verification Completion
~~~

---

# Official Statement

99_Integration Verification Authority independently verified the Cross-domain Regression phase for the Herb & Spice Knowledge Domain.

Provider portfolio preservation, canonical Provider resolution, shared result compatibility, import safety, compilation safety, and the complete Food Knowledge regression suite were successfully verified.

The identified Venison and Goat shared Resolver ambiguity was reproduced against the pre-Herb & Spice baseline and is therefore classified as a pre-existing, non-blocking Architecture Observation that is not attributable to Herb & Spice.

Accordingly, no new regression attributable to the Herb & Spice integration was identified.

The Cross-domain Regression Verification phase is officially completed with an Architecture Observation.

---

**Issued By**

**99_Integration Verification Authority**

Commerce AI Generator
