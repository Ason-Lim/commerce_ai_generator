# MA-2026-038 F2-A Four-File Removal Execution Exact-Scope Decision

## Status and result

- Lifecycle: `MA-2026-038`
- Stage: `F2A_FOUR_FILE_REMOVAL_EXECUTION`
- Decision status: `ESTABLISHED`
- Result: `ESTABLISH_EXACT_FOUR_FILE_REMOVAL_AND_37_FILE_VERIFICATION_SCOPE`
- Execution authority: `NONE`

## Exact removal set

Exactly these four tracked production files form one atomic deletion set:

1. `app/services/recommendation_engine.py`
2. `app/services/recommendation/score_engine.py`
3. `app/services/recommendation/compare_engine.py`
4. `app/services/ai_ranking_engine_v7.py`

No partial deletion and no fifth production target is admitted.

## Preserved production boundary

These files must remain present and unchanged:

- `app/services/recommendation_pipeline.py`
- `app/services/generator_compatibility.py`
- `app/services/recommendation/recommendation_score_v8.py`
- `app/services/recommendation_intelligence_v55.py`

V55 remains `PRESERVED_DEFERRED`. Ranking Score V8 remains a bounded compatibility surface and does not revive retired Ranking Engine V7.

## Exact post-removal verification scope

One pytest invocation must select exactly the following 37 tracked test files.

### Group A — direct canonical contract: 15 files

- `tests/services/recommendation/test_canonical_context_contract.py`
- `tests/services/recommendation/test_canonical_deduplication_contract.py`
- `tests/services/recommendation/test_canonical_identity_provider_integration.py`
- `tests/services/recommendation/test_canonical_market_provider_integration.py`
- `tests/services/recommendation/test_canonical_parser_contract.py`
- `tests/services/recommendation/test_canonical_policy_contract.py`
- `tests/services/recommendation/test_canonical_popularity_provider_integration.py`
- `tests/services/recommendation/test_canonical_price_provider_integration.py`
- `tests/services/recommendation/test_canonical_price_utility_contract.py`
- `tests/services/recommendation/test_canonical_provider_contract.py`
- `tests/services/recommendation/test_canonical_ranking_contract.py`
- `tests/services/recommendation/test_canonical_scoring_contract.py`
- `tests/services/recommendation/test_canonical_signal_availability_contract.py`
- `tests/services/recommendation/test_canonical_trust_provider_integration.py`
- `tests/services/recommendation/test_models_contract.py`

### Group B — preserved Cross-Border contracts: 20 files

- `tests/services/recommendation/test_cross_border_aligned_controlled_scoring.py`
- `tests/services/recommendation/test_cross_border_aligned_scoring_runtime_composition.py`
- `tests/services/recommendation/test_cross_border_candidate_component_alignment.py`
- `tests/services/recommendation/test_cross_border_candidate_component_binding.py`
- `tests/services/recommendation/test_cross_border_candidate_disclosure_projection.py`
- `tests/services/recommendation/test_cross_border_candidate_ranking.py`
- `tests/services/recommendation/test_cross_border_candidate_score_composition.py`
- `tests/services/recommendation/test_cross_border_canonical_candidate_projection.py`
- `tests/services/recommendation/test_cross_border_canonical_result_composition.py`
- `tests/services/recommendation/test_cross_border_canonical_result_projection.py`
- `tests/services/recommendation/test_cross_border_controlled_provider_binding.py`
- `tests/services/recommendation/test_cross_border_controlled_scoring.py`
- `tests/services/recommendation/test_cross_border_original_candidate_binding.py`
- `tests/services/recommendation/test_cross_border_original_candidate_binding_set.py`
- `tests/services/recommendation/test_cross_border_price_signal_adapter.py`
- `tests/services/recommendation/test_cross_border_production_entrypoint_binding.py`
- `tests/services/recommendation/test_cross_border_production_provider_composition.py`
- `tests/services/recommendation/test_cross_border_provider_adjacent_result_orchestration.py`
- `tests/services/recommendation/test_cross_border_ranked_original_candidate.py`
- `tests/services/recommendation/test_cross_border_upstream_result_composition.py`

### Group C — compatibility contract: 1 file

- `tests/services/recommendation/test_production_compatibility_adapter.py`

### Group D — F2-A removal boundary: 1 file

- `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`

The expected post-removal result is 416 passing tests, derived from the sealed 412-pass F1 baseline and sealed 4-pass F2-A protection. The actual collected count must be reported and must equal 416; failures, errors, and skips must all equal zero.

## Required future execution shape

Any later implementation requires a separate one-use bounded production deletion and verification execution authority. It must:

1. verify all four source hashes and all preserved boundaries before deletion;
2. delete exactly the four files as one staged set;
3. execute exactly one pytest invocation over the 37 listed files;
4. require exactly 416 passes with zero failures, errors, and skips;
5. create exactly one four-file deletion commit, one annotated tag, and atomically push `main` with that tag.

## Exclusions

- no test or preserved production modification;
- no fifth production deletion;
- no V55 or Persistence-test modification;
- no application import or full-suite execution;
- no Cross-Border reopening or Ranking V8 revival;
- no F2-B/F3 opening, database operation, migration, deployment, or lifecycle completion.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_FOUR_FILE_REMOVAL_EXECUTION
f2a_removal_execution_exact_scope_decision_write_authority=CONSUMED
f2a_removal_execution_exact_scope_status=ESTABLISHED
f2a_removal_execution_exact_scope_result=ESTABLISH_EXACT_FOUR_FILE_REMOVAL_AND_37_FILE_VERIFICATION_SCOPE
removal_candidate_file_count=4
preserved_file_count=4
post_removal_verification_file_count=37
post_removal_expected_test_result=SATISFIED_416_PASS
post_removal_verification_pytest_invocation_count=1
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
v55_disposition=PRESERVED_DEFERRED
next_eligible_action=ESTABLISH_MA_2026_038_F2A_FOUR_FILE_REMOVAL_AND_37_FILE_VERIFICATION_EXECUTION_AUTHORITY
```
