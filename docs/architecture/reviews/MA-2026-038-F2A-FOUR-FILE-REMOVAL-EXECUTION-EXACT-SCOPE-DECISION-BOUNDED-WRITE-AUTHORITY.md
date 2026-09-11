# MA-2026-038 F2-A Four-File Removal Execution Exact-Scope Decision Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized target

Exactly one new decision file is authorized:

`docs/architecture/reviews/MA-2026-038-F2A-FOUR-FILE-REMOVAL-EXECUTION-EXACT-SCOPE-DECISION.md`

## Decision boundary

The decision may define only a later F2-A removal execution consisting of:

- deletion of exactly the four sealed removal candidates;
- preservation of the three bounded compatibility adapters and V55;
- one post-removal pytest invocation over the 36-file F1 canonical baseline plus the one-file F2-A boundary test, for exactly 37 test files.

The result vocabulary is limited to `ESTABLISH_EXACT_FOUR_FILE_REMOVAL_AND_37_FILE_VERIFICATION_SCOPE` or `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`.

## Commit and tag boundary

- exactly one decision file;
- exactly one commit;
- exactly one annotated tag;
- atomic push of `main` and that tag.

## Exclusions

No production deletion or modification, test modification or execution, application import, removal execution authority, V55/Persistence-test change, compatibility-adapter change, Cross-Border reopening, Ranking V8 revival, F2-B/F3 opening, database operation, migration, deployment, or lifecycle completion is authorized.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_FOUR_FILE_REMOVAL_EXECUTION
f2a_test_protection_status=ESTABLISHED
f2a_test_protection_result=SATISFIED_4_PASS
f2a_removal_execution_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a_removal_execution_exact_scope_status=NOT_ESTABLISHED
removal_candidate_file_count=4
preserved_file_count=4
post_removal_verification_file_count=37
post_removal_verification_pytest_invocation_count=1
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A_FOUR_FILE_REMOVAL_EXECUTION_EXACT_SCOPE_DECISION
```
