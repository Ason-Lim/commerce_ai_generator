# MA-2026-034 Phase 4 I1-B Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1-B — Fake-Backed Canonical Engine Lifecycle Core`
- Decision: `MA-2026-034-PHASE4-I1B-EXACT-SCOPE-DECISION`
- Governing I1-A completion commit: `94da061f76258e3b5842d6c6d550c1295f9f4adf`
- Governing I1-A completion tag: `ma-2026-034-phase4-i1a-completion-review-established-v1.0`
- Decision effect: split I1-B before any lifecycle production write
- Implementation authority: `NOT_ISSUED`

## 2. Read-Only Evidence Determination

The I1-B exact-scope preflight established:

- `app/db/database.py` currently consists of module-scope engine construction:
  `engine = create_engine(DATABASE_URL, pool_pre_ping=True)`;
- `app/db.database.engine` has 23 direct production importers;
- those consumers perform `engine.connect()` and `engine.begin()` directly;
- six additional production modules independently construct module-scope engines;
- no dedicated engine lifecycle/factory tests currently exist;
- no explicit application shutdown/disposal implementation exists;
- the I0 real-resource denial guard is established;
- the I0 transaction-owner fake/factory is established;
- I1-A canonical configuration resolution is complete;
- consumer migration is explicitly not authorized in I1.

## 3. Compatibility Consequence

Removing or replacing the module-scope `engine` binding in `app/db/database.py` during
the first I1-B write would implicitly affect 23 direct production consumers.

That would cross the established boundary from lifecycle foundation into consumer
migration.

Therefore the current `app/db/database.py` compatibility surface must remain
unchanged until a separately governed compatibility-access/disposal step is ready.

## 4. I1-B Split Decision

I1-B SHALL be split into two sequential sub-units:

### I1-B1 — Test-Only Engine Lifecycle Characterization Foundation

I1-B1 is the next implementation authority candidate.

It shall establish non-networking, fake-backed characterization for:

- zero real engine creation during lifecycle module import;
- one engine construction per lifecycle instance/process authority;
- idempotent initialization;
- `pool_pre_ping=True`;
- canonical I1-A resolver input propagation;
- stable engine identity after initialization;
- initialization failure leaves the lifecycle uninitialized;
- lifecycle ownership is substitutable and observable;
- no consumer migration;
- no disposal implementation yet.

I1-B1 shall not modify production code.

### I1-B2 — Canonical Lifecycle Core Production Module

After I1-B1 completion, I1-B2 may introduce the minimal canonical lifecycle module
needed to satisfy the characterized contract.

I1-B2 shall be separately scoped and separately authorized.

It must not remove or replace the legacy `app.db.database.engine` compatibility
surface unless explicitly authorized by a later bridge decision.

## 5. Exact I1-B1 Candidate File Scope

The next authority candidate is exactly one new test file:

`tests/test_persistence_engine_lifecycle_contract.py`

No production file is writable under I1-B1.

Existing files used as read-only dependencies include:

- `app/core/config.py`;
- `app/db/database.py`;
- `app/db/protocols.py`;
- `tests/conftest.py`;
- `tests/test_persistence_transaction_owner_fake.py`.

## 6. I1-B1 Characterization Requirements

The test-only lifecycle contract shall define a bounded fake/sentinel engine factory
and lifecycle model sufficient to characterize:

1. import purity;
2. construction count;
3. canonical URL propagation;
4. `pool_pre_ping=True`;
5. idempotent initialization;
6. stable engine identity;
7. failure-before-publication;
8. no implicit disposal;
9. no connection or transaction acquisition during initialization;
10. no consumer binding.

The test-only lifecycle model is characterization evidence only and does not become
production API.

## 7. I1-B2 Deferred Production Questions

The later I1-B2 exact-scope preflight must determine whether the production lifecycle
core belongs in:

- `app/db/lifecycle.py`;
- `app/db/engine_factory.py`;
- or another minimal leaf module.

It must also determine whether `app/db/database.py` is:

- unchanged as a legacy compatibility surface;
- read-only dependent on the new lifecycle core;
- or deferred entirely until I1-C.

That decision must account for all 23 direct importers.

## 8. I1-C Boundary Preservation

I1-C remains responsible for the separately governed compatibility/disposal
boundary, including where applicable:

- explicit disposal (`TB-18`);
- idempotent disposal;
- state-gated compatibility access;
- migration-safe handling of the legacy `app.db.database.engine` surface;
- readiness for I2 FastAPI composition.

I1-B1 does not authorize any of these.

## 9. Explicitly Not Authorized

This decision does not authorize changes to:

- `app/db/database.py`;
- `app/db/protocols.py`;
- `app/core/config.py`;
- any consumer module;
- any existing test file.

It also does not authorize:

- real engine construction;
- database connection execution;
- application-network execution;
- database/schema/data mutation;
- DDL/migration execution;
- shutdown disposal;
- consumer migration;
- Phase 5 verification.

## 10. Verification Boundary

A later I1-B1 test-write authority may authorize only:

- syntax compilation of the new test file;
- pytest execution of the new lifecycle characterization module;
- I0 real-resource denial guard regression;
- I1-A resolver regression;
- static scope checks;
- collection-only checks.

No real database or network execution is required.

## 11. Rollback Unit

I1-B1 rollback is exactly deletion/reversion of:

`tests/test_persistence_engine_lifecycle_contract.py`

Rollback requires no production, database, schema, data, migration, or deployment
action.

## 12. Authority State After Establishment

If this decision is successfully established:

- `phase_4_status=OPEN`
- `i1a_status=COMPLETE`
- `i1b_scope=I1B1_THEN_I1B2`
- `i1b1_scope=EXACT_ONE_NEW_TEST_FILE`
- `i1b1_implementation_authority=NOT_ISSUED`
- `i1b2_production_authority=NOT_ISSUED`
- `i1c_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I1B1_TEST_WRITE_AUTHORITY`

No further authority is implied.
