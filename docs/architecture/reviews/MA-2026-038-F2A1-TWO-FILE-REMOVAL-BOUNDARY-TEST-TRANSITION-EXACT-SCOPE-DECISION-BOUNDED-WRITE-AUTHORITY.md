# MA-2026-038 F2-A1 Two-File Removal Boundary-Test Transition Exact-Scope Decision Bounded Write Authority

## Status

ESTABLISHED — ONE USE — BOUNDED

## Authorized write

This authority permits creation of exactly one decision artifact:

- `docs/architecture/reviews/MA-2026-038-F2A1-TWO-FILE-REMOVAL-BOUNDARY-TEST-TRANSITION-EXACT-SCOPE-DECISION.md`

The decision may either establish the exact one-file transition scope or record exact blockers.

## Evidence boundary

- lifecycle: `MA-2026-038`;
- sealed removal-scope correction: `ESTABLISHED`;
- original four-file execution scope: `SUPERSEDED_NON_EXECUTABLE`;
- immediate F2-A1 removal candidates: exactly two files;
- preserved deferred F2-A2 migration modules: exactly two files;
- transition target: exactly one existing test file;
- corrected post-removal verification boundary: 38 files;
- corrected expected result: `SATISFIED_418_PASS`.

## Required decision content

The authorized decision must bind exactly:

- transition target: `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`;
- immediate removal pair: `app/services/recommendation_engine.py` and `app/services/ai_ranking_engine_v7.py`;
- preserved deferred pair: `app/services/recommendation/score_engine.py` and `app/services/recommendation/compare_engine.py`;
- preservation of the bounded adapters and V55;
- exactly four boundary tests and one later pytest invocation;
- expected transition verification result: `SATISFIED_4_PASS`;
- no production removal or source migration under the decision.

## Result vocabulary

- `ESTABLISH_EXACT_ONE_FILE_F2A1_BOUNDARY_TEST_TRANSITION_SCOPE`
- `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`

## Exclusions

- no modification of the transition test in this authority step;
- no test execution or application import;
- no production-file write or removal;
- no modification or removal of the deferred migration modules;
- no reuse of the superseded original execution authority;
- no F2-A1 implementation, completion, or F2-A2 opening.

## Markers

```text
lifecycle_identity=MA-2026-038
stage=F2A1_TWO_FILE_REMOVAL_BOUNDARY_TEST_TRANSITION_EXACT_SCOPE_DECISION_AUTHORITY
f2a_scope_correction_status=ESTABLISHED
f2a_original_four_file_scope_execution_status=SUPERSEDED_NON_EXECUTABLE
f2a1_boundary_test_transition_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a1_boundary_test_transition_exact_scope_status=NOT_ESTABLISHED
transition_target_file_count=1
f2a1_immediate_removal_candidate_file_count=2
f2a2_preserved_deferred_migration_file_count=2
corrected_post_removal_verification_file_count=38
corrected_post_removal_expected_result=SATISFIED_418_PASS
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A1_TWO_FILE_REMOVAL_BOUNDARY_TEST_TRANSITION_EXACT_SCOPE_DECISION
```
