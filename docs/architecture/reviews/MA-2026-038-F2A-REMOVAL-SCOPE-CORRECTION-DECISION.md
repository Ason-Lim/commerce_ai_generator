# MA-2026-038 F2-A Removal Scope Correction Decision

## Status

ESTABLISHED

## Result

`ESTABLISH_CORRECTED_CLOSED_REMOVAL_MIGRATION_AND_VERIFICATION_SCOPE`

## Reason for correction

The authorized four-file removal attempt failed safely during collection and rolled back because two proposed removal files remain active package and internal-runtime dependencies. The original static preflight did not resolve package-relative imports and the original 37-file verification scope omitted the package-export contract.

The original four-file removal scope is therefore superseded for execution and must not be retried independently.

## Corrected partition

### F2-A1 — immediate two-file removal candidates

Exactly these two files have no direct external import consumers and remain eligible for removal after separately governed test transition and execution authority:

- `app/services/recommendation_engine.py`
- `app/services/ai_ranking_engine_v7.py`

### F2-A2 — preserved deferred migration modules

These two files must remain present in F2-A1 because active package and internal-runtime consumers depend on their exported functions:

- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`

Their later removal requires a separately governed canonical-function migration, package-export transition, consumer transition, and verification scope. They are not authorized for removal by this decision.

### Preserved direct-dependent production files

The following files remain unchanged in F2-A1:

- `app/services/recommendation/__init__.py`
- `app/services/recommendation/compare_snapshot_engine.py`
- `app/services/recommendation/identity_engine.py`
- `app/services/recommendation/reason_engine.py`
- `app/ui/streamlit_app.py`

### Required test transition

Exactly one existing test file requires a separately governed transition before F2-A1 removal:

- `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`

The test must replace the original four-file all-present/all-absent invariant with these exact boundaries:

- the two F2-A1 candidates are either both present before removal or both absent after removal;
- `score_engine.py` and `compare_engine.py` remain present;
- the four previously preserved adapters remain present;
- V55 remains preserved and deferred;
- no external imports or textual module references target the two removed F2-A1 modules.

### Corrected post-removal verification scope

The corrected verification scope contains exactly 38 tracked test files in one pytest invocation:

- all 37 files from the sealed original removal-execution decision;
- plus `tests/services/recommendation/test_package_export_contract.py`.

The package-export contract contributes two tests. With the sealed 416-test original aggregate unchanged by the boundary-test transition, the corrected expected result is exactly 418 passes, zero failures, zero errors, and zero skips.

## Required order

1. establish exact scope for the one-file boundary-test transition;
2. establish bounded test-write and execution authority;
3. modify and verify exactly the boundary-test file;
4. establish corrected two-file removal and 38-file execution authority;
5. remove exactly the two F2-A1 candidates;
6. execute exactly one pytest invocation over the corrected 38-file scope;
7. commit and tag only after `SATISFIED_418_PASS`.

## Original authority disposition

The original four-file removal and 37-file verification authority remains historically established and unconsumed, but it is non-executable after this correction because its scope has been superseded. It must not be reused as authority for the corrected execution.

## Exclusions

- no removal of `score_engine.py` or `compare_engine.py` in F2-A1;
- no modification of package exports or Streamlit consumers in F2-A1;
- no V55 modification or removal;
- no canonical-function migration in this decision;
- no production or test write under this decision artifact;
- no test or application import execution;
- no F2-A completion declaration;
- no F2-B opening.

## Markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_REMOVAL_SCOPE_CORRECTION
f2a_scope_correction_decision_write_authority=CONSUMED
f2a_scope_correction_status=ESTABLISHED
f2a_scope_correction_result=ESTABLISH_CORRECTED_CLOSED_REMOVAL_MIGRATION_AND_VERIFICATION_SCOPE
f2a_original_four_file_scope_execution_status=SUPERSEDED_NON_EXECUTABLE
f2a1_immediate_removal_candidate_file_count=2
f2a2_preserved_deferred_migration_file_count=2
f2a1_test_transition_target_file_count=1
f2a1_corrected_verification_file_count=38
f2a1_corrected_expected_test_result=SATISFIED_418_PASS
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
next_eligible_action=RUN_MA_2026_038_F2A1_TWO_FILE_REMOVAL_BOUNDARY_TEST_TRANSITION_READ_ONLY_PREFLIGHT
```
