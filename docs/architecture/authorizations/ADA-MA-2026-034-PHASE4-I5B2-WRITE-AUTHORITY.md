# ADA-MA-2026-034 Phase 4 I5-B2 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I5-B2 — First Bounded Collector Production Migration`
- Exact-scope predecessor commit:
  `dd392452030cc8b024bc67d57741d8a407094907`
- Exact-scope predecessor tag:
  `ma-2026-034-phase4-i5b2-exact-scope-decision-established-v1.0`

## 2. Authorized Exact File Scope

This authority permits exactly two files:

1. existing production file:
   `app/services/collector_v4_runner.py`
2. one new migration test:
   `tests/test_persistence_i5b2_collector_v4_runner_migration.py`

No other production or test file may be modified.

## 3. Authorized Production Migration

The production migration is limited to replacing legacy engine acquisition with the
existing bounded canonical provider.

Required post-migration semantics:

- `fetch_targets`
  - no direct `app.db.database.engine` dependency;
  - bounded provider acquisition;
  - preserve nontransactional read semantics corresponding to existing `connect()`.

- `update_snapshot`
  - no direct `app.db.database.engine` dependency;
  - bounded provider acquisition;
  - preserve per-call transactional semantics corresponding to existing `begin()`.

- `run_collector_v4`
  - preserve orchestration loop ownership;
  - preserve absence of direct transaction ownership;
  - preserve per-item call to `update_snapshot`.

## 4. Migration Mechanism

The authorized mechanism is:

`app.db.engine_provider.get_engine`

No alternate provider, compatibility proxy, local engine constructor, or module-level
engine export is authorized.

## 5. Frozen Surfaces

No write is authorized to:

- `app/db/engine_provider.py`
- `app/main.py`
- `app/db/lifecycle.py`
- `app/db/database.py`
- `app/services/naver_datalab_service.py`
- any caller of collector services
- any existing test file

## 6. TB Boundary

This authority covers only:

`TB-06 + TB-07`

TB-10 remains:

`DEFERRED_TO_LATER_I5B_SUBWAVE`

## 7. DDL Boundary

Runtime DDL remains excluded from I5-B2.

DDL remains reserved for:

`I7 / TB-15`

## 8. Compatibility Bridge

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge or proxy is authorized.

## 9. Verification Boundary

Permitted verification is non-networking and non-mutating.

The implementation may run:

- Python compilation;
- the new migration test;
- the existing I5-B1 characterization test;
- persistence real-resource denial guards;
- selected collector/market/persistence regressions;
- collection-only verification.

It may not perform:

- real database access;
- database network execution;
- database mutation;
- external network collection;
- DDL execution.

## 10. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i5b2_production_write_authority=ISSUED`
- `i5b2_test_write_authority=ISSUED`
- `i5b2_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i5b2_exact_file_count=TWO`
- `i5b2_production_file=app/services/collector_v4_runner.py`
- `i5b2_test_file=tests/test_persistence_i5b2_collector_v4_runner_migration.py`
- `i5b2_tb_scope=TB06_PLUS_TB07`
- `i5b2_migration_mechanism=BOUNDED_GET_ENGINE`
- `tb10_status=DEFERRED_TO_LATER_I5B_SUBWAVE`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_I5B2_EXACT_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I5B2_EXACT_COLLECTOR_V4_RUNNER_BOUNDED_PROVIDER_MIGRATION`
