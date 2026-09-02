# ADA-MA-2026-034 Phase 4 I5-B2 Second Superseding Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I5-B2 — Second Superseding Collector V4 Runner Migration`
- Second supersession predecessor commit:
  `294aa68c27abfb6a1885c7298d44b7041b57c2b0`
- Second supersession predecessor tag:
  `ma-2026-034-phase4-i5b2-second-scope-supersession-decision-established-v1.0`

## 2. Superseded Authority

The prior superseding I5-B2 authority is:

`SUPERSEDED_UNCONSUMED`

The preserved three-file partial migration remains unstaged and must be recovered,
not discarded.

## 3. Authorized Exact File Scope

This second superseding authority permits exactly six files:

1. `app/services/collector_v4_runner.py`
2. `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
3. `tests/test_persistence_i5b2_collector_v4_runner_migration.py`
4. `tests/test_persistence_engine_disposal.py`
5. `tests/test_persistence_engine_lifecycle.py`
6. `tests/test_persistence_fastapi_lifecycle_composition.py`

No other file may be modified.

## 4. Authorized Recovery and Transition

The existing partial migration may be retained.

The three legacy-importer count contract tests may transition:

- `EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 23` -> `22`
- test name suffix `remains_23` -> `remains_22`

No other assertion or semantic contract in those files may be altered.

The existing I5-B characterization transition remains limited to TB-06/TB-07
provider-aware authority-shape detection while preserving transaction semantics.

## 5. Required Post-Migration Semantics

- TB-06 `fetch_targets`
  - bounded `get_engine().connect()`
  - no transaction ownership

- TB-07 `update_snapshot`
  - bounded `get_engine().begin()`
  - per-call transaction ownership preserved

- `run_collector_v4`
  - orchestration loop preserved
  - per-item update call preserved
  - no direct transaction ownership

- direct legacy importer count
  - exactly `22`

- TB-10
  - unchanged and deferred

## 6. Frozen Surfaces

No write is authorized to:

- `app/services/naver_datalab_service.py`
- `app/services/naver_shopping_api_collector.py`
- `app/db/engine_provider.py`
- `app/main.py`
- `app/db/lifecycle.py`
- `app/db/database.py`
- caller modules
- any other production or test file

## 7. DDL / Compatibility Boundary

DDL remains excluded and reserved for:

`I7 / TB-15`

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge or proxy is authorized.

## 8. Verification Boundary

Permitted verification is non-networking and non-mutating:

- Python compilation;
- I5-B2 migration tests;
- I5-B characterization tests;
- the three importer-count contract test files;
- persistence real-resource denial guard;
- selected collector/market/persistence regressions;
- collection-only verification.

No real database access, database network execution, database mutation, DDL
execution, or external network collection is authorized.

## 9. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_prior_superseding_authority_status=SUPERSEDED_UNCONSUMED`
- `i5b2_status=AUTHORIZED_NOT_IMPLEMENTED_OR_PARTIAL`
- `i5b2_second_superseding_production_write_authority=ISSUED`
- `i5b2_second_superseding_test_write_authority=ISSUED`
- `i5b2_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_FOUR_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i5b2_exact_file_count=SIX`
- `i5b2_importer_count_transition=AUTHORIZED`
- `i5b2_direct_legacy_importer_count=22`
- `partial_three_file_state=PRESERVED_UNSTAGED`
- `tb10_status=DEFERRED_TO_LATER_I5B_SUBWAVE`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_SECOND_SUPERSEDING_I5B2_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=RECOVER_AND_IMPLEMENT_SECOND_SUPERSEDING_I5B2_EXACT_MIGRATION`
