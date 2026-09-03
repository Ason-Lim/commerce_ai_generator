# MA-2026-034 Phase 4 I6-B3 TB-11 Exact Scope Decision

## 1. Decision Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I6-B3 — TB-11 Naver Shopping API Collector Runtime Migration`
- Predecessor commit: `20ecdbfd7359057513e7c80fb7db015335bbdc4d`
- Predecessor tag: `ma-2026-034-phase4-post-i6b2-next-subwave-routing-decision-established-v1.0`
- Predecessor tag object: `4ebbae2c64a1e06230928cc870ca08a16dfdd09a`

## 2. Exact Three-File Scope

Exactly the following three files form the I6-B3 implementation scope:

1. `app/services/naver_shopping_api_collector.py`
2. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
3. `tests/test_persistence_i6b3_tb11_naver_shopping_collector_migration.py` — new

No importer-count contract file is included because the production module's
legacy import remains required exclusively by its DDL-bearing function. The
direct legacy importer count therefore remains `19`.

## 3. Required Runtime Migration

In `app/services/naver_shopping_api_collector.py`:

- retain `from app.db.database import engine` solely for
  `ensure_collector_v2_columns`;
- add `from app.db.engine_provider import get_engine` for ordinary runtime work;
- migrate `insert_products` from `engine.begin()` to `get_engine().begin()`;
- preserve its state-changing INSERT behavior and explicit transaction ownership;
- preserve `get_naver_credentials` behavior;
- preserve `call_naver_api` behavior without executing application network I/O;
- preserve `collect_naver_products` without direct engine acquisition;
- preserve call signatures, SQL, row construction, control flow, and return behavior.

## 4. DDL Separation Boundary

`ensure_collector_v2_columns` remains byte-preserved and continues to use legacy
`engine.begin()` until the separately governed I7/TB-15 wave. Its existing call
relationship with `insert_products` is preserved.

This decision does not authorize DDL extraction, execution, rewriting, or
migration.

## 5. Test Transition

The existing I6 characterization file must transition to the final mixed I6
boundary:

- TB-08 and TB-09 provider-runtime characterization remains preserved;
- TB-11 runtime write uses provider `begin()`;
- TB-11 DDL remains legacy-engine-owned;
- credential lookup, external I/O, and orchestrator boundaries remain preserved;
- the global direct legacy importer count remains `19`.

The new migration test must verify the mixed legacy-DDL/provider-runtime shape,
the `insert_products` transaction boundary, behavior preservation, and denial of
real database, application-network, and DDL execution.

## 6. Frozen Boundaries

This decision excludes:

- importer-count contract changes;
- I5-B characterization or caller-test changes;
- provider, lifecycle, `app/main.py`, or database-module changes;
- credential-contract or external-API behavior changes;
- real database or application-network execution;
- DDL execution, extraction, rewriting, or migration;
- compatibility bridge work;
- I6 or Phase 4 completion.

## 7. Authority State

This document establishes exact scope only. It does not issue production or test
write authority. A separate single-use authority is required before
implementation.

## 8. Canonical Result

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6a_status=COMPLETE`
- `i6b1_status=COMPLETE`
- `i6b2_status=COMPLETE`
- `i6b3_status=SCOPED_NOT_AUTHORIZED`
- `i6_completion_readiness=PREMATURE_TB11_UNRESOLVED`
- `i6b3_semantic_boundary=TB11_NAVER_SHOPPING_API_COLLECTOR_RUNTIME_WRITE_EXTERNAL_IO_EXCLUDING_DDL`
- `i6b3_scope_status=ESTABLISHED`
- `i6b3_exact_file_count=THREE`
- `i6b3_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_CHARACTERIZATION_PLUS_ONE_NEW_MIGRATION_TEST`
- `i6b3_write_target=GET_ENGINE_BEGIN`
- `i6b3_external_io_target=BEHAVIOR_PRESERVED_NO_EXECUTION`
- `i6b3_orchestrator_target=NO_DIRECT_ENGINE_ACQUISITION`
- `i6b3_ddl_target=LEGACY_ENGINE_BEGIN_PRESERVED_UNTIL_I7`
- `i6b3_importer_count_transition=19_TO_19`
- `i6b3_importer_contract_write_requirement=NONE`
- `i6b3_existing_i5b_characterization_write_requirement=NONE`
- `i6b3_implementation_authority=NOT_ISSUED`
- `i7_ddl_scope=RESERVED_TB15_DDL01_THROUGH_DDL14`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i6_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I6B3_TB11_WRITE_AUTHORITY`
