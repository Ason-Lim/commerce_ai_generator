# MA-2026-034 Phase 4 I2-A Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I2-A — FastAPI Lifecycle Characterization`
- Decision: `MA-2026-034-PHASE4-I2A-EXACT-SCOPE-DECISION`
- Governing post-I1 routing commit: `c045d74eb308ac010957ab7a8c07f3a4fb7e864a`
- Governing routing tag: `ma-2026-034-phase4-post-i1-next-wave-routing-decision-established-v1.0`
- Implementation authority: `NOT_ISSUED`

## 2. Read-Only Evidence Determination

The I2-A recovery preflight established:

- repository baseline and remote identity are synchronized;
- earlier failed preflight left no partial mutation;
- repository virtualenv Python is available;
- FastAPI version is `0.136.1`;
- `FastAPI` constructor supports `lifespan`;
- Starlette version is `1.0.0`;
- HTTPX version is `0.28.1`;
- `app.main` can be imported under a denied/inert SQLAlchemy engine factory;
- `app.main.app` is a FastAPI application;
- `app.main` currently has application state support;
- an explicit `app.router.lifespan_context(app)` probe executes startup and shutdown deterministically;
- no existing FastAPI lifecycle TestClient precedent exists;
- no production file must change to characterize the lifecycle boundary.

## 3. Selected I2-A Scope

I2-A shall be implemented as:

`EXACT_ONE_NEW_TEST_FILE`

The only candidate implementation file is:

`tests/test_persistence_fastapi_lifecycle_characterization.py`

No production file is writable in I2-A.

## 4. Production Files Frozen During I2-A

The following must remain unchanged throughout I2-A:

- `app/main.py`;
- `app/db/lifecycle.py`;
- `app/db/database.py`;
- all 23 direct production importers of `app.db.database.engine`.

No compatibility bridge may be introduced.

## 5. Characterization Method

I2-A shall characterize FastAPI lifespan semantics without production wiring.

The preferred mechanism is:

`EXPLICIT_APP_ROUTER_LIFESPAN_CONTEXT`

A test-local FastAPI application may bind a fake `EngineLifecycle` to a test-local
lifespan function.

No HTTP request is required.

`TestClient` is not required.

## 6. Required Characterization Claims

The single new test file shall establish:

1. a fake lifecycle can be bound to FastAPI lifespan;
2. startup invokes lifecycle initialization exactly once;
3. shutdown invokes lifecycle disposal exactly once;
4. lifecycle state can be observed through `app.state` during lifespan;
5. application import is distinct from lifecycle startup;
6. explicit lifespan execution can occur without HTTP routing;
7. no real database or network resource is reached;
8. `app/main.py` remains unchanged;
9. legacy compatibility surfaces remain unchanged;
10. no consumer migration occurs.

## 7. App.Main Import Characterization

I2-A may import `app.main` only under the existing non-networking pytest safety
foundation.

The characterization may assert import-level facts, but must not add production
lifespan wiring.

## 8. Compatibility Bridge Decision

The I1-C2 compatibility bridge remains:

`DEFERRED_UNTIL_I2_EVIDENCE`

I2-A current evidence does not require:

- a global engine accessor;
- rebinding `app.db.database.engine`;
- modifying `app/db/database.py`;
- migrating any legacy importer.

## 9. Explicitly Not Authorized

I2-A does not authorize:

- production writes;
- modification of `app/main.py`;
- modification of `app/db/lifecycle.py`;
- modification of `app/db/database.py`;
- FastAPI production lifespan wiring;
- application startup/shutdown integration;
- compatibility bridge implementation;
- consumer migration;
- real database/network execution;
- database/schema/data mutation;
- I2-B implementation;
- Phase 5 or Phase 6 authority.

## 10. Verification Boundary

A later I2-A test-write authority may authorize only:

- syntax compilation of the new test file;
- execution of the new characterization tests;
- I1 lifecycle/disposal regression tests;
- I0 real-resource denial guard regression;
- collection-only checks;
- static proof that `app/main.py` remains unchanged;
- static proof that `app/db/lifecycle.py` remains unchanged;
- static proof that `app/db/database.py` remains unchanged;
- static proof that direct legacy engine importer count remains `23`;
- exact one-file scope/diff checks.

No real database/network execution is authorized.

## 11. Completion Condition

I2-A may be considered complete only if the single new characterization file proves
the required lifespan behavior without any production mutation.

## 12. Authority State After Establishment

If this decision is successfully established:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_scope=I2A_THEN_I2B`
- `i2a_scope=EXACT_ONE_NEW_TEST_FILE`
- `i2a_candidate_file=tests/test_persistence_fastapi_lifecycle_characterization.py`
- `i2a_production_write_required=NO`
- `i2a_implementation_authority=NOT_ISSUED`
- `i2b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_I2_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I2A_TEST_WRITE_AUTHORITY`

No further authority is implied.
