# MA-2026-038 F2 Legacy Surface Disposition and Convergence Exact-Scope Decision Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized target

Exactly one new decision file is authorized:

`docs/architecture/reviews/MA-2026-038-F2-LEGACY-SURFACE-DISPOSITION-AND-CONVERGENCE-EXACT-SCOPE-DECISION.md`

## Decision boundary

The decision may determine only the F2 disposition and convergence scope for:

- three bounded compatibility adapters that remain preserved;
- the three-file internally connected legacy migration-candidate cluster;
- two retired artifacts, including V55's three-file Persistence test evidence boundary.

The result vocabulary is limited to `ESTABLISH_BOUNDED_LEGACY_CONVERGENCE_SCOPE` or `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`.

## Commit and tag boundary

- exactly one decision file;
- exactly one commit;
- exactly one annotated tag;
- atomic push of `main` and that tag.

## Exclusions

No implementation, deletion, source/test/resource write, test or import execution, F3 opening, Cross-Border reopening, Ranking V8 revival, database operation, migration, deployment, or lifecycle completion is authorized.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F2_LEGACY_SURFACE_DISPOSITION_AND_CONVERGENCE
f1_contract_baseline_status=ESTABLISHED
f1_verification_result=SATISFIED_412_PASS
f2_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2_exact_scope_status=NOT_ESTABLISHED
bounded_compatibility_adapter_count=3
migration_candidate_count=3
retired_artifact_count=2
v55_persistence_test_evidence_file_count=3
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
application_import_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2_LEGACY_SURFACE_DISPOSITION_AND_CONVERGENCE_EXACT_SCOPE_DECISION
```
