# Independent Provider Registration Verification Request

## IPR-SEAFOOD-2026-001

**Title:** Seafood Knowledge Domain — Independent Provider Registration Verification Request

---

# Document Identity

| Item                   | Value                              |
| ---------------------- | ---------------------------------- |
| Document ID            | IPR-SEAFOOD-2026-001               |
| Project                | Commerce AI Generator              |
| Domain                 | Seafood Knowledge Domain           |
| Domain Workspace       | 20_Seafood                         |
| Sprint                 | Sprint 3                           |
| Submitting Authority   | 20_Seafood Domain                  |
| Verification Authority | 99_Integration                     |
| Architecture Authority | 00_1 Master Architecture           |
| Date                   | 2026-08-10                         |
| Status                 | INDEPENDENT VERIFICATION REQUESTED |

---

# 1. Purpose

This document formally requests independent verification by **99_Integration** of the Seafood Knowledge Domain provider registration and associated integration evidence.

The Seafood Domain has completed its authorized implementation and domain-level verification under:

```text
ADA-MA-2026-019-SEAFOOD
```

and has recorded its implementation evidence in:

```text
IVR-SEAFOOD-2026-001
```

The purpose of this IPR is not to declare Integration Verification complete.

Its purpose is to transfer the Seafood implementation evidence to the independent Integration Verification Authority for reproducible verification.

The governing principle is:

```text
Domain Evidence
        ≠
Independent Verification
```

and:

```text
No Independent Evidence
        ↓
No Integration Approval
```

---

# 2. Governing References

This request shall be reviewed under the currently approved Commerce AI Generator Sprint 3 architecture and governance framework, including:

* ADA-MA-2026-019-SEAFOOD
* IVR-SEAFOOD-2026-001
* Commerce AI Generator Architecture Handbook v1.1
* SED-2026-001 Sprint 3 Domain Completion Directive
* approved Sprint 3 Domain Evidence Chain
* approved Sprint 3 Integration Verification Lifecycle
* Evidence First Principle
* Progressive Maturity Model
* Project Governance Architecture v1.0 Official
* Governance Registry v1.0 RC1
* MAN-2026-002

---

# 3. Verification Scope

99_Integration is requested to independently verify the following Seafood integration properties.

```text
Provider Registration
Provider Identity
Provider Uniqueness
Provider Ordering
Legacy Provider Preservation
Category Registration
Provider Availability
Representative Provider Selection
Negative Routing Boundaries
Result Contract Compatibility
Regression Attribution Evidence
```

This IPR is specifically the **Provider Registration verification stage**.

Subsequent verification stages remain separate:

```text
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
```

Passing this IPR shall not by itself constitute completion of those later stages.

---

# 4. Submitted Implementation

The Seafood implementation submitted for independent verification consists of:

```text
app/services/food/knowledge/seafood/
├── __init__.py
├── attributes.py
├── parser.py
├── parser_models.py
├── provider.py
├── registries.py
├── rules.py
└── scoring.py
```

Seafood verification tests:

```text
tests/services/food/knowledge/seafood/
├── test_seafood_attributes.py
├── test_seafood_parser.py
├── test_seafood_parser_models.py
├── test_seafood_provider.py
├── test_seafood_registry_integration.py
├── test_seafood_rules.py
└── test_seafood_scoring.py
```

Minimum shared registration changes:

```text
app/services/food/category_registry.py

app/services/food/knowledge/registry.py
```

No common provider contract, common knowledge model, or resolver redesign is submitted as part of this request.

---

# 5. Requested Provider Identity Verification

The expected Seafood Provider identity is:

```text
category_id = seafood
category_name = 수산물
provider = SeafoodKnowledgeProvider
```

99_Integration is requested to verify that:

```text
□ SeafoodKnowledgeProvider is importable

□ provider.category_id == "seafood"

□ provider identity is stable

□ the provider is registered exactly once

□ no existing provider is replaced

□ no existing provider is disabled

□ no duplicate provider category_id is introduced
```

---

# 6. Expected Provider Registry State

Prior to Seafood registration, the verified provider baseline was:

```text
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
```

The expected post-Seafood provider registry is:

```text
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
```

Expected provider count:

```text
15
```

Expected Seafood position:

```text
LAST
```

---

# 7. Legacy Provider Preservation Requirement

The Seafood Domain submits the following claimed invariant for independent reproduction:

```text
current_without_seafood
==
pre_seafood_baseline
```

Submitted observed evidence:

```text
legacy_exact_preservation = True

only_additive_change = True

provider_ids_unique = True
```

99_Integration shall independently confirm or reject this result.

The critical architectural requirement is not merely that Seafood exists.

It is that Seafood registration does not alter the relative order of any previously registered Provider.

---

# 8. Category Registry Verification

Expected Category Registry registration:

```text
category_id = seafood

display_name = 수산물

provider_id = seafood
```

The Category Registry change is intended to be additive only.

99_Integration is requested to verify that:

```text
□ Seafood category exists

□ provider_id resolves to seafood

□ existing categories remain available

□ Category Registry structure is unchanged

□ Resolver behavior is not redesigned

□ no unrelated category entry was altered for Seafood
```

---

# 9. Representative Seafood Selection Evidence

The Seafood Domain recorded the following representative routing results:

```text
노르웨이 연어 500g
→ seafood

냉동 새우 800g
→ seafood

자연산 대게 1kg
→ seafood

생물 전복 1kg
→ seafood

손질 오징어 500g
→ seafood
```

These cases are submitted as reproducible verification inputs.

Full Provider Selection verification remains the responsibility of the subsequent **IPS** stage.

For this IPR, they serve as supporting registration evidence.

---

# 10. Representative Legacy Routing Evidence

The Seafood Domain also recorded representative legacy routing:

```text
제주 사과 3kg
→ fruit

양배추 1통
→ vegetable

에티오피아 원두 500g
→ coffee
```

99_Integration is requested to verify that Seafood registration has not displaced these representative existing-domain routes.

This evidence does not replace broader IRR or IRG verification.

---

# 11. Negative Routing Boundary

The following ambiguous composite-food cases were intentionally excluded from Seafood ownership:

```text
간장게장
양념게장
```

Submitted observed result:

```text
간장게장
→ None

양념게장
→ None
```

Expected verification condition:

```text
provider.category_id != seafood
```

The purpose is to confirm that Seafood registration does not expand through an overly broad or ambiguous short alias.

Composite-food classification is outside the authorized Sprint 3 Seafood scope.

---

# 12. Domain Verification Evidence

The Seafood Domain test suite produced:

```text
63 passed
```

Command:

```bash
pytest -q tests/services/food/knowledge/seafood
```

Exit code:

```text
0
```

Compilation evidence:

```bash
python -m compileall -q app
```

Result:

```text
compileall_exit_code=0
```

99_Integration may independently rerun these checks as supporting evidence.

---

# 13. Cross-Domain Regression Evidence

The submitted Food Knowledge cross-domain regression result is:

```text
1813 passed
4 failed
```

The submitted full project regression result is:

```text
1858 passed
4 failed
```

The four failing tests are:

```text
tests/services/food/knowledge/cheese/
    test_cheese_registry_integration.py

tests/services/food/knowledge/coffee/
    test_coffee_registry_integration.py

tests/services/food/knowledge/herb_spice/
    test_herb_spice_registry_integration.py

tests/services/food/knowledge/vegetable/
    test_vegetable_registry_integration.py
```

These failures shall remain visible in the verification record.

They shall not be reported as passing.

---

# 14. Submitted Regression Attribution

The Seafood Domain recorded the following observation:

```text
AO-SEAFOOD-2026-001

Historical Provider Membership Expectation Drift
```

The four failing tests contain historical assertions expecting the complete Provider Registry to end with:

```text
duck
```

After authorized Seafood registration, the actual Registry ends with:

```text
duck
seafood
```

The Seafood Domain independently established:

```text
legacy_exact_preservation = True

only_additive_change = True

provider_ids_unique = True
```

Based on this evidence, the Seafood Domain classified the failures as:

```text
Historical Provider Membership Expectation Drift
```

rather than as an established Seafood runtime defect.

---

# 15. Independent Attribution Required

The attribution in Section 14 is a **Domain submission**, not an Integration Authority decision.

99_Integration is explicitly requested to independently determine whether:

```text
A. the four failures are caused only by stale fixed-membership expectations;

B. Seafood introduced an actual runtime or integration regression;

C. additional evidence is required; or

D. the failures require remediation before further promotion.
```

99_Integration shall not be required to accept the Seafood Domain attribution.

The purpose of independent verification is to reproduce and challenge the submitted evidence.

---

# 16. Cross-Domain Test Ownership Boundary

The Seafood Domain has intentionally not modified the failing tests owned by:

```text
Cheese
Coffee
Herb & Spice
Vegetable
```

This preserves Domain responsibility boundaries.

Any decision to update those expectations shall be made through the appropriate integration and governance process.

Seafood does not request authorization through this IPR to directly modify other Domain test files.

---

# 17. Evidence Requested from 99_Integration

99_Integration is requested to record independently reproducible evidence for:

```text
□ IPR-01 Seafood Provider import

□ IPR-02 Seafood Provider registration

□ IPR-03 Seafood Provider identity

□ IPR-04 Provider ID uniqueness

□ IPR-05 Provider count

□ IPR-06 Seafood registration position

□ IPR-07 Existing Provider preservation

□ IPR-08 Existing Provider relative-order preservation

□ IPR-09 Seafood Category Registry registration

□ IPR-10 Representative Seafood availability

□ IPR-11 Representative legacy availability

□ IPR-12 Ambiguous composite negative routing

□ IPR-13 Compilation safety

□ IPR-14 Regression failure reproduction

□ IPR-15 Regression attribution determination
```

---

# 18. Requested Verification Commands

The following commands are provided as reproducible starting points.

## Provider Registry

```bash
python - <<'PY'
from app.services.food.knowledge.registry import (
    list_food_providers,
)

providers = list_food_providers()

for index, provider in enumerate(providers):
    print(
        index,
        provider.category_id,
        provider.__class__.__name__,
    )
PY
```

Expected Provider order:

```text
0 fruit
1 vegetable
2 cheese
3 coffee
4 wine
5 tea
6 olive_oil
7 herb_spice
8 venison
9 goat
10 beef
11 lamb
12 chicken
13 duck
14 seafood
```

---

## Seafood Domain Verification

```bash
pytest -q tests/services/food/knowledge/seafood
```

Submitted result:

```text
63 passed
```

---

## Food Knowledge Regression

```bash
pytest -q tests/services/food/knowledge
```

Submitted result:

```text
1813 passed
4 failed
```

---

## Full Regression

```bash
pytest -q
```

Submitted result:

```text
1858 passed
4 failed
```

---

## Compilation

```bash
python -m compileall -q app
```

Submitted result:

```text
compileall_exit_code=0
```

---

# 19. IPR Acceptance Criteria

This IPR may be recorded as **PASS** when independent evidence establishes:

```text
□ Seafood Provider is registered

□ Seafood Provider ID is unique

□ Seafood Provider registration is additive

□ all pre-existing Provider identities remain available

□ all pre-existing Provider relative ordering is preserved

□ Seafood is registered at the expected position

□ Seafood Category registration is valid

□ no shared contract incompatibility is discovered

□ no registration defect is discovered

□ regression observations are independently classified
```

A regression observation may remain open without automatically causing IPR failure if 99_Integration determines that the observation is not a Provider Registration defect and records the required follow-up action.

---

# 20. IPR Failure Conditions

This IPR should fail if independent evidence establishes any of the following:

```text
- Seafood is not registered;

- Seafood Provider identity is duplicated;

- an existing Provider is removed;

- an existing Provider is replaced;

- existing Provider relative ordering is unintentionally changed;

- Seafood registration changes the shared Provider contract;

- Category Registry structure was redesigned without authorization;

- Seafood registration causes attributable runtime breakage;

- submitted evidence cannot be reproduced.
```

---

# 21. Requested Decision

The Seafood Domain requests one of the following formal outcomes from 99_Integration:

```text
PASS

PASS WITH OBSERVATION

REQUIRES REMEDIATION

FAIL
```

If the outcome is `PASS` or `PASS WITH OBSERVATION`, the Seafood Domain requests authorization to proceed to the next independent verification stage:

```text
IPS-SEAFOOD-2026-001
```

---

# 22. Current Evidence Chain

```text
ADA-MA-2026-019-SEAFOOD
        │
        ▼
Seafood Implementation
        │
        ▼
Domain Verification
        │
        └── 63 PASS
        │
        ▼
IVR-SEAFOOD-2026-001
        │
        └── IMPLEMENTATION VERIFIED
        │
        ▼
IPR-SEAFOOD-2026-001
        │
        └── INDEPENDENT VERIFICATION REQUESTED
        │
        ▼
99_Integration
        │
        └── PENDING
        │
        ▼
IPS-SEAFOOD-2026-001
        │
        └── NOT STARTED
```

---

# 23. Official Request

The **20_Seafood Domain** formally submits the Seafood Knowledge Provider for independent Provider Registration verification by **99_Integration**.

The submitted evidence demonstrates a domain implementation that:

* passes all 63 Seafood Domain tests;
* compiles successfully;
* registers a unique Seafood Provider;
* appends Seafood after the pre-existing Provider sequence;
* preserves the exact relative ordering of the existing 14 Providers;
* supports representative Seafood routing;
* preserves representative existing-domain routing; and
* avoids claiming the tested ambiguous composite-food cases.

Four cross-domain test failures remain explicitly disclosed.

The Seafood Domain has classified those failures as historical Provider membership expectation drift, but does not claim authority to make the final Integration determination.

99_Integration is requested to independently reproduce the evidence, determine regression attribution, and issue the formal IPR result.

---

**Submitted By**

**20_Seafood Domain**

Commerce AI Generator

**Date**

2026-08-10

---

## Verification Status

```text
IPR-SEAFOOD-2026-001

INDEPENDENT PROVIDER REGISTRATION
VERIFICATION REQUESTED
```

