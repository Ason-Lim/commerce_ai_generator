# RAB-MA-2026-032-RECOMMENDATION-ENGINE

## Recommendation Engine Runtime Architecture Baseline

**Project:** Commerce AI Generator
**Architecture Domain:** 32_Recommendation Engine
**Authority:** 00_1 Master Architecture
**Document Type:** Runtime Architecture Baseline
**Status:** Draft for Architecture Review
**Baseline Branch:** `main`
**Baseline Commit:** `633e0e4`
**Architecture Contract:** Commerce AI Generator Architecture Handbook v1.1

---

## 1. Purpose

This document establishes the runtime architecture baseline for the Commerce AI Generator Recommendation Engine prior to canonical architecture migration.

The purpose of this baseline is to:

1. preserve the currently functioning Recommendation Engine behavior;
2. identify the actual runtime ownership of recommendation responsibilities;
3. distinguish legacy implementations from future canonical architecture;
4. freeze compatibility-sensitive runtime contracts;
5. define cross-domain dependency boundaries;
6. provide an evidence-based foundation for subsequent architecture migration.

This document does not authorize implementation changes.

---

## 2. Governing Architecture Principles

The Recommendation Engine shall remain consistent with the Commerce AI Generator Architecture Handbook v1.1.

The governing principles include:

```text
Parse once
Score separately
Register declaratively
Orchestrate centrally
Integrate safely
Extend without breaking
```

Recommendation architecture shall additionally preserve the following responsibility boundaries:

```text
Parser
- parsing only

Scoring
- scoring only

Provider / Engine
- orchestration only

Registry
- data only
```

The Recommendation Engine shall not redefine common models, shared architecture contracts, Marketplace Core contracts, Market Intelligence contracts, or Food Knowledge domain contracts.

Cross-domain architecture changes require separate architecture review.

---

## 3. Baseline Evidence

The Phase 1 and Phase 2 baseline inspections established the following repository state:

```text
Branch:                 main
Commit:                 633e0e4

python -m compileall:   PASS
Full Regression:        1995 passed
git diff --check:       PASS
Working Tree:           CLEAN
```

The Recommendation Engine therefore begins this architecture lifecycle from a functioning regression baseline.

The current baseline shall be treated as the compatibility reference for subsequent migration work.

---

## 4. Existing Recommendation Runtime

The current Recommendation Engine is not contained entirely within:

```text
app/services/recommendation/
```

Recommendation responsibilities are currently distributed across multiple runtime layers.

### 4.1 Recommendation Package

Current package contents include:

```text
app/services/recommendation/
├── __init__.py
├── compare_engine.py
├── compare_identity_engine.py
├── compare_snapshot_engine.py
├── identity_engine.py
├── market_engine.py.bak
├── price_signal_engine.py
├── reason_engine.py
├── recommendation_score_v8.py
└── score_engine.py
```

This structure does not yet match the canonical Recommendation Engine structure described in Architecture Handbook v1.1.

---

## 5. Distributed Runtime Ownership

### 5.1 API and Orchestration

Recommendation request orchestration currently exists in:

```text
app/main.py
app/services/recommendation_pipeline.py
app/services/recommendation_engine.py
```

The Recommendation Pipeline is invoked by the production API and is therefore part of the current runtime contract.

---

### 5.2 Ranking

Ranking responsibilities currently exist in:

```text
app/services/ai_ranking_engine_v7.py
app/services/ai_ranking_engine_v8.py
app/services/recommendation/score_engine.py
app/services/recommendation/recommendation_score_v8.py
app/services/recommendation_pipeline.py
```

This represents multiple generations of Recommendation and Ranking logic.

The coexistence of these implementations is considered legacy architecture debt, but not an immediate implementation defect.

---

### 5.3 Explanation

Recommendation explanation responsibilities currently exist in:

```text
app/services/recommendation/reason_engine.py
app/services/recommendation/compare_engine.py
app/services/recommendation_story_engine_v61.py
app/services/recommendation_compare_engine_v62.py
app/services/explainability_service.py
```

Explanation responsibility is therefore distributed across multiple modules.

---

### 5.4 Personalization

Personalization responsibilities currently exist in:

```text
app/services/preference_service.py
app/services/session_context_service.py
app/services/analytics_logger.py
app/main.py
```

The runtime currently maintains preference signals including:

```text
price_affinity
quality_affinity
trust_affinity
exploration_affinity
last_query
last_priority
```

Adaptive recommendation behavior is represented through:

```text
*_adaptive
```

priority modes.

Personalization shall therefore be treated as an existing subsystem dependency rather than collapsed directly into a single Recommendation module without compatibility analysis.

---

### 5.5 Identity and Comparison

Identity and comparison responsibilities currently exist in:

```text
app/services/recommendation/identity_engine.py
app/services/recommendation/compare_identity_engine.py
app/services/recommendation/compare_snapshot_engine.py
```

These modules are currently consumed directly by UI components.

Their public behavior shall therefore remain compatibility-sensitive during migration.

---

### 5.6 Price Signals

Price signal normalization currently exists in:

```text
app/services/recommendation/price_signal_engine.py
```

This module is also consumed outside the Recommendation package.

Accordingly, migration of price signal responsibilities must preserve existing import contracts until replacement consumers are validated.

---

## 6. Current Runtime Dependency Model

The current runtime can be summarized as:

```text
Marketplace / Product Data
        │
        ▼
Product / Food Intelligence
        │
        ▼
Ranking V7 / V8
        │
        ▼
Recommendation Pipeline
        │
        ├── Recommendation Scoring
        ├── Recommendation Type
        ├── Exploration / Discovery
        ├── Personalization
        ├── Revisit Logic
        └── Explanation
        │
        ▼
API / UI
```

This is the observed runtime architecture.

It is not yet the canonical target architecture.

---

## 7. Marketplace Core Boundary

Marketplace Core remains responsible for marketplace-level product and platform information.

The Recommendation Engine may consume marketplace signals such as:

```text
Marketplace Health
Listing Integrity
Platform Score
Seller Trust
Price
Availability
Delivery Signals
```

The Recommendation Engine shall not become the owner of marketplace collection, marketplace normalization, marketplace adapter behavior, or marketplace registry semantics.

Recommended dependency direction:

```text
30 Marketplace Core
        │
        │ normalized marketplace signals
        ▼
32 Recommendation Engine
```

---

## 8. Market Intelligence Boundary

Market Intelligence is an independent architecture domain.

The Recommendation Engine may consume outputs including:

```text
trend_score
trend_direction
market_stage
season_status
availability_score
price_signal
buy_timing
```

The Recommendation Engine shall not reimplement Market Intelligence classification or modify Market Intelligence results.

Recommended dependency direction:

```text
31 Market Intelligence
        │
        │ market intelligence signals
        ▼
32 Recommendation Engine
```

The existing file:

```text
app/services/recommendation/market_engine.py.bak
```

is not considered production ownership.

It shall be treated as a legacy backup artifact.

---

## 9. Recommendation Runtime Contract Freeze

The following runtime contracts shall remain frozen during initial canonicalization.

### 9.1 API Contracts

```text
/recommendations/nl
/recommendations/v2
/recommendations/revisit
```

No behavior change is authorized by this baseline document.

---

### 9.2 Recommendation Priority Semantics

Existing priority semantics shall remain compatible:

```text
ranking
mix
price
quality
trust
exploration
discovery
revisit
*_adaptive
```

Legacy aliases shall not be removed without migration evidence.

---

### 9.3 Score Compatibility

The following output fields currently participate in runtime compatibility:

```text
v7_final_score
v8_final_score
final_recommendation_score
score
adaptive_score
```

Existing aliases shall remain available during migration.

Canonicalization may define a future primary field, but removal of legacy fields requires explicit migration approval.

---

### 9.4 Personalization Contract

The following current user preference signals shall remain behaviorally compatible:

```text
price_affinity
quality_affinity
trust_affinity
exploration_affinity
last_query
last_priority
```

Recommendation architecture shall consume these signals without moving user preference data into shared Registry structures.

---

### 9.5 Recommendation Package Exports

The following existing exports shall remain compatibility-sensitive:

```text
calculate_mode_score
calculate_price_value_score
get_brix_value
calculate_reaction_trust_score
calculate_hidden_gem_score
calculate_ai_scores

classify_recommendation_type
build_reason_list

build_compare_message
build_info_chips

extract_price_signals
```

Replacement or relocation requires compatibility tests before removal.

---

## 10. Architecture Conflicts Identified

The following architecture conflicts are confirmed.

### 10.1 Canonical Structure Misalignment

Architecture Handbook v1.1 recommends:

```text
app/services/recommendation/
├── models.py
├── engine.py
├── scoring.py
├── ranking.py
├── reason_builder.py
├── personalization.py
└── policies/
```

The current runtime does not follow this ownership structure.

Classification:

```text
Architecture Debt
Canonicalization Required
Not Immediate Runtime Failure
```

---

### 10.2 Ranking Ownership Duplication

Recommendation scoring and ranking exist simultaneously across V7, V8, score engine, recommendation score, and pipeline layers.

Classification:

```text
Architecture Ownership Conflict
Migration Required
```

No scoring implementation shall be deleted or merged until compatibility behavior is captured by tests.

---

### 10.3 Explanation Ownership Duplication

Recommendation reasoning and presentation-oriented recommendation text are distributed across several modules.

Classification:

```text
Architecture Ownership Conflict
Boundary Clarification Required
```

Recommendation explanation semantics shall belong to Recommendation Engine.

UI rendering semantics shall remain outside Recommendation Engine.

---

### 10.4 UI Direct Dependency

UI modules directly consume internal Recommendation functions.

Classification:

```text
Compatibility Constraint
Migration Risk
```

Internal module relocation shall therefore require transitional compatibility exports.

---

### 10.5 Personalization Distribution

Personalization logic is split between service, API, analytics, session context, and recommendation execution.

Classification:

```text
Existing Subsystem
Canonical Interface Required
```

Direct physical consolidation is not authorized at this stage.

---

## 11. Canonical Ownership Target

The future canonical Recommendation Engine should converge toward:

```text
app/services/recommendation/
├── __init__.py
├── models.py
├── engine.py
├── scoring.py
├── ranking.py
├── reason_builder.py
├── personalization.py
├── policies/
└── compatibility/
```

The conceptual ownership shall be:

```text
models.py
- Recommendation contracts

engine.py
- orchestration

scoring.py
- recommendation score calculation only

ranking.py
- ordering and tie-breaking only

reason_builder.py
- explanation generation only

personalization.py
- recommendation-facing personalization interface

policies/
- recommendation mode policies

compatibility/
- temporary legacy compatibility adapters
```

This structure is a migration target and is not yet an implementation authorization.

---

## 12. Migration Principles

The Recommendation Engine migration shall follow:

```text
Canonical Ownership First
Compatibility Tests Second
Physical Migration Third
Legacy Removal Last
```

The migration shall be incremental.

No large-bang rewrite is authorized.

Each migration step shall preserve the full regression baseline unless an explicitly approved behavior change is introduced.

---

## 13. Non-Goals

This baseline does not authorize:

* Recommendation score redesign
* Recommendation weight changes
* API response redesign
* UI redesign
* Marketplace Core changes
* Market Intelligence changes
* Food Knowledge changes
* database schema changes
* user preference schema changes
* Registry contract changes
* shared model changes
* deletion of legacy score fields
* removal of compatibility aliases

---

## 14. Required Verification Before Migration

Before physical canonicalization begins, dedicated Recommendation Engine tests shall be added for at least:

```text
Recommendation scoring
Ranking determinism
Priority normalization
Recommendation type classification
Exploration behavior
Discovery behavior
Revisit behavior
Adaptive priority compatibility
Legacy score aliases
Explanation generation
API compatibility
```

The current Recommendation-specific test surface is insufficient for safe architecture migration.

---

## 15. Golden Regression Baseline

The following baseline shall be preserved:

```text
python -m compileall -q app
PASS

pytest -q
1995 passed

git diff --check
PASS
```

Any migration phase that reduces this baseline requires investigation before proceeding.

---

## 16. Architecture Change Classification

Changes shall be classified as follows.

### 32 Local Change

Allowed after architecture authorization when limited to Recommendation Engine implementation and compatibility-preserving behavior.

### 30 Marketplace Core Dependency Change

Requires Marketplace Core review if marketplace contracts or ownership must change.

### 31 Market Intelligence Dependency Change

Requires Market Intelligence review if Market Intelligence contracts must change.

### Master Architecture RFC

Required if the change affects:

```text
common models
shared contracts
registry structure
cross-domain dependency rules
public architecture semantics
```

---

## 17. Phase 3 Completion Criteria

This Runtime Architecture Baseline is complete when:

```text
Current runtime ownership documented
Legacy runtime dependencies identified
Score compatibility frozen
Priority compatibility frozen
Personalization compatibility frozen
Marketplace boundary documented
Market Intelligence boundary documented
Canonical ownership target documented
Migration non-goals documented
Golden regression baseline recorded
```

---

## 18. Architecture Statement

The current Recommendation Engine is a functioning legacy runtime with distributed ownership across multiple implementation generations.

Its behavior is currently validated by the project-wide regression baseline.

The architecture objective is therefore not to replace the functioning Recommendation Engine immediately.

The objective is to establish canonical ownership while preserving current runtime behavior.

Accordingly:

```text
Existing Runtime
        ↓
Characterize
        ↓
Freeze Contracts
        ↓
Establish Canonical Ownership
        ↓
Add Compatibility Evidence
        ↓
Migrate Incrementally
        ↓
Remove Legacy Only After Verification
```

---

## 19. Baseline Decision

```text
RECOMMENDATION ENGINE
RUNTIME ARCHITECTURE BASELINE

STATUS:
ESTABLISHED FOR ARCHITECTURE REVIEW

IMPLEMENTATION CHANGE:
NOT YET AUTHORIZED

NEXT:
ARCHITECTURE AUTHORIZATION
AND
COMPATIBILITY TEST FOUNDATION
```

---

**32_Recommendation Engine**
Commerce AI Generator

---

## Authoritative Canonical Implementation Baseline

The canonical Recommendation Engine implementation reviewed by this
artifact is fixed at the following Git baseline:

```text
CANONICAL IMPLEMENTATION BASELINE
3e512f5

COMMIT SUBJECT
feat(recommendation): establish canonical recommendation engine

RECOMMENDATION REGRESSION
369 PASSED

FULL PROJECT REGRESSION
2364 PASSED

APPLICATION COMPILE
PASS

GIT DIFF CHECK
PASS
```

This commit is the immutable implementation and verification baseline
for MA-2026-032 architecture completion review.
