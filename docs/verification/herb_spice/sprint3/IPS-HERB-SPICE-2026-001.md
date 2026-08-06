# Provider Selection Verification Request

## IPS-HERB-SPICE-2026-001

**Title**

**Provider Selection Verification Request — Herb & Spice Knowledge Domain**

---

# Document Identity

| Item                    | Value                                            |
| ----------------------- | ------------------------------------------------ |
| Document ID             | IPS-HERB-SPICE-2026-001                          |
| Project                 | Commerce AI Generator                            |
| Domain                  | 15_Herb & Spice                                  |
| Submitted By            | 15_Herb & Spice Domain Development               |
| Submitted To            | 99_Integration                                   |
| Architecture Authority  | 00_1 Master Architecture                         |
| Governing Authorization | ADA-MA-2026-016-HERB-SPICE                       |
| Date                    | 2026-08-06                                       |
| Status                  | OFFICIAL PROVIDER SELECTION VERIFICATION REQUEST |

---

# 1. Purpose

This document requests independent verification that the shared Food Knowledge runtime selects the Herb & Spice Provider correctly for representative Herb & Spice products.

The objective is to verify deterministic Provider selection while preserving routing behavior for all previously approved Knowledge Domains.

---

# 2. Governing References

* IPR-HERB-SPICE-2026-001
* IVR-HERB-SPICE-2026-001
* ADA-MA-2026-016-HERB-SPICE
* APR-MA-2026-001 Revision 1 — Sprint 3 Architecture Review Governance
* AAR-MA-2026-001
* MAN-2026-003
* ARN-MA-2026-001 Revision 1
* SED-2026-001
* Evidence First Principle
* Progressive Maturity Model

---

# 3. Verification Scope

99_Integration is requested to verify:

## Provider Selection

* Correct Provider selection for Herb & Spice products
* Correct category resolution
* Deterministic Provider selection
* Stable runtime behavior

## Shared Resolver

* `resolve_knowledge_provider()`
* `resolve_food_provider()`
* `analyze_food_product()`

## Cross-domain Preservation

Verify that existing routing remains unchanged for:

* Fruit
* Cheese
* Coffee
* Wine
* Tea
* Olive Oil
* Venison
* Goat
* Beef
* Lamb
* Chicken
* Duck

---

# 4. Representative Verification Cases

Representative runtime verification should include at least:

| Product  | Expected Provider |
| -------- | ----------------- |
| 바질       | herb_spice        |
| 오레가노     | herb_spice        |
| 로즈마리     | herb_spice        |
| 타임       | herb_spice        |
| 계피       | herb_spice        |
| 후추       | herb_spice        |
| 파프리카 파우더 | herb_spice        |
| 강황       | herb_spice        |

Additional representative products may be selected independently by the Verification Authority.

---

# 5. Expected Runtime Behavior

The verifier is requested to confirm:

* Provider selection is deterministic.
* Exactly one Provider is selected.
* No conflicting Provider selection occurs.
* Existing Provider routing is preserved.

---

# 6. Expected Evidence

Independent verification should include:

```text
resolve_knowledge_provider()

resolve_food_provider()

analyze_food_product()
```

Evidence shall be independently recorded.

---

# 7. Expected Result

Upon successful verification:

```text
IPS-HERB-SPICE-2026-001

RESULT

PASS
```

If any routing inconsistency is identified, findings shall be documented with supporting evidence.

---

# Official Request

```text
HERB & SPICE

PROVIDER SELECTION

INDEPENDENT VERIFICATION REQUESTED
```

Successful completion of this verification authorizes progression to:

```text
IRC-HERB-SPICE-2026-001

Result Contract Verification
```

---

**Submitted By**

**15_Herb & Spice Domain Development**

Commerce AI Generator
