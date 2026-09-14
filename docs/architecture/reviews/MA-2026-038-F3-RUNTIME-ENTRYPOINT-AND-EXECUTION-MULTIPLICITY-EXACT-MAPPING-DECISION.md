# MA-2026-038 F3 Runtime Entrypoint and Execution Multiplicity Exact Mapping Decision

Decision status: `ESTABLISHED`

## 1. Decision identity

- Lifecycle: `MA-2026-038`
- Stage: `F3 — Canonical Runtime Composition`
- Decision class: `RUNTIME_ENTRYPOINT_AND_EXECUTION_MULTIPLICITY_EXACT_MAPPING`
- Evidence mode: `STATIC_AST_AND_FIXED_SOURCE_IDENTITY`
- Establishment effect: `DOCUMENTARY_MAPPING_DECISION_ONLY`

This decision records the exact static runtime topology supported by the sealed
post-F2 repository. It separates resolved call-graph facts from activation and
dynamic-invocation questions that static evidence cannot establish.

## 2. Controlling predecessor

The controlling predecessor is:

- `docs/architecture/reviews/MA-2026-038-F3-CANONICAL-RUNTIME-COMPOSITION-EXACT-SCOPE-DECISION.md`
- `canonical_destination=EXISTING_APP_SERVICES_RECOMMENDATION_PACKAGE`
- `f3_status=OPEN`

The predecessor requires preservation of exactly one ranking execution and one
priority-sort execution where applicable. It does not permit static reference
counts to be treated as dynamic execution proof.

## 3. Fixed evidence boundary

The mapping is bound to these sealed runtime sources:

- `app/main.py`
- `app/services/recommendation_pipeline.py`
- `app/services/recommendation/provider.py`
- `app/services/recommendation/ranking.py`
- `app/services/recommendation/cross_border_candidate_ranking.py`
- `app/services/generator_service.py`
- `app/ui/streamlit_app.py`

The evidence was produced without application imports, test execution, or
repository writes.

## 4. Resolved canonical API entrypoints

Exactly two application callsites invoke `run_recommendation_pipeline`, both in
`app/main.py`:

1. `recommendations_v2`
2. `natural_language_recommendations`

The first returns the pipeline directly. The second returns the pipeline from
its protected `try` path.

`canonical_api_entrypoint_mapping_status=RESOLVED_TWO_PIPELINE_CALLSITES`

## 5. Resolved canonical pipeline chain

The canonical pipeline statically contains the responsibility chain:

1. `build_canonical_context`
2. `compose_production_recommendation_provider`
3. `provider.recommend`
4. `canonical_result_to_compatibility_response`

`canonical_pipeline_chain_status=RESOLVED_CONTEXT_PROVIDER_RECOMMEND_RESULT_COMPOSITION`

## 6. Resolved provider ranking boundary

`app.services.recommendation.provider.recommend` contains exactly one static
callsite to `rank_candidates`.

`canonical_provider_ranking_callsite_status=RESOLVED_EXACT_ONE`

The ranking function has four `sorted` return sites. They are branch-exclusive
static alternatives, not evidence of four executions in one request.

`canonical_ranking_branch_status=RESOLVED_FOUR_BRANCH_EXCLUSIVE_SORT_SITES`

## 7. Dormant pipeline priority-sort helper

`apply_priority_sort` is defined once and contains four branch-specific sort
sites, but the sealed application tree contains zero callsites to the helper.

`pipeline_priority_sort_helper_status=RESOLVED_DORMANT_ZERO_CALLERS`

Its presence does not prove a priority-sort execution on the canonical pipeline.

## 8. Natural-language exception fallback

The natural-language entrypoint returns the canonical pipeline in its `try`
path. Its exception handler does not terminate the function, so the post-try
legacy fallback remains statically reachable only after that exception path.

The fallback contains four branch-exclusive sort candidates.

`nl_exception_fallback_status=RESOLVED_AS_CONTINGENT_STATIC_PATH`

This classification does not establish that the exception occurs or how many
times a sort executes dynamically.

## 9. Separate unresolved runtime surfaces

The application contains one additional static `rank_candidates` callsite in
`rank_cross_border_candidate_pair`.

`cross_border_ranking_activation_status=UNRESOLVED`

The Streamlit UI also contains separate runtime paths and direct imports.

`ui_runtime_activation_status=UNRESOLVED`

Static evidence does not establish whether either surface participates in the
same request as a canonical API entrypoint.

## 10. Exact multiplicity decision

`mapping_decision=PARTIAL_ESTABLISHMENT_WITH_EXACT_RESOLVED_AND_UNRESOLVED_BOUNDARIES`

`runtime_execution_multiplicity_status=PARTIALLY_RESOLVED_STATICALLY_DYNAMIC_COUNT_UNRESOLVED`

Resolved:

- two canonical API pipeline callsites;
- one provider-to-ranking callsite;
- four branch-exclusive canonical ranking sort sites;
- zero callers of the pipeline priority-sort helper;
- a contingent natural-language exception fallback.

Unresolved:

- actual invocation counts per runtime request;
- cross-border activation relative to canonical API requests;
- UI activation relative to canonical API requests;
- dynamic exception and fallback frequency.

No unresolved item is silently converted into a production-change premise.

## 11. Initial-wave consequence

`first_bounded_production_wave_candidate=PRIMARY_API_PROVIDER_PATH_AND_NL_EXCEPTION_FALLBACK_CHARACTERIZATION`

`first_bounded_production_wave_selection=NOT_ESTABLISHED_BY_THIS_DECISION`

The candidate identifies the smallest evidence-bearing boundary for a later
review. This decision neither selects nor authorizes that wave.

## 12. Preserved lifecycle boundaries

- `f3_status=OPEN`
- `v55_future_work_status=PRESERVED_DEFERRED_NOT_REOPENED`
- `f4_status=NOT_OPEN`
- `f5_status=NOT_OPEN`
- `ma_2026_038_status=NOT_DETERMINED_BY_THIS_DECISION`

## 13. Authority boundary

- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `test_execution_authority=NONE`
- `application_import_authority=NONE`
- `runtime_composition_change_authority=NONE`
- `package_export_change_authority=NONE`
- `canonical_owner_change_authority=NONE`
- `consumer_transition_authority=NONE`
- `f3_completion_authority=NONE`
- `f4_f5_opening_authority=NONE`
- `ma_2026_038_completion_authority=NONE`

## 14. Next bounded route

`PREFLIGHT_MA_2026_038_F3_RUNTIME_MAPPING_DECISION_ESTABLISHMENT_READ_ONLY`

The next step may establish only this exact decision artifact through one file,
one commit, one annotated tag, and an atomic branch-and-tag push. It must not
alter production code, tests, package exports, consumers, or lifecycle stages.
