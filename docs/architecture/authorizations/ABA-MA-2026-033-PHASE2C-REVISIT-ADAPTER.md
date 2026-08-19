# ABA-MA-2026-033-PHASE2C-REVISIT-ADAPTER

## Architecture Boundary Authorization

**Project:** Commerce AI Generator
**Architecture Program:** MA-2026-033
**Architecture Domain:** Experience Architecture
**Phase:** 2C
**Boundary:** Revisit Adapter
**Authority:** 00_1 Master Architecture
**Status:** AUTHORIZED
**Authorization Type:** Selective Boundary Implementation
**Implementation Scope:** Minimal Revisit Transport Abstraction

---

# 1. Authorization Purpose

This Architecture Boundary Authorization establishes the controlled
implementation boundary for MA-2026-033 Phase 2C.

Phase 2C is authorized to introduce a minimal Experience-layer Revisit
Adapter that removes direct Revisit HTTP transport knowledge from the
Presentation layer while preserving all existing Recommendation semantics,
API behavior, database ownership, and runtime result contracts.

This authorization does not authorize a redesign of the Revisit
Recommendation capability.

---

# 2. Governing Architecture Program

The governing architecture program is:

```text
MA-2026-033
EXPERIENCE ARCHITECTURE
```

Phase 2C remains subordinate to the architecture authority established by
MA-2026-033.

---

# 3. Governing Architecture Decision

The governing Experience Architecture decision is:

```text
IASM-DECISION-2026-001
EXPERIENCE ARCHITECTURE
```

Decision baseline:

```text
9774d19
iasm-decision-2026-001-v1.0
```

---

# 4. Parent Architecture Authorization

The parent Architecture Development Authorization is:

```text
ADA-MA-2026-033-EXPERIENCE-ARCHITECTURE
```

Authorization baseline:

```text
2e1aaa5
ada-ma-2026-033-experience-architecture-v1.0
```

---

# 5. Phase 2A Completion Baseline

Phase 2A established the Comparison Experience Boundary.

```text
42dddae
ma-2026-033-phase2a-comparison-boundary-complete-v1.0
```

Phase 2C shall preserve the completed Phase 2A boundary.

---

# 6. Phase 2B Completion Baseline

The authoritative implementation baseline for Phase 2C is:

```text
1dcd2b1
ma-2026-033-phase2b-presentation-integration-complete-v1.0
```

Phase 2B established selective Presentation integration with the
Experience Comparison Boundary.

Phase 2C begins from this baseline.

---

# 7. Pre-Authorization Inspection Result

The Phase 2C pre-authorization inspection identified a direct Revisit
transport dependency inside the Presentation layer.

Observed runtime path:

```text
Presentation
    |
    v
requests.get(...)
    |
    v
http://127.0.0.1:8000/recommendations/revisit
```

The direct HTTP call is currently owned by:

```text
app/ui/streamlit_app.py
```

Function:

```text
load_revisit_recommendations(session_id)
```

---

# 8. Existing Revisit API Contract

The existing Revisit endpoint is:

```text
GET /recommendations/revisit
```

The endpoint accepts:

```text
session_id
limit
```

The endpoint currently owns the existing Revisit orchestration behavior,
including retrieval of recent user interest context and invocation of the
existing Recommendation path.

Phase 2C shall not change this API contract.

---

# 9. Existing Recommendation Ownership

Revisit recommendation semantics remain owned by the existing
Recommendation/Application runtime.

Observed Recommendation concepts include:

```text
RecommendationPriority.REVISIT
revisit priority policy
revisit reason generation
revisit ranking signals
/recommendations/revisit
```

No Recommendation semantic ownership is transferred to the Experience
layer by this authorization.

---

# 10. Architecture Problem

The current Presentation layer knows the following infrastructure detail:

```text
http://127.0.0.1:8000/recommendations/revisit
```

It also directly performs:

```text
requests.get(...)
response.raise_for_status()
response.json()
```

This creates a Presentation-to-transport coupling that is inconsistent
with the Experience Architecture direction established by MA-2026-033.

---

# 11. Target Architecture

Phase 2C shall establish the following dependency direction:

```text
Presentation
    |
    v
Experience Revisit Adapter
    |
    v
Existing Revisit API
    |
    v
Existing Recommendation Runtime
```

The Experience Revisit Adapter is a boundary adapter.

It is not a Recommendation Engine.

---

# 12. Experience Revisit Adapter Responsibility

The Experience Revisit Adapter MAY own:

```text
Revisit request transport
request parameter composition
transport timeout behavior
HTTP status validation
response decoding
safe fallback response
Presentation-facing Revisit payload delivery
```

The adapter SHALL NOT own Recommendation semantics.

---

# 13. Presentation Responsibility

The Presentation layer MAY:

```text
request Revisit data through the Experience boundary
read summary
read fruit_name
read items
render Revisit results
apply presentation-only filtering
apply presentation-only ordering
limit visible presentation items
```

The Presentation layer SHALL NOT directly know the Revisit endpoint URL
after successful Phase 2C completion.

---

# 14. Recommendation Responsibility

The Recommendation/Application runtime retains ownership of:

```text
Revisit recommendation semantics
priority interpretation
ranking
scoring
reason generation
Recommendation Provider behavior
Recommendation Pipeline behavior
result generation
```

Phase 2C shall not modify these responsibilities.

---

# 15. Database Responsibility

Existing database ownership remains unchanged.

Phase 2C does not authorize migration of:

```text
engine.connect()
vw_user_top_fruit
SQL queries
session interest persistence
preference persistence
database transactions
```

Database access remains outside the Experience Revisit Adapter.

---

# 16. Authorized Additions

Phase 2C authorizes creation of:

```text
app/services/experience/revisit.py
tests/services/experience/test_revisit.py
```

No additional production module is authorized without further architecture
review.

---

# 17. Authorized Modifications

Phase 2C authorizes controlled modification of:

```text
app/services/experience/__init__.py
app/ui/streamlit_app.py
```

Modification of `streamlit_app.py` shall be limited to the Revisit
integration seam.

---

# 18. Protected Files

The following files are protected from modification under this
authorization:

```text
app/main.py
app/services/experience/comparison.py
app/ui/product_card_renderer.py
app/ui/hero_renderer_v3.py
app/services/recommendation/**
```

Any required modification to a protected file requires separate
architecture review.

---

# 19. Protected Presentation Baseline

At pre-authorization inspection, the protected Presentation file hash was:

```text
app/ui/streamlit_app.py
4d0587beac52d7f85c8306df35e5d78138160cdb
```

Phase 2C is explicitly authorized to modify this file only within the
Revisit integration seam.

Unrelated Presentation changes are prohibited.

---

# 20. Protected Comparison Baseline

The completed Comparison Experience Boundary hash observed during
pre-authorization inspection was:

```text
app/services/experience/comparison.py
33417d9c6dae9c6ec374c89b863b45a1068e6f5c
```

Phase 2C shall preserve this file unchanged.

---

# 21. Required Delegation Contract

After implementation, Presentation-level Revisit loading shall delegate to
the Experience Revisit Adapter.

The intended conceptual contract is:

```text
load_revisit_recommendations(session_id)
    |
    v
Experience Revisit Adapter
```

The existing Presentation call sites should remain stable unless a
minimal change is demonstrably required.

---

# 22. Failure Contract

The existing Presentation behavior provides a safe empty result when the
Revisit request fails.

Phase 2C shall preserve an equivalent failure contract.

Minimum safe result:

```text
summary = ""
fruit_name = ""
items = []
```

Transport failure shall not crash the Presentation runtime.

---

# 23. Input Contract

The Experience Revisit Adapter shall accept the minimum information
required to execute the existing Revisit request.

Primary input:

```text
session_id
```

Any additional configuration shall remain infrastructure-oriented and
shall not introduce Recommendation semantics.

---

# 24. Output Contract

The Experience Revisit Adapter shall return a Presentation-compatible
mapping containing the existing Revisit response shape.

Expected fields include:

```text
summary
fruit_name
items
```

The adapter shall not invent new Recommendation ranking or scoring fields.

---

# 25. Tracking Boundary Exclusion

The pre-authorization inspection also identified a separate Presentation
HTTP seam associated with:

```text
track-click
```

That seam is explicitly excluded from Phase 2C.

Phase 2C SHALL NOT modify or migrate Tracking behavior.

Tracking Adapter work requires a separate authorization.

---

# 26. Preference Boundary Exclusion

Phase 2C does not authorize:

```text
Preference Persistence migration
session preference redesign
user profile redesign
database persistence abstraction
```

These remain future architecture candidates.

---

# 27. General HTTP Cleanup Exclusion

This authorization is not a general Presentation HTTP cleanup.

Only the Revisit transport seam is authorized.

The existence of other direct transport dependencies does not expand the
Phase 2C implementation boundary.

---

# 28. Recommendation Modification Prohibition

Phase 2C SHALL NOT modify:

```text
ranking logic
scoring logic
RecommendationPriority
Recommendation Provider
Recommendation Pipeline
reason generation
market signal composition
identity composition
```

Recommendation regression protection is mandatory.

---

# 29. Experience Boundary Principle

The Experience layer shall coordinate consumer-facing interaction
boundaries without absorbing domain semantics that belong to
Recommendation, Market Intelligence, Marketplace Core, or persistence
infrastructure.

Therefore:

```text
Experience owns interaction boundary adaptation.

Recommendation owns recommendation intelligence.
```

---

# 30. Required Tests

Phase 2C implementation shall provide tests covering at minimum:

```text
successful Revisit response
session_id parameter forwarding
response payload preservation
transport failure fallback
HTTP error fallback
invalid or exceptional response handling
Presentation delegation
```

Tests shall not require a live external HTTP server.

---

# 31. Regression Requirements

Before Phase 2C may be considered complete, the following shall pass:

```text
tests/services/experience
tests/services/recommendation
```

Application compilation shall also pass.

---

# 32. Repository Integrity Requirements

Completion evidence shall include:

```text
python -m compileall -q app
git diff --check
```

The final implementation boundary shall contain only authorized files.

---

# 33. Baseline Test Evidence

Pre-authorization baseline evidence established:

```text
EXPERIENCE
19 PASSED

RECOMMENDATION
378 PASSED

APPLICATION COMPILE
PASS

GIT DIFF CHECK
PASS
```

These results form the regression reference for Phase 2C.

---

# 34. Implementation Boundary

The complete authorized Phase 2C write boundary is:

```text
AUTHORIZED ADD

app/services/experience/revisit.py
tests/services/experience/test_revisit.py


AUTHORIZED MODIFY

app/services/experience/__init__.py
app/ui/streamlit_app.py
```

No other file modification is authorized.

---

# 35. Completion Evidence Requirement

Phase 2C completion evidence shall demonstrate:

```text
Revisit transport moved behind Experience boundary
Presentation no longer directly calls Revisit HTTP endpoint
existing Revisit API contract preserved
existing Recommendation semantics preserved
safe failure behavior preserved
Tracking seam unchanged
Comparison boundary unchanged
authorized file boundary respected
Experience regression PASS
Recommendation regression PASS
compile PASS
diff check PASS
```

---

# 36. Completion State

Successful implementation and verification shall permit Phase 2C to enter:

```text
COMPLETE CANDIDATE
```

Architecture completion remains subject to evidence review.

---

# 37. Subsequent Architecture Work

Completion of Phase 2C does not automatically authorize subsequent
Experience Architecture phases.

Potential future candidates include:

```text
Tracking Adapter
Preference Persistence Boundary
Experience Presentation Payload Composition
```

Each requires independent inspection and authorization.

---

# 38. Final Authorization

00_1 Master Architecture authorizes:

```text
MA-2026-033
PHASE 2C
REVISIT ADAPTER

AUTHORIZED
```

Authorized scope:

```text
REVISIT TRANSPORT ABSTRACTION
EXPERIENCE BOUNDARY DELEGATION
SAFE RESPONSE ADAPTATION
TARGETED PRESENTATION INTEGRATION
```

Not authorized:

```text
TRACKING MIGRATION
PREFERENCE MIGRATION
RECOMMENDATION ENGINE MODIFICATION
DATABASE OWNERSHIP MIGRATION
GENERAL PRESENTATION REFACTOR
GENERAL HTTP CLEANUP
```

---

# 39. Governing Implementation Baseline

Implementation shall begin only after this authorization is committed and
tagged.

The resulting ABA commit and tag shall become the governing implementation
baseline for MA-2026-033 Phase 2C.

---

# 40. Architecture Authority Statement

This authorization intentionally favors a narrow, evidence-backed seam
over broad refactoring.

Phase 2C shall remove one specific Presentation infrastructure dependency
without disturbing the already validated Recommendation and Comparison
architecture.

```text
FINAL STATUS
AUTHORIZED

MA-2026-033 PHASE 2C
REVISIT ADAPTER

WRITE BOUNDARY
CONTROLLED

IMPLEMENTATION
AUTHORIZED AFTER ABA BASELINE COMMIT
```

---

**End of Document**
