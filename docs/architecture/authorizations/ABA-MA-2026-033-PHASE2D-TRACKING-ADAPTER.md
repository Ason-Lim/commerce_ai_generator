# ABA-MA-2026-033-PHASE2D-TRACKING-ADAPTER

## Architecture Boundary Authorization

**Project:** Commerce AI Generator

**Architecture Program:** MA-2026-033

**Architecture Domain:** Experience Architecture

**Phase:** 2D

**Boundary:** Tracking Adapter

**Authority:** 00_1 Master Architecture

**Status:** AUTHORIZED

**Authorization Type:** Selective Boundary Implementation

---

# 1. Authorization Purpose

This document authorizes MA-2026-033 Phase 2D implementation of a
minimal Experience-layer Tracking Adapter.

The purpose is to remove direct tracking URL composition and endpoint
knowledge from Presentation while preserving the existing Tracking API,
click logging semantics, redirect behavior, Recommendation behavior,
database ownership, and completed Experience boundaries.

---

# 2. Governing Architecture Program

The governing architecture program is:

```text
MA-2026-033
EXPERIENCE ARCHITECTURE
```

Phase 2D remains subordinate to the approved Experience Architecture.

---

# 3. Governing Completion Baseline

The authoritative Phase 2D implementation baseline is:

```text
COMMIT
cafdeae

TAG
ma-2026-033-phase2c-revisit-adapter-complete-v1.0
```

Repository state:

```text
HEAD = main = origin/main
PASS

WORKTREE
CLEAN
```

---

# 4. Previous Experience Boundaries

The following completed Experience boundaries shall remain preserved:

```text
Phase 2A
Comparison Experience Boundary

Phase 2B
Selective Presentation Integration

Phase 2C
Revisit Adapter
```

Phase 2D shall not alter their established architecture responsibilities.

---

# 5. Pre-Authorization Inspection Result

Inspection identified the current tracking URL builder in:

```text
app/ui/streamlit_app.py
```

Function:

```text
build_tracking_url()
```

Current responsibilities include:

```text
Presentation session context read
Tracking parameter construction
Tracking query encoding
Tracking endpoint composition
```

---

# 6. Existing Tracking Runtime

The existing tracking endpoint is:

```text
GET /track-click
```

owned by:

```text
app/main.py
```

The endpoint currently performs:

```text
click logging
product URL validation
redirect response
```

These behaviors shall remain unchanged.

---

# 7. Existing Tracking API Parameters

The current tracking API accepts:

```text
session_id
query
product_name
seller_name
product_url
selected_priority
selected_section
recommendation_mode
fruit_name
```

Phase 2D shall preserve these parameter semantics.

---

# 8. Architecture Problem

Presentation currently contains infrastructure knowledge:

```text
http://127.0.0.1:8000/track-click
```

and directly owns:

```text
urlencode()
tracking parameter composition
tracking endpoint composition
```

This creates unnecessary Presentation-to-transport coupling.

---

# 9. Target Architecture

Phase 2D shall establish:

```text
Presentation
    ↓
Experience Tracking Adapter
    ↓
Existing /track-click API
    ↓
Existing click logging
    ↓
Existing redirect semantics
```

The Experience Tracking Adapter is a Presentation-facing transport
composition boundary.

It is not a Tracking analytics engine.

---

# 10. Presentation Responsibility

Presentation shall continue to own:

```text
st.session_state access
current session_id acquisition
current query acquisition
product interaction intent
CTA rendering
widget lifecycle
```

No Streamlit dependency shall enter the Experience Tracking Adapter.

---

# 11. Experience Tracking Responsibility

The Experience Tracking Adapter MAY own:

```text
tracking parameter normalization
tracking query construction
URL encoding
tracking endpoint composition
Presentation-facing tracking URL generation
```

The adapter shall operate on plain Python values.

---

# 12. Tracking Runtime Responsibility

The existing application runtime retains ownership of:

```text
log_product_click()
click persistence
product URL validation
redirect behavior
tracking endpoint semantics
```

Phase 2D shall not move these responsibilities.

---

# 13. Recommendation Boundary

Phase 2D shall not modify:

```text
Recommendation scoring
Recommendation ranking
Recommendation Provider
Recommendation Pipeline
RecommendationPriority
reason generation
market signal composition
identity composition
```

Tracking URL composition shall remain independent of Recommendation
intelligence.

---

# 14. Database Boundary

Phase 2D does not authorize:

```text
database migration
click persistence redesign
SQL ownership migration
preference persistence migration
transaction redesign
```

Database and persistence behavior remain unchanged.

---

# 15. Product Card Boundary

Inspection established that:

```text
app/ui/product_card_renderer.py
```

consumes an injected:

```text
build_tracking_url
```

service.

Therefore Product Card modification is not required and is prohibited
under this authorization.

---

# 16. Hero Renderer Boundary

The following remains protected:

```text
app/ui/hero_renderer_v3.py
```

No Hero Renderer modification is authorized.

---

# 17. Revisit Boundary

The completed Revisit Adapter remains protected:

```text
app/services/experience/revisit.py
```

Phase 2D shall not modify Revisit behavior.

---

# 18. Comparison Boundary

The completed Comparison Experience Boundary remains protected:

```text
app/services/experience/comparison.py
```

No comparison behavior is authorized for modification.

---

# 19. Protected File Hashes

Pre-authorization protected hashes:

```text
app/main.py
b124643bfa2e722b40022c6e40fc1728061f3e4d

app/services/experience/comparison.py
33417d9c6dae9c6ec374c89b863b45a1068e6f5c

app/services/experience/revisit.py
3465d1b296ef78d6d5f7de08f95b33108e6d5d02

app/ui/product_card_renderer.py
0c0b2ac8cd9a0735b3bfc0d492efec32bd35ff12

app/ui/hero_renderer_v3.py
175171e5d07555151fdfe54040b86122a35ad817
```

---

# 20. Tracking Module Collision Check

Pre-authorization inspection confirmed:

```text
app/services/experience/tracking.py
AVAILABLE

tests/services/experience/test_tracking.py
AVAILABLE
```

No existing module collision was identified.

---

# 21. Authorized Additions

Phase 2D authorizes creation of:

```text
app/services/experience/tracking.py

tests/services/experience/test_tracking.py
```

No additional production or test file may be created.

---

# 22. Authorized Modifications

Phase 2D authorizes controlled modification of:

```text
app/services/experience/__init__.py

app/ui/streamlit_app.py
```

The `streamlit_app.py` modification shall be limited to the
`build_tracking_url()` integration seam and required import cleanup.

---

# 23. Protected Files

The following are explicitly protected:

```text
app/main.py

app/services/experience/comparison.py

app/services/experience/revisit.py

app/ui/product_card_renderer.py

app/ui/hero_renderer_v3.py

app/services/recommendation/**
```

Modification requires separate architecture authorization.

---

# 24. Required Delegation Contract

After Phase 2D implementation:

```text
build_tracking_url()
```

shall retain Presentation context acquisition but delegate tracking URL
composition to the Experience Tracking Adapter.

Conceptually:

```text
Presentation
    ├─ session_id
    ├─ query
    ├─ product_url
    ├─ item
    ├─ section
    └─ priority
          ↓
Experience Tracking Adapter
          ↓
tracking URL
```

---

# 25. Required Input Contract

The Experience Tracking Adapter shall accept plain Python inputs
sufficient to preserve the current contract.

Expected inputs include:

```text
product_url
item
session_id
query
section
priority
```

The adapter shall not read `st.session_state`.

---

# 26. Required Output Contract

The primary output is:

```text
tracking URL string
```

If `product_url` is empty, the current behavior shall remain:

```text
""
```

---

# 27. Parameter Preservation Requirement

The generated URL shall preserve the current parameter names:

```text
session_id
query
product_name
seller_name
product_url
selected_priority
selected_section
recommendation_mode
fruit_name
```

No parameter rename is authorized.

---

# 28. Item Field Semantics

Existing item fallbacks shall be preserved:

```text
product_name
or name

seller_name
or ""

recommendation_mode
or "ranking"

fruit_name
or ""
```

Phase 2D shall not reinterpret these values.

---

# 29. Endpoint Preservation Requirement

The Tracking Adapter may own the canonical tracking endpoint value:

```text
http://127.0.0.1:8000/track-click
```

The Presentation layer shall no longer directly compose this endpoint
after successful Phase 2D completion.

---

# 30. Existing API Preservation

Phase 2D shall not modify:

```text
@app.get("/track-click")
track_click()
log_product_click()
RedirectResponse behavior
```

The existing runtime contract remains authoritative.

---

# 31. Existing Consumer Preservation

Existing consumers of:

```text
build_tracking_url()
```

shall remain compatible.

This includes:

```text
Hero Presentation usage
Product Card service injection
CTA rendering
```

No consumer signature change is authorized unless required solely to
preserve existing behavior and independently reviewed.

---

# 32. Tracking Analytics Boundary

Phase 2D does not establish a new analytics subsystem.

The Experience Tracking Adapter shall not own:

```text
click analytics
engagement scoring
conversion modeling
event aggregation
recommendation adaptation
user preference mutation
```

---

# 33. Tracking Failure Semantics

Tracking URL generation is a local composition operation.

Phase 2D shall not introduce:

```text
live tracking HTTP requests
network retries
background delivery
async tracking execution
```

The resulting URL shall continue to be consumed by browser navigation.

---

# 34. General HTTP Cleanup Exclusion

Phase 2D is not a general Presentation HTTP cleanup.

Only the tracking URL composition seam is authorized.

Other HTTP or infrastructure dependencies remain outside this phase.

---

# 35. Preference Boundary Exclusion

Phase 2D does not authorize:

```text
Preference Persistence Boundary
user profile migration
session preference redesign
database persistence abstraction
```

These remain separate future architecture candidates.

---

# 36. Presentation Payload Exclusion

Phase 2D does not authorize:

```text
Experience Presentation Payload Composition
general view-model redesign
Product Card payload rewrite
Hero payload rewrite
```

---

# 37. Required Tracking Tests

Tests shall verify at minimum:

```text
empty product URL
canonical URL generation
session_id forwarding
query forwarding
product_name fallback
seller_name forwarding
priority forwarding
section forwarding
recommendation_mode fallback
fruit_name forwarding
URL encoding
Presentation delegation
```

Tests shall not require a live server.

---

# 38. Regression Requirements

Before Phase 2D completion:

```text
tests/services/experience
PASS

tests/services/recommendation
PASS
```

The existing baseline is:

```text
Experience
31 PASSED

Recommendation
378 PASSED
```

---

# 39. Repository Integrity Requirements

Completion evidence shall include:

```text
python -m compileall -q app
PASS

git diff --check
PASS

authorized file inventory
PASS
```

---

# 40. Authorized Write Boundary

The complete Phase 2D write boundary is:

```text
AUTHORIZED ADD

app/services/experience/tracking.py
tests/services/experience/test_tracking.py


AUTHORIZED MODIFY

app/services/experience/__init__.py
app/ui/streamlit_app.py
```

No other file is authorized.

---

# 41. Completion Criteria

Phase 2D may enter COMPLETE CANDIDATE state when:

```text
Tracking URL composition is delegated to Experience
Presentation no longer owns /track-click endpoint composition
Streamlit state acquisition remains in Presentation
Tracking API remains unchanged
Tracking semantics remain unchanged
Product Card remains unchanged
Hero Renderer remains unchanged
Revisit Adapter remains unchanged
Comparison boundary remains unchanged
Recommendation boundary remains unchanged
Experience tests pass
Recommendation regression passes
compile passes
diff check passes
authorized file boundary passes
```

---

# 42. Subsequent Architecture Work

Completion of Phase 2D does not authorize the next MA-2026-033 phase.

Remaining candidates include:

```text
Preference Persistence Boundary

Experience Presentation Payload Composition
```

A new inspection and authorization are required.

---

# 43. Final Authorization

00_1 Master Architecture authorizes:

```text
MA-2026-033

PHASE 2D

TRACKING ADAPTER

STATUS
AUTHORIZED
```

Authorized purpose:

```text
TRACKING URL COMPOSITION EXTRACTION

PRESENTATION → EXPERIENCE DELEGATION

TRACKING ENDPOINT ABSTRACTION
```

Not authorized:

```text
TRACKING API MODIFICATION
TRACKING ANALYTICS REDESIGN
DATABASE MIGRATION
RECOMMENDATION MODIFICATION
PREFERENCE MIGRATION
GENERAL PRESENTATION REFACTOR
GENERAL HTTP CLEANUP
```

---

# 44. Governing Implementation Baseline

Implementation shall begin only after this ABA is:

```text
verified
committed
pushed
tagged
```

The resulting ABA commit and tag become the authoritative Phase 2D
implementation baseline.

---

# 45. Architecture Authority Statement

Phase 2D continues the incremental MA-2026-033 migration strategy:

```text
Presentation-specific context
        ↓
Experience interaction boundary
        ↓
Existing governed runtime
```

The objective is not code movement for its own sake.

The objective is explicit responsibility ownership.

```text
FINAL STATUS
AUTHORIZED

MA-2026-033 PHASE 2D
TRACKING ADAPTER

WRITE BOUNDARY
CONTROLLED

IMPLEMENTATION
AUTHORIZED AFTER ABA BASELINE COMMIT
```

---

**00_1 Master Architecture**

Commerce AI Generator
