# MA-2026-038 F2-A Four-File Removal Test-Protection Exact-Scope Decision Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized target

Exactly one new decision file is authorized:

`docs/architecture/reviews/MA-2026-038-F2A-FOUR-FILE-REMOVAL-TEST-PROTECTION-EXACT-SCOPE-DECISION.md`

## Decision boundary

The decision may establish only the exact test-protection scope that must precede any separately authorized removal of these four F2-A candidates:

- `app/services/recommendation_engine.py`
- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`
- `app/services/ai_ranking_engine_v7.py`

The sealed preflight observed zero external runtime reference files and zero direct test reference files for the candidates. The decision must preserve that distinction and may not treat absence of direct references as removal authority or as proof that no replacement characterization is required.

The result vocabulary is limited to `ESTABLISH_EXACT_TEST_PROTECTION_SCOPE` or `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`.

## Preserved exclusion

`app/services/recommendation_intelligence_v55.py` remains outside F2-A and deferred until persistence-test transition evidence exists.

## Commit and tag boundary

- exactly one decision file;
- exactly one commit;
- exactly one annotated tag;
- atomic push of `main` and that tag.

## Exclusions

No source or test write, file removal, test or import execution, removal execution authority, F2-B opening, V55 change, database operation, migration, deployment, or lifecycle completion is authorized.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION
f2_exact_scope_status=ESTABLISHED
f2a_candidate_file_count=4
f2a_external_runtime_reference_file_count=0
f2a_direct_test_reference_file_count=0
f2a_test_protection_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a_test_protection_exact_scope_status=NOT_ESTABLISHED
v55_in_f2a_scope=NO
v55_disposition=PRESERVED_DEFERRED
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
application_import_authority=NONE
file_removal_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION_EXACT_SCOPE_DECISION
```
