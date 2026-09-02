# ADA-MA-2026-034 Phase 4 I5-A Test-Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I5-A — Presentation Seam Characterization`
- Exact-scope predecessor commit:
  `d829ace90eae8afe693d21e338b5dbb1d5b96f33`
- Exact-scope predecessor tag:
  `ma-2026-034-phase4-i5-exact-scope-decision-established-v1.0`

## 2. Authorized Scope

This authority permits exactly one new test file:

`tests/test_persistence_presentation_seam_characterization.py`

No existing test file may be modified.

No production file may be modified.

## 3. Required Characterization Targets

The new characterization shall establish the observed presentation seam split.

### `app/ui/admin_dashboard.py`

Current pre-migration behavior to characterize:

- direct import of `engine` from `app.db.database`;
- exactly two `engine.connect()` acquisitions;
- `load_df` owns one read acquisition;
- `load_view` owns one read acquisition;
- no observed external import dependency on `app.ui.admin_dashboard`.

### `app/ui/streamlit_app.py`

Current post-I3 behavior to characterize:

- bounded `get_engine` import;
- no direct `app.db.database.engine` import;
- bounded `get_engine().connect()` acquisition remains present;
- bounded `get_engine().begin()` acquisition remains present;
- existing presentation regression consumers remain outside this test-write scope.

## 4. Purpose

I5-A is characterization-only.

The purpose is to establish a stable pre-migration contract before any presentation
production migration is scoped.

This authority does not decide or authorize the eventual admin-dashboard migration
mechanism.

## 5. Frozen Production Surfaces

The following remain read-only under this authority:

- `app/ui/admin_dashboard.py`
- `app/ui/streamlit_app.py`
- `app/db/engine_provider.py`
- `app/main.py`
- `app/db/lifecycle.py`
- `app/db/database.py`

## 6. I5-B

I5-B remains:

`NOT_YET_DETERMINED`

No collector or per-item boundary production/test mutation is authorized here.

A separate exact-scope read-only TB/cohort mapping preflight remains required after
I5-A completion.

## 7. Compatibility Bridge

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge or proxy is authorized.

## 8. Verification Boundary

Permitted verification is non-networking and non-mutating.

The I5-A implementation may run:

- Python compilation of the new test;
- the exact new characterization test;
- selected presentation regressions;
- persistence denial guards;
- collection-only verification.

It may not perform:

- real database access;
- database network execution;
- database mutation;
- production implementation.

## 9. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i4_status=COMPLETE`
- `i5_scope=I5A_THEN_I5B`
- `i5a_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i5a_test_write_authority=ISSUED`
- `i5a_exact_file_scope=ONE_NEW_TEST_FILE`
- `i5a_test_file=tests/test_persistence_presentation_seam_characterization.py`
- `i5a_production_write_authority=NONE`
- `i5b_scope_status=NOT_YET_DETERMINED`
- `i5b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I5A_EXACT_PRESENTATION_SEAM_CHARACTERIZATION`
