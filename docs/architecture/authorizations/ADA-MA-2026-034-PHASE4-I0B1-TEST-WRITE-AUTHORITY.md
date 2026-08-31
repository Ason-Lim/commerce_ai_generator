# ADA-MA-2026-034 Phase 4 I0-B1 Test-Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Authority: `ADA-MA-2026-034-PHASE4-I0B1-TEST-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `e2ec65133dd3aa4fe0d7c2c0e6556c2b10a8e904`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i0b-exact-scope-decision-established-v1.0`
- Authority type: `TEST_WRITE_ONLY`
- Production implementation authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I0-B1 implementation unit.

Its purpose is to establish test-only characterization for:

- borrowed execution-connection structural capability;
- exact borrowed-connection object identity forwarding;
- a bounded non-networking transaction-owner fake/factory;
- success, exceptional exit, rollback-equivalent outcome, release,
  cancellation, unknown-outcome, and prohibited post-release-use semantics.

This authority does not adopt a production protocol and does not migrate any
production persistence owner.

## 3. Exact Authorized File Scope

Test-write authority is issued only for exactly these two new files:

1. `tests/test_persistence_borrowed_connection_protocol.py`
2. `tests/test_persistence_transaction_owner_fake.py`

No other file may be created, modified, renamed, or deleted under this authority.

If either target already exists when implementation begins, implementation must
stop for explicit scope reconciliation.

## 4. Borrowed-Connection Characterization Authority

Within `tests/test_persistence_borrowed_connection_protocol.py`, implementation may:

- define test-local structural `Protocol` types;
- define test-local execute-only sentinels;
- characterize Preference store execute capability;
- characterize Session Context store execute capability;
- prove exact connection-object identity forwarding through Preference services;
- prove exact connection-object identity forwarding through Session Context services;
- prove borrowed consumers do not require lifecycle-owner capabilities such as
  `begin`, `commit`, `rollback`, `close`, or `dispose`;
- preserve opaque `object()` service-substitution behavior when downstream
  persistence is replaced;
- enumerate the nine existing `conn: Any` migration targets as evidence without
  modifying production annotations.

Test-local protocol definitions do not become production API.

## 5. Transaction-Owner Fake/Factory Authority

Within `tests/test_persistence_transaction_owner_fake.py`, implementation may define
and verify a bounded non-networking transaction-owner fake/factory that records:

- context entry;
- execute calls;
- normal context exit;
- exceptional context exit;
- rollback-equivalent failure outcome;
- release;
- prohibited post-release use;
- cancellation propagation;
- unknown-outcome representation.

The fake/factory must remain local to the test module.

It must not replace or widen the existing Preference store `_FakeConnection`.

## 6. Existing I0-A Safety Foundation

The established I0-A files are dependencies only:

- `tests/conftest.py`
- `tests/test_persistence_real_resource_denial_guard.py`

They are not writable under this authority.

The I0-A real-resource denial guard must remain active during I0-B1 verification.

## 7. Explicitly Not Authorized

This ADA does not authorize any change to:

- `app/services/preference/service.py`
- `app/services/preference/store.py`
- `app/services/session_context/service.py`
- `app/services/session_context/store.py`
- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- `tests/conftest.py`
- `tests/test_persistence_real_resource_denial_guard.py`
- any other existing test file;
- any other production file;
- any new module under `app/`.

It also does not authorize:

- production protocol adoption;
- replacement of the nine `Any` annotations;
- logger transaction-owner migration;
- consumer migration or cutover;
- real database access;
- application-network access;
- schema/data mutation;
- DDL or migration execution;
- deployment mutation;
- Phase 5 verification execution.

## 8. Authorized Verification

This ADA authorizes only non-networking verification needed for I0-B1:

- syntax compilation of the two authorized new files;
- pytest execution of the two new I0-B1 modules;
- existing Preference service/store tests;
- existing Session Context service tests;
- I0-A real-resource denial guard tests;
- pytest collection-only checks;
- static diff and exact-scope checks.

No real DB/network/integration execution is authorized.

## 9. Acceptance Conditions

I0-B1 may be considered implementation-complete only if:

1. exactly two new test files are changed;
2. all I0-B1 tests pass;
3. the I0-A guard tests remain green;
4. selected Preference tests remain green;
5. selected Session Context tests remain green;
6. no production file changes;
7. no real persistence/network capability is reached;
8. rollback remains deletion/reversion of exactly the two new files;
9. the implementation commit contains exactly the two authorized files.

## 10. Rollback Unit

The rollback unit is exactly:

- `tests/test_persistence_borrowed_connection_protocol.py`
- `tests/test_persistence_transaction_owner_fake.py`

Rollback requires no production, database, schema, or data action.

## 11. Establishment and Implementation Separation

Establishing this ADA does not itself create the two authorized test files.

After this ADA is established, a separately prepared implementation establishment
script may create exactly those files, execute only authorized non-networking
verification, commit exactly those files, create one annotated tag, and atomically
push branch plus tag.

## 12. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i0a_status=COMPLETE`
- `i0b_scope=I0B1_THEN_I0B2`
- `i0b1_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i0b1_test_write_authority=ISSUED`
- `i0b1_exact_file_scope=TWO_NEW_TEST_FILES`
- `i0b2_production_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`
- `next_action=IMPLEMENT_I0B1_EXACT_TWO_FILE_TEST_FOUNDATION`

No further authority is implied.
