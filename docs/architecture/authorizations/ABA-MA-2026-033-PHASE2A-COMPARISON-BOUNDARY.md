# ABA-MA-2026-033-PHASE2A-COMPARISON-BOUNDARY

# Phase 2A Comparison Experience Boundary Authorization

**Project:** Commerce AI Generator

**Architecture Program:** MA-2026-033

**Architecture:** Commerce AI Experience Architecture

**Authorization Authority:** 00_1 Master Architecture

**Parent Authorization:** ADA-MA-2026-033-EXPERIENCE-ARCHITECTURE

**Phase:** 2A

**Date:** 2026-08-19

**Status:** AUTHORIZED

---

# 1. Authorization Purpose

This document authorizes the first narrowly scoped production write
under MA-2026-033.

The authorized objective is to establish a pure Experience-layer
Comparison State coordination boundary without modifying the existing
Streamlit presentation runtime.

---

# 2. Governing Baseline

The governing Architecture Development Authorization is:

```text
ADA-MA-2026-033-EXPERIENCE-ARCHITECTURE

COMMIT
2e1aaa5

TAG
ada-ma-2026-033-experience-architecture-v1.0
```

Repository state at Phase 2A pre-write verification:

```text
HEAD
2e1aaa5

HEAD / MAIN / ORIGIN
ALIGNED

WORKTREE
CLEAN
```

---

# 3. Governing Discovery Evidence

Phase 1 established sufficient evidence through:

```text
PHASE 1A
Experience Production Discovery
PASS

PHASE 1B
State / Responsibility / Contract Inspection
PASS

PHASE 1C
Migration Seam / Adapter Candidate Inspection
PASS
```

The selected first migration seam is:

```text
COMPARISON STATE COORDINATION
```

---

# 4. Pre-write Verification

The Phase 2A pre-write verification established:

```text
Experience package collision
NONE

Experience test collision
NONE

Compare identity engine import
PASS

Compare snapshot engine import
PASS

Recommendation regression
378 PASSED

Application compile
PASS

Git diff check
PASS

Worktree
CLEAN
```

---

# 5. Architecture Finding

Current comparison responsibility is distributed across:

```text
Presentation

Streamlit session state

Product Card renderer

Recommendation compare identity engine

Recommendation compare snapshot engine
```

The current UI performs:

```text
selection mutation

deduplication

maximum-selection enforcement

snapshot insertion

widget-state coordination
```

inside Presentation code.

This is accepted as a valid first Experience Architecture migration
seam.

---

# 6. Target Responsibility Boundary

The intended architecture boundary is:

```text
Presentation
    ↓
comparison interaction intent
    ↓
Experience Comparison Coordinator
    ↓
existing Recommendation compare contracts
    ↓
deterministic transition result
    ↓
Presentation state persistence
```

The Experience layer shall not directly own Streamlit state.

---

# 7. Authorized Production Files

The following new production files are authorized:

```text
app/services/experience/__init__.py

app/services/experience/comparison.py
```

No other production file is authorized for modification in Phase 2A.

---

# 8. Authorized Test Files

The following new test files are authorized:

```text
tests/services/experience/__init__.py

tests/services/experience/test_comparison.py
```

No existing test file is authorized for modification in Phase 2A.

---

# 9. Authorized Comparison Responsibilities

The new Experience Comparison boundary may implement:

```text
normalize current comparison selection

deduplicate comparison selection

add selected item

remove deselected item

enforce maximum comparison size of three

consume get_compare_identity()

consume build_compare_snapshot()

return deterministic comparison transition result
```

---

# 10. Protected Existing Contracts

The following existing contracts shall remain unchanged:

```text
app/services/recommendation/
compare_identity_engine.py

app/services/recommendation/
compare_snapshot_engine.py
```

The Experience boundary shall consume these contracts.

It shall not duplicate or replace their canonical responsibility.

---

# 11. Presentation Boundary

The new Experience comparison implementation shall not import:

```text
streamlit
```

and shall not access:

```text
st.session_state

st.warning

st.rerun

Streamlit widget keys
```

Presentation remains responsible for UI framework lifecycle.

---

# 12. Explicitly Forbidden Responsibilities

The Phase 2A Experience comparison implementation shall not perform:

```text
Recommendation scoring

Recommendation ranking

comparison recommendation scoring

build_compare_summary ownership migration

price intelligence redesign

product identity redesign

HTTP access

database access

analytics logging

preference persistence

Streamlit rendering
```

---

# 13. Comparison Recommendation Finding

The existing Presentation function:

```text
build_compare_summary()
```

contains comparison recommendation logic.

This logic is explicitly excluded from Phase 2A.

It shall not be copied into the Experience layer.

Its authority disposition requires separate review against
Recommendation Engine ownership.

---

# 14. Required Contract Properties

The Experience Comparison transition shall be:

```text
pure with respect to UI framework state

deterministic

non-mutating to caller-owned input collections

stable under duplicate inputs

bounded to maximum three selections

compatible with existing compare identity semantics

compatible with existing compare snapshot semantics
```

---

# 15. Expected Transition Model

Conceptually:

```text
INPUT

current_items

selected

item

display
```

produces:

```text
OUTPUT

items

accepted

limit_reached

compare_identity
```

Exact Python representation may be a dataclass or equivalent typed
contract.

---

# 16. Required Test Coverage

Phase 2A tests shall verify at minimum:

```text
empty selection

first item selection

multiple item selection

duplicate selection

third item acceptance

fourth item rejection

deselection

identity preservation

snapshot normalization

input list non-mutation

deterministic repeated execution
```

---

# 17. Existing File Modification Boundary

The following files are explicitly protected during Phase 2A:

```text
app/ui/streamlit_app.py

app/ui/product_card_renderer.py

app/ui/hero_renderer_v3.py

app/services/recommendation/**
```

No migration call-site change is authorized yet.

---

# 18. Verification Requirements

Phase 2A implementation requires:

```text
Experience comparison tests
PASS

Recommendation regression
PASS

Application compile
PASS

Git diff check
PASS

Authorized file inventory
PASS
```

Full project regression is not required before the additive boundary
itself is proven, but may be required before Presentation integration.

---

# 19. Completion Boundary

Phase 2A is complete when:

```text
the pure Experience Comparison boundary exists;

its contract tests pass;

existing Recommendation contracts remain unchanged;

no Presentation runtime has been migrated;

no unauthorized file has changed.
```

---

# 20. Next Authorization Boundary

After Phase 2A completion, 00_1 shall independently determine whether
to authorize:

```text
PHASE 2B

SELECTIVE PRESENTATION INTEGRATION
```

Potential Phase 2B write candidates include:

```text
app/ui/product_card_renderer.py
```

and only the minimum additional Experience files necessary for
integration.

No Phase 2B write is authorized by this document.

---

# 21. Final Authorization

```text
MA-2026-033

PHASE 2A

COMPARISON EXPERIENCE BOUNDARY

STATUS
AUTHORIZED

PRODUCTION WRITE
AUTHORIZED — NEW FILES ONLY

EXISTING PRODUCTION FILE MODIFICATION
NOT AUTHORIZED

EXISTING TEST FILE MODIFICATION
NOT AUTHORIZED

STREAMLIT INTEGRATION
NOT AUTHORIZED

RECOMMENDATION ENGINE MODIFICATION
NOT AUTHORIZED
```

---

**00_1 Master Architecture**

Commerce AI Generator
