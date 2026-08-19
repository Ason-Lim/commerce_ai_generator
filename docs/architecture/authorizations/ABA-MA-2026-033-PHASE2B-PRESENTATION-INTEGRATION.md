# ABA-MA-2026-033-PHASE2B-PRESENTATION-INTEGRATION

# Phase 2B Selective Presentation Integration Authorization

**Project:** Commerce AI Generator

**Architecture Program:** MA-2026-033

**Architecture:** Commerce AI Experience Architecture

**Authorization Authority:** 00_1 Master Architecture

**Parent Authorization:** ADA-MA-2026-033-EXPERIENCE-ARCHITECTURE

**Completed Predecessor:** Phase 2A Comparison Experience Boundary

**Phase:** 2B

**Date:** 2026-08-19

**Status:** AUTHORIZED

---

# 1. Authorization Purpose

This document authorizes the first selective integration of the
Experience Comparison boundary into the Presentation layer.

The authorized objective is narrowly limited to replacing comparison
state transition logic currently embedded in Product Card Presentation
code with delegation to the previously established Experience
Comparison coordinator.

---

# 2. Governing Architecture Baseline

The governing completed Phase 2A baseline is:

```text
MA-2026-033

PHASE 2A
COMPARISON EXPERIENCE BOUNDARY

COMMIT
42dddae

TAG
ma-2026-033-phase2a-comparison-boundary-complete-v1.0
```

Repository state at Phase 2B pre-authorization inspection:

```text
HEAD
42dddae

HEAD / MAIN / ORIGIN
ALIGNED

WORKTREE
CLEAN
```

---

# 3. Governing Parent Authorization

The parent Architecture Development Authorization is:

```text
ADA-MA-2026-033-EXPERIENCE-ARCHITECTURE

COMMIT
2e1aaa5

TAG
ada-ma-2026-033-experience-architecture-v1.0
```

The Phase 2A write authorization is:

```text
ABA-MA-2026-033-PHASE2A-COMPARISON-BOUNDARY

COMMIT
cacb958

TAG
aba-ma-2026-033-phase2a-comparison-boundary-v1.0
```

---

# 4. Pre-Authorization Inspection Result

Phase 2B pre-authorization inspection established:

```text
Product Card comparison mutation seam
IDENTIFIED

Experience Comparison boundary
AVAILABLE

Experience tests
13 PASSED

Recommendation regression
378 PASSED

Application compile
PASS

Git diff check
PASS

Worktree
CLEAN
```

Protected Product Card baseline hash:

```text
c98f122d924474b930767aa28e44d5e1a51ddaa8
```

---

# 5. Current Presentation Responsibility

The current Product Card comparison path owns:

```text
checkbox interaction handling

Streamlit session_state reads

Streamlit session_state mutation

comparison selection normalization

comparison deduplication

maximum-selection enforcement

comparison snapshot construction

warning emission

widget rollback behavior
```

This responsibility mix exceeds the intended passive Presentation
boundary.

---

# 6. Target Integration Boundary

The target Phase 2B architecture is:

```text
Product Card Presentation
        ↓
comparison interaction intent
        ↓
Experience Comparison Coordinator
        ↓
existing Recommendation comparison contracts
        ↓
ComparisonTransitionResult
        ↓
Product Card Presentation
        ↓
Streamlit state persistence / warning / widget lifecycle
```

---

# 7. Authorized Production Modification

Phase 2B authorizes modification of exactly:

```text
app/ui/product_card_renderer.py
```

No other existing production file is authorized for modification.

---

# 8. Authorized Test Addition

Phase 2B authorizes creation of:

```text
tests/services/experience/
test_product_card_comparison_integration.py
```

No existing test file is authorized for modification.

---

# 9. Protected Experience Files

The following completed Phase 2A files are protected:

```text
app/services/experience/__init__.py

app/services/experience/comparison.py
```

Phase 2B shall consume these contracts without modifying them.

---

# 10. Protected Recommendation Files

The following Recommendation authority remains protected:

```text
app/services/recommendation/**
```

In particular:

```text
compare_identity_engine.py

compare_snapshot_engine.py
```

shall not be modified.

---

# 11. Protected Presentation Files

The following Presentation files are explicitly outside Phase 2B write
scope:

```text
app/ui/streamlit_app.py

app/ui/hero_renderer_v3.py
```

No modification is authorized.

---

# 12. Authorized Integration Responsibility

The Product Card Presentation may be modified to:

```text
import transition_comparison_selection()

delegate comparison transition logic

persist returned comparison items into session_state

rollback checkbox state when selection limit is reached

emit existing warning behavior

preserve widget lifecycle

preserve compare widget key semantics
```

---

# 13. Experience Delegation Requirement

The function:

```text
sync_compare_selection()
```

shall delegate the following responsibilities to the Experience
Comparison coordinator:

```text
normalization

deduplication

addition

removal

maximum-selection enforcement

snapshot transition
```

These responsibilities shall no longer be independently implemented in
the Presentation mutation path.

---

# 14. Presentation Ownership Requirement

Presentation shall continue to own:

```text
st.session_state access

checkbox state

warning emission

widget lifecycle

on_change callback wiring

Streamlit-specific behavior
```

No Streamlit dependency shall be introduced into the Experience layer.

---

# 15. Compare Identity Usage

Phase 2B does not require complete removal of:

```text
get_compare_identity()

build_compare_widget_key()
```

from Product Card Presentation.

These may remain where required for:

```text
widget preparation

checkbox identity

existing selection read behavior
```

The goal of Phase 2B is mutation delegation, not universal identity
dependency removal.

---

# 16. Compare Snapshot Usage

Direct use of:

```text
build_compare_snapshot()
```

inside the Product Card mutation path should be removed where the
Experience Comparison coordinator already owns snapshot transition.

No change to the canonical Recommendation snapshot implementation is
authorized.

---

# 17. Existing Behavior Preservation

Phase 2B shall preserve observable behavior for:

```text
first selection

multiple selection

duplicate selection

third-item acceptance

fourth-item rejection

deselection

checkbox rollback on limit

comparison list persistence
```

---

# 18. Explicitly Forbidden Changes

Phase 2B shall not modify or migrate:

```text
build_compare_summary()

comparison recommendation scoring

Recommendation scoring

Recommendation ranking

Product Identity architecture

Price Intelligence architecture

Preference architecture

tracking architecture

HTTP architecture

database architecture
```

---

# 19. Comparison Recommendation Finding

The existing:

```text
build_compare_summary()
```

contains recommendation-like comparison logic.

Its ownership remains unresolved under this authorization.

It shall not be copied, moved, rewritten, or reclassified during
Phase 2B.

---

# 20. Integration Test Scope

The new integration test shall verify at minimum:

```text
Product Card mutation delegates to Experience transition

selected item persists to compare_items

duplicate selection remains stable

deselection removes matching item

third item remains accepted

fourth item triggers limit behavior

checkbox is rolled back when limit reached

Experience transition result controls persisted comparison state
```

---

# 21. Test Isolation Requirement

The Phase 2B integration test should isolate the Product Card comparison
mutation seam rather than exercising the entire Streamlit application.

Streamlit-specific dependencies may be replaced with controlled test
doubles or monkeypatching only as necessary to verify:

```text
session_state persistence

warning behavior

checkbox rollback
```

---

# 22. Protected Contract Verification

Phase 2B verification shall include:

```text
Experience tests
PASS

Recommendation regression
PASS

Product Card comparison integration tests
PASS

Experience files unchanged
PASS

Recommendation files unchanged
PASS
```

---

# 23. Application Integrity Verification

Phase 2B shall require:

```text
Application compile
PASS

Git diff check
PASS

Authorized file inventory
PASS
```

---

# 24. Authorized File Boundary

Expected change inventory is limited to:

```text
MODIFY

app/ui/product_card_renderer.py


ADD

tests/services/experience/
test_product_card_comparison_integration.py
```

Unexpected production or test changes invalidate the Phase 2B
authorization boundary.

---

# 25. Completion Criteria

Phase 2B is complete when:

```text
Product Card comparison mutation delegates to Experience;

Streamlit lifecycle remains in Presentation;

Experience Comparison contract remains unchanged;

Recommendation comparison contracts remain unchanged;

observable comparison behavior is preserved;

targeted integration tests pass;

Experience regression passes;

Recommendation regression passes;

application compile passes;

git diff check passes;

authorized file boundary passes.
```

---

# 26. Phase 2B Completion Boundary

Phase 2B does not declare:

```text
Experience Architecture complete

Product Card fully migrated

Streamlit Application migrated

Comparison recommendation authority resolved

Presentation dependency cleanup complete
```

It establishes only the first selective Presentation integration seam.

---

# 27. Next Review Boundary

After Phase 2B completion, 00_1 shall determine the next architecture
step based on evidence.

Possible next candidates may include:

```text
additional comparison presentation cleanup

Revisit adapter

Preference persistence boundary

Tracking adapter

Experience presentation payload composition
```

No such migration is authorized by this document.

---

# 28. Final Authorization

```text
MA-2026-033

PHASE 2B

SELECTIVE PRESENTATION INTEGRATION

STATUS
AUTHORIZED

AUTHORIZED MODIFY
app/ui/product_card_renderer.py

AUTHORIZED ADD
tests/services/experience/
test_product_card_comparison_integration.py

EXPERIENCE IMPLEMENTATION MODIFICATION
NOT AUTHORIZED

RECOMMENDATION ENGINE MODIFICATION
NOT AUTHORIZED

STREAMLIT APP MODIFICATION
NOT AUTHORIZED

HERO RENDERER MODIFICATION
NOT AUTHORIZED

COMPARISON RECOMMENDATION LOGIC MIGRATION
NOT AUTHORIZED
```

---

**00_1 Master Architecture**

Commerce AI Generator
