# ADA-MA-2026-034 Phase 4 I6-A Test-Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I6-A — Intelligence Pipeline Boundary Characterization`
- Exact-scope predecessor commit:
  `c37e84a197a99d31545f13a720fea170d3aff6e4`
- Exact-scope predecessor tag:
  `ma-2026-034-phase4-i6-exact-scope-decision-established-v1.0`
- Exact-scope decision SHA-256:
  `d8237f7b32b8977fb20bc8c243b2e50c823c615deb5e02bd8c3879a4c718cf14`

## 2. Authorized Write Scope

This authority permits creation of exactly one new file:

`tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`

No existing file may be modified.

## 3. Required Characterization

The test shall characterize, without real-resource execution:

- the five-member TB-08 market-intelligence cohort;
- the seven-member TB-09 product-intelligence cohort;
- the one-member TB-11 shopping-collector cohort;
- legacy engine import and `begin()` acquisition shapes;
- DDL-bearing functions and their separation from ordinary runtime work;
- read/fetch, compute, update/UoW, external-I/O, and orchestrator boundaries;
- preservation of the I7/TB-15 DDL reservation;
- the current direct legacy importer count of `19`.

The characterization may use static source inspection, AST inspection, monkeypatches,
fakes, and denial guards. It may not connect to a real database or application network.

## 4. Single-Use Rule

This authority is single-use and is consumed only by one implementation commit whose
diff contains exactly the authorized new test file.

If another file is required, implementation must stop and a superseding scope decision
and authority must be established before work resumes.

## 5. Non-Authorization

This authority does not authorize:

- production writes;
- modification of existing tests;
- I6-B consumer migration;
- database mutation or network execution;
- application-network execution;
- DDL execution or extraction;
- compatibility bridge implementation;
- I6 completion or Phase 4 completion.

## 6. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6_status=AUTHORIZED_I6A_NOT_IMPLEMENTED`
- `i6_entry_strategy=CHARACTERIZATION_FIRST`
- `i6a_scope_status=ESTABLISHED`
- `i6a_exact_file_count=ONE`
- `i6a_test_write_authority=ISSUED`
- `i6a_authorized_file=tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
- `production_write_authority=NONE`
- `existing_test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i6b_implementation_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_EXACT_I6A_ONE_FILE_CHARACTERIZATION`
