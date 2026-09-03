# MA-2026-034 Phase 4 I5-B4 TB-05 Exact Scope Decision

## Decision

The exact I5-B4 TB-05 migration scope is six files:

1. `app/services/coupang_review_matcher.py`
2. `app/services/db_product_collector.py`
3. `tests/test_persistence_i5b4_tb05_simple_reader_migration.py`
4. `tests/test_persistence_engine_disposal.py`
5. `tests/test_persistence_engine_lifecycle.py`
6. `tests/test_persistence_fastapi_lifecycle_composition.py`

This is one atomic cohort containing two existing production files, one new
migration test file, and three existing importer-count contract files. No other
production or test file is in I5-B4 scope.

## Governing Evidence

The Phase 3 seam register defines TB-05 as three simple DB readers with three
bounded read acquisitions and no transaction-owning acquisition:

- `app/services/coupang_review_matcher.py`;
- `app/services/db_product_collector.py`;
- `app/services/market/collector.py`.

`market/collector.py` already uses the canonical bounded provider read shape and
requires no I5-B4 write. The two unresolved readers each have exactly one direct
legacy engine import and one `engine.connect()` SELECT-only acquisition.

The governing transaction/unit-of-work contract requires pure reads to use a
bounded `engine.connect()` scope. No state-changing SQL, DDL, or explicit unit
of work exists in either unresolved reader.

## Authorized Future Production Shape

A subsequent exact write authority may migrate both production files as one
atomic cohort:

- replace `from app.db.database import engine` with
  `from app.db.engine_provider import get_engine`;
- replace each single `engine.connect()` acquisition with a single bounded
  `get_engine().connect()` acquisition;
- preserve public function signatures, SQL, parameters, row materialization,
  filtering, scoring, enrichment, and return behavior.

The two module-level legacy engine imports are removed. No compatibility proxy
is required because no external dependency on either module-level engine was
observed.

## Dedicated Migration Test

One new shared migration test file,
`tests/test_persistence_i5b4_tb05_simple_reader_migration.py`, is required for
the atomic two-reader cohort.

It must verify for both production modules:

- provider import and legacy engine import removal;
- exactly one `get_engine().connect()` acquisition;
- absence of `get_engine().begin()`;
- preservation of SQL execution, row materialization, signatures, and return
  behavior using fakes, sentinels, or static inspection;
- denial of real database and application-network resource acquisition.

No existing characterization test requires a governed assertion transition.
Existing generator characterization remains a regression anchor and is not an
I5-B4 write target.

## Importer-Count Consequence

The atomic production migration removes exactly two direct legacy engine
imports. The repository-wide direct legacy importer count therefore changes:

`21 -> 19`

Exactly three existing regression contracts encode the superseded count of 21:

- `tests/test_persistence_engine_disposal.py`;
- `tests/test_persistence_engine_lifecycle.py`;
- `tests/test_persistence_fastapi_lifecycle_composition.py`.

They are in the same exact scope so a subsequent authority may transition only
their importer-count constants and test names from 21 to 19 while preserving
all other lifecycle, disposal, database identity, compatibility, composition,
and resource-denial contracts.

## Provider and Composition Sufficiency

The existing engine provider and FastAPI lifespan binding are sufficient. No
write is required to `app/db/engine_provider.py`, `app/main.py`,
`app/db/lifecycle.py`, or `app/db/database.py`.

No caller, marketplace collector, presentation, or Streamlit write is required.

## Frozen Boundaries

I5-B4 excludes:

- every production and test file not among the six named files;
- changes to `app/services/market/collector.py`;
- provider, lifecycle, database-module, and FastAPI composition changes;
- caller, presentation, and Streamlit changes;
- state-changing persistence behavior;
- DDL or schema migration;
- unrelated legacy engine importers;
- compatibility bridge implementation;
- real database access, database mutation, or application-network execution;
- I5 completion and Phase 4 completion.

DDL remains reserved for `I7 / TB-15`. I1-C2 remains
`DEFERRED_UNTIL_FURTHER_EVIDENCE`.

If later regression evidence proves another file is required, implementation
must stop and the scope must be reviewed and superseded before expansion.

## Non-Authorization

This decision is governance-only. It does not authorize production writes,
test writes, consumer migration implementation, database access or mutation,
application-network execution, DDL, a compatibility bridge, I5 completion, or
Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_status=COMPLETE`
- `i5b3_status=COMPLETE`
- `i5b4_status=SCOPED_NOT_AUTHORIZED`
- `i5_completion_readiness=PREMATURE_TB05_UNRESOLVED`
- `i5b4_semantic_boundary=TB05_SIMPLE_READER_SERVICES`
- `i5b4_scope_status=ESTABLISHED`
- `i5b4_scope=TWO_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_PLUS_THREE_EXISTING_IMPORTER_CONTRACT_FILES`
- `i5b4_exact_file_count=SIX`
- `i5b4_production_file_1=app/services/coupang_review_matcher.py`
- `i5b4_production_file_2=app/services/db_product_collector.py`
- `i5b4_migration_test=tests/test_persistence_i5b4_tb05_simple_reader_migration.py`
- `i5b4_importer_count_contract_count=THREE`
- `i5b4_importer_count_transition=21_TO_19`
- `i5b4_read_target=GET_ENGINE_CONNECT`
- `i5b4_legacy_engine_imports=REMOVE_TWO`
- `i5b4_existing_characterization_write_required=NO`
- `i5b4_provider_write_required=NO`
- `i5b4_app_main_write_required=NO`
- `i5b4_lifecycle_write_required=NO`
- `i5b4_database_module_write_required=NO`
- `i5b4_caller_write_required=NO`
- `i5b4_implementation_authority=NOT_ISSUED`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i5_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I5B4_TB05_WRITE_AUTHORITY`
