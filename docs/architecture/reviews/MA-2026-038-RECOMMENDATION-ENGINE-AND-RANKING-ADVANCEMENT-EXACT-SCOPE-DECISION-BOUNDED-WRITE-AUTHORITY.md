# MA-2026-038 Recommendation Engine and Ranking Advancement Exact-Scope Decision Bounded Write Authority

## Status

ESTABLISHED — ONE USE — BOUNDED

## Authorized operation

Create exactly one exact-scope decision artifact at:

`docs/architecture/reviews/MA-2026-038-RECOMMENDATION-ENGINE-AND-RANKING-ADVANCEMENT-EXACT-SCOPE-DECISION.md`

The decision must classify the lifecycle into separately governed stages. It may establish architecture and verification scope, but it may not authorize or perform implementation.

## Required admitted scope

1. Baseline and ownership classification of the canonical `app/services/recommendation/` package.
2. Classification of legacy-generation surfaces including Ranking V7, older recommendation engines, score engines, and compatibility paths.
3. Canonical runtime convergence planning across recommendation scoring, ranking, provider orchestration, and `RecommendationResult`.
4. Direct consumer alignment for the recommendation pipeline, API, UI, generator compatibility, preference consumption, and selected integration contracts.
5. Independent verification and regression boundaries before completion.

## Required preserved facts

- Ranking V8 production runtime was retired; it must not be reintroduced.
- The earlier duplicate ranking and priority-sort execution was resolved; it is not an open defect.
- Ranking remains owned by `32_RECOMMENDATION_ENGINE`.
- Food Intelligence, Market Intelligence, Marketplace Core, Product Identity, Price Intelligence, Preference, Experience, and Cross-Border retain their own ownership.
- Existing Cross-Border Recommendation integration is preserved unless a later exact subwave separately proves a required change.

## Exclusions

This authority grants no production, test, resource, registry-data, database, migration, deployment, full-suite, application-import, Cross-Border reopening, upstream-domain redesign, or lifecycle-completion authority.

It authorizes exactly one decision file, one commit, one annotated tag, and one atomic push.

## State markers

```text
lifecycle_identity=MA-2026-038
lifecycle_subject=RECOMMENDATION_ENGINE_AND_RANKING_ADVANCEMENT
exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
exact_scope_status=NOT_ESTABLISHED
scope_structure=STAGED_CANONICAL_CONVERGENCE
ranking_v8_disposition=PRESERVE_RETIRED
duplicate_ranking_execution_disposition=PRESERVE_RESOLVED
production_write_authority=NONE
test_write_authority=NONE
resource_write_authority=NONE
tests_execution_authority=NONE
application_import_authority=NONE
```
