# IPS-SEAFOOD-2026-001

## Independent Provider Selection Verification Request

**Document ID:** IPS-SEAFOOD-2026-001  
**Domain:** Seafood  
**Authority:** 99_Integration Verification Authority  
**Verification Type:** Independent Provider Selection Verification  
**Sprint:** Sprint 3  
**Status:** VERIFICATION REQUESTED  
**Date:** 2026-08-13

---

# 1. Purpose

This document formally requests independent verification of provider
selection behavior for the Seafood Domain.

The objective is to verify that the Seafood provider is selected
correctly through the canonical Food Knowledge runtime resolution paths
without disturbing provider selection behavior of existing domains.

This verification follows completion of:

- ADA-MA-2026-019-SEAFOOD
- IVR-SEAFOOD-2026-001
- IPR-SEAFOOD-2026-001

The requested verification is limited to provider selection behavior.

---

# 2. Verification Principle

The verification SHALL be evidence-based.

The existence of a registered Seafood provider does not by itself prove
correct provider selection.

Independent verification SHALL confirm that:

1. declared Seafood products resolve to the Seafood provider;
2. canonical provider resolution paths agree;
3. representative legacy-domain routing remains preserved;
4. undeclared Seafood aliases are not implicitly introduced;
5. provider selection remains deterministic and bounded by the
   implemented runtime contract.

No expansion of the Seafood alias contract is requested by this
document.

---

# 3. Verification Scope

99_Integration is requested to independently verify the following.

## 3.1 Seafood Positive Selection

Representative declared Seafood products SHALL resolve to:

~~~text
category_id = seafood
~~~

Verification cases:

~~~text
노르웨이 연어
고등어
참치
새우
꽃게
전복
오징어
~~~

---

## 3.2 Canonical Resolution Path Agreement

Provider selection SHALL be verified through both:

~~~text
app.services.food.knowledge.registry.resolve_food_provider
~~~

and:

~~~text
app.services.food.resolver.resolve_knowledge_provider
~~~

For each representative Seafood case, both resolution paths SHALL
select:

~~~text
seafood
~~~

---

## 3.3 Legacy Provider Selection Preservation

Representative existing-domain products SHALL continue to resolve to
their established providers.

Expected evidence:

~~~text
고당도 사과
fruit

양배추
vegetable

브리 치즈
cheese

예가체프 원두
coffee

프랑스 레드 와인
wine

제주 녹차
tea

엑스트라 버진 올리브 오일
olive_oil

바질
herb_spice

한우 등심
beef

프리미엄 도퍼 어린양 프렌치랙
lamb

토종닭
chicken

훈제오리
duck
~~~

The introduction of Seafood SHALL NOT alter these representative
provider selections.

---

# 4. Seafood Alias Boundary Verification

Provider selection SHALL remain bounded by the aliases explicitly
declared by the Seafood provider.

The current verification evidence establishes that the following names
are not declared Seafood provider aliases:

~~~text
광어
국산 광어
광어회
넙치
국산 넙치
~~~

The expected runtime result for this IPS verification is:

~~~text
Seafood provider is NOT selected.
~~~

A `None` result is acceptable where no other provider legitimately
claims the product.

This requirement verifies current runtime behavior only.

It SHALL NOT be interpreted as a statement that 광어 or 넙치 are
conceptually outside the seafood domain.

Their absence from the current alias contract is an implementation
boundary, not a domain-taxonomy conclusion.

---

# 5. Existing Execution Evidence

The submitting authority provides the following execution evidence for
independent reproduction.

## 5.1 Seafood Provider Selection

Observed:

~~~text
'노르웨이 연어'
EXPECTED= seafood
DIRECT= seafood
SHARED= seafood
PASS= True

'고등어'
EXPECTED= seafood
DIRECT= seafood
SHARED= seafood
PASS= True

'참치'
EXPECTED= seafood
DIRECT= seafood
SHARED= seafood
PASS= True

'새우'
EXPECTED= seafood
DIRECT= seafood
SHARED= seafood
PASS= True

'꽃게'
EXPECTED= seafood
DIRECT= seafood
SHARED= seafood
PASS= True

'전복'
EXPECTED= seafood
DIRECT= seafood
SHARED= seafood
PASS= True

'오징어'
EXPECTED= seafood
DIRECT= seafood
SHARED= seafood
PASS= True
~~~

Observed aggregate result:

~~~text
IPS_PROVIDER_SELECTION_PASS= True
~~~

---

# 6. Legacy Selection Evidence

Representative legacy-domain selection was observed as follows:

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
~~~

Both canonical resolution paths returned the expected provider for
every representative case.

Observed aggregate result:

~~~text
IPS_PROVIDER_SELECTION_PASS= True
~~~

---

# 7. Undeclared Alias Boundary Evidence

Observed:

~~~text
'광어'
DIRECT= None
SHARED= None
SEAFOOD_NOT_SELECTED= True

'국산 광어'
DIRECT= None
SHARED= None
SEAFOOD_NOT_SELECTED= True

'광어회'
DIRECT= None
SHARED= None
SEAFOOD_NOT_SELECTED= True

'넙치'
DIRECT= None
SHARED= None
SEAFOOD_NOT_SELECTED= True

'국산 넙치'
DIRECT= None
SHARED= None
SEAFOOD_NOT_SELECTED= True
~~~

Observed aggregate result:

~~~text
SEAFOOD_UNDECLARED_ALIAS_BOUNDARY_PASS= True
~~~

---

# 8. Compilation and Domain Regression Evidence

Observed compilation result:

~~~text
compile_exit_code=0
~~~

Observed Seafood domain regression:

~~~text
63 passed
~~~

These results establish that the provider-selection verification
evidence was obtained from a compilable runtime with the Seafood domain
test suite passing.

---

# 9. Requested Independent Verification

99_Integration is requested to independently reproduce and determine:

1. whether declared Seafood products select the Seafood provider;
2. whether direct and shared resolution paths agree;
3. whether representative legacy provider selections remain preserved;
4. whether undeclared aliases remain outside the current Seafood
   provider-selection contract;
5. whether Seafood provider selection introduces any unintended
   cross-domain routing collision;
6. whether the observed provider-selection behavior is suitable for
   advancement to Result Contract Verification.

---

# 10. Requested Result

If all required verification evidence is reproduced successfully, the
requested result is:

~~~text
PROVIDER SELECTION VERIFIED
~~~

with:

~~~text
IPS-SEAFOOD-2026-001
PASS
~~~

If the implementation is functionally correct but an architecture or
governance observation remains, 99_Integration MAY return:

~~~text
PASS WITH OBSERVATION
~~~

If provider selection cannot be reproduced or a material routing
regression is identified, the result SHALL NOT be PASS.

---

# 11. Requested Decision

99_Integration Verification Authority is requested to issue one of:

~~~text
PASS
PASS WITH OBSERVATION
REQUIRES REMEDIATION
FAIL
~~~

The decision SHALL distinguish verified runtime facts from architecture
observations.

---

# 12. Authority Boundary

This document does not authorize implementation changes.

99_Integration is responsible for independent verification and
verification attribution.

Seafood Domain Development remains responsible for implementation.

00_1 Master Architecture remains responsible for architecture-level
interpretation and final architecture completion decisions.

---

# 13. Next Stage

Upon successful completion of IPS-SEAFOOD-2026-001, the Seafood
Evidence Chain SHALL advance to:

~~~text
IRC-SEAFOOD-2026-001
Independent Result Contract Verification
~~~

The next stage SHALL NOT be treated as verified until its own evidence
has been independently reproduced.

---

# 14. Submission Status

~~~text
IPS-SEAFOOD-2026-001
INDEPENDENT PROVIDER SELECTION
VERIFICATION REQUESTED
~~~
