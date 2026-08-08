# Cross-domain Regression Verification Request

## IRG-VEGETABLE-2026-001

**Title**

Cross-domain Regression Verification Request for the Vegetable Knowledge Domain

---

# Document Identity

| Item | Value |
|---|---|
| Document ID | IRG-VEGETABLE-2026-001 |
| Requesting Authority | Vegetable Domain Development |
| Receiving Authority | 99_Integration Verification Authority |
| Project | Commerce AI Generator |
| Domain | 22_Vegetable |
| Verification Phase | Sprint 3 |
| Verification Type | Cross-domain Regression Verification |
| Status | OFFICIAL REQUEST |

---

# 1. Purpose

This document officially requests independent Cross-domain Regression
Verification for the Vegetable Knowledge Domain.

The preceding Sprint 3 Integration Verification phases have established
that the Vegetable provider is registered, selectable, contract
compatible, and correctly routed through the shared Food Knowledge
runtime architecture.

The purpose of this phase is to determine whether inclusion of the
Vegetable Knowledge Domain preserves the behavior and compatibility of
the wider Food Knowledge provider portfolio.

---

# 2. Governing References

This verification request is governed by:

- ADA-MA-2026-018-VEGETABLE
- IVR-VEGETABLE-2026-001
- IPR-VEGETABLE-2026-001
- IPS-VEGETABLE-2026-001
- IRC-VEGETABLE-2026-001
- IRR-VEGETABLE-2026-001
- SED-2026-001 Sprint 3 Domain Completion Directive
- Commerce AI Generator Architecture Handbook v1.1
- Evidence First Principle
- Progressive Maturity Model

The preceding Runtime Routing Verification decision is:

~~~text
IRR-VEGETABLE-2026-001

RUNTIME ROUTING VERIFIED

PASS
~~~

---

# 3. Verification Scope

The 99_Integration Verification Authority is requested to independently
verify:

1. Provider portfolio preservation
2. Provider registration uniqueness
3. Provider registration order
4. Legacy provider relative-order preservation
5. Canonical provider resolution
6. Fruit / Vegetable routing boundary preservation
7. Shared result contract preservation
8. Cross-domain runtime compatibility
9. Runtime determinism
10. Import safety
11. Compilation safety
12. Vegetable domain regression
13. Full Food Knowledge regression
14. Regression attribution

---

# 4. Provider Portfolio Verification

The current integrated Food Knowledge provider portfolio is expected to
contain:

~~~text
fruit
vegetable
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

The verification shall confirm:

- Vegetable is registered exactly once.
- Existing providers remain registered.
- Provider IDs remain unique.
- No provider is unintentionally removed.
- The integrated provider order is deterministic.

Expected result:

~~~text
PROVIDER_PORTFOLIO_PRESERVATION_PASS=True
~~~

---

# 5. Legacy Provider Order Preservation

Vegetable is expected to extend the provider portfolio without changing
the relative ordering of the pre-existing providers.

When `vegetable` is removed from the current provider sequence, the
remaining provider order is expected to be:

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

The verification shall distinguish legitimate portfolio extension from
stale historical test expectations.

Expected result:

~~~text
LEGACY_PROVIDER_ORDER_PRESERVATION_PASS=True
~~~

---

# 6. Canonical Provider Resolution

Representative products from the integrated Food Knowledge portfolio
shall resolve to their expected providers.

The verification set should include, at minimum:

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

Expected result:

~~~text
CANONICAL_PROVIDER_RESOLUTION_PASS=True
~~~

---

# 7. Fruit / Vegetable Boundary Preservation

The regression verification shall explicitly preserve the routing
boundary established during Runtime Routing Verification.

Fruit cases:

~~~text
배
국산 배 선물세트
나주 배
~~~

Expected provider:

~~~text
fruit
~~~

Vegetable cases:

~~~text
양배추
배추
상추
브로콜리
시금치
~~~

Expected provider:

~~~text
vegetable
~~~

The purpose of this verification is to ensure that subsequent
cross-domain execution does not reintroduce the previously identified
short-alias collision.

Expected result:

~~~text
FRUIT_VEGETABLE_BOUNDARY_PRESERVATION_PASS=True
~~~

---

# 8. Shared Result Contract Preservation

Representative products from multiple domains shall be analyzed through
the shared runtime.

Each result shall continue to conform to:

~~~text
FoodKnowledgeResult
~~~

Required shared fields shall remain available, including:

~~~text
category_id
category_name
product_name
attributes
attribute_details
scores
score_details
rules
reasons
warnings
confidence
final_score
metadata
raw_product
~~~

Expected result:

~~~text
SHARED_RESULT_CONTRACT_PRESERVATION_PASS=True
~~~

---

# 9. Runtime Compatibility and Determinism

The verification shall confirm that repeated runtime resolution remains
stable for representative products across the integrated portfolio.

No provider-selection instability shall be introduced by Vegetable
integration.

Expected result:

~~~text
RUNTIME_DETERMINISM_PASS=True
~~~

---

# 10. Import and Compilation Safety

The verification shall independently confirm import safety for shared
Food Knowledge runtime modules, including:

~~~text
app.services.food.category_registry
app.services.food.knowledge.registry
app.services.food.knowledge.models
app.services.food.knowledge.vegetable.provider
app.services.food.resolver
~~~

Compilation shall also be verified using:

~~~text
python -m compileall -q app
~~~

Expected results:

~~~text
IMPORT_SAFETY_PASS=True

compile_exit_code=0
~~~

---

# 11. Regression Test Requirements

The following test scopes shall be executed independently.

## Vegetable Domain

~~~text
pytest tests/services/food/knowledge/vegetable -q
~~~

The most recently verified baseline is:

~~~text
26 passed
~~~

## Full Food Knowledge Portfolio

~~~text
pytest tests/services/food/knowledge -q
~~~

The most recently verified baseline is:

~~~text
1754 passed
~~~

The IRG phase shall record the actual results observed during its own
execution rather than assuming those baseline values.

---

# 12. Regression Attribution

Any failure discovered during this verification shall be classified
before an Integration Completion decision is made.

The verification authority shall distinguish between:

- Vegetable implementation regression
- Shared architecture regression
- Existing domain regression
- Stale test expectation
- Test infrastructure failure
- Unrelated pre-existing failure

A failing test alone shall not be attributed to the Vegetable Domain
without supporting evidence.

Conversely, any regression causally introduced by Vegetable integration
shall be treated as a blocking finding.

---

# 13. Expected Verification Evidence

The requested evidence shall include:

~~~text
Provider portfolio
Provider ID uniqueness
Provider order
Legacy relative-order preservation
Canonical provider resolution
Fruit / Vegetable routing boundary
Shared result contract
Runtime determinism
Import safety
Compilation
Vegetable regression
Full Food Knowledge regression
Regression attribution
~~~

Each verification item shall produce independently reproducible
evidence.

---

# 14. Requested Result

If all required verification areas pass, the requested result is:

~~~text
IRG-VEGETABLE-2026-001

CROSS-DOMAIN REGRESSION VERIFIED

PASS
~~~

No PASS result is presumed by this request.

The decision shall be based solely on independently observed evidence.

---

# 15. Requested Decision

The 99_Integration Verification Authority is requested to determine
whether:

~~~text
Vegetable integration preserves the existing Food Knowledge portfolio
without introducing attributable cross-domain regression.
~~~

Possible decisions include:

~~~text
PASS
FAIL
BLOCKED
PASS WITH OBSERVATION
~~~

---

# 16. Next Stage

If Cross-domain Regression Verification passes, the Vegetable Knowledge
Domain may proceed to:

~~~text
IVC-VEGETABLE-2026-001
Integration Verification Completion
~~~

The IRG decision does not itself constitute final Integration
Completion or Domain Completion.

Those determinations remain subject to the subsequent governance stages.

---

**Requested By**

**Vegetable Domain Development**

Commerce AI Generator

**Submitted To**

**99_Integration Verification Authority**
