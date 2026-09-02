# MA-2026-034 Phase 4 I5 Exact Scope Decision

## 1. Decision

I5 shall proceed as two sequential evidence-bounded sub-waves:

`I5-A -> I5-B`

I5-A is the presentation-seam characterization wave.

I5-B remains the collector per-item boundary wave, but its exact production cohort
is not established by this decision and requires a separate read-only exact-scope
preflight after I5-A completion.

## 2. Governing Basis

The Phase 2 compatibility migration seam register defines I5 as:

- Streamlit and admin presentation seams.

The Phase 3 transaction-boundary migration seam register defines I5 as:

- TB-05, TB-06, TB-07, TB-10 collector per-item boundaries;
- external I/O outside transaction;
- per-item atomicity, bounded retry, and partial batch outcome verification.

These are complementary I5 obligations, not evidence that all candidate files should
be mutated in one implementation cohort.

## 3. I5-A Exact Scope

I5-A is characterization-first and test-only.

Authorized future I5-A scope, once a separate test-write authority is issued:

- exactly one new test file:
  `tests/test_persistence_presentation_seam_characterization.py`

No production file is authorized for modification in I5-A.

The characterization shall establish the observed presentation seam split:

### `app/ui/admin_dashboard.py`

Current evidence:

- directly imports `engine` from `app.db.database`;
- owns two active `engine.connect()` read acquisitions;
- the acquisitions are in `load_df` and `load_view`;
- no external module import dependency on `app.ui.admin_dashboard` was observed by
  the I5 read-only preflight.

### `app/ui/streamlit_app.py`

Current evidence:

- no longer directly imports legacy `app.db.database.engine`;
- imports bounded `get_engine`;
- contains bounded `get_engine().connect()` and `get_engine().begin()` acquisitions;
- has existing presentation regression consumers.

I5-A shall characterize these current semantics without changing them.

## 4. Why I5-A Starts With Presentation Characterization

The presentation cohort is currently exact and small:

- one remaining legacy presentation importer: `app/ui/admin_dashboard.py`;
- one already-migrated comparison surface: `app/ui/streamlit_app.py`.

This provides a bounded characterization target without guessing the much broader
collector cohort.

## 5. I5-B Status

I5-B remains required.

However, the I5 read-only inventory identified multiple collector-like modules with
different combinations of:

- read acquisition;
- update transaction;
- per-item loops;
- DDL/ensure-column behavior.

The inventory alone does not establish the exact mapping of TB-05, TB-06, TB-07,
and TB-10 to a safe production mutation cohort.

Therefore:

- `i5b_scope_status=NOT_YET_DETERMINED`
- no I5-B production write authority is issued;
- no collector file is authorized for mutation by this decision;
- after I5-A completion, I5-B must begin with a dedicated read-only TB/cohort
  mapping preflight.

## 6. Compatibility Bridge

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No current I5-A evidence requires a global compatibility bridge.

No compatibility proxy or legacy engine export is authorized.

## 7. Provider / Composition Boundary

The existing bounded provider and app.main lifespan remain frozen during I5-A.

I5-A authorizes no changes to:

- `app/db/engine_provider.py`;
- `app/main.py`;
- `app/db/lifecycle.py`.

## 8. Non-Authorization

This decision does not authorize:

- I5-A test implementation;
- any production write;
- I5-B implementation;
- admin dashboard migration;
- Streamlit migration;
- collector migration;
- compatibility bridge implementation;
- database mutation;
- database network execution;
- Phase 4 completion.

## 9. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i4_status=COMPLETE`
- `i5_scope=I5A_THEN_I5B`
- `i5a_scope=EXACT_ONE_NEW_TEST_FILE`
- `i5a_test_file=tests/test_persistence_presentation_seam_characterization.py`
- `i5a_production_write_required=NO`
- `i5a_implementation_authority=NOT_ISSUED`
- `i5b_scope_status=NOT_YET_DETERMINED`
- `i5b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I5A_TEST_WRITE_AUTHORITY`
