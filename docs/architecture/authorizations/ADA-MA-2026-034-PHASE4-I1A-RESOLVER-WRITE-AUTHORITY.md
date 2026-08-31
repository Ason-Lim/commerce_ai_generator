# ADA-MA-2026-034 Phase 4 I1-A Resolver Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1-A — Canonical Configuration Resolver Foundation`
- Authority: `ADA-MA-2026-034-PHASE4-I1A-RESOLVER-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `03a7852e6911d174c6e552c4b981dfd0360911ad`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i1-exact-scope-decision-established-v1.0`
- Authority type: `PRODUCTION_AND_TEST_WRITE_BOUNDED`
- Database/network execution authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I1-A implementation unit.

Its purpose is to centralize database URL resolution semantics inside
`app.core.config` and establish non-networking tests for the canonical alias/default
contract.

This authority does not change engine lifecycle, consumer ownership, or database
runtime behavior.

## 3. Exact Authorized File Scope

Write authority is issued only for exactly these two files:

1. `app/core/config.py` — existing production file
2. `tests/test_persistence_configuration_resolver.py` — new test file

No other file may be created, modified, renamed, or deleted under this authority.

## 4. Authorized Resolver Behavior

`app/core/config.py` may be changed to provide one canonical resolver implementing:

1. `DATABASE_URL`
2. `COMMERCE_DB_URL`
3. `FRUIT_DB_URL`

with the following semantics:

- empty/whitespace values are absent;
- one non-empty value resolves;
- multiple equal non-empty values are accepted;
- conflicting non-empty values fail closed;
- compatibility aliases remain supported;
- no alias is removed in this unit;
- when none is set, the canonical local default is
  `postgresql+psycopg2://mom@localhost:5432/dashboard_db`.

The module may continue to expose `DATABASE_URL` for existing consumers.

## 5. Error and Redaction Boundary

Conflict errors must not expose credential-bearing full URL values.

Error output may identify conflicting environment variable names, but must not echo
secret-bearing connection strings.

No telemetry or external logging is required or authorized.

## 6. Import Boundary

Importing `app.core.config` must remain:

- non-networking;
- non-database;
- free of engine construction;
- free of schema/data mutation.

`load_dotenv()` behavior may be preserved if required for compatibility, but tests
must isolate process-local environment state.

## 7. Authorized Test Coverage

`tests/test_persistence_configuration_resolver.py` may establish tests for:

- no aliases set;
- only `DATABASE_URL`;
- only `COMMERCE_DB_URL`;
- only `FRUIT_DB_URL`;
- empty/whitespace values treated as absent;
- duplicate equal aliases accepted;
- conflicting aliases rejected;
- precedence identity with equal aliases;
- canonical local default;
- redaction of credential-bearing values in conflict errors;
- import remains non-networking under the established I0 guard.

## 8. Explicitly Not Authorized

This ADA does not authorize changes to:

- `app/db/database.py`;
- `app/db/protocols.py`;
- `app/main.py`;
- any logger module;
- collectors;
- recommendation pipeline;
- Streamlit/admin surfaces;
- any other test file.

It also does not authorize:

- engine lifecycle implementation;
- engine construction migration;
- shutdown/disposal implementation;
- consumer migration;
- database connection execution;
- application-network execution;
- database/schema/data mutation;
- DDL or migration execution;
- Phase 5 verification.

## 9. Authorized Non-Networking Verification

This ADA authorizes only:

- syntax compilation of the two authorized files;
- pytest execution of the new resolver test module;
- I0 real-resource denial guard tests;
- static import/scope checks;
- static proof that no engine construction is added to `app.core.config`.

No real database/network/integration execution is authorized.

## 10. Acceptance Conditions

I1-A may be considered implementation-complete only if:

1. exactly the two authorized files change;
2. all resolver matrix tests pass;
3. conflict cases fail closed;
4. credential-bearing URL values do not appear in conflict errors;
5. the canonical local default is preserved;
6. no engine construction appears in `app.core.config`;
7. I0 guard tests remain green;
8. no consumer file changes;
9. rollback is exact and code-only.

## 11. Rollback Unit

Rollback is exactly:

- revert `app/core/config.py`;
- delete/revert `tests/test_persistence_configuration_resolver.py`.

Rollback requires no database, schema, data, migration, or deployment action.

## 12. Establishment and Implementation Separation

Establishing this ADA does not itself modify the authorized files.

After establishment, a separately prepared implementation script may change exactly
the two authorized files, run only authorized non-networking verification, commit
exactly those files, create one annotated tag, and atomically push branch plus tag.

## 13. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i1_scope=I1A_THEN_I1B_THEN_I1C`
- `i1a_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i1a_production_write_authority=ISSUED`
- `i1a_test_write_authority=ISSUED`
- `i1a_exact_file_scope=ONE_PRODUCTION_PLUS_ONE_TEST_FILE`
- `i1b_implementation_authority=NOT_ISSUED`
- `i1c_implementation_authority=NOT_ISSUED`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`
- `next_action=IMPLEMENT_I1A_EXACT_RESOLVER_FOUNDATION`

No further authority is implied.
