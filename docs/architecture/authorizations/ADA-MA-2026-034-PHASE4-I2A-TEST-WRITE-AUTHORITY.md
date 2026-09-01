# ADA-MA-2026-034 Phase 4 I2-A Test Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I2-A — FastAPI Lifecycle Characterization`
- Authority: `ADA-MA-2026-034-PHASE4-I2A-TEST-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `5d9a392f92e025c41095dec762d393de7f836e35`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i2a-exact-scope-decision-established-v1.0`
- Authority type: `TEST_WRITE_ONLY`
- Production write authority: `NONE`
- Database/network execution authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I2-A characterization unit.

Its purpose is to establish FastAPI lifespan ownership semantics using a fake-backed,
test-local lifecycle binding before any production FastAPI composition wiring is
changed.

## 3. Exact Authorized File Scope

Write authority is issued only for exactly one new file:

`tests/test_persistence_fastapi_lifecycle_characterization.py`

No existing file may be modified, renamed, or deleted.

## 4. Production Freeze

The following production files remain read-only:

- `app/main.py`
- `app/db/lifecycle.py`
- `app/db/database.py`

All 23 direct legacy importers of `app.db.database.engine` remain read-only.

No compatibility bridge may be introduced.

## 5. Authorized Characterization Semantics

The new test file may establish, using a test-local FastAPI application and
fake/sentinel lifecycle authority:

- lifespan startup invokes lifecycle initialization exactly once;
- lifespan shutdown invokes lifecycle disposal exactly once;
- lifecycle state is observable through `app.state` during the active lifespan;
- application construction/import is distinct from lifecycle startup;
- explicit `app.router.lifespan_context(app)` execution requires no HTTP request;
- no real database or network resource is reached;
- no production composition file is changed;
- no legacy compatibility surface is changed;
- no consumer migration occurs.

## 6. Preferred Execution Method

The preferred characterization mechanism is:

`EXPLICIT_APP_ROUTER_LIFESPAN_CONTEXT`

`TestClient` is not required.

The characterization may use `asyncio.run(...)` or an equivalent local async test
driver, provided the execution remains fake-backed and non-networking.

## 7. App.Main Import Boundary

The new test may import `app.main` only under the existing I0 real-resource denial
guard and only to assert import-level composition facts.

It must not trigger a real engine connection, transaction, or network operation.

## 8. Read-Only Dependencies

The characterization may inspect or import, but not modify:

- `app/main.py`
- `app/db/lifecycle.py`
- `app/db/database.py`
- `tests/conftest.py`
- existing I1 lifecycle/disposal tests

## 9. Explicitly Not Authorized

This authority does not authorize:

- production writes;
- modification of `app/main.py`;
- modification of `app/db/lifecycle.py`;
- modification of `app/db/database.py`;
- FastAPI production lifespan wiring;
- compatibility bridge implementation;
- consumer migration;
- legacy engine replacement/rebinding/removal;
- real database/network execution;
- database/schema/data mutation;
- I2-B implementation;
- Phase 5 or Phase 6 authority.

## 10. Authorized Verification

This ADA authorizes only:

- syntax compilation of the new test file;
- execution of the new I2-A characterization tests;
- I1 lifecycle regression tests;
- I1 disposal regression tests;
- I0 real-resource denial guard regression;
- collection-only verification;
- static proof that `app/main.py` remains unchanged;
- static proof that `app/db/lifecycle.py` remains unchanged;
- static proof that `app/db/database.py` remains unchanged;
- static proof that direct legacy engine importer count remains `23`;
- exact one-file scope/diff checks.

## 11. Acceptance Conditions

I2-A may be considered implemented only if:

1. exactly one new test file changes;
2. all I2-A characterization tests pass;
3. startup initialize count is exactly one;
4. shutdown dispose count is exactly one;
5. `app.state` observation is demonstrated;
6. import/startup distinction is demonstrated;
7. no HTTP request is required;
8. all frozen production files remain unchanged;
9. no real DB/network access occurs;
10. no consumer migration occurs.

## 12. Rollback Unit

Rollback is exactly deletion/reversion of:

`tests/test_persistence_fastapi_lifecycle_characterization.py`

No production, database, schema, data, migration, compatibility, or deployment
rollback is required.

## 13. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_scope=I2A_THEN_I2B`
- `i2a_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i2a_test_write_authority=ISSUED`
- `i2a_exact_file_scope=ONE_NEW_TEST_FILE`
- `i2a_production_write_authority=NONE`
- `i2b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_I2_EVIDENCE`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=IMPLEMENT_I2A_EXACT_FASTAPI_LIFECYCLE_CHARACTERIZATION`

No further authority is implied.
