# MA-2026-038 F2-A Removal Scope Correction Decision Bounded Write Authority

## Status

ESTABLISHED_ONE_USE_BOUNDED

## Purpose

Authorize exactly one evidence-based correction decision after the authorized four-file removal attempt failed safely during test collection and rolled back completely.

This authority does not itself correct the scope, modify source or test files, remove files, execute tests, or consume the previously established removal-and-verification execution authority.

## Sealed correction evidence

- original removal-and-verification execution authority remains established and unconsumed;
- original four candidate files are restored and tracked;
- result commit and result tag are absent locally and remotely;
- removal attempt failed during collection because `app/services/recommendation/__init__.py` imported removed `score_engine`;
- AST resolution found exactly 5 direct candidate-import statements across exactly 4 non-candidate files;
- the direct dependent files are `app/services/recommendation/__init__.py`, `app/services/recommendation/compare_snapshot_engine.py`, `app/services/recommendation/identity_engine.py`, and `app/services/recommendation/reason_engine.py`;
- 152 tracked Python files import the recommendation package or its submodules and therefore trigger package initialization;
- AST parse failure count is zero;
- `app/ui/streamlit_app.py` imports ten package-level symbols and actively uses legacy exports;
- `tests/services/recommendation/test_package_export_contract.py` preserves the package export contract;
- that package-export contract test is absent from the original 37-file post-removal verification scope.

## Authorized exact write target

Exactly one new file may be created:

`docs/architecture/reviews/MA-2026-038-F2A-REMOVAL-SCOPE-CORRECTION-DECISION.md`

The decision must classify an exact closed migration/removal boundary, exact preserved compatibility boundary, exact test-transition boundary, and corrected verification scope.

## Decision vocabulary

- `ESTABLISH_CORRECTED_CLOSED_REMOVAL_MIGRATION_AND_VERIFICATION_SCOPE`
- `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`

## Exclusions

- no production, test, resource, database, or migration write;
- no file removal;
- no test or application import execution;
- no modification of the original authority artifact;
- no claim that the original four-file scope is sufficient;
- no corrected implementation or execution authority;
- no F2-A completion declaration;
- no F2-B opening.

## One-use rule

This authority is consumed only by one conforming correction-decision artifact, one commit, one annotated tag, and their atomic push.

## Markers

```text
lifecycle_identity=MA-2026-038
stage=F2A_REMOVAL_SCOPE_CORRECTION_DECISION
f2a_original_execution_authority_status=ESTABLISHED_UNCONSUMED
f2a_original_four_file_removal_status=NOT_ESTABLISHED
f2a_scope_correction_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a_scope_correction_status=NOT_ESTABLISHED
direct_candidate_import_statement_count=5
direct_candidate_import_file_count=4
recommendation_package_initializer_trigger_file_count=152
package_export_contract_in_original_37_file_scope=NO
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A_REMOVAL_SCOPE_CORRECTION_DECISION
```
