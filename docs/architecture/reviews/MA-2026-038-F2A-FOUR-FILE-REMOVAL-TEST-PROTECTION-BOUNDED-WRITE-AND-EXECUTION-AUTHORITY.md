# MA-2026-038 F2-A Four-File Removal Test-Protection Bounded Write and Execution Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized write target

Exactly one new test file is authorized:

`tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`

No existing test or production file may be modified.

## Authorized contract

The test must use filesystem/static-source inspection without importing the application and must protect:

- zero external references to the three legacy recommendation modules;
- zero external references to Ranking Engine V7;
- exact membership of the four-file F2-A candidate set;
- continued presence and exclusion of the three bounded compatibility adapters;
- continued presence and exclusion of V55;
- a post-removal predicate in which all four candidates are absent while all preserved files remain present.

Candidate content hashes may be used only as pre-write fail-closed inputs and must not become enduring behavior assertions.

## Authorized execution

Exactly one pytest invocation is authorized, selecting only:

`tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`

The test must pass before the commit and tag are created. The one-use authority is consumed whether the authorized test passes or fails.

## Commit and tag boundary

- exactly one new test file;
- exactly one commit;
- exactly one annotated tag;
- atomic push of `main` and that tag only after the test passes.

## Exclusions

No production write or deletion, existing-test modification, full-suite or regression-suite execution, application import, V55/Persistence-test change, compatibility-adapter change, F2-B/F3 opening, database operation, migration, deployment, or lifecycle completion is authorized.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION
f2a_test_protection_exact_scope_status=ESTABLISHED
f2a_test_protection_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a_test_protection_execution_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a_test_protection_target_file_count=1
f2a_test_protection_target=tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py
f2a_existing_test_modification_count=0
f2a_candidate_file_count=4
v55_in_f2a_scope=NO
v55_disposition=PRESERVED_DEFERRED
production_write_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=IMPLEMENT_AND_VERIFY_MA_2026_038_F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION
```
