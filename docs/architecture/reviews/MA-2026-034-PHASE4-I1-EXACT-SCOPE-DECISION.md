# MA-2026-034 Phase 4 I1 Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1 — Canonical resolver and fake-backed lifecycle core`
- Decision: `MA-2026-034-PHASE4-I1-EXACT-SCOPE-DECISION`
- Governing routing commit: `12579c6bb452bd0be72c79a59f15ee55f3e47762`
- Governing routing tag: `ma-2026-034-phase4-post-i0-next-wave-routing-decision-established-v1.0`
- Decision effect: split I1 into independently reversible authority units
- Implementation authority: `NOT_ISSUED`

## 2. Read-Only Evidence Determination

The I1 exact-scope preflight established:

- `app/core/config.py` is the only current canonical configuration module;
- it currently resolves only `DATABASE_URL` and performs `load_dotenv()` at import;
- `DATABASE_URL`, `COMMERCE_DB_URL`, and `FRUIT_DB_URL` remain distributed across
  consumers with divergent fallback behavior;
- `app/db/database.py` still constructs a module-scope engine at import;
- `app/db.database` has many direct engine importers;
- additional independent module-scope engines remain in `app.main`, analytics,
  context, impression, market collector, and recommendation pipeline surfaces;
- no explicit application shutdown/disposal implementation was identified;
- no dedicated configuration resolver tests exist;
- no dedicated engine lifecycle/factory tests exist;
- the I0 real-resource denial guard and protocol characterization foundation are
  established;
- consumer migration remains explicitly outside I1.

## 3. Scope Split Decision

I1 SHALL NOT be implemented as one monolithic authority unit.

I1 is split into three sequential sub-units:

### I1-A — Canonical Configuration Resolver Foundation

Establish and verify canonical resolver semantics for:

`DATABASE_URL > COMMERCE_DB_URL > FRUIT_DB_URL`

including empty/whitespace handling, conflict failure, explicit local default, and
redacted error behavior.

I1-A must not change consumer modules.

### I1-B — Fake-Backed Canonical Engine Lifecycle Core

After I1-A completion, establish a canonical lifecycle composition primitive using
the verified resolver and fake/sentinel-backed engine construction tests.

I1-B must make engine ownership substitutable and observable without migrating
consumer cohorts.

### I1-C — Shutdown Disposal / Compatibility Access Boundary

After I1-B completion, determine and establish the minimal explicit disposal and,
only if required, state-gated compatibility access needed before I2 FastAPI
composition.

I1-C must not migrate the 23 direct `app.db.database.engine` importers or independent
consumer-owned engines.

## 4. Exact I1-A Candidate Scope

The first authority candidate is I1-A.

Its exact candidate scope is:

1. `app/core/config.py` — existing production file;
2. `tests/test_persistence_configuration_resolver.py` — new test file.

No other production or test file is in I1-A candidate scope.

## 5. I1-A Resolver Contract

The canonical resolver must implement the established precedence:

1. `DATABASE_URL`
2. `COMMERCE_DB_URL`
3. `FRUIT_DB_URL`

Whitespace-only or empty values are treated as absent.

If multiple non-empty aliases are present with different values, resolution must
fail closed rather than silently choose one.

Equivalent duplicate values may resolve successfully according to precedence.

If none is present, the canonical explicit local default is:

`postgresql+psycopg2://mom@localhost:5432/dashboard_db`

The resolver must not remove compatibility aliases.

## 6. I1-A Import and Runtime Boundary

I1-A may centralize configuration semantics inside `app.core.config`, but must not:

- create an engine;
- connect to a database;
- access application network resources;
- mutate consumer modules;
- migrate `app.main`;
- migrate logger modules;
- migrate collectors;
- migrate recommendation pipeline;
- modify `app/db/database.py`;
- modify `app/db/protocols.py`.

Importing `app.core.config` must remain non-networking.

## 7. I1-A Test Requirements

The new resolver test module must characterize at minimum:

- no aliases set;
- only `DATABASE_URL`;
- only `COMMERCE_DB_URL`;
- only `FRUIT_DB_URL`;
- empty/whitespace values treated as absent;
- duplicate equal aliases accepted;
- conflicting aliases rejected;
- precedence identity when equal aliases coexist;
- canonical local default;
- error output does not expose credential-bearing URL values.

Tests must manipulate only process-local environment state and must not access a
real database or network.

## 8. Deferred I1-B Scope

I1-B exact scope is deferred until I1-A is complete.

The later I1-B preflight must inspect and bound:

- `app/db/database.py`;
- a new lifecycle/factory module if needed;
- fake/sentinel engine factory tests;
- one-engine-per-process semantics;
- idempotent initialization;
- no import-time real engine construction;
- `pool_pre_ping=True`;
- canonical engine authority binding (`TB-19`).

No consumer migration is implied.

## 9. Deferred I1-C Scope

I1-C remains deferred until I1-B is complete.

It must resolve:

- explicit disposal (`TB-18`);
- idempotent disposal;
- disposal observation;
- state-gated compatibility accessor only if required by the next migration wave;
- readiness for I2 FastAPI composition.

## 10. Authority Separation

Establishing this decision authorizes only preparation of an exact I1-A
production/test write authority artifact.

It does not authorize modification of `app/core/config.py` or creation of the new
test file.

## 11. Authority State After Establishment

If this decision is successfully established:

- `phase_4_status=OPEN`
- `i0_foundation_status=COMPLETE`
- `i1_scope=I1A_THEN_I1B_THEN_I1C`
- `i1a_scope=EXACT_ONE_PRODUCTION_PLUS_ONE_TEST_FILE`
- `i1a_implementation_authority=NOT_ISSUED`
- `i1b_implementation_authority=NOT_ISSUED`
- `i1c_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I1A_RESOLVER_WRITE_AUTHORITY`

No further authority is implied.
