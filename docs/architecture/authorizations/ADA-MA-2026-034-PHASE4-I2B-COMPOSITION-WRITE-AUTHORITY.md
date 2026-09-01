# ADA-MA-2026-034 Phase 4 I2-B Composition Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I2-B — FastAPI Canonical Lifecycle Composition`
- Authority: `ADA-MA-2026-034-PHASE4-I2B-COMPOSITION-WRITE-AUTHORITY`
- Governing exact-scope decision commit:
  `a4ec69e63827d807c21069290f736774d562dbe2`
- Governing exact-scope decision tag:
  `ma-2026-034-phase4-i2b-exact-scope-decision-established-v1.0`
- Authority type: `PRODUCTION_AND_TEST_WRITE_BOUNDED`
- Database/network execution authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I2-B implementation unit.

Its purpose is to establish canonical FastAPI lifecycle ownership in the application
composition root without expanding migration to the legacy persistence surface.

## 3. Exact Authorized File Scope

Write authority is issued only for exactly these two files:

1. `app/main.py`
2. `tests/test_persistence_fastapi_lifecycle_composition.py`

No other file may be created, modified, renamed, or deleted under this authority.

## 4. Authorized Production Changes

`app/main.py` may be changed only to:

- import `EngineLifecycle`;
- establish one module-scope canonical `EngineLifecycle` authority;
- avoid engine construction at module import;
- define FastAPI lifespan ownership;
- publish the lifecycle through `app.state.engine_lifecycle`;
- initialize exactly once on startup;
- dispose exactly once on shutdown;
- construct the FastAPI application with the lifespan;
- remove the independent module-scope `create_engine(DB_URL)` authority;
- remove no-longer-needed local engine-construction configuration;
- redirect exactly the five current local `engine.connect()` sites to the
  lifecycle-owned engine;
- fail closed if canonical engine access occurs before startup or after shutdown.

## 5. Dual-Authority Prohibition

The final I2-B production state must not retain both:

- the independent `app.main` module-scope SQLAlchemy engine; and
- the canonical lifecycle-owned engine.

The independent `app.main` engine authority must be eliminated.

## 6. Canonical Application Exposure

During active lifespan:

`app.state.engine_lifecycle`

must reference the same `EngineLifecycle` identity used by the five local connection
sites.

No global compatibility bridge is authorized.

## 7. Frozen Production Surfaces

The following remain read-only and byte-for-byte unchanged:

- `app/db/lifecycle.py`
- `app/db/database.py`

All 23 direct production importers of `app.db.database.engine` remain unchanged.

No separate `app/db/composition.py` may be introduced.

## 8. I1-C2 Compatibility Bridge

The compatibility bridge remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

This authority does not authorize:

- a compatibility accessor;
- rebinding of `app.db.database.engine`;
- migration of legacy importers;
- fallback to the legacy engine from `app.main`.

## 9. Authorized Test Coverage

The new composition test may verify, using fake/sentinel engine construction and the
existing real-resource denial guard:

- importing `app.main` does not construct the canonical engine;
- startup initializes exactly once;
- shutdown disposes exactly once;
- `app.state.engine_lifecycle` is the canonical lifecycle identity;
- independent `app.main` `create_engine(DB_URL)` authority is absent;
- exactly five local connection-acquisition sites use canonical lifecycle access;
- access before startup fails closed;
- access after shutdown fails closed;
- no real database/network access occurs;
- `app/db/lifecycle.py` remains unchanged;
- `app/db/database.py` remains unchanged;
- direct legacy importer count remains 23;
- no compatibility bridge exists;
- no consumer migration occurs.

## 10. Authorized Verification

This ADA authorizes only:

- syntax compilation of the two authorized files;
- I2-B fake-backed/non-networking composition tests;
- I2-A characterization regression;
- I1 lifecycle/disposal regressions;
- I0 real-resource denial guard regression;
- collection-only checks;
- static proof of removal of independent `app.main` engine construction;
- static proof that exactly five local connection sites were migrated;
- static proof of frozen production surfaces;
- exact two-file scope/diff checks.

No live database/network execution is authorized.

## 11. Explicitly Not Authorized

This authority does not authorize:

- any third-file write;
- modification of `app/db/lifecycle.py`;
- modification of `app/db/database.py`;
- compatibility bridge implementation;
- legacy importer migration;
- broader consumer migration;
- database/schema/data mutation;
- live database/network execution;
- I2 completion artifact;
- Phase 4 completion;
- Phase 5 or Phase 6 authority.

## 12. Acceptance Conditions

I2-B may be considered implemented only if:

1. exactly the two authorized files change;
2. production import no longer constructs the canonical engine;
3. one canonical lifecycle owns startup/shutdown;
4. independent `app.main` engine authority is removed;
5. exactly five local connection sites use canonical lifecycle access;
6. pre-start and post-shutdown access fail closed;
7. `app.state` exposes canonical lifecycle identity during active lifespan;
8. I2-B tests pass;
9. I2-A and I1/I0 regressions remain green;
10. frozen production surfaces remain unchanged;
11. legacy importer count remains 23;
12. no real DB/network access or consumer migration occurs.

## 13. Authority State After Establishment

If successfully established:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2a_status=COMPLETE`
- `i2b_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i2b_production_write_authority=ISSUED`
- `i2b_test_write_authority=ISSUED`
- `i2b_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i2b_dual_authority_policy=ELIMINATE_APP_MAIN_INDEPENDENT_ENGINE`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=IMPLEMENT_I2B_EXACT_FASTAPI_CANONICAL_LIFECYCLE_COMPOSITION`

No further authority is implied.
