# MA-2026-034 Phase 4 I6-B2 TB-09 Exact Scope Decision

## 1. Decision Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I6-B2 — TB-09 Product Intelligence Runtime Migration`
- Predecessor commit: `b98b80d95e8c87b243e547f53ffb16d6d4ff0e03`
- Predecessor tag: `ma-2026-034-phase4-post-i6b1-next-subwave-routing-decision-established-v1.0`
- Predecessor tag object: `f56bed7e09475b4c5f0b6df404c8ff699864469b`

## 2. Exact Nine-File Scope

Exactly the following nine files form the I6-B2 implementation scope:

1. `app/services/product_attribute_engine_v8.py`
2. `app/services/product_cluster_representative_v5.py`
3. `app/services/product_family_variant_v6.py`
4. `app/services/product_identity_cluster_v4.py`
5. `app/services/product_quality_engine_v10_runner.py`
6. `app/services/product_quality_engine_v9.py`
7. `app/services/product_variety_engine_v7.py`
8. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
9. `tests/test_persistence_i6b2_tb09_product_intelligence_migration.py` — new

No importer-count contract file is included because all seven legacy imports
remain required by the DDL functions reserved for I7. The direct legacy importer
count therefore remains `19`.

## 3. Required Runtime Migration

For each of the seven production modules:

- retain `from app.db.database import engine` solely for its DDL-bearing function;
- add `from app.db.engine_provider import get_engine` for ordinary runtime work;
- migrate every classified fetch/read function from `engine.connect()` to
  `get_engine().connect()`;
- migrate every classified state-changing function from `engine.begin()` to
  `get_engine().begin()`;
- preserve the orchestrator without direct engine acquisition;
- preserve call signatures, SQL, row materialization, computation, and return
  behavior.

The two state-changing functions in
`app/services/product_cluster_representative_v5.py`—`reset_cluster_flags` and
`update_row_flags`—are both within this runtime write boundary.

## 4. DDL Separation Boundary

The DDL-bearing function in each production module remains byte-preserved and
continues to use legacy `engine.begin()` until the separately governed I7/TB-15
wave.

This decision does not authorize DDL extraction, execution, rewriting, or
migration.

## 5. Test Transition

The existing I6 characterization file must transition to the mixed boundary
established by I6-B2:

- TB-08 and TB-09 runtime reads use provider `connect()`;
- TB-08 and TB-09 runtime writes use provider `begin()`;
- TB-08 and TB-09 DDL remains legacy-engine-owned;
- TB-11 remains unchanged and deferred;
- the global direct legacy importer count remains `19`.

The new shared migration test must verify all seven modules and the complete
classified runtime function set without real-resource execution.

## 6. Frozen Boundaries

This decision excludes:

- TB-11 production migration;
- importer-count contract changes;
- provider, lifecycle, `app/main.py`, or database-module changes;
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
- `i6b2_status=SCOPED_NOT_AUTHORIZED`
- `i6_completion_readiness=PREMATURE_TB09_TB11_UNRESOLVED`
- `i6b2_semantic_boundary=TB09_PRODUCT_INTELLIGENCE_RUNTIME_READ_WRITE_EXCLUDING_DDL`
- `i6b2_scope_status=ESTABLISHED`
- `i6b2_exact_file_count=NINE`
- `i6b2_scope=SEVEN_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_CHARACTERIZATION_PLUS_ONE_NEW_MIGRATION_TEST`
- `i6b2_read_target=GET_ENGINE_CONNECT`
- `i6b2_write_target=GET_ENGINE_BEGIN`
- `i6b2_ddl_target=LEGACY_ENGINE_BEGIN_PRESERVED_UNTIL_I7`
- `i6b2_importer_count_transition=19_TO_19`
- `i6b2_importer_contract_write_requirement=NONE`
- `i6b2_implementation_authority=NOT_ISSUED`
- `tb11_status=DEFERRED_TO_LATER_I6_SUBWAVE`
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
- `next_action=AUTHOR_EXACT_I6B2_TB09_WRITE_AUTHORITY`
