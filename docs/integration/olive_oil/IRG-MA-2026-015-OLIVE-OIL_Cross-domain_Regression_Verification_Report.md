# Cross-domain Regression Verification Report

## IRG-MA-2026-015-OLIVE-OIL

| Item | Value |
|---|---|
| Document ID | IRG-MA-2026-015-OLIVE-OIL |
| Title | Olive Oil Knowledge Domain Cross-domain Regression Verification Report |
| Project | Commerce AI Generator |
| Sprint | Sprint 3 |
| Domain | Olive Oil Knowledge Domain |
| Verification Authority | 99_Integration Verification Authority |
| Status | OFFICIAL |
| Verification Result | PASS WITH ARCHITECTURE OBSERVATION |
| Verification Date | 2026-08-06 |

---

# 1. Purpose

This report records the independent Cross-domain Regression Verification performed following integration of the Olive Oil Knowledge Domain.

The purpose of this phase is to determine whether Olive Oil integration introduced any regression to the shared Food Knowledge runtime, Provider portfolio, existing domain routing, result contracts, imports, compilation, or Food Knowledge regression baseline.

This report also records a pre-existing shared routing ambiguity identified during independent execution and distinguishes that observation from Olive Oil integration regression.

---

# 2. Governing References

- IVR-OLIVE-OIL-2026-001
- IPR-MA-2026-015-OLIVE-OIL
- IPS-MA-2026-015-OLIVE-OIL
- IRC-MA-2026-015-OLIVE-OIL
- IRR-MA-2026-015-OLIVE-OIL
- IRG-MA-2026-015-OLIVE-OIL Cross-domain Regression Verification Request
- ARN-MA-2026-001 Revision 1
- ARR-MA-2026-001 Category Registry Responsibility Boundary Clarification
- SED-2026-001 Sprint 3 Domain Completion Directive
- Commerce AI Generator Architecture Handbook v1.1
- Evidence First Principle
- Progressive Maturity Model
- Pre-Olive Oil comparison baseline commit `376f83f`
- IRG request baseline commit `9e9ee83`

---

# 3. Verification Scope

Independent verification covered:

- Provider portfolio preservation;
- Provider identifier uniqueness;
- Provider Registry order;
- cross-domain Provider resolution;
- shared Resolver category routing;
- `FoodKnowledgeResult` compatibility;
- Category Registry preservation;
- Provider Registry preservation;
- import safety;
- compilation safety;
- full Food Knowledge regression;
- comparison against the pre-Olive Oil baseline;
- regression attribution.

---

# 4. Provider Portfolio Preservation

The independently verified Provider order was:

~~~text
fruit
cheese
coffee
wine
tea
olive_oil
venison
goat
beef
lamb
chicken
duck
~~~

Independent execution produced:

~~~text
UNIQUE=True
MATCH=True
PORTFOLIO_PASS=True
~~~

Verification confirmed:

- all expected Providers remained registered;
- `olive_oil` was registered exactly once;
- Provider identifiers remained unique;
- Provider order remained deterministic.

## Result

~~~text
PASS
~~~

---

# 5. Canonical Cross-domain Routing Execution

The following representative products were evaluated through the shared Resolver:

| Product | Expected Domain | Observed Domain | Result |
|---|---|---|---|
| 고당도 사과 | fruit | fruit | PASS |
| 프랑스 브리 치즈 | cheese | cheese | PASS |
| 에티오피아 아라비카 원두 | coffee | coffee | PASS |
| 카베르네 소비뇽 레드 와인 | wine | wine | PASS |
| 제주 녹차 | tea | tea | PASS |
| 엑스트라 버진 올리브 오일 | olive_oil | olive_oil | PASS |
| 사슴 안심 스테이크 | venison | beef | OBSERVATION |
| 보어 어린 염소 갈비 | goat | beef | OBSERVATION |
| 국내산 한우 1++ 등심 | beef | beef | PASS |
| 프리미엄 도퍼 어린양 프렌치랙 | lamb | lamb | PASS |
| 토종닭 가슴살 | chicken | chicken | PASS |
| 훈제오리 슬라이스 | duck | duck | PASS |

The initial execution summary was:

~~~text
CANONICAL_PROVIDER_RESOLUTION_PASS=False
~~~

This result required further attribution analysis before an IRG decision could be issued.

---

# 6. Provider Registry Resolution Analysis

Direct Provider Registry resolution was independently compared with shared Resolver routing.

For `사슴 안심 스테이크`:

~~~text
Matched Providers:
venison
beef

Direct Provider Registry Result:
venison
~~~

For `보어 어린 염소 갈비`:

~~~text
Matched Providers:
goat
beef

Direct Provider Registry Result:
goat
~~~

The Provider Registry therefore preserved the expected domain-specific resolution behavior.

## Result

~~~text
PASS
~~~

---

# 7. Shared Resolver Category Routing Analysis

The shared Resolver evaluates the Category Registry before falling back to Provider Registry resolution.

The following routing path was confirmed:

~~~text
Product
    ↓
resolve_product_category(...)
    ↓
Category Registry
    ↓
category_config.provider_id
    ↓
get_food_provider(...)
~~~

For `사슴 안심 스테이크`:

~~~text
CATEGORY_DIRECT=beef
CATEGORY_DIRECT_PROVIDER_ID=beef
CATEGORY_SHARED=beef
CATEGORY_SHARED_PROVIDER_ID=beef
PROVIDER_REGISTRY_RESULT=venison
SHARED_RESOLVER_RESULT=beef
~~~

For `보어 어린 염소 갈비`:

~~~text
CATEGORY_DIRECT=beef
CATEGORY_DIRECT_PROVIDER_ID=beef
CATEGORY_SHARED=beef
CATEGORY_SHARED_PROVIDER_ID=beef
PROVIDER_REGISTRY_RESULT=goat
SHARED_RESOLVER_RESULT=beef
~~~

The behavior was traced to general Beef Category Registry aliases including:

~~~text
안심
갈비
등심
채끝
~~~

These aliases can classify cross-domain meat products as Beef before domain-specific Provider resolution occurs.

## Result

~~~text
ARCHITECTURE OBSERVATION
~~~

---

# 8. Pre-Olive Oil Baseline Comparison

A detached Git worktree was created from the pre-Olive Oil comparison baseline:

~~~text
Commit:
376f83f

Description:
Olive Oil Integration Verification Request baseline
~~~

The same routing cases were executed against that baseline.

For `사슴 안심 스테이크`:

~~~text
EXPECTED=venison
CATEGORY_REGISTRY=beef
PROVIDER_REGISTRY=venison
SHARED_RESOLVER=beef
SHARED_ROUTING_PASS=False
~~~

For `보어 어린 염소 갈비`:

~~~text
EXPECTED=goat
CATEGORY_REGISTRY=beef
PROVIDER_REGISTRY=goat
SHARED_RESOLVER=beef
SHARED_ROUTING_PASS=False
~~~

The baseline execution summary was:

~~~text
PRE_OLIVE_OIL_SHARED_ROUTING_PASS=False
~~~

This independently confirms that the routing ambiguity existed before Olive Oil Provider integration.

## Result

~~~text
PRE-EXISTING BEHAVIOR CONFIRMED
~~~

---

# 9. Regression Attribution

Based on current and historical baseline comparison:

- the same Venison and Goat routing ambiguity existed before Olive Oil integration;
- Olive Oil did not introduce the general Beef aliases;
- Olive Oil did not modify shared Resolver priority behavior;
- Provider Registry direct resolution remained correct;
- the current full Food Knowledge regression remained passing.

Therefore:

~~~text
OLIVE_OIL_REGRESSION_ATTRIBUTION=False
~~~

The identified routing ambiguity is not attributable to the Olive Oil Knowledge Domain.

## Result

~~~text
NO NEW OLIVE OIL REGRESSION
~~~

---

# 10. Result Contract Preservation

Representative cross-domain products continued to return `FoodKnowledgeResult`.

Verified examples included:

- Brie Cheese
- Yirgacheffe Coffee
- Olive Oil
- Jeju Green Tea
- High-sugar Apple

Independent execution produced:

~~~text
RESULT_CONTRACT_PASS=True
~~~

No shared result contract regression was identified.

## Result

~~~text
PASS
~~~

---

# 11. Import Safety

The following shared modules imported successfully:

~~~text
app.services.food.category_registry
app.services.food.knowledge.registry
app.services.food.resolver
~~~

Independent execution produced:

~~~text
IMPORT_REGRESSION_PASS=True
~~~

No circular-import or module-import failure was identified.

## Result

~~~text
PASS
~~~

---

# 12. Compilation Safety

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

# 13. Full Food Knowledge Regression

The complete Food Knowledge regression suite was independently executed.

~~~text
1464 passed
0 failed
~~~

No test regression was identified.

## Result

~~~text
PASS
~~~

---

# 14. Architecture Observation

## AO-MA-2026-015-OLIVE-OIL-001

**Title**

Pre-existing Shared Category Routing Ambiguity for Venison and Goat Products

**Classification**

~~~text
SHARED RUNTIME ARCHITECTURE OBSERVATION
~~~

**Status**

~~~text
RECORDED
DEFERRED
NON-BLOCKING FOR OLIVE OIL IRG
~~~

**Observed Behavior**

General Beef Category Registry aliases such as `안심` and `갈비` can classify Venison and Goat product names as Beef before the shared Resolver reaches domain-specific Provider resolution.

**Verified Boundary**

~~~text
Provider Registry direct resolution:
Correct

Shared Resolver category-first resolution:
Ambiguous for the verified cases
~~~

**Regression Attribution**

~~~text
PRE-EXISTING
NOT INTRODUCED BY OLIVE OIL
~~~

**Deferred Evaluation Scope**

The observation may be considered during Sprint 4 evaluation of:

- Alias Resolution Layer;
- shared category-routing heuristics;
- category-versus-provider precedence;
- cross-domain meat alias ownership;
- domain-specific routing evidence.

No Sprint 3 architecture redesign is authorized by this report.

---

# 15. Architecture Constraints Preserved

This verification introduced no modification to:

- Category Registry architecture;
- Knowledge Registry architecture;
- shared Resolver behavior;
- Provider interface;
- `FoodKnowledgeResult`;
- Provider ordering policy;
- Alias Resolution Layer;
- shared runtime contracts.

The pre-existing observation was recorded without expanding Sprint 3 implementation scope.

---

# 16. Verification Matrix

| Verification Item | Result |
|---|---|
| Provider Portfolio Preservation | PASS |
| Provider Identifier Uniqueness | PASS |
| Provider Order Determinism | PASS |
| Olive Oil Provider Resolution | PASS |
| Provider Registry Direct Resolution | PASS |
| Result Contract Preservation | PASS |
| Import Safety | PASS |
| Compilation Safety | PASS |
| Full Food Knowledge Regression | PASS |
| New Olive Oil Regression | NOT FOUND |
| Venison Shared Resolver Routing | ARCHITECTURE OBSERVATION |
| Goat Shared Resolver Routing | ARCHITECTURE OBSERVATION |
| Pre-Olive Oil Baseline Comparison | PRE-EXISTING BEHAVIOR CONFIRMED |

---

# 17. Findings

## Verified Facts

- The expected Provider portfolio is present and unique.
- Olive Oil is registered exactly once.
- Provider Registry direct resolution selects Venison and Goat for the verified domain-specific samples.
- Shared Resolver category-first routing selects Beef for those samples.
- The same Shared Resolver behavior existed at pre-Olive Oil baseline commit `376f83f`.
- The routing ambiguity is therefore not attributable to Olive Oil integration.
- Shared `FoodKnowledgeResult` compatibility remains preserved.
- Shared modules import successfully.
- Application compilation completed with exit code `0`.
- Full Food Knowledge regression completed with `1464 passed`.
- No new Olive Oil cross-domain regression was identified.

## Assumptions

~~~text
NONE
~~~

The final decision is based on reproduced current-state evidence and a reproduced pre-Olive Oil baseline comparison.

---

# 18. Official Decision

## Review Result

~~~text
PASS WITH ARCHITECTURE OBSERVATION
~~~

## Regression Decision

~~~text
NO NEW REGRESSION ATTRIBUTABLE TO OLIVE OIL
~~~

## Observation Status

~~~text
AO-MA-2026-015-OLIVE-OIL-001

RECORDED
DEFERRED
NON-BLOCKING
~~~

## Phase Status

~~~text
CROSS-DOMAIN REGRESSION VERIFIED
~~~

## Next Phase

~~~text
IVC-MA-2026-015-OLIVE-OIL
Integration Verification Completion
~~~

---

# Official Statement

99_Integration Verification Authority independently verified the Cross-domain Regression phase for the Olive Oil Knowledge Domain.

Provider portfolio preservation, direct Provider Registry behavior, shared result compatibility, import safety, compilation safety, and the complete Food Knowledge regression suite were successfully verified.

A shared category-routing ambiguity involving Venison and Goat products was reproduced. Independent comparison against pre-Olive Oil baseline commit `376f83f` confirmed that the same behavior existed before Olive Oil integration.

Accordingly, the identified behavior is recorded as a pre-existing Shared Runtime Architecture Observation and is not attributed to the Olive Oil Knowledge Domain.

The Olive Oil Cross-domain Regression Verification phase is therefore completed with the result:

~~~text
PASS WITH ARCHITECTURE OBSERVATION
~~~

---

**Issued By**

99_Integration Verification Authority
