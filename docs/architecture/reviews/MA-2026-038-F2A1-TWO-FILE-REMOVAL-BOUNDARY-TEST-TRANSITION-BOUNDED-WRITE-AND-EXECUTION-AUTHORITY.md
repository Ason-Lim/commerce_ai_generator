# MA-2026-038 F2-A1 Boundary-Test Transition Bounded Write and Execution Authority

## Status

ESTABLISHED — ONE USE — BOUNDED

## Authorized target

Exactly one existing test file may be modified:

- `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`

## Authorized transition

The file may be changed only to implement the sealed F2-A1 exact-scope decision:

- reduce the immediate atomic removal candidate set from four files to exactly `recommendation_engine.py` and `ai_ranking_engine_v7.py`;
- preserve `score_engine.py` and `compare_engine.py` as required deferred migration modules;
- preserve the three bounded adapters and V55;
- prohibit external imports and textual module references to the immediate two-file removal pair;
- retain exactly four test functions.

## Authorized execution

- exactly one pytest invocation;
- exactly the authorized test file;
- expected result: `SATISFIED_4_PASS`;
- zero failures, errors, and skips.

Upon satisfaction, exactly one test-only commit and one annotated result tag may be created and atomically pushed with `main`.

## Exclusions

- no production-file write or removal;
- no other test-file write;
- no package-export or consumer migration;
- no application import;
- no 38-file post-removal verification execution;
- no reuse of the superseded original four-file execution authority;
- no F2-A1 removal or completion.

## Markers

```text
lifecycle_identity=MA-2026-038
stage=F2A1_TWO_FILE_REMOVAL_BOUNDARY_TEST_TRANSITION
f2a1_boundary_test_transition_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a1_boundary_test_transition_execution_authority=ESTABLISHED_ONE_USE_BOUNDED
transition_target_file_count=1
transition_test_definition_count=4
transition_pytest_invocation_count=1
transition_expected_result=SATISFIED_4_PASS
f2a1_immediate_removal_candidate_file_count=2
f2a2_preserved_deferred_migration_file_count=2
corrected_post_removal_verification_file_count=38
corrected_post_removal_expected_result=SATISFIED_418_PASS
original_four_file_execution_scope=SUPERSEDED_NON_EXECUTABLE
production_write_authority=NONE
file_removal_authority=NONE
tests_executed=0
next_eligible_action=IMPLEMENT_AND_VERIFY_MA_2026_038_F2A1_TWO_FILE_REMOVAL_BOUNDARY_TEST_TRANSITION
```
