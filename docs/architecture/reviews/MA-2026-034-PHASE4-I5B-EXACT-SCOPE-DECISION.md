# MA-2026-034 Phase 4 I5-B Exact Scope Decision

## Decision

I5-B shall proceed as `I5-B1` characterization first, followed by a separately
scoped `I5-B2` production migration.

I5-B1 is exactly one new test file:

`tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`

No production write is authorized by this decision.

## Governing TB Boundary

I5 governs TB-05, TB-06, TB-07, and TB-10.

- TB-05: simple reader services acquire directly.
- TB-06: collector fetch functions acquire directly.
- TB-07: collector update functions open per-call transactions.
- TB-10: `naver_datalab_service` uses `begin` for cached read and write.

The register does not enumerate exact files/functions for TB-05 through TB-07.
Therefore the production mutation cohort SHALL NOT be inferred before
characterization.

TB-10 has a concrete module identity:
`app/services/naver_datalab_service.py`, including
`get_cached_keyword_trend` and `save_keyword_trend_cache`.

## Characterization Purpose

I5-B1 shall characterize, without production mutation:

1. representative simple-reader acquisition shape;
2. collector fetch/read acquisition shape;
3. collector update per-call transaction shape;
4. orchestration loops that invoke per-item update functions;
5. external I/O separation from database transaction ownership;
6. TB-10 cached-read versus cached-write transaction shape;
7. direct caller surfaces where observed;
8. DDL-bearing functions as excluded seams, not I5-B production targets.

## DDL Exclusion

Runtime DDL is not authorized in I5-B.

`ensure_*` / column-creation functions containing `ALTER TABLE`, `CREATE TABLE`,
`CREATE INDEX`, or equivalent DDL remain reserved for I7/TB-15 authority.

`naver_shopping_api_collector.ensure_collector_v2_columns` is therefore not an
I5-B production migration target merely because the module also contains a
collector insert path.

## I6 Separation

Market/product intelligence modules governed by TB-08, TB-09, and TB-11 remain
outside I5-B production scope even when their code exhibits superficially similar
fetch/update patterns.

## Production Scope Deferral

I5-B2 exact production scope remains `NOT_YET_DETERMINED`.

It shall be decided only after I5-B1 establishes a stable TB-to-file/function
characterization and identifies the smallest atomic migration cohort.

## Provider / Lifecycle

The existing bounded canonical provider is available.

No `app.main`, `app.db.engine_provider`, or lifecycle write is authorized here.
Whether a later exact cohort can use `get_engine()` without those changes shall be
decided from I5-B1 evidence.

## Compatibility Bridge

I1-C2 remains `DEFERRED_UNTIL_FURTHER_EVIDENCE`.

No current I5-B evidence establishes a need for a global compatibility bridge.

## Non-Authorization

This decision authorizes no production write, test write, database mutation,
database network execution, consumer migration implementation, DDL execution,
compatibility bridge, or Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b_scope=I5B1_THEN_I5B2`
- `i5b1_scope=EXACT_ONE_NEW_TEST_FILE`
- `i5b1_test_file=tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
- `i5b1_production_write_required=NO`
- `i5b1_implementation_authority=NOT_ISSUED`
- `i5b2_scope_status=NOT_YET_DETERMINED`
- `i5b2_implementation_authority=NOT_ISSUED`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I5B1_TEST_WRITE_AUTHORITY`
