# IRG-SEAFOOD-2026-001
# Seafood Cross-domain Regression Verification Request

**Document ID:** IRG-SEAFOOD-2026-001  
**Domain:** Seafood  
**Verification Stage:** Cross-domain Regression Verification  
**Verification Authority:** 99_Integration Verification Authority  
**Status:** VERIFICATION REQUESTED  
**Date:** 2026-08-13  

---

# 1. Purpose

This document formally requests independent Cross-domain Regression
Verification for the Seafood Knowledge Domain.

The purpose of this verification is to determine whether Seafood
integration preserves the existing Food Knowledge provider portfolio,
runtime behavior, shared result contract, and representative
cross-domain behavior without introducing an attributable regression.

This stage shall also determine the final attribution of the four
full-suite failures carried forward from earlier integration
verification stages.

---

# 2. Governing Evidence

The following Seafood Sprint 3 integration verification stages have
been completed:

~~~text
IPR-SEAFOOD-2026-001
Provider Registration Verification
PASS WITH OBSERVATION

IPS-SEAFOOD-2026-001
Provider Selection Verification
PASS

IRC-SEAFOOD-2026-001
Result Contract Verification
PASS WITH OBSERVATION

IRR-SEAFOOD-2026-001
Runtime Routing Verification
PASS WITH OBSERVATION
~~~

The open observation carried into IRG is:

~~~text
Historical Provider Membership Expectation Drift
~~~

IRG shall independently determine whether this attribution is
supported by the full cross-domain evidence.

---

# 3. Verification Scope

The independent IRG verification shall examine:

1. provider portfolio membership;
2. provider ID uniqueness;
3. Seafood single registration;
4. Seafood provider position;
5. existing provider relative-order preservation;
6. canonical provider resolution;
7. shared result contract preservation;
8. runtime routing preservation;
9. runtime determinism;
10. Seafood alias boundary behavior;
11. import safety;
12. compilation safety;
13. Seafood domain regression;
14. full Food Knowledge regression;
15. exact reproduction of the four known failures;
16. regression attribution;
17. blocking status determination.

---

# 4. Provider Portfolio Preservation

The expected current provider portfolio is:

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
seafood
~~~

Verification shall confirm:

~~~text
Provider Count = 15
Provider IDs Unique = TRUE
Seafood Registered Once = TRUE
Seafood Position = LAST
~~~

After removing Seafood, the existing 14-provider sequence shall remain:

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

Expected result:

~~~text
PROVIDER_PORTFOLIO_PRESERVATION_PASS=True
LEGACY_PROVIDER_ORDER_PRESERVATION_PASS=True
~~~

---

# 5. Canonical Provider Resolution

Representative current-domain products shall retain their expected
providers.

The verification set shall include:

~~~text
고당도 사과                    -> fruit
양배추                         -> vegetable
브리 치즈                      -> cheese
예가체프 원두                  -> coffee
프랑스 레드 와인              -> wine
제주 녹차                      -> tea
엑스트라 버진 올리브 오일     -> olive_oil
바질                           -> herb_spice
한우 등심                      -> beef
프리미엄 도퍼 어린양 프렌치랙 -> lamb
토종닭                         -> chicken
훈제오리                       -> duck
노르웨이 연어                 -> seafood
고등어                         -> seafood
새우                           -> seafood
~~~

Both direct and shared runtime resolution shall be examined.

---

# 6. Shared Result Contract Preservation

Representative cross-domain runtime analysis shall continue to return:

~~~text
FoodKnowledgeResult
~~~

with the expected:

~~~text
category_id
~~~

for each tested domain.

Seafood integration shall not alter the established shared result
contract.

Expected result:

~~~text
CROSS_DOMAIN_RESULT_CONTRACT_PASS=True
~~~

---

# 7. Runtime Routing Preservation

IRG shall confirm that the routing evidence established during IRR
remains valid.

Expected evidence includes:

~~~text
EXPLICIT_SEAFOOD_CATEGORY_ROUTING_PASS=True
SEAFOOD_RUNTIME_ROUTING_PASS=True
LEGACY_RUNTIME_ROUTING_PRESERVATION_PASS=True
RUNTIME_ROUTING_DETERMINISM_PASS=True
~~~

No new runtime routing failure may be hidden by the existing provider
membership observation.

---

# 8. Seafood Alias Boundary

The following names are not currently declared Seafood aliases:

~~~text
광어
국산 광어
광어회
넙치
국산 넙치
~~~

The current contract expects Seafood not to be selected for these
inputs.

Expected result:

~~~text
SEAFOOD_UNDECLARED_ALIAS_BOUNDARY_PASS=True
~~~

This verification concerns the current implementation contract only.

---

# 9. Import and Compilation Safety

The following modules shall import successfully:

~~~text
app.services.food.category_registry
app.services.food.knowledge.registry
app.services.food.knowledge.models
app.services.food.knowledge.seafood.provider
app.services.food.resolver
~~~

Expected result:

~~~text
IMPORT_SAFETY_PASS=True
~~~

Compilation command:

~~~bash
python -m compileall -q app
~~~

Expected result:

~~~text
compile_exit_code=0
~~~

---

# 10. Seafood Domain Regression

Verification command:

~~~bash
pytest tests/services/food/knowledge/seafood -q
~~~

Current baseline:

~~~text
63 passed
~~~

Any new Seafood-domain failure shall be treated as potentially
blocking until independently attributed.

---

# 11. Full Food Knowledge Regression

Verification command:

~~~bash
pytest tests/services/food/knowledge -q
~~~

Previous observed result:

~~~text
1813 passed
4 failed
~~~

IRG shall independently reproduce the full suite.

The exact failure nodes shall be recorded.

---

# 12. Known Failure Set

The previously observed failures are:

~~~text
tests/services/food/knowledge/cheese/
test_cheese_registry_integration.py
::test_cheese_provider_registration_order

tests/services/food/knowledge/coffee/
test_coffee_registry_integration.py
::test_provider_registration_order

tests/services/food/knowledge/herb_spice/
test_herb_spice_registry_integration.py
::test_default_provider_order

tests/services/food/knowledge/vegetable/
test_vegetable_registry_integration.py
::test_vegetable_registration_preserves_legacy_provider_order
~~~

IRG shall determine whether these failures:

1. demonstrate a Seafood implementation defect;
2. demonstrate a shared registry defect;
3. demonstrate runtime routing regression;
4. demonstrate Result Contract regression;
5. represent stale historical provider membership/order expectations;
6. require remediation before Integration Verification Completion.

---

# 13. Regression Attribution Requirement

Each reproduced failure shall be attributed using independently
observed evidence.

Possible classifications include:

~~~text
SEAFOOD IMPLEMENTATION REGRESSION
SHARED ARCHITECTURE REGRESSION
RUNTIME ROUTING REGRESSION
RESULT CONTRACT REGRESSION
HISTORICAL PROVIDER MEMBERSHIP EXPECTATION DRIFT
PRE-EXISTING REGRESSION
OTHER
~~~

No failure may be reclassified merely to obtain a PASS result.

Likewise, no stale historical expectation shall automatically be
treated as a Seafood implementation defect.

---

# 14. Blocking Status Requirement

IRG shall determine whether any reproduced issue prevents advancement
to:

~~~text
IVC-SEAFOOD-2026-001
Integration Verification Completion
~~~

Possible blocking determinations:

~~~text
BLOCKING
NON-BLOCKING
REQUIRES REMEDIATION
~~~

---

# 15. Expected Verification Evidence

The requested evidence includes:

~~~text
PROVIDER_PORTFOLIO_PRESERVATION_PASS
LEGACY_PROVIDER_ORDER_PRESERVATION_PASS
CANONICAL_PROVIDER_RESOLUTION_PASS
CROSS_DOMAIN_RESULT_CONTRACT_PASS
SEAFOOD_RUNTIME_ROUTING_PASS
LEGACY_RUNTIME_ROUTING_PRESERVATION_PASS
SEAFOOD_UNDECLARED_ALIAS_BOUNDARY_PASS
RUNTIME_ROUTING_DETERMINISM_PASS
IMPORT_SAFETY_PASS
COMPILATION_SAFETY_PASS
SEAFOOD_DOMAIN_REGRESSION
FULL_FOOD_KNOWLEDGE_REGRESSION
REGRESSION_ATTRIBUTION
BLOCKING_STATUS
~~~

---

# 16. Requested Result

If the evidence demonstrates that Seafood integration introduces no
blocking cross-domain regression, the requested result is:

~~~text
CROSS-DOMAIN REGRESSION VERIFIED
~~~

The official decision may be:

~~~text
PASS
PASS WITH OBSERVATION
REQUIRES REMEDIATION
FAIL
~~~

The decision shall explicitly state the disposition of the four known
failures.

---

# 17. Authority Boundary

IRG determines cross-domain regression status.

It does not itself establish:

~~~text
Integration Verification Completion
Master Architecture Completion
Sprint 3 Completion
~~~

Those decisions belong to later governance stages.

---

# 18. Next Stage

If IRG concludes that no blocking cross-domain regression remains, the
Seafood evidence chain may proceed to:

~~~text
IVC-SEAFOOD-2026-001
Integration Verification Completion
~~~

---

# 19. Submission Status

~~~text
IRG-SEAFOOD-2026-001

INDEPENDENT CROSS-DOMAIN REGRESSION

VERIFICATION REQUESTED
~~~
