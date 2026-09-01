# MA-2026-034 Phase 4 I2-B Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I2-B — FastAPI Canonical Lifecycle Composition`
- Decision: `MA-2026-034-PHASE4-I2B-EXACT-SCOPE-DECISION`
- Governing predecessor commit: `c9bc2aa086a5f300f2e2c4f1c2b28c0cf1031c0e`
- Governing predecessor tag: `ma-2026-034-phase4-i2a-completion-review-established-v1.0`
- Implementation authority: `NOT_ISSUED`

## 2. Evidence Determination

The I2-B read-only preflight established:

- `app/main.py` is the FastAPI composition root;
- it currently owns an independent module-scope SQLAlchemy engine;
- that engine has exactly five `engine.connect()` use sites;
- the independent engine has no explicit disposal path;
- the canonical `EngineLifecycle` already supports lazy initialization and terminal disposal;
- I2-A proved FastAPI lifespan can initialize/dispose that lifecycle exactly once;
- `app.state` can expose lifecycle state;
- no application import cycle blocks direct use of `EngineLifecycle` from `app/main.py`;
- `app/db/database.py` remains the frozen legacy surface;
- the 23 legacy direct engine importers remain outside this wave;
- no compatibility bridge prerequisite has been proven.

## 3. Dual-Authority Determination

Leaving the existing `app.main` module-scope engine in place while adding a second
canonical lifecycle-owned engine would create two persistence authorities inside
the same application composition root.

That is not an acceptable final I2-B state.

Therefore I2-B must eliminate the independent `app.main` engine authority and
redirect the five local connection-acquisition sites to the engine owned by the
canonical application lifecycle.

This is local composition-root migration, not migration of the 23 legacy consumers.

## 4. Exact I2-B Scope

I2-B shall use exactly:

1. existing production file:
   `app/main.py`
2. new test file:
   `tests/test_persistence_fastapi_lifecycle_composition.py`

No third file is authorized.

## 5. Production Composition Contract

`app/main.py` may be changed only to establish the canonical application-level
persistence lifecycle:

- import `EngineLifecycle`;
- define one module-scope `EngineLifecycle` authority without constructing an engine;
- define a FastAPI lifespan context;
- publish the lifecycle through `app.state.engine_lifecycle`;
- initialize exactly once on lifespan startup;
- dispose exactly once on lifespan shutdown;
- construct `FastAPI(lifespan=...)`;
- remove the independent module-scope `create_engine(DB_URL)` authority;
- remove no-longer-needed local DB URL engine-construction configuration;
- redirect exactly the five current `engine.connect()` sites to the
  lifecycle-owned initialized engine.

## 6. Lifecycle Access Rule

The five local connection sites must resolve the canonical engine through a bounded
application-composition helper or equivalent local fail-closed mechanism in
`app/main.py`.

Access before startup or after successful shutdown must fail closed rather than
silently construct or fall back to another engine.

`app/db/lifecycle.py` itself remains unchanged.

## 7. App.State Contract

During active FastAPI lifespan:

`app.state.engine_lifecycle`

shall reference the same canonical lifecycle authority used by the five local
connection sites.

This establishes application-level observability without creating a global
compatibility bridge.

## 8. Compatibility Preservation

The following remain frozen:

- `app/db/lifecycle.py`;
- `app/db/database.py`;
- all 23 direct importers of `app.db.database.engine`.

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge is required for I2-B.

## 9. No Separate Composition Module

Current evidence does not justify `app/db/composition.py`.

`app/main.py` is already the application composition root and can own the bounded
FastAPI lifecycle integration directly.

Adding a separate production module would expand scope without demonstrated need.

## 10. Required Test Contract

The new I2-B test file shall verify, without real DB/network access:

- importing `app.main` does not construct the canonical engine;
- startup initializes the canonical lifecycle exactly once;
- shutdown disposes exactly once;
- `app.state.engine_lifecycle` is the canonical lifecycle identity;
- the independent `app.main` `create_engine(DB_URL)` authority is absent;
- exactly five local connection sites use canonical lifecycle engine access;
- access before startup fails closed;
- access after shutdown fails closed;
- no `app/db/lifecycle.py` mutation occurred;
- no `app/db/database.py` mutation occurred;
- direct legacy engine importer count remains 23;
- no compatibility bridge is introduced;
- no consumer migration occurs.

## 11. Authorized Verification Boundary

A later write authority may authorize only:

- syntax compilation of the two authorized files;
- I2-B fake-backed/non-networking composition tests;
- I2-A characterization regression;
- I1 lifecycle/disposal regression;
- I0 real-resource denial guard regression;
- collection-only checks;
- static proof of exact five-site migration;
- static proof of removal of independent `app.main` engine construction;
- static proof that frozen production surfaces remain unchanged;
- exact two-file scope/diff checks.

No real database/network execution is authorized.

## 12. Explicitly Not Authorized

This decision does not authorize:

- writes to any file other than the two exact I2-B targets;
- modification of `app/db/lifecycle.py`;
- modification of `app/db/database.py`;
- migration of the 23 legacy direct engine importers;
- compatibility bridge implementation;
- database/schema/data mutation;
- live database/network execution;
- broader consumer migration;
- I2 completion;
- Phase 4 completion;
- Phase 5 or Phase 6 authority.

## 13. Authority State After Establishment

If successfully established:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2a_status=COMPLETE`
- `i2b_scope=EXACT_ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i2b_production_file=app/main.py`
- `i2b_test_file=tests/test_persistence_fastapi_lifecycle_composition.py`
- `i2b_local_engine_connect_sites=5`
- `i2b_dual_authority_policy=ELIMINATE_APP_MAIN_INDEPENDENT_ENGINE`
- `i2b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I2B_COMPOSITION_WRITE_AUTHORITY`

No further authority is implied.
