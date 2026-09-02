# ADA-MA-2026-034 Phase 4 I5-B3 TB-10 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Subwave: `I5-B3 — TB-10 Naver DataLab Cached Read/Write Migration`
- Exact-scope predecessor commit:
  `ef44a0f28576bd2cdd2941fd680964c4e0f6e147`
- Exact-scope predecessor tag:
  `ma-2026-034-phase4-i5b3-tb10-exact-scope-decision-established-v1.0`
- Exact-scope decision SHA-256:
  `3c0eff4391c7fdda9227a7f68dfafb161352fd5e91b981610726c895756e6143`

## 2. Authorized Exact File Scope

This authority permits writes to exactly six files:

1. `app/services/naver_datalab_service.py`
2. `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
3. `tests/test_persistence_i5b3_tb10_naver_datalab_migration.py`
4. `tests/test_persistence_engine_disposal.py`
5. `tests/test_persistence_engine_lifecycle.py`
6. `tests/test_persistence_fastapi_lifecycle_composition.py`

The third file may be created. The other five files already exist and may be
modified only as authorized below. No other file may be created or modified.

## 3. Authorized Production Transition

Within `app/services/naver_datalab_service.py`, authority is limited to:

- replacing `from app.db.database import engine` with
  `from app.db.engine_provider import get_engine`;
- migrating `get_cached_keyword_trend` from legacy `engine.begin()` acquisition
  to bounded `get_engine().connect()` acquisition;
- migrating `save_keyword_trend_cache` from legacy `engine.begin()` acquisition
  to bounded `get_engine().begin()` acquisition;
- removing the obsolete module-level legacy engine authority.

The implementation must preserve SQL text, bind parameters, row materialization,
return values, exception behavior, cache orchestration, public function
signatures, and all unrelated Naver DataLab behavior.

## 4. Authorized Characterization Transition

Within
`tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`,
only the TB-10 characterization may transition from the legacy shared
module-level engine shape to the provider-aware final shape:

- cached read acquires through `get_engine()` and uses `connect()`;
- cached write acquires through `get_engine()` and uses `begin()`;
- neither function imports or uses `app.db.database.engine`;
- the read/write semantic distinction remains explicit.

Unrelated I5-B characterization contracts must remain unchanged.

## 5. Authorized Dedicated Migration Test

The new file
`tests/test_persistence_i5b3_tb10_naver_datalab_migration.py` may be created to
verify:

- provider-based engine acquisition;
- bounded cached-read `connect()` semantics;
- bounded cached-write `begin()` semantics;
- removal of the direct legacy engine import;
- preservation of SQL, parameters, result behavior, and public contracts;
- denial of real database and external network resource acquisition.

The test must use fakes, sentinels, static inspection, or equivalent isolated
techniques. It must not connect to a real database or external network.

## 6. Authorized Importer-Count Transition

Within exactly these three files:

- `tests/test_persistence_engine_disposal.py`;
- `tests/test_persistence_engine_lifecycle.py`;
- `tests/test_persistence_fastapi_lifecycle_composition.py`;

authority is limited to changing:

- `EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 22` to `21`;
- test-name suffix `remains_22` to `remains_21`;
- directly corresponding assertion text, only if required for the exact count
  transition.

All other disposal, lifecycle, database-module identity, compatibility-bridge,
composition, and resource-denial contracts must remain unchanged.

## 7. Required Post-Implementation State

- cached read target: `get_engine().connect()`;
- cached write target: `get_engine().begin()`;
- direct legacy engine importer count: exactly `21`;
- external `naver_datalab_service.engine` compatibility proxy: absent;
- TB-10 DDL: absent;
- caller and orchestration behavior: preserved.

## 8. Frozen Surfaces

No write is authorized to:

- `app/db/engine_provider.py`;
- `app/main.py`;
- `app/db/lifecycle.py`;
- `app/db/database.py`;
- `app/ui/streamlit_app.py`;
- caller modules;
- `app/services/naver_shopping_api_collector.py`;
- any unrelated production or test file;
- any other direct legacy engine importer.

No compatibility bridge or legacy-engine proxy may be created.

If implementation or regression evidence indicates that another file or
semantic change is required, implementation must stop. The new evidence must be
classified read-only and the exact scope and authority must be superseded before
work resumes.

## 9. DDL and Resource Boundary

DDL remains excluded from I5-B3 and reserved for:

`I7 / TB-15`

No real database access, database mutation, database network execution, DDL
execution, or external network collection is authorized.

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

## 10. Permitted Verification

Permitted verification is non-networking and non-mutating:

- Python compilation;
- the dedicated I5-B3 TB-10 migration test;
- the existing I5-B characterization test;
- the three importer-count contract test files;
- persistence real-resource denial guards;
- selected Naver DataLab, market, and persistence regression tests;
- collection-only verification;
- exact six-file diff and commit-scope verification.

Tests must deny or replace real resource acquisition before importing or
executing affected runtime paths.

## 11. Authority Consumption

This authority is single-use and bounded to one exact I5-B3 implementation
commit. It is consumed when the authorized six-file implementation is committed.
It does not authorize a second implementation commit, repair commit, completion
review, or any scope expansion.

## 12. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_status=COMPLETE`
- `i5b3_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i5_completion_readiness=PREMATURE`
- `i5b3_semantic_boundary=TB10_NAVER_DATALAB_CACHED_READ_WRITE`
- `i5b3_scope_status=ESTABLISHED`
- `i5b3_exact_file_count=SIX`
- `i5b3_importer_count_transition=AUTHORIZED_22_TO_21`
- `i5b3_cached_read_target=GET_ENGINE_CONNECT`
- `i5b3_cached_write_target=GET_ENGINE_BEGIN`
- `i5b3_production_write_authority=ISSUED`
- `i5b3_test_write_authority=ISSUED`
- `consumer_migration_authority=BOUNDED_TO_EXACT_I5B3_TB10_SCOPE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `i5_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_EXACT_I5B3_TB10_SIX_FILE_MIGRATION`
