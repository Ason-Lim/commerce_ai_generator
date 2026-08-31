# MA-2026-034 Phase 4 I0-B Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Decision: `MA-2026-034-PHASE4-I0B-EXACT-SCOPE-DECISION`
- Governing I0-A completion commit: `e9d64137cba8e65253be9f2baf73920419117474`
- Governing I0-A completion tag: `ma-2026-034-phase4-i0a-completion-review-established-v1.0`
- Decision effect: bound I0-B before implementation authority
- Implementation authority: `NOT_ISSUED`

## 2. Read-Only Evidence Determination

The I0-B scope preflight established:

- exactly nine production `conn: Any` parameters;
- five are Preference service/store surfaces;
- four are Session Context service/store surfaces;
- Preference and Session Context services preserve borrowed connection identity;
- Preference store has one execute-only `_FakeConnection`;
- four service tests intentionally use opaque `object()` substitutes;
- no transaction-capable persistence-owner fake/factory exists;
- no rollback/cancellation/unknown-outcome persistence characterization tests were found;
- analytics, context, and impression loggers own `engine.begin()` transaction scopes;
- current logger-specific persistence coverage is insufficient for transaction-owner
  characterization;
- no existing canonical persistence protocol module was identified.

## 3. Scope Separation Decision

I0-B SHALL be split into two sequential sub-units:

### I0-B1 — Test-Only Protocol and Transaction-Owner Characterization Foundation

I0-B1 is the next implementation authority candidate.

It establishes test-only structural protocol characterization and a bounded
non-networking transaction-owner fake/factory without modifying production
signatures or logger implementations.

### I0-B2 — Production Borrowed-Connection Protocol Adoption

I0-B2 is deferred.

It may later replace the nine `Any` annotations with a canonical minimal structural
protocol only after I0-B1 proves compatibility.

I0-B2 requires separate production-write authority.

## 4. Exact I0-B1 Candidate File Scope

The next authority proposal SHALL be limited to exactly two new test files:

1. `tests/test_persistence_borrowed_connection_protocol.py`
2. `tests/test_persistence_transaction_owner_fake.py`

No production file is in I0-B1 scope.

`tests/conftest.py` from I0-A is an established dependency and SHALL NOT be modified
under I0-B1.

## 5. Borrowed-Connection Characterization Requirements

`tests/test_persistence_borrowed_connection_protocol.py` shall characterize:

- execute-only capability sufficient for Preference store calls;
- execute-only capability sufficient for Session Context store calls;
- exact object identity forwarding by Preference service functions;
- exact object identity forwarding by Session Context service functions;
- absence of consumer lifecycle requirements such as `begin`, `commit`, `rollback`,
  `close`, or `dispose`;
- continued validity of opaque service substitutes when downstream persistence is
  replaced;
- all nine current `conn: Any` surfaces as migration targets without changing them.

The test module may define local `Protocol` types or sentinels solely for
characterization. Such local definitions do not become production API.

## 6. Transaction-Owner Fake/Factory Requirements

`tests/test_persistence_transaction_owner_fake.py` shall define and test a bounded
non-networking owner fake/factory capable of recording:

- context entry;
- execute calls;
- normal/successful context exit;
- exceptional context exit;
- rollback-equivalent failure outcome representation;
- release;
- prohibited post-release use;
- cancellation propagation;
- unknown-outcome representation.

The fake/factory shall remain test-local and shall not widen the existing Preference
store `_FakeConnection`.

## 7. Logger Boundary Characterization

I0-B1 may characterize owner semantics against test-local owner behavior, but it
shall not monkeypatch or modify production logger source to introduce new ownership
composition.

Direct production logger migration is deferred to a later authorized wave.

## 8. Explicitly Deferred Production Scope

The following production files are not authorized by I0-B1:

- `app/services/preference/service.py`
- `app/services/preference/store.py`
- `app/services/session_context/service.py`
- `app/services/session_context/store.py`
- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- any new module under `app/`

No production protocol module shall be created under I0-B1.

## 9. Verification Boundary

A later I0-B1 test-write authority may authorize only non-networking verification:

- syntax compilation of the two new test files;
- pytest for the two new I0-B1 modules;
- existing Preference service/store tests;
- existing Session Context service tests;
- I0-A guard tests;
- collection-only checks.

No DB/network/integration execution is required.

## 10. Rollback Unit

I0-B1 rollback is exactly deletion/reversion of:

- `tests/test_persistence_borrowed_connection_protocol.py`
- `tests/test_persistence_transaction_owner_fake.py`

Rollback requires no production, database, schema, or data action.

## 11. Authority Result

Establishment of this decision does not issue test-write or production-write
authority.

After successful establishment:

- `phase_4_status=OPEN`
- `i0a_status=COMPLETE`
- `i0b_scope=I0B1_THEN_I0B2`
- `i0b1_scope=EXACT_TWO_NEW_TEST_FILES`
- `i0b1_implementation_authority=NOT_ISSUED`
- `i0b2_production_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I0B1_TEST_WRITE_AUTHORITY`

No further authority is implied.
