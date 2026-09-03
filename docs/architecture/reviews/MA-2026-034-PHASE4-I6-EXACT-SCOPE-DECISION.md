# MA-2026-034 Phase 4 I6 Exact Scope Decision

## 1. Decision

I6 shall proceed as `I6-A` followed by separately governed `I6-B` migration cohorts.

The entry strategy is `CHARACTERIZATION_FIRST`.

## 2. I6-A Exact Scope

I6-A is exactly one new test file:

`tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`

The test shall characterize the current 13-module TB-08/TB-09/TB-11 boundary without
executing a real database, application network, or DDL.

It shall make observable:

- the exact TB-08 five-module cohort;
- the exact TB-09 seven-module cohort;
- the exact TB-11 one-module cohort;
- the current legacy engine import and `begin()` acquisition shape;
- DDL-bearing function boundaries;
- read/fetch, compute, update/UoW, external-I/O, and orchestrator boundaries;
- the constraint that I6 may not execute or silently extract I7/TB-15 DDL;
- the current global direct legacy importer count of `19`.

I6-A does not change production behavior or importer counts.

## 3. I6-B Candidate Partition

After I6-A completion, production migration must be scoped again from characterized
evidence. The candidate partition is:

- I6-B/TB-08: five market-intelligence modules;
- I6-B/TB-09: seven product-intelligence modules;
- I6-B/TB-11: one shopping-collector module.

These are three separate candidate cohorts, not one authorized 13-file migration.
Their ordering, exact test companions, importer-count consequences, and safe handling
of DDL-bearing entry points remain subject to later read-only exact-scope decisions.

## 4. DDL Boundary

All 13 candidates currently colocate runtime DDL with legacy transaction acquisition.
I6 governs read/fetch and update/UoW separation only. TB-15 and DDL-01 through DDL-14
remain reserved for I7, including any DDL extraction or migration execution.

## 5. Frozen Boundaries

I6-A shall not modify production code, existing tests, provider/lifecycle composition,
callers, database configuration, compatibility bridge artifacts, or DDL artifacts.

## 6. Non-Authorization

This decision does not itself authorize:

- creation of the I6-A test;
- production or existing-test writes;
- any I6-B migration;
- database mutation or network execution;
- DDL execution or extraction;
- I6 completion or Phase 4 completion.

## 7. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6_status=SCOPED_NOT_AUTHORIZED`
- `i6_entry_strategy=CHARACTERIZATION_FIRST`
- `i6a_scope_status=ESTABLISHED`
- `i6a_exact_file_count=ONE`
- `i6a_scope=ONE_NEW_TEST_FILE`
- `i6a_file=tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
- `i6a_test_write_authority=NOT_ISSUED`
- `i6b_candidate_partition=TB08_5_TB09_7_TB11_1`
- `i6b_production_scope_status=NOT_YET_DETERMINED`
- `remaining_direct_legacy_engine_importer_count=19`
- `i7_ddl_scope=RESERVED_TB15_DDL01_THROUGH_DDL14`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i6_implementation_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I6A_TEST_WRITE_AUTHORITY`
