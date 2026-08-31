# MA-2026-034 Phase 4 I1-B2 Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1-B2 — Canonical Lifecycle Core Production Module`
- Decision: `MA-2026-034-PHASE4-I1B2-EXACT-SCOPE-DECISION`
- Governing I1-B1 completion commit: `8d37adc27c68c6121af3e0640bc594147e3ed084`
- Governing I1-B1 completion tag: `ma-2026-034-phase4-i1b1-completion-review-established-v1.0`
- Implementation authority: `NOT_ISSUED`

## 2. Read-Only Evidence Determination

The I1-B2 exact-scope preflight established:

- `app/db/database.py` remains a four-line legacy module with module-scope
  `create_engine(DATABASE_URL, pool_pre_ping=True)`;
- its SHA256 is
  `8bbbdebd98553bba2045b647a33d5b159a14eeb07c641cfafb8c87d51e465f77`;
- 23 production modules directly import `app.db.database.engine`;
- six additional production surfaces independently construct engines;
- no production lifecycle module currently exists;
- no production shutdown/disposal surface exists;
- I1-B1 has established the lifecycle characterization contract;
- `app/core/config.py` provides the canonical I1-A resolver;
- no import-cycle evidence prevents a new leaf lifecycle module.

## 3. Selected Production Shape

I1-B2 selects:

`shape_A = add app/db/lifecycle.py only; leave app/db/database.py unchanged`

The exact production candidate scope is therefore one new production file:

`app/db/lifecycle.py`

No existing production file is writable in I1-B2.

## 4. Why app/db/database.py Must Remain Unchanged

Changing `app/db/database.py` in I1-B2 would alter the compatibility surface used by
23 direct production importers.

That would mix lifecycle-core establishment with compatibility bridging or consumer
migration.

Therefore `app/db/database.py` must remain byte-for-byte at the established SHA256
through I1-B2.

Its legacy module-scope engine remains temporarily in place until the separately
governed I1-C compatibility/disposal boundary.

## 5. Canonical Lifecycle Core Contract

`app/db/lifecycle.py` may define a minimal lifecycle authority that:

- accepts or defaults a canonical database URL resolver;
- accepts or defaults an engine factory;
- performs zero engine construction at module import;
- constructs an engine only on explicit initialization;
- passes `pool_pre_ping=True`;
- publishes the engine only after successful factory return;
- returns the same engine identity on repeated initialization;
- exposes lifecycle state sufficiently for bounded observation;
- performs no connection acquisition during initialization;
- performs no transaction acquisition during initialization;
- performs no implicit disposal during initialization.

## 6. Production Factory Default

The lifecycle module may use SQLAlchemy `create_engine` as its default factory.

This does not authorize calling that factory during module import or during
non-networking tests.

Tests must inject a fake/sentinel factory.

## 7. Resolver Default

The lifecycle module may use the established I1-A canonical resolver as its default
resolver.

Resolution must occur only when initialization is explicitly invoked.

No new configuration precedence semantics are authorized in I1-B2.

## 8. Disposal Boundary

Disposal remains deferred to I1-C.

I1-B2 must not implement:

- shutdown hooks;
- `dispose_engine`;
- application lifespan integration;
- `atexit`;
- automatic cleanup;
- compatibility-surface replacement.

The I1-B2 core may retain state needed for later disposal design, but may not perform
disposal.

## 9. Test Strategy Decision

The existing I1-B1 characterization file remains immutable evidence.

I1-B2 shall use one new production-facing test file:

`tests/test_persistence_engine_lifecycle.py`

The exact later implementation candidate scope is therefore:

1. `app/db/lifecycle.py` — new production file;
2. `tests/test_persistence_engine_lifecycle.py` — new test file.

No existing file may be modified.

## 10. Production-Facing Test Requirements

The new test file must verify the real lifecycle module using injected fake/sentinel
dependencies for:

- import purity / zero construction;
- exactly one construction;
- idempotent initialization;
- stable identity;
- canonical resolver propagation;
- `pool_pre_ping=True`;
- failure-before-publication;
- no connect/begin/dispose during initialization;
- no consumer binding;
- preservation of the legacy `app/db/database.py` SHA256;
- preservation of 23 direct legacy engine importers.

## 11. Explicitly Out of Scope

I1-B2 does not authorize changes to:

- `app/db/database.py`;
- `app/db/protocols.py`;
- `app/core/config.py`;
- `tests/test_persistence_engine_lifecycle_contract.py`;
- any consumer module;
- any other existing test file.

It also does not authorize:

- disposal implementation;
- legacy engine replacement;
- state-gated compatibility access;
- consumer migration;
- real database execution;
- application-network execution;
- database/schema/data mutation;
- DDL/migration execution;
- Phase 5 verification.

## 12. Verification Boundary

A later I1-B2 write authority may authorize only:

- syntax compilation of the two new files;
- production-facing lifecycle tests;
- I1-B1 characterization regression;
- I1-A resolver regression;
- I0 real-resource denial guard regression;
- static proof that `app/db/database.py` remains at the established SHA256;
- static proof that the 23 direct importers remain unchanged in count;
- exact two-file scope/diff checks.

No real database/network execution is authorized.

## 13. Rollback Unit

Rollback is exactly deletion/reversion of:

- `app/db/lifecycle.py`;
- `tests/test_persistence_engine_lifecycle.py`.

Rollback requires no change to the legacy engine surface, database, schema, data,
migration, or deployment.

## 14. Authority State After Establishment

If this decision is successfully established:

- `phase_4_status=OPEN`
- `i1a_status=COMPLETE`
- `i1b1_status=COMPLETE`
- `i1b2_scope=EXACT_ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i1b2_database_py_policy=BYTE_FOR_BYTE_UNCHANGED`
- `i1b2_production_authority=NOT_ISSUED`
- `i1b2_test_authority=NOT_ISSUED`
- `i1c_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I1B2_LIFECYCLE_CORE_WRITE_AUTHORITY`

No further authority is implied.
