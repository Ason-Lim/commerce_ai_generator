# MA-2026-034 Phase 4 I6-B1 TB-08 Exact Scope Decision

## 1. Decision Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I6-B1 — TB-08 Market Intelligence Runtime Migration`
- Predecessor commit: `757e2338cd7a95f7ea7c07e9e24188d64f4e8de2`
- Predecessor tag: `ma-2026-034-phase4-i6a-completion-review-established-v1.0`
- Predecessor tag object: `e7f5ed38f3d202bec3f96e13a4c80bae03fa4a58`

## 2. Exact Seven-File Scope

Exactly the following seven files form the I6-B1 implementation scope:

1. `app/services/market_collector_v5.py`
2. `app/services/market_collector_v51.py`
3. `app/services/market_identity_cluster_v53.py`
4. `app/services/market_representative_price_v54.py`
5. `app/services/market_signal_propagation_v52.py`
6. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
7. `tests/test_persistence_i6b1_tb08_market_intelligence_migration.py` — new

No importer-count contract file is included because the direct legacy importer
count remains `19` while the DDL engine imports are retained.

## 3. Required Runtime Migration

For each of the five production modules:

- retain `from app.db.database import engine` solely for the DDL-bearing function;
- add `from app.db.engine_provider import get_engine` for ordinary runtime work;
- migrate the fetch/read function from `engine.connect()` to `get_engine().connect()`;
- migrate the state-changing update function from `engine.begin()` to `get_engine().begin()`;
- preserve the orchestrator without direct engine acquisition;
- preserve call signatures, SQL, row materialization, computation, and return behavior.

## 4. DDL Separation Boundary

The DDL-bearing function in each production module remains unchanged and continues
to use legacy `engine.begin()` until the separately governed I7/TB-15 wave.

This decision does not authorize DDL extraction, execution, rewriting, or migration.

## 5. Test Transition

The existing I6 characterization file must transition from an all-legacy statement
to the mixed boundary established by I6-B1:

- TB-08 DDL remains legacy-engine-owned;
- TB-08 runtime reads use provider `connect()`;
- TB-08 runtime writes use provider `begin()`;
- TB-09 and TB-11 remain unchanged;
- global legacy importer count remains `19`.

The new migration test must verify all five modules without real-resource execution.

## 6. Frozen Boundaries

This decision excludes:

- TB-09 and TB-11 production migration;
- importer-count contract changes;
- provider, lifecycle, `app/main.py`, or database-module changes;
- real database or application-network execution;
- DDL execution or migration;
- compatibility bridge work;
- I6 or Phase 4 completion.

## 7. Authority State

This document establishes exact scope only. It does not issue production or test
write authority. A separate single-use authority is required before implementation.

## 8. Canonical Result

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6a_status=COMPLETE`
- `i6b1_status=SCOPED_NOT_AUTHORIZED`
- `i6b1_semantic_boundary=TB08_MARKET_INTELLIGENCE_RUNTIME_READ_WRITE_EXCLUDING_DDL`
- `i6b1_scope_status=ESTABLISHED`
- `i6b1_exact_file_count=SEVEN`
- `i6b1_scope=FIVE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_CHARACTERIZATION_PLUS_ONE_NEW_MIGRATION_TEST`
- `i6b1_read_target=GET_ENGINE_CONNECT`
- `i6b1_write_target=GET_ENGINE_BEGIN`
- `i6b1_ddl_target=LEGACY_ENGINE_BEGIN_PRESERVED_UNTIL_I7`
- `i6b1_importer_count_transition=19_TO_19`
- `i6b1_importer_contract_write_requirement=NONE`
- `i6b1_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i6_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I6B1_TB08_WRITE_AUTHORITY`
