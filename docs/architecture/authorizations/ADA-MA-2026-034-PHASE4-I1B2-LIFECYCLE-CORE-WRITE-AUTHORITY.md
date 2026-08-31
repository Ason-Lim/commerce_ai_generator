# ADA-MA-2026-034 Phase 4 I1-B2 Lifecycle Core Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1-B2 — Canonical Lifecycle Core Production Module`
- Authority: `ADA-MA-2026-034-PHASE4-I1B2-LIFECYCLE-CORE-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `fae11397d3b75f08d29d2090214ed937f3cc4886`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i1b2-exact-scope-decision-established-v1.0`
- Authority type: `PRODUCTION_AND_TEST_WRITE_BOUNDED`
- Database/network execution authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I1-B2 implementation unit.

Its purpose is to introduce the canonical engine lifecycle core as a new leaf module
and verify it with a new production-facing lifecycle test module, without modifying
the legacy `app.db.database.engine` compatibility surface.

## 3. Exact Authorized File Scope

Write authority is issued only for exactly these two new files:

1. `app/db/lifecycle.py`
2. `tests/test_persistence_engine_lifecycle.py`

No existing file may be modified, renamed, or deleted under this authority.

## 4. Legacy Compatibility Freeze

The following file is an immutable compatibility dependency during I1-B2:

`app/db/database.py`

Its required SHA256 is:

`8bbbdebd98553bba2045b647a33d5b159a14eeb07c641cfafb8c87d51e465f77`

The 23 direct production importers of `app.db.database.engine` must remain unchanged
in count and content under this authority.

I1-B2 does not authorize replacement, delegation, rebinding, or removal of the
legacy module-scope engine.

## 5. Authorized Lifecycle Core Behavior

`app/db/lifecycle.py` may define a canonical lifecycle authority that:

- performs zero engine construction at module import;
- accepts or defaults the I1-A canonical database URL resolver;
- accepts or defaults an engine factory;
- initializes only on explicit lifecycle initialization;
- passes `pool_pre_ping=True` to the engine factory;
- publishes the engine only after successful factory return;
- returns one stable engine identity after initialization;
- makes repeated initialization idempotent;
- exposes bounded lifecycle state for observation;
- performs no connection acquisition during initialization;
- performs no transaction acquisition during initialization;
- performs no disposal during initialization.

## 6. Default Factory Boundary

The module may use SQLAlchemy `create_engine` as its default engine factory.

The default factory must not be invoked:

- during module import;
- during test collection;
- during authorized non-networking verification.

Production-facing tests must inject fake/sentinel factories.

## 7. Resolver Boundary

The lifecycle core may default to the established I1-A resolver:

`app.core.config.resolve_database_url`

Resolution must occur only during explicit initialization.

No configuration precedence, alias, default, or conflict semantics may be changed.

## 8. Disposal Deferral

I1-B2 does not authorize disposal implementation.

The lifecycle core must not add:

- shutdown hooks;
- `atexit`;
- FastAPI lifespan binding;
- automatic disposal;
- legacy engine replacement;
- state-gated compatibility access.

Those remain reserved for I1-C.

## 9. Authorized Test Coverage

`tests/test_persistence_engine_lifecycle.py` may verify the real lifecycle module
using injected fakes/sentinels for:

- import purity;
- zero construction before initialization;
- exactly one construction;
- idempotent initialization;
- stable engine identity;
- resolver URL propagation;
- `pool_pre_ping=True`;
- failure-before-publication;
- no connect/begin/dispose during initialization;
- lifecycle observability;
- no consumer binding;
- preservation of `app/db/database.py` SHA256;
- preservation of 23 direct legacy engine importers.

## 10. Existing Read-Only Dependencies

These files may be imported or inspected but are not writable:

- `app/core/config.py`;
- `app/db/database.py`;
- `app/db/protocols.py`;
- `tests/test_persistence_engine_lifecycle_contract.py`;
- `tests/test_persistence_real_resource_denial_guard.py`;
- `tests/test_persistence_configuration_resolver.py`.

## 11. Explicitly Not Authorized

This ADA does not authorize changes to any existing production or test file.

It also does not authorize:

- legacy engine compatibility changes;
- disposal implementation;
- consumer migration;
- real database engine construction during verification;
- database connection execution;
- application-network execution;
- database/schema/data mutation;
- DDL/migration execution;
- Phase 5 verification.

## 12. Authorized Non-Networking Verification

This ADA authorizes only:

- syntax compilation of the two new files;
- pytest execution of the new production-facing lifecycle tests;
- I1-B1 characterization regression;
- I1-A resolver regression;
- I0 real-resource denial guard regression;
- collection-only checks;
- exact file-scope checks;
- static proof that `app/db/database.py` retains its required SHA256;
- static proof that direct legacy engine importer count remains 23.

No real database/network/integration execution is authorized.

## 13. Acceptance Conditions

I1-B2 may be considered implementation-complete only if:

1. exactly two new files are changed;
2. lifecycle core tests pass;
3. I1-B1 characterization remains green;
4. I1-A resolver remains green;
5. I0 guard remains green;
6. `app/db/database.py` is byte-for-byte unchanged;
7. direct legacy importer count remains 23;
8. no existing file changes;
9. no real DB/network capability is reached;
10. rollback remains exact and code-only.

## 14. Rollback Unit

Rollback is exactly deletion/reversion of:

- `app/db/lifecycle.py`;
- `tests/test_persistence_engine_lifecycle.py`.

Rollback requires no compatibility-surface, database, schema, data, migration, or
deployment action.

## 15. Establishment and Implementation Separation

Establishing this ADA does not itself create the lifecycle core or its tests.

After establishment, a separately prepared implementation script may create exactly
the two authorized files, run only authorized non-networking verification, commit
exactly those two files, create one annotated tag, and atomically push branch plus
tag.

## 16. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i1a_status=COMPLETE`
- `i1b1_status=COMPLETE`
- `i1b2_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i1b2_production_write_authority=ISSUED`
- `i1b2_test_write_authority=ISSUED`
- `i1b2_exact_file_scope=ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i1b2_database_py_policy=BYTE_FOR_BYTE_UNCHANGED`
- `i1c_implementation_authority=NOT_ISSUED`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=IMPLEMENT_I1B2_EXACT_LIFECYCLE_CORE`

No further authority is implied.
