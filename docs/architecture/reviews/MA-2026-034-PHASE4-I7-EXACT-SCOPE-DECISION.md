# MA-2026-034 Phase 4 I7 Exact-Scope Decision

## 1. Decision

I7 uses a characterization-first entry strategy.

The exact I7-A scope is one new test file:

`tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`

I7-B production extraction scope remains undetermined. This decision does not
authorize the I7-A test write or any production, extraction, database, or DDL
work.

## 2. Governing Boundary

I7 is bounded to TB-15 and DDL-01 through DDL-14 extraction. Its exit condition
is that ordinary runtime paths contain no self-migrating DDL while execution
continues to require separate migration and database-mutation authority.

The current boundary consists of 14 runtime-reachable DDL functions containing
124 DDL statements. Thirteen are retained inside the completed I6 cohort and
one is in `app/services/recommendation_intelligence_v55.py`.

## 3. Why Characterization Must Precede Production Scope

The evidence is not yet sufficient to authorize one production extraction
shape:

- 13 DDL functions are called directly by their orchestrators;
- DDL-06 is called inside the `insert_products` write path;
- removing the DDL functions would make 13 completed-I6 legacy imports
  removable, while DDL-14 must retain its legacy import for non-I7 runtime use;
- the candidate direct legacy-engine importer transition is therefore `19` to
  `6`, but is not yet authorized;
- `sql/collector_v2_migration.sql` covers all 18 DDL-06 runtime statements and
  also contains one additional index statement;
- no Alembic or equivalent repository migration framework is established;
- the existing I6 characterization covers only the 13-member I6 cohort and is
  regression evidence, not the complete I7 extraction contract.

The partial DDL-06 artifact means a consolidated or partitioned migration
artifact cannot be selected safely without first making overlap, canonicality,
and supersession expectations executable as non-resource characterization.

## 4. Exact I7-A Characterization Contract

The authorized-file candidate, if separately authorized, shall characterize
without importing or executing the production DDL functions:

1. the exact DDL-01 through DDL-14 module/function mapping;
2. the exact 124-statement inventory and per-seam statement counts;
3. zero-argument DDL function and legacy `engine.begin()` acquisition shapes;
4. runtime reachability through 13 direct orchestrator calls and one nested
   `insert_products` call;
5. the DDL-06 SQL-artifact overlap of 18 matching statements plus one additional
   index statement;
6. absence of a repository migration framework;
7. the candidate importer consequence `19` to `6`;
8. retention of the five non-DDL legacy importers outside automatic I7 scope;
9. prohibition of real database, application-network, and DDL execution.

The characterization must use source/AST/text inspection only. It must not
connect to a database, import a production module for execution, invoke a DDL
function, make an application-network request, or mutate repository state.

## 5. Deferred I7-B Decisions

Only after I7-A characterization is implemented and reviewed may a later
read-only preflight determine:

- one atomic production cohort versus bounded extraction subwaves;
- consolidated versus partitioned migration-artifact topology;
- treatment or supersession of `sql/collector_v2_migration.sql`;
- exact production, artifact, characterization-transition, migration-test, and
  importer-contract files;
- exact code-migration authority required to remove runtime DDL reachability;
- verification proving that extraction performs no DDL execution.

## 6. Non-Authorization

This decision does not authorize:

- creation of the I7-A test file;
- modification of existing tests;
- production or SQL-artifact writes;
- DDL extraction, migration, mutation, or execution;
- database or application-network execution;
- the candidate importer transition;
- migration of the five non-DDL legacy importers;
- I1-C2 compatibility-bridge implementation;
- I7 completion or Phase 4 completion.

## 7. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6_status=COMPLETE`
- `i7_status=SCOPED_NOT_AUTHORIZED`
- `i7_semantic_boundary=TB15_DDL01_THROUGH_DDL14_EXTRACTION_EXCLUDING_EXECUTION`
- `i7_entry_strategy=CHARACTERIZATION_FIRST`
- `i7a_scope_status=ESTABLISHED`
- `i7a_exact_file_count=ONE`
- `i7a_scope=ONE_NEW_TEST_FILE`
- `i7a_file=tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`
- `i7a_test_write_authority=NOT_ISSUED`
- `i7a_characterization=DDL_MAPPING_STATEMENT_INVENTORY_RUNTIME_REACHABILITY_ARTIFACT_OVERLAP_AND_IMPORTER_CONSEQUENCE`
- `i7b_production_extraction_scope_status=NOT_YET_DETERMINED`
- `i7_registered_ddl_boundary_count=14`
- `i7_runtime_ddl_statement_count=124`
- `existing_ddl06_artifact_status=PARTIAL_RUNTIME_COVERAGE_WITH_ONE_EXTRA_INDEX`
- `candidate_direct_legacy_engine_importer_transition=19_TO_6_NOT_YET_AUTHORIZED`
- `remaining_non_ddl_legacy_importer_count=5`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_extraction_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i7_implementation_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I7A_TEST_WRITE_AUTHORITY`
