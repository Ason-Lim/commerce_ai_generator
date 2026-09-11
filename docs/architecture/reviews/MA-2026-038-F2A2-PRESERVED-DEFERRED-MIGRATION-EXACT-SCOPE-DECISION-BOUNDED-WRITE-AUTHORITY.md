# MA-2026-038 F2-A2 Preserved Deferred Migration Exact-Scope Decision Bounded Write Authority

## Status

ESTABLISHED — ONE USE — BOUNDED

## Authorized target

Exactly one new file is authorized:

`docs/architecture/reviews/MA-2026-038-F2A2-PRESERVED-DEFERRED-MIGRATION-EXACT-SCOPE-DECISION.md`

## Authorized decision

The target may decide only whether the sealed static evidence establishes a closed package-export migration scope for F2-A2.

Permitted result vocabulary:

- `ESTABLISH_CLOSED_PACKAGE_EXPORT_MIGRATION_SCOPE`
- `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`

## Required evidence boundary

- two preserved deferred migration files: `score_engine.py` and `compare_engine.py`;
- two package-level consumer files;
- two initializer imports from the preserved modules;
- one internal `compare_engine` to `score_engine` dependency;
- five direct score-engine reference files and one direct compare-engine reference file;
- the package initializer and package-export contract test remain present.

## Required decision partition

The decision must classify, without implementation, the canonical destination, package export transition, internal dependency transition, test-protection requirement, verification boundary, and removal eligibility of both preserved modules.

## Exclusions

- no F2-A2 opening or migration execution in this authority stage;
- no production, test, resource, registry, database, or migration write;
- no file removal, test execution, application import, or full-suite execution;
- no F2-A1 reopening or successor lifecycle opening;
- no research-candidate implementation, experiment, contract expansion, or adoption.

## Consumption

Consumed only by one commit adding exactly the authorized decision file and its annotated tag. A fully rolled-back pre-push failure does not consume it.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_PRESERVED_DEFERRED_MIGRATION_EXACT_SCOPE_DECISION_AUTHORITY
f2a1_completion_status=COMPLETE
f2a2_preflight_result=READY_FOR_EXACT_SCOPE_DECISION_BOUNDED_WRITE_AUTHORITY
f2a2_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f2a2_exact_scope_status=NOT_ESTABLISHED
f2a2_status=NOT_OPENED
preserved_deferred_migration_file_count=2
package_level_consumer_file_count=2
initializer_candidate_import_statement_count=2
internal_compare_to_score_dependency_count=1
direct_score_engine_reference_file_count=5
direct_compare_engine_reference_file_count=1
research_grounded_architecture_candidates=DEFERRED_ROUTING_ONLY
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A2_PRESERVED_DEFERRED_MIGRATION_EXACT_SCOPE_DECISION
```
