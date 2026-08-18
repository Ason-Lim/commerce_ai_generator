# MACR-MA-2026-032-RECOMMENDATION-ENGINE

## Master Architecture Completion Review Submission

**Project:** Commerce AI Generator  
**Domain:** 32_Recommendation Engine  
**Architecture:** MA-2026-032  
**Submission Type:** Master Architecture Completion Review  
**Submitting Domain:** 32_Recommendation Engine  
**Review Authority:** 00_1 Master Architecture  
**Date:** 2026-08-18  
**Status:** SUBMITTED FOR ARCHITECTURE COMPLETION REVIEW

---

## 1. Submission Purpose

This document formally submits the MA-2026-032 Recommendation Engine
implementation to 00_1 Master Architecture for architecture completion review.

The submission requests review of the canonical Recommendation Engine
architecture developed through the independent Recommendation Engine lifecycle
following the architecture handoffs from:

- 30_Marketplace Core
- 31_Market Intelligence

This submission requests domain architecture review only.

It does not request project-level integration certification.

---

## 2. Governing Architecture Principles

The implementation was developed under the Commerce AI Generator architecture
and governance baseline.

The following principles were treated as normative:

- Parser performs parsing only.
- Scoring performs scoring only.
- Ranking performs ordering only.
- Provider performs orchestration only.
- Registry and upstream domain semantics are not redefined by Recommendation.
- Cross-domain ownership remains preserved.
- Missing evidence is distinct from observed zero.
- Evidence First governs completion claims.
- Legacy compatibility behavior is not silently promoted to canonical behavior.

---

## 3. Canonical Recommendation Architecture

The canonical Recommendation Engine now separates the following concerns:

1. Query Parsing
2. Policy Resolution
3. Recommendation Context Construction
4. Candidate Collection
5. Candidate Deduplication
6. Platform Normalization
7. Food Intelligence Enrichment
8. Price Utility Preparation
9. Trust Evidence Preparation
10. Popularity Evidence Preparation
11. Market Evidence Preparation
12. Identity Evidence Preparation
13. Canonical Component Construction
14. Canonical Scoring
15. Canonical Ranking
16. Recommendation Result Construction

The Recommendation Provider coordinates these stages without assuming ownership
of their underlying signal semantics.

---

## 4. Canonical Provider Lifecycle

The verified Provider lifecycle is:

```text
collect
  ↓
deduplicate
  ↓
normalize
  ↓
Food Intelligence enrichment
  ↓
Price preparation
  ↓
Trust preparation
  ↓
Popularity preparation
  ↓
Market preparation
  ↓
Identity preparation
  ↓
Canonical component construction
  ↓
Canonical scoring
  ↓
Canonical ranking
  ↓
RecommendationResult
```

The preparation stages are dependency-injectable and independently testable.

---

## 5. Canonical Score Contract

The canonical Recommendation Score contains six axes:

* quality
* price
* trust
* popularity
* market
* identity

Each axis separates:

* numeric value; and
* evidence availability.

Accordingly:

```text
missing evidence != observed zero
```

Available evidence participates in effective weight calculation.

Unavailable evidence contributes neither value nor configured weight.

---

## 6. Quality Boundary

Quality evidence is consumed from approved Food Intelligence enrichment.

Recommendation does not redefine Food Knowledge or Food Intelligence semantics.

Quality remains an upstream evidence source consumed by the Recommendation
Engine.

---

## 7. Price Architecture

Canonical price utility is owned by:

`app/services/recommendation/price_utility.py`

The implementation:

* parses usable positive finite raw prices;
* separates raw price from recommendation-relative utility;
* preserves equal-price equality;
* preserves monotonic lower-price preference;
* handles missing price as unavailable;
* preserves observed zero utility as available evidence;
* does not mutate source candidates;
* produces deterministic output.

Price calculation is not implemented inline in the Provider.

---

## 8. Trust Architecture

Canonical trust adaptation is owned by:

`app/services/recommendation/trust_adapter.py`

Accepted trust-specific evidence includes:

1. `trust_score`
2. `platform_trust_score`

The following are explicitly not treated as canonical trust:

* `platform_boost_score`
* `v7_platform_score`
* `v8_platform_score`
* identity evidence
* popularity/reaction evidence
* raw rating/review evidence

The previous platform-composite-to-trust fallback was removed from the
canonical Provider.

---

## 9. Popularity Architecture

Canonical popularity adaptation is owned by:

`app/services/recommendation/popularity_adapter.py`

Canonical precedence is:

1. `popularity_score`
2. `reaction_score`

The adapter does not construct popularity inline from:

* click count
* CTR
* impression count
* rating
* review count
* purchase count
* market signal score

Behavioral engagement, social proof, and market adoption remain distinct
semantic concerns.

---

## 10. Market Intelligence Handoff

Canonical market adaptation is owned by:

`app/services/recommendation/market_adapter.py`

The accepted Recommendation-facing handoff is:

```text
31_Market Intelligence
        ↓
canonical market_score
        ↓
32_Recommendation Engine
```

The Recommendation Engine does not directly reinterpret:

* `trend_score`
* `trend_direction`
* `market_signal_score`
* `market_signal_score_final`
* `propagated_market_signal_score`
* `market_stage`
* raw rating/review/purchase evidence

Market interpretation ownership therefore remains with 31_Market Intelligence.

---

## 11. Identity Architecture

Canonical identity adaptation is owned by:

`app/services/recommendation/identity_adapter.py`

Canonical precedence is:

1. `identity_score`
2. `_identity_score`
3. `_identity_validation["identity_score"]`

The latter two fields are retained as compatibility fallbacks.

The adapter:

* rejects missing/invalid/non-finite identity evidence;
* preserves observed zero;
* clamps finite values to `[0, 100]`;
* does not calculate product identity;
* does not reinterpret trust, quality, cluster confidence, family confidence,
  variant confidence, or market confidence as identity.

Identity remains independent from Trust.

---

## 12. Signal Availability Contract

The Recommendation Score contract explicitly tracks evidence availability.

This prevents missing evidence from being interpreted as observed zero.

The scoring layer renormalizes configured weights over available evidence only.

If no canonical evidence exists, scoring records insufficient evidence instead
of synthesizing a score from absent signals.

---

## 13. Scoring Architecture

Canonical scoring is owned by:

`app/services/recommendation/scoring.py`

Scoring responsibilities include:

* canonical component normalization;
* configured priority weights;
* evidence-aware weight renormalization;
* canonical final score calculation;
* structured reason codes;
* structured warnings.

Scoring does not:

* collect candidates;
* parse queries;
* resolve Marketplace semantics;
* interpret Market Intelligence raw signals;
* rank candidates.

---

## 14. Ranking Architecture

Canonical ranking is owned by:

`app/services/recommendation/ranking.py`

Ranking receives already-scored candidates and performs deterministic ordering.

Ranking does not:

* calculate scores;
* discover signals;
* mutate candidates;
* parse queries;
* perform Marketplace lookup;
* perform Market Intelligence interpretation;
* persist recommendation state.

Scoring and Ranking remain separate architectural responsibilities.

---

## 15. Parser, Policy, and Context Separation

Canonical request processing is separated across:

* `parser.py`
* `policy.py`
* `context.py`

Parser owns query parsing.

Policy owns canonical priority resolution and compatibility alias normalization.

Context binds already-parsed query semantics and already-resolved policy into
RecommendationContext.

These concerns are not merged into Provider, Scoring, or Ranking.

---

## 16. Direct Raw Provider Fallback Audit

Phase 5H-4A audited the canonical Provider for direct consumption of raw or
legacy signal semantics.

The audit searched for direct Provider fallback usage including:

* `platform_boost_score`
* `v7_platform_score`
* `v8_platform_score`
* `popularity_score`
* `reaction_score`
* `market_score`
* `trend_score`
* `identity_score`
* `_identity_score`
* `_identity_validation`

Result:

```text
DIRECT RAW PROVIDER FALLBACK
ZERO
```

Canonical preparation paths are used instead.

---

## 17. Legacy Compatibility Surface

The repository continues to contain compatibility-oriented components including:

* `recommendation_score_v8.py`
* `score_engine.py`
* `identity_engine.py`
* comparison/reason engines
* legacy compatibility tests

Some of these files retain historical direct signal semantics.

They are not declared canonical by this submission.

No legacy component removal, API migration, or compatibility deprecation is
requested as part of MA-2026-032 completion review.

Any such change requires separately authorized architecture work.

---

## 18. Verification Evidence

The final Recommendation Engine domain verification baseline is:

```text
Recommendation Regression
369 passed

Application Compile
PASS

Full Project Regression
2364 passed

git diff --check
PASS
```

Dedicated canonical tests cover:

* parser
* policy
* context
* price utility
* price/provider integration
* trust adapter
* trust/provider integration
* popularity adapter
* popularity/provider integration
* market adapter
* market/provider integration
* identity adapter
* identity/provider integration
* signal availability
* canonical scoring
* canonical ranking
* canonical provider orchestration

---

## 19. Completion Evidence Reference

The detailed evidence record is:

`CER-MA-2026-032-RECOMMENDATION-ENGINE`

That document records:

* canonical architecture boundaries;
* signal ownership;
* Provider lifecycle;
* direct fallback audit;
* compatibility boundary;
* regression evidence;
* completion candidate assessment.

---

## 20. Architecture Completion Assessment

The submitting domain records the following implementation state:

```text
Query / Context Axis            READY
Policy Axis                     READY
Quality Axis                    READY
Price Axis                      READY
Trust Axis                      READY
Popularity Axis                 READY
Market Handoff Axis             READY
Identity Axis                   READY
Canonical Scoring               READY
Canonical Ranking               READY
Provider Orchestration          READY

Direct Raw Provider Fallback    ZERO
Legacy Compatibility Surface    IDENTIFIED

Recommendation Regression       PASS
Full Project Regression         PASS
Compile                         PASS
Diff Validation                 PASS
```

---

## 21. Scope Limitation

This submission does not independently assert:

* project-level integration completion;
* API migration completion;
* UI migration completion;
* removal of legacy recommendation implementations;
* Marketplace Core completion;
* Market Intelligence completion;
* cross-domain integration certification.

Those determinations remain within their respective governance authorities.

---

## 22. Review Request

32_Recommendation Engine respectfully requests 00_1 Master Architecture to
review MA-2026-032 for:

1. canonical architecture boundary compliance;
2. Provider orchestration compliance;
3. Parser / Policy / Context separation;
4. Scoring / Ranking separation;
5. six-axis evidence architecture;
6. Marketplace and Market Intelligence ownership preservation;
7. legacy compatibility isolation;
8. evidence sufficiency;
9. domain architecture completion status.

Upon architecture approval, the domain should proceed to independent
Integration Verification according to the established governance process.

---

## 23. Requested Decision

The requested architecture decision is:

```text
MA-2026-032
RECOMMENDATION ENGINE

DOMAIN ARCHITECTURE
APPROVED
```

or an architecture review response identifying any required corrective action.

---

## 24. Submission Declaration

32_Recommendation Engine declares that this submission is based on observed
implementation and verification evidence.

No project-level integration completion claim is made by this document.

The domain requests formal architecture completion review by 00_1 Master
Architecture.

---

**Submitted by:** 32_Recommendation Engine
**Review Authority:** 00_1 Master Architecture
**Project:** Commerce AI Generator

**End of MACR-MA-2026-032-RECOMMENDATION-ENGINE**

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
