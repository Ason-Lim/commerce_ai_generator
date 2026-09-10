# MA-2026-038 F1 Canonical Contract Baseline Verification Result

## Status

`ESTABLISHED`

## Result

`SATISFIED_412_PASS`

## Authorized scope

The verification executed exactly once over the 36 files sealed by the F1 exact-scope decision. No test outside the authorized three groups was selected.

| Group | Boundary | Files | Collected | Passed | Failed | Errors | Skipped |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | Direct canonical contract baseline | 15 | 253 | 253 | 0 | 0 | 0 |
| B | Preserved Cross-Border regression | 20 | 148 | 148 | 0 | 0 | 0 |
| C | Production compatibility regression | 1 | 11 | 11 | 0 | 0 | 0 |
| Total | Three-group F1 baseline | 36 | 412 | 412 | 0 | 0 | 0 |

## Integrity determination

- pytest invocation count: `1`;
- repository HEAD and `origin/main` remained unchanged during execution;
- worktree remained clean and staged index remained empty;
- production, test, and resource files modified: `0`;
- commits, tags, and pushes created during test execution: `0`.

The canonical contract baseline is therefore established for F1. This result grants no F2 implementation or write authority.

## Preserved boundaries

- Cross-Border behavior remains preserved as regression evidence;
- compatibility behavior remains preserved as regression evidence;
- no legacy surface disposition or convergence is performed here;
- no production, test, resource, database, migration, or deployment write is authorized;
- no lifecycle completion is declared.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F1_CANONICAL_CONTRACT_BASELINE
f1_verification_execution_authority=CONSUMED
f1_verification_result_write_authority=CONSUMED
f1_verification_result_status=ESTABLISHED
f1_verification_result=SATISFIED_412_PASS
f1_contract_baseline_status=ESTABLISHED
pytest_invocation_count=1
total_selected_test_file_count=36
total_collected=412
total_passed=412
total_failed=0
total_errors=0
total_skipped=0
production_files_modified=0
test_files_modified=0
resource_files_modified=0
f2_status=NOT_OPENED
f2_write_authority=NONE
next_eligible_action=RUN_MA_2026_038_F2_LEGACY_SURFACE_DISPOSITION_AND_CONVERGENCE_READ_ONLY_PREFLIGHT
```
