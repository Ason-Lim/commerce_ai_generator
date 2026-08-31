# ADA-MA-2026-034 Phase 4 I1-B1 Test-Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1-B1 — Test-Only Engine Lifecycle Characterization Foundation`
- Authority: `ADA-MA-2026-034-PHASE4-I1B1-TEST-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `43fc25f17cb2b9b69b46b1bb309373c3ecf98ca6`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i1b-exact-scope-decision-established-v1.0`
- Authority type: `TEST_WRITE_ONLY`
- Production implementation authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded test-only implementation unit for the
canonical engine lifecycle contract.

Its purpose is to characterize lifecycle behavior with fake/sentinel resources
before any production lifecycle module is introduced.

## 3. Exact Authorized File Scope

Test-write authority is issued only for exactly one new file:

`tests/test_persistence_engine_lifecycle_contract.py`

No existing file may be modified.

No production file may be created, modified, renamed, or deleted under this
authority.

## 4. Authorized Lifecycle Characterization

The new test module may define test-local fake/sentinel engine factory and lifecycle
models sufficient to characterize:

- import purity;
- zero real engine construction during lifecycle module import/definition;
- exactly one engine construction per initialized lifecycle authority;
- idempotent initialization;
- canonical I1-A resolver URL propagation;
- `pool_pre_ping=True`;
- stable engine identity after initialization;
- initialization failure before publication;
- lifecycle ownership substitutability and observability;
- no connection acquisition during initialization;
- no transaction acquisition during initialization;
- no implicit disposal during initialization;
- no consumer binding.

The test-local lifecycle model is characterization evidence only and does not become
production API.

## 5. Existing Read-Only Dependencies

The following established files may be imported or inspected by tests but are not
writable under this authority:

- `app/core/config.py`;
- `app/db/database.py`;
- `app/db/protocols.py`;
- `tests/conftest.py`;
- `tests/test_persistence_real_resource_denial_guard.py`;
- `tests/test_persistence_configuration_resolver.py`;
- `tests/test_persistence_transaction_owner_fake.py`.

## 6. Explicitly Not Authorized

This ADA does not authorize changes to:

- `app/db/database.py`;
- `app/db/protocols.py`;
- `app/core/config.py`;
- any consumer module;
- any existing test file;
- any other file.

It also does not authorize:

- production lifecycle module creation;
- real engine construction;
- engine replacement;
- legacy `app.db.database.engine` compatibility changes;
- shutdown disposal;
- state-gated engine access;
- consumer migration;
- database connection execution;
- application-network execution;
- database/schema/data mutation;
- DDL or migration execution;
- Phase 5 verification.

## 7. Authorized Non-Networking Verification

This ADA authorizes only:

- syntax compilation of the new test file;
- pytest execution of the new lifecycle characterization module;
- I0 real-resource denial guard regression;
- I1-A resolver regression;
- collection-only checks;
- static exact-scope checks.

No real database, application-network, integration, migration, or DDL execution is
authorized.

## 8. Acceptance Conditions

I1-B1 may be considered implementation-complete only if:

1. exactly one new test file is changed;
2. lifecycle characterization tests pass;
3. I0 real-resource denial guard remains green;
4. I1-A resolver tests remain green;
5. no production file changes;
6. no existing test file changes;
7. no real persistence/network capability is reached;
8. rollback remains exact and test-only.

## 9. Rollback Unit

Rollback is exactly deletion/reversion of:

`tests/test_persistence_engine_lifecycle_contract.py`

Rollback requires no production, database, schema, data, migration, or deployment
action.

## 10. Establishment and Implementation Separation

Establishing this ADA does not itself create the authorized test file.

After establishment, a separately prepared implementation script may create exactly
that one test file, run only authorized non-networking verification, commit exactly
that file, create one annotated tag, and atomically push branch plus tag.

## 11. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i1a_status=COMPLETE`
- `i1b_scope=I1B1_THEN_I1B2`
- `i1b1_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i1b1_test_write_authority=ISSUED`
- `i1b1_exact_file_scope=ONE_NEW_TEST_FILE`
- `i1b2_production_authority=NOT_ISSUED`
- `i1c_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`
- `next_action=IMPLEMENT_I1B1_ENGINE_LIFECYCLE_CHARACTERIZATION`

No further authority is implied.
