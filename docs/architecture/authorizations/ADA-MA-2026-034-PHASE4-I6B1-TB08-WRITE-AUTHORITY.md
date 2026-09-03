# ADA-MA-2026-034 Phase 4 I6-B1 TB-08 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I6-B1 — TB-08 Market Intelligence Runtime Migration`
- Exact-scope predecessor commit: `88fcd4c57483ccc45efad3020b0be21f8522b113`
- Exact-scope predecessor tag: `ma-2026-034-phase4-i6b1-tb08-exact-scope-decision-established-v1.0`
- Exact-scope decision SHA-256: `59ba413bad10177c23248cabd7018fc966d8075c24a14dcdd1b4138a68bcb8eb`

## 2. Authorized Exact Scope

This single-use authority permits changes to exactly seven files:

1. `app/services/market_collector_v5.py`
2. `app/services/market_collector_v51.py`
3. `app/services/market_identity_cluster_v53.py`
4. `app/services/market_representative_price_v54.py`
5. `app/services/market_signal_propagation_v52.py`
6. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
7. `tests/test_persistence_i6b1_tb08_market_intelligence_migration.py` — new

No other production or test file may be changed.

## 3. Authorized Migration

Within each of the five production modules, this authority permits only:

- adding the bounded engine-provider import;
- migrating the designated runtime read to `get_engine().connect()`;
- migrating the designated runtime write to `get_engine().begin()`;
- preserving the legacy engine import and legacy `engine.begin()` exclusively for
  the unchanged DDL-bearing function;
- preserving orchestrator transaction non-ownership, signatures, SQL, computation,
  row materialization, and return behavior.

The existing characterization test may be transitioned to the mixed I6-B1 state,
and the one dedicated migration test may be created.

## 4. DDL Freeze

DDL remains reserved for I7/TB-15. This authority does not permit changing,
extracting, invoking, or migrating any DDL-bearing function.

## 5. Importer Contract

The direct legacy importer count remains `19` because all five DDL functions retain
the legacy engine import. Importer-count contract files are outside this authority.

## 6. Verification Boundary

Verification may use static/AST inspection, fakes, monkeypatches, denial guards,
compilation, and non-resource pytest execution. It may not use a real database,
application network, or DDL execution.

## 7. Single-Use Rule

This authority is consumed only by one implementation commit whose diff is exactly
the seven authorized files. If another file is required, implementation must stop
and a superseding scope decision and authority must be established.

## 8. Non-Authorization

This authority does not authorize:

- TB-09 or TB-11 migration;
- provider, lifecycle, `app/main.py`, or database-module changes;
- importer-count contract changes;
- database mutation or network execution;
- application-network execution;
- DDL execution or migration;
- compatibility bridge implementation;
- I6 or Phase 4 completion.

## 9. Canonical Result

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6a_status=COMPLETE`
- `i6b1_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i6b1_scope_status=ESTABLISHED`
- `i6b1_exact_file_count=SEVEN`
- `i6b1_read_target=GET_ENGINE_CONNECT`
- `i6b1_write_target=GET_ENGINE_BEGIN`
- `i6b1_ddl_target=LEGACY_ENGINE_BEGIN_PRESERVED_UNTIL_I7`
- `i6b1_importer_count_transition=AUTHORIZED_19_TO_19`
- `i6b1_production_write_authority=ISSUED`
- `i6b1_test_write_authority=ISSUED`
- `consumer_migration_authority=BOUNDED_TO_EXACT_I6B1_TB08_SCOPE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `i6b2_implementation_authority=NONE`
- `i6_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_EXACT_I6B1_TB08_SEVEN_FILE_MIGRATION`
