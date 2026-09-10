# MA-2026-038 F2 Legacy Surface Disposition and Convergence Exact-Scope Decision

## Status and result

- Lifecycle: `MA-2026-038`
- Stage: `F2_LEGACY_SURFACE_DISPOSITION_AND_CONVERGENCE`
- Decision status: `ESTABLISHED`
- Result: `ESTABLISH_BOUNDED_LEGACY_CONVERGENCE_SCOPE`
- Implementation authority: `NONE`

## Preserved bounded compatibility adapters

The following remain required compatibility surfaces and are excluded from F2 modification:

- `app/services/recommendation_pipeline.py`
- `app/services/generator_compatibility.py`
- `app/services/recommendation/recommendation_score_v8.py`

Their observed reference-file counts are respectively 11, 17, and 5. Recommendation Score V8 remains a compatibility score surface and does not revive retired Ranking V8.

Disposition: `PRESERVE_UNCHANGED_BOUNDED_COMPATIBILITY_ADAPTER`.

## F2-A bounded removal candidate set

The following internally connected legacy cluster has zero observed external app-or-test import roots:

- `app/services/recommendation_engine.py`
- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`

The cluster contains two files participating in internal reference edges. It may proceed only as one atomic three-file removal candidate set after a separate read-only test-protection preflight and bounded production-write authority.

`app/services/ai_ranking_engine_v7.py` also has zero observed external app-or-test references and joins F2-A as the fourth removal candidate. Its removal must preserve `ranking_v8_disposition=PRESERVE_RETIRED` and `duplicate_ranking_execution_disposition=PRESERVE_RESOLVED`.

F2-A disposition: `FOUR_FILE_REMOVAL_CANDIDATE_PENDING_TEST_PROTECTION_AND_WRITE_AUTHORITY`.

## V55 preserved deferred boundary

`app/services/recommendation_intelligence_v55.py` has zero observed external runtime consumer but is referenced by exactly three MA-2026-034 Persistence boundary tests. Those tests protect historical DDL extraction and runtime detachment evidence.

V55 is therefore not admitted to F2-A and must remain present and unchanged. Removal may be reconsidered only after a separate exact test-transition analysis proves how all three Persistence boundaries remain valid.

Disposition: `RETIRED_ARTIFACT_PRESERVED_DEFERRED_UNTIL_PERSISTENCE_TEST_TRANSITION_EVIDENCE`.

## Required next preflight

The next read-only action must identify the exact test files and static contracts that protect the four-file F2-A candidate set. It may not delete files, execute tests, import the application, or open F3.

## Exclusions

- no source or test modification;
- no production deletion;
- no test or application import execution;
- no V55 modification or deletion;
- no bounded adapter modification;
- no Cross-Border reopening;
- no Ranking V8 revival;
- no F3 opening or lifecycle completion.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2_LEGACY_SURFACE_DISPOSITION_AND_CONVERGENCE
f2_exact_scope_decision_write_authority=CONSUMED
f2_exact_scope_status=ESTABLISHED
f2_exact_scope_result=ESTABLISH_BOUNDED_LEGACY_CONVERGENCE_SCOPE
bounded_compatibility_adapter_disposition=PRESERVE_UNCHANGED
bounded_compatibility_adapter_count=3
f2a_removal_candidate_file_count=4
f2a_migration_cluster_file_count=3
f2a_ai_ranking_engine_v7_file_count=1
f2a_status=NOT_OPENED
f2a_write_authority=NONE
v55_disposition=RETIRED_ARTIFACT_PRESERVED_DEFERRED_UNTIL_PERSISTENCE_TEST_TRANSITION_EVIDENCE
v55_persistence_test_evidence_file_count=3
ranking_v8_disposition=PRESERVE_RETIRED
duplicate_ranking_execution_disposition=PRESERVE_RESOLVED
cross_border_reopening_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
application_import_authority=NONE
next_eligible_action=RUN_MA_2026_038_F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION_READ_ONLY_PREFLIGHT
```
