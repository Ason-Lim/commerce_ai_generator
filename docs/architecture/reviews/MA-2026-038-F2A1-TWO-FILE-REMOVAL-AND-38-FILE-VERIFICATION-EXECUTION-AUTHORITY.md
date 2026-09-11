# MA-2026-038 F2-A1 Two-File Removal and 38-File Verification Execution Authority

## Status

ESTABLISHED — ONE USE — BOUNDED

## Authorized production removal

Exactly two production files may be removed:

- `app/services/recommendation_engine.py`
- `app/services/ai_ranking_engine_v7.py`

No production file may be added or modified.

## Preserved deferred migration boundary

The following files shall remain present and unchanged:

- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`
- `app/services/recommendation/__init__.py`
- `app/services/recommendation_pipeline.py`
- `app/services/generator_compatibility.py`
- `app/services/recommendation/recommendation_score_v8.py`
- `app/services/recommendation_intelligence_v55.py`

## Authorized verification

- exactly one pytest invocation;
- exactly the sealed 37-file verification list plus `tests/services/recommendation/test_package_export_contract.py`;
- exactly 38 test files in total;
- expected result: `SATISFIED_418_PASS`;
- zero failures, errors, and skips.

Upon satisfaction, exactly one removal-only commit and one annotated result tag may be created and atomically pushed with `main`.

## Exclusions

- no test-file write;
- no production-file addition or modification;
- no removal of `score_engine.py` or `compare_engine.py`;
- no package-initializer modification;
- no bounded-adapter or V55 modification;
- no application import outside pytest;
- no use of the superseded original four-file authority;
- no F2-A2 opening or F2 completion.

## Markers

```text
lifecycle_identity=MA-2026-038
stage=F2A1_TWO_FILE_REMOVAL_AND_38_FILE_VERIFICATION
f2a1_production_removal_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a1_post_removal_verification_execution_authority=ESTABLISHED_ONE_USE_BOUNDED
removal_candidate_file_count=2
preserved_deferred_migration_file_count=2
post_removal_verification_file_count=38
post_removal_pytest_invocation_count=1
post_removal_expected_test_result=SATISFIED_418_PASS
test_write_authority=NONE
production_modification_authority=NONE
original_four_file_execution_scope=SUPERSEDED_NON_EXECUTABLE
files_removed=0
tests_executed=0
next_eligible_action=EXECUTE_MA_2026_038_F2A1_TWO_FILE_REMOVAL_AND_38_FILE_VERIFICATION
```
