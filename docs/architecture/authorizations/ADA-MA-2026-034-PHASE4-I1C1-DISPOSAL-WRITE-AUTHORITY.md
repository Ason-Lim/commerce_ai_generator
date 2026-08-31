# ADA-MA-2026-034 Phase 4 I1-C1 Disposal Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1-C1 — Canonical Lifecycle Disposal Foundation`
- Authority: `ADA-MA-2026-034-PHASE4-I1C1-DISPOSAL-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `d358a53b5e6ba32f7ceaab377ccfdc96eadcac22`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i1c-exact-scope-decision-established-v1.0`
- Authority type: `PRODUCTION_AND_TEST_WRITE_BOUNDED`
- Database/network execution authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I1-C1 implementation unit.

Its purpose is to add explicit, testable disposal semantics to the established
canonical lifecycle core without modifying the legacy engine compatibility surface
or any consumer.

## 3. Exact Authorized File Scope

Write authority is issued only for exactly these two files:

1. `app/db/lifecycle.py` — existing production file
2. `tests/test_persistence_engine_disposal.py` — new test file

No other file may be created, modified, renamed, or deleted under this authority.

## 4. Authorized Disposal Semantics

`EngineLifecycle` may be extended to provide explicit disposal with these semantics:

- `dispose()` before initialization is a no-op;
- disposal is idempotent;
- an initialized engine is disposed at most once per published identity;
- successful disposal clears the published engine;
- after successful disposal, `engine is None`;
- after successful disposal, `initialized is False`;
- successful disposal transitions the lifecycle into a terminal disposed state;
- initialization after successful disposal fails closed;
- lifecycle exposes bounded disposed-state observation;
- disposal does not acquire a connection;
- disposal does not begin a transaction.

## 5. Disposal Failure Semantics

If the underlying engine `dispose()` raises:

- the exception propagates;
- the published engine identity remains unchanged;
- `initialized` remains `True`;
- disposed state remains `False`;
- a later disposal call may retry the same engine identity.

The lifecycle must not falsely publish successful disposal after an exception.

## 6. Terminal Lifecycle Rule

A disposed lifecycle instance is terminal.

Re-initialization after successful disposal is not authorized.

A new process/worker lifecycle requires a new lifecycle authority instance.

## 7. Legacy Compatibility Freeze

The following remain immutable during I1-C1:

- `app/db/database.py`;
- all 23 direct production importers of `app.db.database.engine`;
- independent engine constructors;
- `app/main.py`;
- logger modules;
- collector modules;
- recommendation modules;
- Streamlit/admin surfaces.

No compatibility bridge is created in I1-C1.

## 8. I1-C2 Deferral

The compatibility bridge remains:

`DEFERRED_UNTIL_I2_EVIDENCE`

This ADA does not authorize:

- `app/db/compatibility.py`;
- state-gated legacy accessor;
- rebinding `app.db.database.engine`;
- FastAPI composition integration.

## 9. Authorized Test Coverage

`tests/test_persistence_engine_disposal.py` may verify, using injected fake/sentinel
engines:

- dispose-before-init no-op;
- exactly-once disposal after initialization;
- idempotent repeated disposal;
- state clear after successful disposal;
- terminal disposed state;
- initialize-after-dispose fail-closed;
- no connect/begin during disposal;
- disposal failure preserves engine publication;
- disposal failure remains retryable;
- no consumer binding;
- preservation of `app/db/database.py` SHA256;
- preservation of direct legacy importer count `23`.

## 10. Existing Read-Only Dependencies

These established files may be imported or inspected but are not writable:

- `app/core/config.py`;
- `app/db/database.py`;
- `app/db/protocols.py`;
- `tests/test_persistence_engine_lifecycle.py`;
- `tests/test_persistence_engine_lifecycle_contract.py`;
- `tests/test_persistence_configuration_resolver.py`;
- `tests/test_persistence_real_resource_denial_guard.py`.

## 11. Explicitly Not Authorized

This ADA does not authorize:

- FastAPI lifespan integration;
- shutdown hook registration;
- application startup wiring;
- legacy engine replacement/removal/rebinding;
- compatibility accessor implementation;
- consumer migration;
- real database/network execution;
- database/schema/data mutation;
- DDL/migration execution;
- Phase 5 verification.

## 12. Authorized Non-Networking Verification

This ADA authorizes only:

- syntax compilation of the two authorized files;
- fake-backed disposal tests;
- I1-B2 lifecycle regression;
- I1-B1 characterization regression;
- I1-A resolver regression;
- I0 real-resource denial guard regression;
- collection-only checks;
- static proof that `app/db/database.py` retains its required SHA256;
- static proof that direct legacy engine importer count remains `23`;
- exact two-file scope/diff checks.

No real database/network/integration execution is authorized.

## 13. Acceptance Conditions

I1-C1 may be considered implementation-complete only if:

1. exactly the two authorized files change;
2. disposal tests pass;
3. prior lifecycle/resolver/guard regressions remain green;
4. successful disposal is exactly-once and idempotent;
5. disposed state is terminal;
6. failure preserves published state for retry;
7. `app/db/database.py` is byte-for-byte unchanged;
8. direct legacy importer count remains 23;
9. no consumer file changes;
10. rollback remains exact and code-only.

## 14. Rollback Unit

Rollback is exactly:

- revert `app/db/lifecycle.py`;
- delete/revert `tests/test_persistence_engine_disposal.py`.

Rollback requires no database, schema, data, migration, compatibility-surface, or
deployment action.

## 15. Establishment and Implementation Separation

Establishing this ADA does not itself modify either authorized file.

After establishment, a separately prepared implementation script may modify exactly
the two authorized files, run only authorized non-networking verification, commit
exactly those files, create one annotated tag, and atomically push branch plus tag.

## 16. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i1a_status=COMPLETE`
- `i1b_status=COMPLETE`
- `i1c_scope=I1C1_REQUIRED_I1C2_DEFERRED`
- `i1c1_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i1c1_production_write_authority=ISSUED`
- `i1c1_test_write_authority=ISSUED`
- `i1c1_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_I2_EVIDENCE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=IMPLEMENT_I1C1_EXACT_DISPOSAL_FOUNDATION`

No further authority is implied.
