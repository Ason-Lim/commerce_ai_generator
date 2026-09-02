# MA-2026-034 Phase 4 I5-B3 TB-10 Exact Scope Decision

## Decision

The exact I5-B3 TB-10 migration scope is six files:

1. `app/services/naver_datalab_service.py`
2. `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
3. `tests/test_persistence_i5b3_tb10_naver_datalab_migration.py`
4. `tests/test_persistence_engine_disposal.py`
5. `tests/test_persistence_engine_lifecycle.py`
6. `tests/test_persistence_fastapi_lifecycle_composition.py`

This is one existing production file, four existing test files, and one new
migration test file. No other production or test file is in I5-B3 scope.

## Governing Evidence

The Phase 3 transaction-boundary migration seam register defines TB-10 as:

- current cached read and cached write both use `begin`;
- target cached read uses a read scope;
- target cached write uses an explicit unit of work.

The governing transaction/unit-of-work contract requires:

- a pure read to use bounded `engine.connect()` unless it participates in an
  already-owned unit of work;
- a state-changing operation to use an explicitly owned `engine.begin()` unit
  of work or a caller-provided connection already owned by one.

Repository evidence establishes that `get_cached_keyword_trend` is SELECT-only
and that `save_keyword_trend_cache` performs `INSERT ... ON CONFLICT DO UPDATE`.

## Authorized Future Production Shape

A subsequent exact write authority may migrate
`app/services/naver_datalab_service.py` as follows:

- replace `from app.db.database import engine` with
  `from app.db.engine_provider import get_engine`;
- migrate `get_cached_keyword_trend` to bounded
  `get_engine().connect()` read acquisition;
- migrate `save_keyword_trend_cache` to bounded
  `get_engine().begin()` transaction ownership;
- preserve SQL, parameters, row materialization, return behavior, cache behavior,
  and public function signatures except where a separately governed regression
  proves an exact change necessary.

The module-level legacy engine import is removed. No compatibility proxy is
required because no external dependency on `naver_datalab_service.engine` was
observed.

## Characterization Transition

The existing I5-B characterization file must transition its TB-10 assertions
from the legacy shared module-level engine shape to the provider-aware final
shape:

- cached read acquires through `get_engine()` and uses `connect()`;
- cached write acquires through `get_engine()` and uses `begin()`;
- neither function imports or uses the legacy module-level database engine;
- the read/write semantic distinction remains explicit.

This is a governed transition of the existing characterization, not silent test
relaxation.

## Dedicated Migration Test

One new test file,
`tests/test_persistence_i5b3_tb10_naver_datalab_migration.py`, is required to
verify the bounded provider migration and the cached read/write transaction
semantics without real database or network execution.

The migration test must fail closed against real resource acquisition and must
verify behavioral preservation through fakes, sentinels, static inspection, or
other non-network/non-database techniques appropriate to the repository.

## Importer-Count Consequence

The production migration removes exactly one direct legacy engine import.

The repository-wide direct legacy importer count therefore changes exactly:

`22 -> 21`

Exactly three existing regression contracts encode the superseded count of 22:

- `tests/test_persistence_engine_disposal.py`;
- `tests/test_persistence_engine_lifecycle.py`;
- `tests/test_persistence_fastapi_lifecycle_composition.py`.

Those three files are in the same exact migration scope so a subsequent write
authority may transition their importer-count constants and test names from 22
to 21 while preserving all other lifecycle, disposal, database hash,
compatibility-bridge, composition, and resource-denial contracts.

## Provider and Lifespan Sufficiency

The existing bounded engine provider and existing FastAPI lifespan binding are
sufficient for this migration.

No write is required to:

- `app/db/engine_provider.py`;
- `app/main.py`;
- `app/db/lifecycle.py`;
- `app/db/database.py`.

## Caller Boundary

No caller write, Streamlit write, or consumer-interface change is required by
current evidence. Existing cache orchestration remains outside direct
transaction ownership changes except for its calls into the two migrated TB-10
functions.

## DDL Boundary

The two TB-10 functions contain no DDL.

DDL remains excluded from I5-B3 and reserved for `I7 / TB-15`.

## Compatibility Boundary

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge or legacy-engine proxy is required or authorized.

## Frozen Exclusions

This exact scope excludes:

- all production files other than `app/services/naver_datalab_service.py`;
- all test files other than the five named test files;
- provider, lifecycle, database-module, and FastAPI composition production
  changes;
- caller and Streamlit changes;
- DDL or schema migration;
- unrelated legacy engine importers;
- compatibility bridge implementation;
- real database access, database mutation, or network execution;
- I5 completion and Phase 4 completion.

If later regression evidence proves an additional file is required, work must
stop and the scope must be reviewed and superseded before implementation expands.

## Non-Authorization

This decision is governance-only. It does not itself authorize any production
write, test write, consumer migration implementation, database mutation,
database network execution, DDL execution, compatibility bridge, I5 completion,
or Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_status=COMPLETE`
- `i5b3_status=SCOPED_NOT_AUTHORIZED`
- `i5_completion_readiness=PREMATURE`
- `i5b3_semantic_boundary=TB10_NAVER_DATALAB_CACHED_READ_WRITE`
- `i5b3_scope_status=ESTABLISHED`
- `i5b3_scope=ONE_EXISTING_PRODUCTION_PLUS_FOUR_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i5b3_exact_file_count=SIX`
- `i5b3_production_file=app/services/naver_datalab_service.py`
- `i5b3_characterization_test=tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
- `i5b3_migration_test=tests/test_persistence_i5b3_tb10_naver_datalab_migration.py`
- `i5b3_importer_count_contract_count=THREE`
- `i5b3_importer_count_transition=22_TO_21`
- `i5b3_cached_read_target=GET_ENGINE_CONNECT`
- `i5b3_cached_write_target=GET_ENGINE_BEGIN`
- `i5b3_legacy_engine_import=REMOVE`
- `i5b3_external_engine_dependency=ABSENT`
- `i5b3_provider_write_required=NO`
- `i5b3_app_main_write_required=NO`
- `i5b3_lifecycle_write_required=NO`
- `i5b3_database_module_write_required=NO`
- `i5b3_caller_write_required=NO`
- `i5b3_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i5b3_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I5B3_TB10_WRITE_AUTHORITY`
