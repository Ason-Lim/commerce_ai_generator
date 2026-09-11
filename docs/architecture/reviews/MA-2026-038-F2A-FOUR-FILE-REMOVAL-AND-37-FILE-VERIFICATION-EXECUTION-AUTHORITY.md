# MA-2026-038 F2-A Four-File Removal and 37-File Verification Execution Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized production deletion

Exactly these four files may be deleted as one atomic set:

- `app/services/recommendation_engine.py`
- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`
- `app/services/ai_ranking_engine_v7.py`

No production addition or modification and no fifth deletion is authorized.

## Required preserved boundary

The three bounded compatibility adapters and `app/services/recommendation_intelligence_v55.py` must remain present and unchanged.

## Authorized verification

Exactly one pytest invocation over the 37 test files listed in the sealed exact-scope decision is authorized after deletion. It must collect exactly 416 tests and produce 416 passes, zero failures, zero errors, and zero skips.

## Commit and tag boundary

- exactly four deleted production files;
- exactly one commit;
- exactly one annotated tag;
- atomic push of `main` and that tag only after verification passes.

The authority is one-use and is consumed by the authorized execution attempt, whether the tests pass or fail.

## Exclusions

No test-file write, production addition or modification, V55/Persistence-test change, compatibility-adapter change, application import, full-suite execution, Cross-Border reopening, Ranking V8 revival, F2-B/F3 opening, database operation, migration, deployment, or lifecycle completion is authorized.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_FOUR_FILE_REMOVAL_EXECUTION
f2a_removal_execution_exact_scope_status=ESTABLISHED
f2a_production_removal_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a_post_removal_verification_execution_authority=ESTABLISHED_ONE_USE_BOUNDED
removal_candidate_file_count=4
preserved_file_count=4
post_removal_verification_file_count=37
post_removal_expected_test_result=SATISFIED_416_PASS
test_write_authority=NONE
application_import_authority=NONE
next_eligible_action=EXECUTE_MA_2026_038_F2A_FOUR_FILE_REMOVAL_AND_37_FILE_VERIFICATION
```
