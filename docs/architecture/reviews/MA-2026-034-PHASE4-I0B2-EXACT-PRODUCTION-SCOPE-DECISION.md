# MA-2026-034 Phase 4 I0-B2 Exact Production Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Decision: `MA-2026-034-PHASE4-I0B2-EXACT-PRODUCTION-SCOPE-DECISION`
- Governing I0-B1 completion commit: `5fa5d3debada419a61df1d3dee91deb8b736900f`
- Governing I0-B1 completion tag: `ma-2026-034-phase4-i0b1-completion-review-established-v1.0`
- Decision effect: define the first bounded production protocol-adoption unit
- Production implementation authority: `NOT_ISSUED`

## 2. Read-Only Evidence Determination

The I0-B2 production-scope preflight established:

- exactly nine `conn: Any` parameters remain;
- they exist only in four production files:
  - `app/services/preference/service.py`
  - `app/services/preference/store.py`
  - `app/services/session_context/service.py`
  - `app/services/session_context/store.py`
- the store boundary requires only `execute` capability;
- service boundaries forward the exact caller-provided object to stores;
- consumers must not require `begin`, `commit`, `rollback`, `close`, or `dispose`;
- four service tests intentionally retain opaque `object()` substitutes when
  downstream persistence is replaced;
- the existing `app/db/database.py` is an engine-construction module and is not an
  appropriate protocol-definition module;
- no canonical shared persistence protocol module currently exists;
- no import-cycle signal prevents a new leaf protocol module;
- logger files are outside this protocol-adoption unit.

## 3. Selected Scope Shape

The selected production shape is:

`shape_A = one new shared protocol module + four existing production files`

The new shared leaf module SHALL be:

`app/db/protocols.py`

The complete I0-B2 candidate production scope is therefore exactly five files:

1. `app/db/protocols.py` — new
2. `app/services/preference/service.py` — existing
3. `app/services/preference/store.py` — existing
4. `app/services/session_context/service.py` — existing
5. `app/services/session_context/store.py` — existing

No other production file is in I0-B2 scope.

## 4. Canonical Protocol Shape

`app/db/protocols.py` shall define a minimal borrowed execution protocol whose
required lifecycle capability is exactly `execute`.

The protocol shall not require or expose ownership capabilities merely because a
real SQLAlchemy connection supports them.

It shall not require:

- `begin`;
- `commit`;
- `rollback`;
- `close`;
- `dispose`;
- engine acquisition;
- context-manager ownership.

The protocol is a structural typing boundary, not a runtime wrapper.

## 5. Annotation Adoption Boundary

All nine current `conn: Any` annotations in the four scoped files shall migrate to
the shared borrowed execution protocol.

Runtime statements, control flow, SQL, function names, parameter order, return
values, connection forwarding, and resource ownership shall remain unchanged.

`Any` usages unrelated to the connection parameter, including mapping/value return
types, are not part of this migration.

## 6. Opaque Test Substitute Compatibility

Because Python type annotations are not runtime enforcement, the existing service
tests that pass `object()` while replacing downstream persistence shall remain
runtime-compatible.

I0-B2 shall not add runtime `isinstance`, protocol validation, assertion, coercion,
adapter construction, or capability probing at service entry.

The protocol adoption is annotation-only plus the new shared protocol definition.

## 7. Execute-Only Fake Compatibility

The existing Preference `_FakeConnection` and I0-B1 execute-only sentinel shall
remain compatible with store functions.

I0-B2 must not widen those fakes with lifecycle-owner methods.

## 8. Import Topology Decision

The four scoped production modules shall import the shared protocol directly from:

`app.db.protocols`

`app/db/__init__.py` shall not be modified or used as a re-export surface in this
unit.

`app/db/database.py` shall not be modified.

This keeps the protocol module as a leaf typing dependency and avoids coupling type
definitions to engine construction.

## 9. Explicitly Out of Scope

I0-B2 does not authorize changes to:

- `app/db/__init__.py`;
- `app/db/database.py`;
- `app/main.py`;
- `app/ui/streamlit_app.py`;
- `app/services/analytics_logger.py`;
- `app/services/context_logger.py`;
- `app/services/impression_logger.py`;
- any test file;
- any SQL text or persistence behavior;
- any engine acquisition site.

It also does not authorize:

- transaction-owner migration;
- consumer cutover;
- database/network execution;
- database/schema/data mutation;
- DDL or migration execution;
- Phase 5 verification.

## 10. Verification Boundary for Later Authority

A later I0-B2 production-write authority may authorize only non-networking
verification sufficient for this annotation migration:

- syntax compilation of the five scoped production files;
- I0-A guard tests;
- I0-B1 characterization tests;
- existing Preference service/store tests;
- existing Session Context service tests;
- selected static consumer tests;
- grep/static proof that the nine scoped `conn: Any` annotations are replaced;
- grep/static proof that no lifecycle-owner method was added to the protocol;
- exact diff/scope checks.

No real database or application-network execution is required.

## 11. Rollback Unit

The I0-B2 rollback unit is exactly:

- deletion/reversion of `app/db/protocols.py`;
- reversion of the four annotation/import edits.

Rollback requires no database, schema, data, migration, or deployment action.

## 12. Authority Result

Establishment of this decision does not issue production-write authority.

After successful establishment:

- `phase_4_status=OPEN`
- `i0a_status=COMPLETE`
- `i0b1_status=COMPLETE`
- `i0b2_scope=EXACT_FIVE_PRODUCTION_FILES`
- `i0b2_protocol_module=app/db/protocols.py`
- `i0b2_runtime_behavior_change=NONE_AUTHORIZED`
- `i0b2_production_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I0B2_PRODUCTION_WRITE_AUTHORITY`

No further authority is implied.
