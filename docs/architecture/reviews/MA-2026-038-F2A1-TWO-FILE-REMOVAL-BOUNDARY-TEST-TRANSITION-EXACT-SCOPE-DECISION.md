# MA-2026-038 F2-A1 Two-File Removal Boundary-Test Transition Exact-Scope Decision

## Status

ESTABLISHED

## Result

`ESTABLISH_EXACT_ONE_FILE_F2A1_BOUNDARY_TEST_TRANSITION_SCOPE`

## Transition target

Exactly one existing test file may be modified:

- `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`

No other test or production file is part of this transition scope.

## Required post-transition contract

The transitioned file must contain exactly four test functions and enforce all of the following:

1. The immediate F2-A1 removal pair is exactly:
   - `app/services/recommendation_engine.py`
   - `app/services/ai_ranking_engine_v7.py`
2. Those two files must be either both present before removal or both absent after removal.
3. The deferred F2-A2 migration modules must remain present:
   - `app/services/recommendation/score_engine.py`
   - `app/services/recommendation/compare_engine.py`
4. The preserved bounded adapters and retired V55 artifact must remain present:
   - `app/services/recommendation_pipeline.py`
   - `app/services/generator_compatibility.py`
   - `app/services/recommendation/recommendation_score_v8.py`
   - `app/services/recommendation_intelligence_v55.py`
5. Tracked Python files outside the immediate pair and the test itself must contain no import or textual module reference to either immediate-removal module.
6. `score_engine.py` and `compare_engine.py` must no longer be treated as forbidden modules in this F2-A1 boundary test.

## Exact verification

- execute exactly this one test file;
- use exactly one pytest invocation;
- require exactly `SATISFIED_4_PASS`;
- require zero failures, errors, and skips;
- do not execute the corrected 38-file post-removal suite during this transition.

## Authority sequence

The test modification and execution require a separately established one-use bounded write-and-execution authority. This decision itself grants no test-write or execution authority.

## Preserved downstream boundary

- corrected post-removal verification scope: exactly 38 files;
- corrected post-removal expected result: `SATISFIED_418_PASS`;
- original four-file/37-file execution scope: `SUPERSEDED_NON_EXECUTABLE`;
- the original execution authority must not be reused.

## Exclusions

- no production-file modification or removal;
- no package-export or consumer migration;
- no removal or modification of `score_engine.py` or `compare_engine.py`;
- no V55 modification or removal;
- no test modification or execution under this decision artifact;
- no F2-A1 completion or F2-A2 opening.

## Markers

```text
lifecycle_identity=MA-2026-038
stage=F2A1_TWO_FILE_REMOVAL_BOUNDARY_TEST_TRANSITION
f2a1_boundary_test_transition_exact_scope_decision_write_authority=CONSUMED
f2a1_boundary_test_transition_exact_scope_status=ESTABLISHED
f2a1_boundary_test_transition_exact_scope_result=ESTABLISH_EXACT_ONE_FILE_F2A1_BOUNDARY_TEST_TRANSITION_SCOPE
transition_target_file_count=1
transition_test_definition_count=4
transition_verification_pytest_invocation_count=1
transition_expected_result=SATISFIED_4_PASS
f2a1_immediate_removal_candidate_file_count=2
f2a2_preserved_deferred_migration_file_count=2
corrected_post_removal_verification_file_count=38
corrected_post_removal_expected_result=SATISFIED_418_PASS
original_four_file_execution_scope=SUPERSEDED_NON_EXECUTABLE
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A1_TWO_FILE_REMOVAL_BOUNDARY_TEST_TRANSITION_BOUNDED_WRITE_AND_EXECUTION_AUTHORITY
```
