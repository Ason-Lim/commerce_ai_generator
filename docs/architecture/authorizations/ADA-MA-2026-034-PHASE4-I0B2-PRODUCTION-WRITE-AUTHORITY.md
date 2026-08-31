# ADA-MA-2026-034 Phase 4 I0-B2 Production-Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Authority: `ADA-MA-2026-034-PHASE4-I0B2-PRODUCTION-WRITE-AUTHORITY`
- Governing exact-scope decision commit: `7e2156bb93dd11d44eeb22f6b2eb6efdaebff027`
- Governing exact-scope decision tag: `ma-2026-034-phase4-i0b2-exact-production-scope-decision-established-v1.0`
- Authority type: `PRODUCTION_WRITE_ONLY`
- Runtime behavior change authority: `NONE`

## 2. Purpose

This ADA authorizes exactly one bounded I0-B2 production implementation unit.

Its purpose is to introduce one shared borrowed execution protocol and replace the
nine existing `conn: Any` annotations in the authorized Preference and Session
Context modules without changing runtime behavior.

## 3. Exact Authorized File Scope

Production-write authority is issued only for exactly these five files:

1. `app/db/protocols.py` — new
2. `app/services/preference/service.py`
3. `app/services/preference/store.py`
4. `app/services/session_context/service.py`
5. `app/services/session_context/store.py`

No other file may be created, modified, renamed, or deleted under this authority.

## 4. Authorized Protocol Definition

`app/db/protocols.py` may define one minimal structural protocol representing a
borrowed execution connection.

The protocol may require only the capability needed by current consumers:

- `execute(statement, params)`

The protocol must not require or expose owner-lifecycle capabilities such as:

- `begin`
- `commit`
- `rollback`
- `close`
- `dispose`

The protocol is typing structure only. It must not construct engines, open
connections, perform runtime validation, or wrap connection objects.

## 5. Authorized Annotation Migration

The nine current `conn: Any` annotations in the four existing production files may
be replaced with the shared borrowed execution protocol type.

Authorized edits are limited to:

- replacing the relevant `Any` connection annotations;
- adding the required import from `app.db.protocols`;
- removing `Any` imports only when no longer needed in that file;
- preserving all unrelated `Any` usages.

No SQL, control flow, parameter ordering, defaults, function names, return values,
connection forwarding, or persistence behavior may change.

## 6. Runtime Compatibility Requirements

The implementation must preserve:

- exact caller-provided connection object identity;
- execute-only store fake compatibility;
- opaque `object()` service substitution in tests when downstream persistence is
  replaced;
- existing Preference service/store behavior;
- existing Session Context service/store behavior;
- absence of consumer-side transaction ownership.

No runtime `isinstance`, `Protocol` check, coercion, adapter, wrapper, assertion, or
capability probe may be added.

## 7. Explicitly Not Authorized

This ADA does not authorize changes to:

- `app/db/__init__.py`;
- `app/db/database.py`;
- `app/main.py`;
- `app/ui/streamlit_app.py`;
- `app/services/analytics_logger.py`;
- `app/services/context_logger.py`;
- `app/services/impression_logger.py`;
- any test file;
- any other production file.

It also does not authorize:

- transaction-owner migration;
- engine acquisition migration;
- consumer cutover;
- database connection execution;
- application-network execution;
- database/schema/data mutation;
- DDL or migration execution;
- Phase 5 verification execution.

## 8. Authorized Non-Networking Verification

This ADA authorizes only verification needed to prove the exact annotation-only
migration:

- syntax compilation of the five authorized production files;
- I0-A guard tests;
- I0-B1 borrowed-connection and transaction-owner characterization tests;
- existing Preference service/store tests;
- existing Session Context service tests;
- selected static consumer tests;
- static proof that the nine scoped `conn: Any` annotations are gone;
- static proof that exactly nine scoped connection annotations use the shared
  protocol;
- static proof that the shared protocol contains no lifecycle-owner methods;
- exact diff and commit-scope checks.

No real database, application-network, integration, migration, or DDL execution is
authorized.

## 9. Acceptance Conditions

I0-B2 may be considered implementation-complete only if:

1. exactly five authorized production files are changed;
2. `app/db/protocols.py` is the only new production file;
3. exactly nine scoped connection annotations migrate from `Any`;
4. runtime behavior remains unchanged;
5. I0-A guard tests remain green;
6. I0-B1 characterization remains green;
7. selected Preference and Session Context regressions remain green;
8. no test file changes;
9. no real DB/network capability is reached;
10. rollback remains exact and code-only.

## 10. Rollback Unit

The rollback unit is exactly:

- delete/revert `app/db/protocols.py`;
- revert the four authorized annotation/import edits.

Rollback requires no database, schema, data, migration, or deployment action.

## 11. Establishment and Implementation Separation

Establishing this ADA does not itself modify production code.

After this ADA is established, a separately prepared implementation establishment
script may modify exactly the five authorized files, execute only authorized
non-networking verification, commit exactly those files, create one annotated tag,
and atomically push branch plus tag.

## 12. Authority State After Establishment

If this ADA is successfully established:

- `phase_4_status=OPEN`
- `i0a_status=COMPLETE`
- `i0b1_status=COMPLETE`
- `i0b2_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i0b2_production_write_authority=ISSUED`
- `i0b2_exact_file_scope=FIVE_PRODUCTION_FILES`
- `i0b2_runtime_behavior_change=NONE_AUTHORIZED`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`
- `next_action=IMPLEMENT_I0B2_EXACT_FIVE_FILE_PROTOCOL_ADOPTION`

No further authority is implied.
