# MA-2026-034 Phase 3 Connection Acquisition / Release Ownership Contract

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Contract: `MA-2026-034-PHASE3-CONNECTION-ACQUISITION-RELEASE-OWNERSHIP-CONTRACT`
- Contract version: `1.0`
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Governing evidence: Phase 3 Evidence Waves 1–4 and their established classifications

## 2. Purpose

This contract assigns authoritative ownership for acquiring and releasing persistence connections. It defines the boundary between an acquisition owner and a connection consumer, preserves caller-provided connection compatibility, and establishes fail-closed rules for connection lifetime.

This contract is architecture only. It does not authorize production implementation, test implementation, database execution, schema or data mutation, consumer migration, or verification execution.

## 3. Evidence basis

The established evidence supports these bounded facts:

- `app.db.database` is the Phase 2 canonical engine owner;
- application code contains 41 `engine.begin()` and 29 `engine.connect()` persistence acquisition scopes;
- nine functions require a caller-provided `conn` parameter;
- 25 application or test calls exercise that connection-accepting surface;
- application forwarding preserves a syntactically identical `conn` at ten identified calls;
- no explicit database `commit`, `rollback`, `close`, or `dispose` call was identified;
- no transaction-capable test double or persistence resource fixture was identified;
- runtime transaction and release behavior remains unverified.

The contract therefore distinguishes architectural intent from current implementation conformance.

## 4. Normative terms

The key words `MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, and `MAY` are normative.

### 4.1 Canonical engine owner

The module designated by Phase 2 as the canonical authority that constructs and exposes the process-lifecycle SQLAlchemy engine: `app.db.database`.

### 4.2 Acquisition owner

The bounded composition-root, request-entry, job-entry, command-entry, or explicitly designated orchestration scope that calls `engine.connect()` or `engine.begin()`.

### 4.3 Connection consumer

A service, store, query function, writer, logger, or adapter that receives an already-acquired connection from its caller.

### 4.4 Transaction owner

The scope authorized to define success and failure for a unit of work. Under this contract, an `engine.begin()` acquisition owner is also the transaction owner unless a later, more specific established contract assigns ownership differently.

### 4.5 Release

Return of an acquired connection to its engine/pool or closure of the acquired resource by the mechanism that created the acquisition scope. Release does not mean engine disposal.

### 4.6 Disposal

Process-lifecycle shutdown of the canonical engine and its pool. Disposal is distinct from per-operation connection release.

## 5. Canonical ownership rule

Every acquired connection SHALL have exactly one acquisition owner.

The code scope that invokes `engine.connect()` or `engine.begin()` SHALL own:

1. successful context entry;
2. the connection lifetime;
3. admission of downstream consumers;
4. exit on normal completion;
5. exit on exceptional completion;
6. release of the connection through the acquisition context;
7. prevention of connection escape beyond the authorized lifetime.

A downstream connection consumer SHALL NOT assume acquisition or release ownership merely because it can call methods on the connection.

## 6. Canonical acquisition modes

### 6.1 Read or non-transaction-owner scope

An owner that needs a bounded connection without owning an automatic commit unit SHALL use the canonical equivalent of:

```python
with engine.connect() as conn:
    ...
```

The owner SHALL release the connection on every exit path. The owner and all consumers MUST NOT infer commit-on-success semantics from a `connect()` scope.

### 6.2 Transaction-owning scope

An owner that defines one atomic unit of work SHALL use the canonical equivalent of:

```python
with engine.begin() as conn:
    ...
```

The owner SHALL treat normal context completion as the transaction success boundary and exceptional context completion as the transaction failure boundary, subject to the separately established Transaction and Unit-of-Work Boundary Contract.

### 6.3 Prohibited ambiguous acquisition

The following are prohibited architecture targets unless explicitly authorized by a later decision:

- an unbounded connection stored for arbitrary reuse;
- a service acquiring a new connection when its caller supplied one;
- a store acquiring its own connection while accepting a `conn` parameter;
- a consumer closing or disposing a caller-owned resource;
- implicit selection between `connect()` and `begin()` based only on convenience;
- returning a live connection or connection-bound iterator beyond the owner’s context lifetime.

## 7. Caller-provided connection rule

When a function accepts `conn`, the caller owns acquisition and release unless an established contract explicitly states otherwise.

The receiving function:

- MUST use the supplied connection for the bounded persistence work;
- MUST NOT construct or retrieve a replacement engine or connection;
- MUST NOT close the supplied connection;
- MUST NOT dispose the engine behind the supplied connection;
- MUST NOT commit or roll back the caller-owned transaction;
- MUST NOT retain the connection after return;
- MUST NOT pass it to background work whose lifetime exceeds the owner scope;
- MAY forward the exact connection to another compatible consumer within the same synchronous unit of work.

The connection shall be treated as a borrowed capability, not as a transferred resource.

## 8. Connection capability contract

The current `Any` annotation is evidence of an open compatibility surface, not the target contract.

The target architecture SHALL define minimal structural capabilities rather than require a concrete production connection class everywhere.

### 8.1 Execution consumer capability

A basic store that only executes statements MAY depend on a minimal protocol equivalent to:

```python
class ExecutionConnection(Protocol):
    def execute(self, statement, parameters=None): ...
```

The exact Python form is deferred to an authorized implementation phase. The architectural requirement is capability minimization.

### 8.2 Transaction owner capability

Commit, rollback, context entry, and context exit capabilities belong to the acquisition/transaction owner boundary. They SHALL NOT be added to every store protocol merely because a real SQLAlchemy connection exposes them.

### 8.3 Test substitution

Non-networking test substitutes SHALL implement only the capability required by the subject under test. Transaction-owner tests SHALL use a transaction-capable fake or factory that can record entry, success exit, exceptional exit, rollback, release, and prohibited post-release use.

## 9. Ownership by architectural layer

| Layer or role | May acquire | Must release its acquisition | May consume supplied `conn` | May close supplied `conn` | May dispose canonical engine |
|---|---|---|---|---|---|
| Canonical engine owner | bootstrap only | process shutdown obligations | N/A | N/A | shutdown composition only |
| Composition/request/job entry owner | yes, when authorized | yes | yes | only its own context controls release | no |
| Orchestration transaction owner | yes, when designated | yes | yes | only through its owning context | no |
| Service consumer | no when `conn` supplied | no | yes | no | no |
| Store consumer | no | no | yes | no | no |
| UI route/component | only as current compatibility seam pending migration | yes | yes | only through its owning context | no |
| Test harness | only through a non-networking substitute | yes | yes | according to fake ownership | no real-engine disposal |

## 10. Existing compatibility seams

The following current seams SHALL remain behaviorally compatible until a separately authorized migration changes them:

### 10.1 Preference services

- `update_user_preference(conn, ...)`
- `get_user_preference(conn, ...)`
- `get_preference_profile(conn, ...)`

These remain borrowed-connection consumers and may forward the same connection to preference stores.

### 10.2 Session-context services

- `update_session_context(conn, ...)`
- `get_session_context(conn, ...)`

These remain borrowed-connection consumers and may forward the same connection to session-context stores.

### 10.3 Analytics logger

`log_product_click` currently acquires through `engine.begin()` and forwards one connection to both preference and session-context updates. The acquisition scope owns release. The two downstream services MUST NOT independently acquire, close, commit, or roll back.

Atomicity and rollback meaning for the two updates are reserved for the Transaction and Unit-of-Work Boundary Contract.

### 10.4 FastAPI application path

The identified `app.main` path that obtains a connection and calls `get_session_context` remains an acquisition-owner-to-consumer relationship. The consumer may not extend the acquired connection lifetime.

### 10.5 Streamlit path

The identified Streamlit `connect` and `begin` scopes remain compatibility seams. Their lexical scopes own release. A later migration MAY move acquisition into an explicit composition layer, but only under consumer-migration authority.

## 11. Nested and re-entrant calls

Within one authorized unit of work:

- nested services SHALL receive the existing connection;
- a nested service SHALL NOT open a second connection merely to call a store;
- a nested store SHALL NOT begin an independent transaction;
- acquisition depth SHALL NOT silently increase because a helper is reused;
- re-entrant use SHALL be rejected or explicitly supported by a later contract;
- concurrent use of one synchronous connection across threads or tasks SHALL NOT be assumed safe.

If a nested operation requires independent atomicity, it must be modeled as a separately authorized unit of work rather than hidden inside a consumer.

## 12. Connection escape prevention

A connection or connection-bound result SHALL NOT escape its owner scope through:

- global or module state;
- application state without an explicit lifecycle contract;
- cached function results;
- background tasks;
- deferred generators or iterators;
- callbacks executed after context exit;
- session state;
- returned closures;
- object fields whose lifetime is broader than the acquisition scope.

Materialized values MAY cross the boundary after the owner confirms that no live connection dependency remains.

## 13. Normal completion

On normal completion:

1. all synchronous consumers must have returned;
2. connection-bound results must be fully consumed or explicitly closed within the owner scope;
3. the acquisition context must exit exactly once;
4. the connection must become unavailable to downstream code;
5. the owner must not issue further work through the released connection.

For `begin()` scopes, transaction completion semantics are governed additionally by the forthcoming Transaction and Unit-of-Work Boundary Contract.

## 14. Exceptional completion

If acquisition entry fails, no consumer SHALL run.

If a consumer raises:

- the exception SHALL propagate to the acquisition/transaction owner unless an explicit error contract translates it;
- the consumer SHALL NOT close, commit, or roll back the caller-owned connection;
- the owner SHALL exit the context exactly once;
- no subsequent consumer SHALL use the connection after owner exit;
- cleanup failure SHALL not silently replace the primary failure without an explicit precedence rule.

Detailed rollback, cancellation, and exception-precedence rules are reserved for the Failure / Rollback / Cancellation Semantics Contract.

## 15. Release and engine disposal

Per-operation release and process-lifecycle disposal are separate authorities.

- Acquisition owners release their own acquired connections through the canonical context boundary.
- Connection consumers do not dispose engines.
- Request, UI, service, store, and job functions do not dispose the canonical engine.
- Canonical engine disposal belongs only to the authorized application shutdown composition defined by the Phase 2 runtime resource map.
- Engine disposal SHALL occur only after admission is stopped and active scopes are drained.
- This contract does not authorize implementing or executing disposal.

## 16. Observability requirements

Later authorized implementation SHOULD make it possible to observe, without exposing credentials or SQL parameter secrets:

- acquisition mode (`connect` or `begin`);
- owner identity;
- bounded operation identity;
- context entry success or failure;
- normal or exceptional exit;
- release completion;
- prohibited use after release;
- elapsed lifetime;
- correlation across nested consumers.

Observability MUST NOT require a real database in unit tests.

## 17. Verification obligations

Implementation conformance cannot be claimed until authorized tests establish at least:

1. one acquisition per bounded owner scope;
2. exactly one release on success;
3. exactly one release on consumer failure;
4. no consumer-side close, commit, rollback, or dispose;
5. no second acquisition when `conn` is supplied;
6. exact connection identity across nested compatible consumers;
7. no use after release;
8. no connection escape through returned values or background work;
9. separate behavior for `connect()` and `begin()`;
10. shutdown disposal only after active scopes drain;
11. non-networking test substitutes;
12. fail-closed behavior when acquisition entry fails.

These tests are obligations only. Test authoring and execution remain unauthorized.

## 18. Migration consequences

Current module-scope engines, UI acquisition sites, service-local engines, and other direct acquisitions are evidence inputs for the later Transaction Boundary Migration Seam Register.

This contract does not order immediate migration. Later migration must:

- preserve the nine required caller-connection functions unless an explicit compatibility decision changes them;
- preserve consumer-visible behavior;
- avoid mixed old/new ownership within one atomic unit;
- prevent dual acquisition during transition;
- define rollback for every migration wave;
- receive separate production and test write authority.

## 19. Prohibited interpretations

This contract SHALL NOT be interpreted to mean that:

- current code conforms merely because it uses context managers;
- `engine.connect()` owns a transaction commit;
- `engine.begin()` permits downstream services to commit early;
- a connection typed as `Any` may be any arbitrary object in production;
- `IF NOT EXISTS` DDL is safe to execute without migration authority;
- absence of explicit `close()` proves release correctness;
- a synthetic sentinel proves application runtime behavior;
- architecture-contract establishment authorizes code changes.

## 20. Contract result

- `FINAL_RESULT=APPROVED_FOR_ESTABLISHMENT`
- `contract=MA-2026-034-PHASE3-CONNECTION-ACQUISITION-RELEASE-OWNERSHIP-CONTRACT`
- `phase_3=OPEN`
- `connection_acquisition_owner=BOUNDED_COMPOSITION_REQUEST_JOB_OR_ORCHESTRATION_SCOPE`
- `connection_release_owner=THE_SCOPE_THAT_ACQUIRED_THE_CONNECTION`
- `caller_provided_connection=BORROWED_CAPABILITY`
- `consumer_acquisition_when_conn_supplied=PROHIBITED`
- `consumer_close_commit_rollback_dispose=PROHIBITED`
- `read_acquisition_mode=ENGINE_CONNECT`
- `transaction_acquisition_mode=ENGINE_BEGIN`
- `canonical_engine_disposal=AUTHORIZED_SHUTDOWN_COMPOSITION_ONLY`
- `caller_connection_compatibility=PRESERVE`
- `runtime_conformance=NOT_VERIFIED`
- `implementation_authorization=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=TRANSACTION_AND_UNIT_OF_WORK_BOUNDARY_CONTRACT`

## 21. Establishment rule

This contract shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment must include no production or test code, no application import, no test execution, no database or application-network execution, and no unrelated repository mutation.
