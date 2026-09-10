# MA-2026-038 F2-A Four-File Removal Test-Protection Exact-Scope Decision

## Status and result

- Lifecycle: `MA-2026-038`
- Stage: `F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION`
- Decision status: `ESTABLISHED`
- Result: `ESTABLISH_EXACT_TEST_PROTECTION_SCOPE`
- Test-write authority: `NONE`
- File-removal authority: `NONE`

## Evidence determination

The sealed read-only preflight found no external runtime reference file and no direct test reference file for the four F2-A candidates. Absence of direct references does not itself protect the intended deletion boundary. A dedicated static boundary test must therefore be established before removal authority can be considered.

## Exact test-protection target

Exactly one new test file is admitted for a later separately authorized test-write step:

`tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`

No existing test file may be modified in the test-protection step.

## Required assertions

The test file must use filesystem/static-source inspection without importing the application and must protect all of these boundaries:

1. no tracked Python source or test outside the four-candidate cluster imports or references the three legacy recommendation modules;
2. no tracked Python source or test outside its own candidate file imports or references `ai_ranking_engine_v7`;
3. the three bounded compatibility adapters remain tracked and are not admitted to F2-A removal;
4. `app/services/recommendation_intelligence_v55.py` remains tracked and excluded from F2-A;
5. the exact F2-A candidate set remains the three-file legacy cluster plus Ranking Engine V7, with no fifth production target;
6. after a future separately authorized removal, all four candidates must be absent while the preserved adapters and V55 remain present.

The implementation may represent the pre-removal and post-removal states as explicit static predicates, but it may not encode candidate content hashes as enduring behavior contracts.

## Candidate boundary

- `app/services/recommendation_engine.py`
- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`
- `app/services/ai_ranking_engine_v7.py`

## Preserved boundary

- `app/services/recommendation_pipeline.py`
- `app/services/generator_compatibility.py`
- `app/services/recommendation/recommendation_score_v8.py`
- `app/services/recommendation_intelligence_v55.py`

V55 remains `PRESERVED_DEFERRED`; its three Persistence evidence tests are outside this test-write scope.

## Required sequencing

1. establish one-use bounded authority for the exact one-file test write;
2. create only the exact test file and run only that file under the same bounded step;
3. seal its passing result before considering four-file removal authority;
4. authorize and execute any four-file removal only through later separate governance.

## Exclusions

- no production-file modification or deletion;
- no existing-test modification;
- no application import;
- no V55 or Persistence-test modification;
- no compatibility-adapter modification;
- no Cross-Border reopening or Ranking V8 revival;
- no F2-B/F3 opening or lifecycle completion.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION
f2a_test_protection_exact_scope_decision_write_authority=CONSUMED
f2a_test_protection_exact_scope_status=ESTABLISHED
f2a_test_protection_exact_scope_result=ESTABLISH_EXACT_TEST_PROTECTION_SCOPE
f2a_test_protection_target_file_count=1
f2a_test_protection_target=tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py
f2a_existing_test_modification_count=0
f2a_candidate_file_count=4
f2a_external_runtime_reference_file_count=0
f2a_direct_test_reference_file_count=0
v55_in_f2a_scope=NO
v55_disposition=PRESERVED_DEFERRED
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
application_import_authority=NONE
file_removal_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A_FOUR_FILE_REMOVAL_TEST_PROTECTION_BOUNDED_WRITE_AND_EXECUTION_AUTHORITY
```
