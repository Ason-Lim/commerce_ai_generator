# MA-2026-038 F1 Canonical Contract Baseline Verification Execution Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized execution

One pytest execution over exactly the 36 files sealed by the F1 exact-scope decision:

- Group A: 15 direct canonical baseline files;
- Group B: 20 preserved Cross-Border regression files;
- Group C: 1 production compatibility regression file.

The executor must report Group A, Group B, Group C, and aggregate passed/failed counts separately. All 36 files must participate in one pytest invocation so collection and interaction failures are visible.

## Environment boundary

- use repository `.venv/bin/python -m pytest`;
- disable cache provider with `-p no:cacheprovider`;
- do not use `--lf`, `--ff`, selection expressions, deselection, xfail injection, or rerun plugins;
- do not execute the full suite or any unlisted test;
- do not execute a standalone application import.

## Non-mutation boundary

The execution grants no production, test, resource, registry-data, database, migration, deployment, commit, tag, or push authority. The repository must remain byte-for-byte unchanged in tracked scope, with clean worktree and empty staged index.

## Consumption and routing

This authority is consumed by the first conforming pytest invocation. A passing execution establishes evidence only; it does not establish F1. A separate bounded write authority is required to record the verification result.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F1_CANONICAL_CONTRACT_BASELINE
f1_contract_baseline_exact_scope_status=ESTABLISHED
f1_verification_execution_authority=ESTABLISHED_ONE_USE_BOUNDED
authorized_test_invocation_count=1
direct_canonical_test_file_count=15
preserved_cross_border_test_file_count=20
preserved_compatibility_test_file_count=1
total_selected_test_file_count=36
production_write_authority=NONE
test_write_authority=NONE
result_write_authority=NONE
application_import_authority=PYTEST_COLLECTION_ONLY
next_eligible_action=EXECUTE_MA_2026_038_F1_CANONICAL_CONTRACT_BASELINE_VERIFICATION_READ_ONLY
```
