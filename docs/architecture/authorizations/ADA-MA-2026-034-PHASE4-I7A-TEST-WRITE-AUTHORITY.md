# ADA-MA-2026-034 Phase 4 I7-A Test-Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I7-A — DDL Extraction Boundary Characterization`
- Exact-scope predecessor commit:
  `8f06c1fe5355d40b9bb91e0298418983eec48dd3`
- Exact-scope predecessor tag:
  `ma-2026-034-phase4-i7-exact-scope-decision-established-v1.0`
- Exact-scope decision SHA-256:
  `60b8b7cad65a62e958ad103de05253438482b27c494ebc1a802694c843ee8f92`

## 2. Authorized Write Scope

This authority permits creation of exactly one new file:

`tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`

No existing file may be modified.

## 3. Required Characterization

The test shall characterize, using static source, AST, and text inspection only:

- the exact DDL-01 through DDL-14 seam-to-module, DDL-function, caller, and statement-count mapping;
- the exact total of 14 DDL-bearing modules and 124 runtime DDL statements;
- the runtime-reachability partition of 13 direct orchestrator calls and one nested write call;
- zero-argument DDL functions with exactly one legacy `engine.begin()` acquisition and no provider acquisition inside those functions;
- the 13 I6 modules whose legacy engine imports become removal candidates after extraction;
- the DDL-14 module whose non-DDL legacy engine references require import retention;
- the existing DDL-06 SQL artifact's 18-of-18 runtime coverage and one extra `CREATE INDEX` statement;
- absence of an established migration framework;
- the current 19 direct legacy engine importers and the unapproved candidate transition from 19 to 6;
- the five non-DDL legacy importers that remain outside I7 extraction scope.

The test may read repository source and artifacts. It may not import or execute production
DDL paths, connect to a database, perform application-network I/O, mutate an artifact, or
execute DDL.

## 4. Single-Use Rule

This authority is single-use and is consumed only by one implementation commit whose
diff contains exactly the authorized new test file.

If another file is required, implementation must stop and a superseding scope decision
and authority must be established before work resumes.

## 5. Non-Authorization

This authority does not authorize:

- production writes or production DDL extraction;
- modification of existing tests or SQL artifacts;
- creation of migration SQL, a migration framework, or compatibility bridge code;
- database mutation or database-network execution;
- application-network execution;
- DDL extraction or DDL execution;
- removal of legacy engine imports or the candidate `19_TO_6` transition;
- I7-B production scope or implementation;
- I7 completion or Phase 4 completion.

## 6. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6_status=COMPLETE`
- `i7_status=AUTHORIZED_I7A_NOT_IMPLEMENTED`
- `i7_entry_strategy=CHARACTERIZATION_FIRST`
- `i7a_scope_status=ESTABLISHED`
- `i7a_exact_file_count=ONE`
- `i7a_test_write_authority=ISSUED`
- `i7a_authorized_file=tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`
- `i7b_production_extraction_scope_status=NOT_YET_DETERMINED`
- `candidate_direct_legacy_engine_importer_transition=19_TO_6_NOT_AUTHORIZED`
- `production_write_authority=NONE`
- `existing_test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_extraction_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i7b_implementation_authority=NONE`
- `i7_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_EXACT_I7A_ONE_FILE_CHARACTERIZATION`
