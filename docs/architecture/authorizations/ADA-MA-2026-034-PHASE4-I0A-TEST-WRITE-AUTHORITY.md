# ADA-MA-2026-034 Phase 4 I0-A Test-Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Authority: `ADA-MA-2026-034-PHASE4-I0A-TEST-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `2d10d1baca4baeb78bef60749ce70cdc2d277dbe`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i0-exact-scope-decision-established-v1.0`
- Authority type: `TEST_WRITE_ONLY`
- Production implementation authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I0-A implementation unit whose sole purpose
is to establish fail-closed real-persistence-resource denial for non-integration
pytest collection/execution and to self-test that denial boundary.

This authority is a test-safety foundation. It is not consumer migration.

## 3. Exact Authorized File Scope

Test-write authority is issued only for:

1. `tests/conftest.py`
2. `tests/test_persistence_real_resource_denial_guard.py`

No other file may be created, modified, renamed, or deleted under this authority.

Both files are expected to be new at the authorized baseline. If either already
exists when implementation begins, implementation must stop for scope reconciliation.

## 4. Authorized Implementation Behavior

Within the exact two-file scope, implementation may:

- install pytest-visible fail-closed persistence-resource denial;
- prevent non-integration tests from establishing real SQLAlchemy engine/database
  network capability;
- add self-tests proving prohibited capability attempts are rejected;
- preserve ordinary non-networking fake, sentinel, and monkeypatch-based tests;
- define explicit local test-only helpers inside the authorized files where needed.

The implementation must remain test-only.

## 5. Required Guard Properties

The I0-A guard must:

- be active as early as pytest permits before application test-target imports;
- fail closed for non-integration tests;
- deny real engine/database/network acquisition by capability rather than only by
  one URL literal;
- require no real database;
- require no DNS or application-network access;
- require no schema or data mutation;
- require no DDL execution;
- remain deterministic and locally reversible;
- avoid modifying production environment outside the test process.

## 6. Compatibility Requirements

I0-A must preserve existing test compatibility, including:

- Preference execution-only `_FakeConnection` tests;
- Preference caller-provided opaque `object()` connection delegation tests;
- Session Context caller-provided opaque `object()` connection delegation tests;
- patch/monkeypatch based non-networking unit tests;
- current test collection behavior except where a real persistence resource would
  otherwise be reached.

I0-A must not introduce a universal fake connection abstraction.

## 7. Explicitly Not Authorized

This ADA does not authorize:

- any production source-code write;
- any existing application-file change;
- borrowed-connection protocol changes;
- transaction-owner fake/factory implementation;
- logger transaction refactoring;
- engine ownership migration;
- consumer cutover;
- database connection or query execution;
- database mutation;
- DDL or migration execution;
- application-network execution;
- deployment mutation;
- Phase 5 verification execution.

## 8. Verification Authority for I0-A

This ADA authorizes only non-networking verification necessary to validate the exact
two-file I0-A unit.

Authorized verification is limited to:

- `python -m py_compile` or equivalent syntax compilation for the two authorized files;
- pytest execution of `tests/test_persistence_real_resource_denial_guard.py`;
- narrowly selected existing Preference and Session Context non-networking tests;
- pytest collection-only checks needed to prove the guard is active;
- static diff/scope checks.

No real database, network, migration, or integration execution is authorized.

## 9. Acceptance Conditions

I0-A may be considered implementation-complete only if:

1. exact file scope remains two files;
2. guard self-tests pass;
3. no real engine/database/network capability is reached;
4. selected Preference tests remain green;
5. selected Session Context tests remain green;
6. rollback is deletion/reversion of exactly the two authorized files;
7. worktree contains no unrelated change;
8. implementation commit contains exactly the two authorized files.

## 10. Rollback Unit

The rollback unit is exactly:

- `tests/conftest.py`
- `tests/test_persistence_real_resource_denial_guard.py`

Rollback must require no production, database, schema, or data action.

## 11. Establishment and Implementation Separation

Establishing this ADA does not itself modify the authorized test files.

After this ADA is established, a separately prepared implementation establishment
script may create the exact two test files, execute only the authorized non-networking
verification, commit exactly those two files, create one annotated tag, and atomically
push branch plus tag.

## 12. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i0a_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i0a_test_write_authority=ISSUED`
- `i0a_exact_file_scope=TWO_TEST_FILES`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`
- `next_action=IMPLEMENT_I0A_EXACT_TWO_FILE_TEST_SAFETY_FOUNDATION`

No further authority is implied.
