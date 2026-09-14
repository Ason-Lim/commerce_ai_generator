# MA-2026-038 F3 First Bounded Production Wave Exact-Scope Decision

Decision status: `ESTABLISHED`

## 1. Decision identity

- Lifecycle: `MA-2026-038`
- Stage: `F3 — Canonical Runtime Composition`
- Decision class: `FIRST_BOUNDED_PRODUCTION_WAVE_EXACT_SCOPE`
- Selection mode: `CHARACTERIZATION_FIRST`
- Establishment effect: `DOCUMENTARY_SCOPE_SELECTION_ONLY`

This decision selects the smallest evidence-producing wave that can resolve the
remaining dynamic execution-multiplicity gap without authorizing production
changes or expanding into adjacent runtime surfaces.

## 2. Controlling evidence

The controlling decisions are:

- `MA-2026-038-F3-CANONICAL-RUNTIME-COMPOSITION-EXACT-SCOPE-DECISION.md`
- `MA-2026-038-F3-RUNTIME-ENTRYPOINT-AND-EXECUTION-MULTIPLICITY-EXACT-MAPPING-DECISION.md`

The established mapping is partial by design:

- canonical entrypoints and static callsites are resolved;
- dynamic invocation counts remain unresolved;
- cross-border and Streamlit activation remain unresolved and separate.

## 3. Exact selection

`first_bounded_wave_selection=ESTABLISHED_CHARACTERIZATION_FIRST`

`first_bounded_wave_identity=PRIMARY_API_PROVIDER_AND_NL_RUNTIME_MULTIPLICITY_CHARACTERIZATION`

`wave_change_class=TEST_CHARACTERIZATION_ONLY`

`production_change_selection=DEFERRED_PENDING_CHARACTERIZATION_EVIDENCE`

The word “production” in the lifecycle wave name identifies the production
runtime boundary being characterized. It does not authorize a production-file
change in this wave.

## 4. Included runtime surfaces

The selected characterization boundary includes exactly:

1. `POST /generate` through `generate_product_strategy` and the provider;
2. `GET /recommendations/v2` through `run_recommendation_pipeline`;
3. `GET /recommendations/nl` through its canonical `try` path and contingent
   post-try exception fallback;
4. provider-to-`rank_candidates` multiplicity;
5. branch-exclusive ranking and fallback-sort multiplicity.

## 5. Selected behavior claims

- `selected_behavior_1=GENERATE_PROVIDER_RANKING_MULTIPLICITY`
- `selected_behavior_2=RECOMMENDATIONS_V2_PIPELINE_PROVIDER_RANKING_MULTIPLICITY`
- `selected_behavior_3=RECOMMENDATIONS_NL_SUCCESS_PATH_NO_FALLBACK_SORT`
- `selected_behavior_4=RECOMMENDATIONS_NL_FORCED_EXCEPTION_FALLBACK_BRANCH_EXCLUSIVITY`
- `selected_behavior_5=EXACTLY_ONE_RANK_OR_SORT_EXECUTION_WHERE_APPLICABLE`

These are characterization targets, not already-proven dynamic facts.

## 6. New characterization file

Exactly one new test-file candidate is selected:

- `tests/services/recommendation/test_f3_primary_api_provider_and_nl_fallback_characterization.py`

`selected_new_test_file_count=1`

`test_write_candidate_scope=EXACTLY_ONE_NEW_CHARACTERIZATION_FILE`

No test-write authority is created by this decision.

## 7. Existing regression scope

Exactly five existing files form the selected regression boundary:

1. `tests/services/generator/test_legacy_generator_characterization.py`
2. `tests/services/market/test_marketplace_api_route_contract.py`
3. `tests/services/market/test_recommendation_pipeline_execution_contract.py`
4. `tests/services/recommendation/test_canonical_ranking_contract.py`
5. `tests/services/recommendation/test_production_compatibility_adapter.py`

`selected_existing_regression_file_count=5`

`existing_regression_scope=EXACTLY_FIVE_FILES`

## 8. Exact exclusions

The following are outside this first wave:

- `tests/services/recommendation/test_cross_border_production_entrypoint_binding.py`
- cross-border runtime activation;
- Streamlit UI runtime activation;
- activation or modification of dormant `apply_priority_sort`;
- package-export or canonical-owner changes;
- consumer transitions;
- production-code changes.

`excluded_test_reason_1=CROSS_BORDER_ACTIVATION_OUTSIDE_FIRST_WAVE`

`cross_border_ranking_activation_status=UNRESOLVED_EXCLUDED`

`ui_runtime_activation_status=UNRESOLVED_EXCLUDED`

`dormant_priority_sort_helper_status=ZERO_CALLERS_EXCLUDED`

## 9. Evidence gap addressed

The sealed test inventory contains no direct reference to either:

- `natural_language_recommendations`; or
- `/recommendations/nl`.

The new characterization file is selected to close this exact protection gap
and to measure route-level rank/sort multiplicity without modifying runtime
behavior.

`runtime_execution_multiplicity_status=PENDING_SELECTED_CHARACTERIZATION_EXECUTION`

## 10. Execution plan boundary

`test_execution_plan=NEW_CHARACTERIZATION_PLUS_FIVE_EXISTING_REGRESSION_FILES`

`test_execution_plan_status=DEFINED_NOT_AUTHORIZED`

The later implementation decision must fail closed unless the new test file can
be written without production changes and the exact six-file execution set can
be run independently.

## 11. File-count boundary

- `selected_production_file_count=0`
- `selected_new_test_file_count=1`
- `selected_existing_regression_file_count=5`
- `excluded_cross_border_test_file_count=1`

## 12. Preserved lifecycle state

- `f3_status=OPEN`
- `v55_future_work_status=PRESERVED_DEFERRED_NOT_REOPENED`
- `f4_status=NOT_OPEN`
- `f5_status=NOT_OPEN`
- `ma_2026_038_status=NOT_DETERMINED_BY_THIS_DECISION`

## 13. Authority boundary

- `repository_write_authority=NONE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `test_execution_authority=NONE`
- `application_import_authority=NONE`
- `runtime_composition_change_authority=NONE`
- `consumer_transition_authority=NONE`
- `first_bounded_wave_execution_authority=NONE`
- `f3_completion_authority=NONE`
- `f4_f5_opening_authority=NONE`
- `ma_2026_038_completion_authority=NONE`

## 14. Next bounded route

`PREFLIGHT_MA_2026_038_F3_FIRST_BOUNDED_WAVE_CHARACTERIZATION_TEST_WRITE_AUTHORITY_READ_ONLY`

That later preflight may assess authority for exactly one new test file and the
exact six-file test execution plan. It must not authorize production changes.
