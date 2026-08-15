# Architecture Development Authorization

## ADA-MA-2026-026-MARKETPLACE-CORE

**Title**
Marketplace Core Architecture Development Authorization

**Authority**
00_1 Master Architecture

**Target Domain**
30 Marketplace Core

**Date**
2026-08-15

**Status**
AUTHORIZED

---

# 1. Purpose

This Architecture Development Authorization formally authorizes controlled
architecture development for the Commerce AI Generator Marketplace Core.

The authorization is based on completed runtime boundary discovery and confirms
that Marketplace Core is not a greenfield subsystem.

A substantial marketplace runtime already exists.

Accordingly, the authorized development model is:

> Existing Runtime Formalization and Controlled Consolidation

rather than replacement or unrestricted redesign.

---

# 2. Authorization Decision

00_1 Master Architecture authorizes development of:

**30 Marketplace Core**

under the following decision.

```text
AUTHORIZATION STATUS
AUTHORIZED

DEVELOPMENT MODEL
Existing Runtime Formalization
+
Controlled Consolidation

GREENFIELD REBUILD
NOT AUTHORIZED

DESTRUCTIVE REDESIGN
NOT AUTHORIZED

EXISTING RUNTIME PRESERVATION
REQUIRED

BOUNDARY ENFORCEMENT
REQUIRED

REGRESSION PRESERVATION
REQUIRED
```

This authorization does not authorize redesign of:

* 31 Market Intelligence
* 32 Recommendation Engine
* Food Knowledge domains
* Ranking architecture
* Preference / personalization architecture

except where interface-preserving changes are necessary to establish the
Marketplace Core boundary.

---

# 3. Architecture Discovery Basis

Runtime boundary discovery confirmed an existing marketplace package:

```text
app/services/market/
```

including responsibilities for:

```text
Platform Registry
Platform Matching
Market Item Normalization
Partner Marketplace Adaptation
Delivery Policy
Market Item Deduplication
Market Item Aggregation
Search URL Construction
```

The existing implementation therefore provides a strong foundation for
formalization as the Marketplace Core architecture.

---

# 4. Authorized Marketplace Core Boundary

30 Marketplace Core shall own the following responsibilities.

## 4.1 Platform Registry

Marketplace Core owns canonical platform metadata including:

* platform identity
* display name
* platform type
* enabled state
* collection priority
* collector type
* collector identity
* source platform
* platform aliases
* platform domain markers
* supported delivery capabilities
* platform-level baseline scores
* platform search URL builder association

The current `PlatformConfig` and `PLATFORM_REGISTRY` implementation shall be
treated as the primary existing implementation candidate.

---

## 4.2 Platform Identification

Marketplace Core owns determination of marketplace/platform identity from:

* explicit platform identifiers
* platform aliases
* mall names
* seller/source fields
* marketplace URLs
* registered domain markers

Platform identification shall remain Registry-driven.

Platform-specific identification logic shall not be duplicated across
Recommendation Engine or UI layers.

---

## 4.3 Market Item Normalization

Marketplace Core owns conversion of marketplace-specific product structures
into a common marketplace item representation.

Normalization includes, where applicable:

* platform identity
* product name
* seller / mall name
* price
* original price
* discount rate
* product URL
* image URL
* delivery information
* marketplace source metadata

Marketplace-specific raw structures shall not become contracts for downstream
Recommendation components.

---

## 4.4 Partner Marketplace Adaptation

Marketplace Core owns adaptation of marketplace results obtained indirectly
through partner or source marketplaces.

Current examples include partner-filter behavior for marketplace platforms
represented through another marketplace source.

This responsibility includes source-platform preservation and canonical target
platform identification.

---

## 4.5 Delivery Policy

Marketplace Core owns platform capability representation for:

* dawn delivery
* same-day delivery
* scheduled delivery
* parcel delivery
* pickup
* address-dependent availability

Recommendation Engine may consume these capabilities.

Recommendation Engine shall not become the authority that defines marketplace
delivery capability.

---

## 4.6 Marketplace Deduplication

Marketplace Core owns marketplace-level product grouping and duplicate
suppression required before downstream recommendation processing.

Food semantic equivalence and recommendation diversity are not automatically
included in this responsibility.

Those concerns remain subject to their respective architecture boundaries.

---

## 4.7 Marketplace Aggregation

Marketplace Core owns aggregation of normalized marketplace items and
marketplace-level statistics.

The intended architectural direction is:

```text
Raw Marketplace Results
        ↓
Marketplace Adapter
        ↓
Marketplace Normalization
        ↓
Marketplace Deduplication
        ↓
Marketplace Aggregation
        ↓
Downstream Intelligence / Recommendation
```

---

## 4.8 Marketplace Search Navigation

Marketplace Core may own marketplace-specific search URL construction where the
function represents navigation into an external marketplace.

This includes Registry-associated search URL builders.

Such navigation support shall not contain Recommendation ranking logic.

---

# 5. Boundary with 31 Market Intelligence

The following responsibilities are explicitly outside Marketplace Core:

```text
market score
market stage
trend interpretation
search-interest interpretation
market signal
market message
buy timing
market trend intelligence
market signal propagation
market identity clustering
representative market pricing intelligence
```

These capabilities belong to the architecture boundary of:

**31 Market Intelligence**

Marketplace Core may provide normalized marketplace observations to Market
Intelligence.

It shall not become the authority for interpreting those observations into
market intelligence.

---

# 6. Boundary with 32 Recommendation Engine

The following responsibilities are explicitly outside Marketplace Core:

```text
recommendation ranking
recommendation score calculation
priority sorting
adaptive recommendation
user preference interpretation
personalization
recommendation reason generation
recommendation labels
recommendation response orchestration
exploration / revisit behavior
```

These responsibilities belong to:

**32 Recommendation Engine**

Marketplace Core supplies normalized marketplace inputs.

Recommendation Engine determines recommendation outcomes.

---

# 7. SearchContext Boundary

Runtime discovery confirms that `SearchContext` currently combines search and
Market Intelligence information.

The following fields represent Market Intelligence concerns:

```text
trend_score
trend_direction
trend_boost
market_signal
market_message
market_intelligence
```

Their existence inside SearchContext does not transfer ownership to
Marketplace Core.

SearchContext may transport marketplace or intelligence information across
runtime boundaries, but transportation does not imply architectural ownership.

---

# 8. Existing Versioned Market Services

Runtime discovery identified the following existing services:

```text
market_collector_v5.py
market_collector_v51.py
market_signal_propagation_v52.py
market_identity_cluster_v53.py
market_representative_price_v54.py
```

These files shall not automatically be absorbed into Marketplace Core merely
because their names contain the term `market`.

Their responsibilities must be classified semantically.

Initial architecture classification is:

```text
market_collector_v5
market_collector_v51
    → marketplace collection / market observation boundary
    → requires controlled classification

market_signal_propagation_v52
market_identity_cluster_v53
market_representative_price_v54
    → 31 Market Intelligence candidates
```

No destructive migration is authorized by this document.

---

# 9. Legacy Aggregator Boundary

Runtime discovery identified two distinct aggregation implementations:

```text
app/services/market/aggregator.py

app/services/market_aggregator.py
```

The Recommendation Pipeline currently imports:

```python
from app.services.market_aggregator import collect_market_products
```

while the structured Marketplace package contains:

```text
app.services.market.aggregator
```

This represents an architecture convergence requirement.

However, immediate deletion, replacement, or migration is not authorized
without compatibility evidence.

The package implementation shall be treated as the Marketplace Core
architecture candidate.

The top-level implementation shall be treated as an existing runtime
compatibility dependency until migration is independently verified.

---

# 10. Architecture Observations

Runtime discovery identified the following architecture observations.

## AO-MARKETPLACE-001 — Dual Aggregator Architecture

Two marketplace aggregation paths currently exist:

```text
app/services/market/aggregator.py
app/services/market_aggregator.py
```

The active Recommendation Pipeline depends on the top-level implementation.

**Classification**

```text
Architecture Convergence Candidate
```

No immediate deletion is authorized.

---

## AO-MARKETPLACE-002 — Duplicate Ranking Execution

`run_recommendation_pipeline()` currently performs the following sequence twice:

```text
rank_market_items_v8(...)
apply_priority_sort(...)
```

**Classification**

```text
Runtime Redundancy Observation
```

Remediation may be proposed separately with regression evidence.

---

## AO-MARKETPLACE-003 — Duplicate URL Detection Definition

`app/services/market/platform_matcher.py` contains two definitions of:

```text
_detect_platform_from_url()
```

The later definition replaces the earlier definition at module load time.

**Classification**

```text
Implementation Hygiene Observation
```

Removal or consolidation requires focused verification.

---

## AO-MARKETPLACE-004 — Duplicate Recommendations V2 Route

`app/main.py` contains two registrations of:

```text
GET /recommendations/v2
```

with equivalent Recommendation Pipeline invocation.

**Classification**

```text
Runtime Route Registration Observation
```

This authorization does not classify the duplicate as a proven user-visible
defect.

Controlled remediation requires route-level regression verification.

---

# 11. Preservation Requirements

Marketplace Core development shall preserve existing runtime behavior unless a
behavioral change is separately authorized.

The following principles apply:

```text
Evidence First

Preserve Before Replace

Classify Before Move

Verify Before Delete

Boundary Before Optimization
```

Existing code shall not be renamed, relocated, deleted, or merged solely for
architectural cleanliness.

Runtime evidence is required.

---

# 12. Authorized Development Activities

The Marketplace Core team is authorized to:

1. formalize Marketplace Core contracts;
2. document canonical marketplace item representation;
3. strengthen Platform Registry ownership;
4. consolidate platform identification behind Registry-driven behavior;
5. verify marketplace normalization contracts;
6. verify partner marketplace adaptation;
7. verify delivery-policy behavior;
8. establish Marketplace Core unit and integration tests;
9. classify legacy marketplace collectors;
10. prepare compatibility migration from legacy aggregation paths;
11. document boundaries with Market Intelligence;
12. document boundaries with Recommendation Engine;
13. prepare remediation proposals for recorded Architecture Observations.

---

# 13. Activities Not Authorized

The following activities are not authorized by this ADA:

* wholesale Recommendation Engine redesign;
* Ranking V8 redesign;
* preference model redesign;
* personalization redesign;
* Market Intelligence redesign;
* destructive removal of legacy marketplace services;
* database schema redesign without separate authorization;
* marketplace collector replacement without evidence;
* public API contract breakage;
* unrelated UI redesign;
* Food Knowledge architecture modification.

---

# 14. Verification Requirements

Before Marketplace Core may be declared complete, evidence shall demonstrate:

```text
Platform Registry correctness
Platform alias resolution
Platform URL/domain detection
Market item normalization
Delivery policy construction
Partner marketplace adaptation
Marketplace deduplication
Marketplace aggregation
Unknown-platform fallback behavior
Cross-platform compatibility
Recommendation integration compatibility
Regression preservation
```

Focused Marketplace Core tests shall be established where coverage is absent.

---

# 15. Completion Governance

Development authorization does not constitute completion approval.

Marketplace Core shall progress through the established evidence chain.

At minimum:

```text
Implementation
        ↓
Focused Verification
        ↓
Integration Verification
        ↓
Regression Verification
        ↓
Architecture Completion Review
```

00_1 Master Architecture retains authority over final architecture completion.

99_Integration Verification Authority retains responsibility for independent
integration and regression verification where applicable.

---

# 16. Architecture Direction

Marketplace Core shall evolve toward the following architecture:

```text
External Marketplace Sources
          │
          ▼
┌──────────────────────────────┐
│      30 Marketplace Core     │
│                              │
│ Platform Registry            │
│ Platform Identification      │
│ Collection Boundary          │
│ Partner Adaptation           │
│ Normalization                │
│ Delivery Policy              │
│ Deduplication                │
│ Aggregation                  │
└──────────────┬───────────────┘
               │
               ├──────────────► 31 Market Intelligence
               │
               └──────────────► 32 Recommendation Engine
```

Marketplace Core establishes marketplace truth.

Market Intelligence interprets market conditions.

Recommendation Engine determines recommendation outcomes.

These responsibilities shall remain architecturally distinct.

---

# 17. Final Authorization

00_1 Master Architecture concludes that sufficient architecture discovery has
been completed to authorize controlled development of 30 Marketplace Core.

The existing marketplace runtime shall be preserved and formalized rather than
replaced.

The Marketplace package under:

```text
app/services/market/
```

is designated as the primary architecture candidate for Marketplace Core.

This designation is not yet a Canonical Reference Implementation designation.

Canonical or Reference Implementation status requires separate maturity
evaluation under the established Reference Implementation Governance.

---

# Authorization

**Decision**

```text
AUTHORIZED
```

**Architecture Authority**

00_1 Master Architecture

**Document**

ADA-MA-2026-026-MARKETPLACE-CORE

**Effective Date**

2026-08-15
