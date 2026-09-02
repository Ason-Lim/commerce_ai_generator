# MA-2026-034 Phase 4 I5-B2 Exact Scope Decision

## Decision

The first bounded I5-B production migration cohort is:

- existing production file:
  `app/services/collector_v4_runner.py`
- one new migration test:
  `tests/test_persistence_i5b2_collector_v4_runner_migration.py`

No other production or test file is in I5-B2 scope.

## Why This Cohort Is First

`collector_v4_runner.py` is the smallest independently migratable characterized
cohort that jointly represents TB-06 and TB-07 while preserving a clear
orchestration boundary.

Current characterized semantics are:

- `fetch_targets` owns one direct read acquisition using `engine.connect()`;
- `update_snapshot` owns one per-call transaction using `engine.begin()`;
- `run_collector_v4` owns the per-item loop and calls `update_snapshot`;
- `run_collector_v4` owns no direct database transaction.

This cleanly separates external enrichment/orchestration from per-item database
transaction ownership.

## Migration Mechanism

The authorized future implementation mechanism is bounded provider acquisition:

- replace the direct legacy `app.db.database.engine` dependency with
  `app.db.engine_provider.get_engine`;
- preserve `fetch_targets` as a nontransactional read acquisition;
- preserve `update_snapshot` as a per-call transaction;
- preserve `run_collector_v4` as an orchestration loop with no direct transaction.

No provider replacement, compatibility proxy, or lifecycle change is required.

## Caller Boundary

No external module import dependency on `app.services.collector_v4_runner` was
observed in the exact-scope preflight.

No caller write is required by current evidence.

The module does not export its own assigned `engine` symbol.

## TB-10 Deferral

`app/services/naver_datalab_service.py` is not part of this I5-B2 cohort.

TB-10 is a distinct cached-read/cached-write boundary and remains for a later
separately scoped I5-B subwave.

Combining TB-10 with TB-06/TB-07 would widen the first production cohort without
evidence of necessity.

## DDL Boundary

`collector_v4_runner.py` contains no observed runtime DDL.

DDL-bearing collector functions remain excluded from I5-B and reserved for
`I7 / TB-15`.

## Provider / Lifecycle Freeze

No write is required to:

- `app/db/engine_provider.py`;
- `app/main.py`;
- `app/db/lifecycle.py`;
- `app/db/database.py`.

## Compatibility Bridge

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No evidence from this cohort requires a compatibility bridge or proxy.

## Non-Authorization

This decision does not itself authorize production or test implementation.

It authorizes no real database access, database network execution, database
mutation, DDL execution, TB-10 migration, caller migration, provider/lifecycle
write, compatibility bridge, or Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i5b2_exact_file_count=TWO`
- `i5b2_production_file=app/services/collector_v4_runner.py`
- `i5b2_test_file=tests/test_persistence_i5b2_collector_v4_runner_migration.py`
- `i5b2_tb_scope=TB06_PLUS_TB07`
- `i5b2_migration_mechanism=BOUNDED_GET_ENGINE`
- `i5b2_fetch_semantics=PRESERVE_CONNECT`
- `i5b2_update_semantics=PRESERVE_BEGIN`
- `i5b2_orchestrator_transaction_ownership=NONE`
- `i5b2_caller_write_required=NO`
- `i5b2_provider_write_required=NO`
- `i5b2_app_main_write_required=NO`
- `i5b2_compatibility_proxy=PROHIBITED`
- `tb10_status=DEFERRED_TO_LATER_I5B_SUBWAVE`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i5b2_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I5B2_WRITE_AUTHORITY`
