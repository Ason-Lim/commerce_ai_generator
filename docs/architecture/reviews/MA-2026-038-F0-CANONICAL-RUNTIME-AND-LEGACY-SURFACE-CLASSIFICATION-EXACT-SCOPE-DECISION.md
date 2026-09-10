# MA-2026-038 F0 Canonical Runtime and Legacy Surface Classification Exact-Scope Decision

## Status and result

- Lifecycle: `MA-2026-038`
- Stage: `F0_CANONICAL_RUNTIME_AND_LEGACY_SURFACE_CLASSIFICATION`
- Decision status: `ESTABLISHED`
- Result: `CLASSIFIED_WITH_PRESERVED_BOUNDARIES`
- Implementation authority: `NONE`

## Classification rule

Classification records current evidence and controls later bounded work. It does not authorize modification, migration, removal, test execution, or import execution.

## Active canonical runtime

The following package surfaces form the canonical Recommendation contract and runtime core:

- `app/services/recommendation/__init__.py`
- `app/services/recommendation/models.py`
- `app/services/recommendation/parser.py`
- `app/services/recommendation/policy.py`
- `app/services/recommendation/context.py`
- `app/services/recommendation/scoring.py`
- `app/services/recommendation/ranking.py`
- `app/services/recommendation/deduplication.py`
- `app/services/recommendation/reason_engine.py`
- `app/services/recommendation/provider.py`
- `app/services/recommendation/price_utility.py`

Disposition: `ACTIVE_CANONICAL_RUNTIME`.

The 51 `app/services/recommendation/cross_border*.py` files are classified as `ACTIVE_CANONICAL_RUNTIME` integration surfaces and simultaneously preserved outside F0 modification. Their classification does not reopen Cross-Border scope.

## Bounded compatibility adapters

- `app/services/recommendation_pipeline.py` — public/API compatibility facade onto canonical provider composition; owns preserved `apply_priority_sort` compatibility behavior.
- `app/services/generator_compatibility.py` — conversion boundary from canonical `RecommendationResult` to existing generator contracts.
- `app/services/recommendation/recommendation_score_v8.py` — still consumed by Streamlit UI and dedicated contract tests; this is a score compatibility surface and does not revive retired Ranking V8.

Disposition: `BOUNDED_COMPATIBILITY_ADAPTER`.

## Migration candidates

- `app/services/recommendation_engine.py`
- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`

These form an internally connected legacy facade/scoring/comparison cluster without an observed external app-or-test import root at the sealed baseline. Disposition: `MIGRATION_CANDIDATE`. Removal is not authorized; F2 must verify complete call sites and contracts again before any change.

## Retired artifacts

- `app/services/ai_ranking_engine_v7.py`
- `app/services/recommendation_intelligence_v55.py`

No external app-or-test import/call root was observed for these standalone versioned engines. Disposition: `RETIRED_ARTIFACT`. This is a governance classification, not deletion authority.

## Direct consumers outside F0 modification

- `app/main.py`
- `app/services/generator_service.py`
- `app/services/experience/`
- `app/services/preference/`

They remain consumers or independent evidence owners. F4 may admit only proven consumer alignment changes through a separate bounded decision and authority.

## Preserved invariants

- canonical ranking is `app/services/recommendation/ranking.py::rank_candidates`;
- Ranking V8 remains retired;
- Recommendation Score V8 compatibility is not Ranking V8 revival;
- duplicate ranking and priority-sort execution remains resolved;
- Cross-Border remains active but not reopened;
- upstream Food, Market, Marketplace, Product Identity, Price, Preference, and Experience ownership remains unchanged.

## Next routing

F0 is complete at the classification level. F1 may now inspect the canonical contract baseline read-only. No F1 test-write or production-write authority exists.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F0_CANONICAL_RUNTIME_AND_LEGACY_SURFACE_CLASSIFICATION
f0_classification_exact_scope_decision_write_authority=CONSUMED
f0_classification_status=ESTABLISHED
f0_classification_result=CLASSIFIED_WITH_PRESERVED_BOUNDARIES
active_canonical_core_file_count=11
active_cross_border_integration_file_count=51
bounded_compatibility_adapter_count=3
migration_candidate_count=3
retired_artifact_count=2
ranking_v8_disposition=PRESERVE_RETIRED
recommendation_score_v8_disposition=BOUNDED_COMPATIBILITY_ADAPTER
duplicate_ranking_execution_disposition=PRESERVE_RESOLVED
cross_border_reopening_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
application_import_authority=NONE
next_eligible_action=RUN_MA_2026_038_F1_CANONICAL_CONTRACT_BASELINE_READ_ONLY_PREFLIGHT
```
