# ADA-MA-2026-034 Phase 4 I5-B4 TB-05 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Subwave: `I5-B4 — TB-05 Simple Reader Services Migration`
- Exact-scope predecessor commit:
  `290043a86f6bdff07730b726f9ffe54af61e83a5`
- Exact-scope predecessor tag:
  `ma-2026-034-phase4-i5b4-tb05-exact-scope-decision-established-v1.0`
- Exact-scope decision SHA-256:
  `91a381e44c00d344fdb2a1619ae950f27f04e1844b87e1c8f5443fdef753e114`

## 2. Authorized Exact File Scope

This single-use authority permits writes to exactly six files:

1. `app/services/coupang_review_matcher.py`
2. `app/services/db_product_collector.py`
3. `tests/test_persistence_i5b4_tb05_simple_reader_migration.py`
4. `tests/test_persistence_engine_disposal.py`
5. `tests/test_persistence_engine_lifecycle.py`
6. `tests/test_persistence_fastapi_lifecycle_composition.py`

The third file may be created. The other five files already exist and may be
modified only as authorized below. No other file may be created or modified.

## 3. Authorized Production Transition

Within both authorized production files, authority is limited to:

- replacing `from app.db.database import engine` with
  `from app.db.engine_provider import get_engine`;
- replacing the single legacy `engine.connect()` acquisition with one bounded
  `get_engine().connect()` acquisition;
- removing the obsolete module-level legacy engine authority.

The implementation must preserve public function signatures, SQL text, bind
parameters, row materialization, filtering, normalization, scoring, enrichment,
return values, exception behavior, and all unrelated service behavior.

No `get_engine().begin()` transaction may be introduced because both targets
are SELECT-only readers.

## 4. Authorized Dedicated Migration Test

The new file
`tests/test_persistence_i5b4_tb05_simple_reader_migration.py` may be created to
verify both authorized production modules as one atomic cohort:

- provider-based engine acquisition;
- exactly one bounded `get_engine().connect()` acquisition per reader;
- absence of `get_engine().begin()`;
- removal of both direct legacy engine imports;
- preservation of SQL, parameters, materialization, signatures, and return
  behavior;
- denial of real database and application-network resource acquisition.

The test must use fakes, sentinels, static inspection, or equivalent isolated
techniques. It must not connect to a real database or external network.

No existing characterization test is authorized for modification.

## 5. Authorized Importer-Count Transition

Within exactly these three files:

- `tests/test_persistence_engine_disposal.py`;
- `tests/test_persistence_engine_lifecycle.py`;
- `tests/test_persistence_fastapi_lifecycle_composition.py`;

authority is limited to changing:

- `EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 21` to `19`;
- test-name suffix `remains_21` to `remains_19`;
- directly corresponding assertion text only if required.

All other disposal, lifecycle, database identity, compatibility, composition,
and resource-denial contracts must remain unchanged.

## 6. Required Post-Implementation State

- both TB-05 legacy readers use `get_engine().connect()`;
- neither uses `get_engine().begin()`;
- both direct legacy engine imports are absent;
- direct legacy engine importer count is exactly `19`;
- external module-engine compatibility proxies are absent;
- signatures, SQL, materialization, filtering, scoring, and returns are
  preserved;
- TB-05 DDL remains absent.

## 7. Frozen Surfaces

No write is authorized to:

- `app/services/market/collector.py`;
- any existing characterization test;
- `app/db/engine_provider.py`;
- `app/main.py`;
- `app/db/lifecycle.py`;
- `app/db/database.py`;
- presentation or Streamlit files;
- caller modules;
- any unrelated production or test file;
- any other direct legacy engine importer.

No compatibility bridge, legacy-engine proxy, transaction-owning write scope,
or DDL may be introduced.

If implementation or regression evidence indicates another file or semantic
change is required, implementation must stop. The evidence must be classified
read-only and the exact scope and authority superseded before work resumes.

## 8. DDL and Resource Boundary

DDL remains excluded from I5-B4 and reserved for `I7 / TB-15`.

No real database access, database mutation, database network execution, DDL
execution, or external application-network collection is authorized.

I1-C2 remains `DEFERRED_UNTIL_FURTHER_EVIDENCE`.

## 9. Permitted Verification

Permitted verification is non-networking and non-mutating:

- Python compilation;
- the dedicated I5-B4 TB-05 migration test;
- the three importer-count contract test files;
- persistence real-resource denial guards;
- selected generator, marketplace, and persistence regression tests;
- collection-only verification;
- exact six-file diff and commit-scope verification.

Tests must deny or replace real resource acquisition before importing or
executing affected runtime paths.

## 10. Authority Consumption

This authority is single-use and bounded to one exact I5-B4 implementation
commit. It is consumed when the authorized six-file implementation is
committed. It does not authorize a second implementation commit, repair commit,
completion review, or scope expansion.

## 11. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_status=COMPLETE`
- `i5b3_status=COMPLETE`
- `i5b4_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i5_completion_readiness=PREMATURE_TB05_UNRESOLVED`
- `i5b4_semantic_boundary=TB05_SIMPLE_READER_SERVICES`
- `i5b4_scope_status=ESTABLISHED`
- `i5b4_exact_file_count=SIX`
- `i5b4_importer_count_transition=AUTHORIZED_21_TO_19`
- `i5b4_read_target=GET_ENGINE_CONNECT`
- `i5b4_production_write_authority=ISSUED`
- `i5b4_test_write_authority=ISSUED`
- `consumer_migration_authority=BOUNDED_TO_EXACT_I5B4_TB05_SCOPE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `i5_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_EXACT_I5B4_TB05_SIX_FILE_MIGRATION`
