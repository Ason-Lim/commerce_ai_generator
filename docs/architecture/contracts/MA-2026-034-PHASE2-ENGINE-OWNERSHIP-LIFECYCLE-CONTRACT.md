# MA-2026-034 Phase 2 Engine Ownership and Lifecycle Contract

## 1. Contract identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Deliverable | `Engine Ownership and Lifecycle Contract` |
| Governing authorization | `ADA-MA-2026-034-PHASE2-CONFIGURATION-ENGINE-AUTHORITY-CONTRACT` |
| Governing configuration contract | `MA-2026-034-PHASE2-CONFIGURATION-AUTHORITY-CONTRACT` |
| Governing HEAD | `7ced05954b211aea63c3446cefe8cb08d17eb51b` |
| Contract version | `v1.0` |
| Contract date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This contract selects the target SQLAlchemy engine authority and defines engine
construction, identity, reuse, pooling, failure, disposal, and repeated-lifecycle
semantics for each persistence-capable process.

It is a target architecture contract. It does not alter `app/**`, `tests/**`,
dependencies, deployment configuration, environment values, database schema, or
database data. Current implementation conformance remains unverified.

## 3. Evidence basis

The governing evidence establishes the following current-state facts:

1. seven tracked modules construct SQLAlchemy engines at module scope;
2. `app.db.database.engine` is directly imported by 27 tracked files;
3. `app.db.database` is the only observed constructor owner that explicitly supplies
   `pool_pre_ping=True`;
4. five distinct constructor identities were reached by the instrumented `app.main`
   import graph;
5. primary static entry points can reach multiple constructor owners;
6. no declared engine disposal, FastAPI lifespan, startup/shutdown cleanup, or
   persistence `atexit` contract was found;
7. ten tests import modules that currently own engines; and
8. Preference and Session Context boundaries already accept caller-provided
   connections.

These facts are `VERIFIED` or `PARTIALLY_VERIFIED` within their established
boundaries. Every future-state rule below is `PROPOSED` until implemented and
independently verified.

## 4. Canonical engine authority decision

### 4.1 Authority owner

`app.db.database` is selected as the sole canonical SQLAlchemy engine lifecycle
authority.

Classification: `PROPOSED`.

The authority owns:

- acceptance of a validated immutable configuration snapshot from `app.core.config`;
- engine construction through an injected or governed SQLAlchemy engine factory;
- the process-local canonical engine identity;
- pool-option selection and application;
- readiness-state publication without secret disclosure;
- engine disposal; and
- lifecycle-state enforcement.

Selection of this module is based on its broad current adoption, existing database
boundary, and unique observed `pool_pre_ping=True` policy. Adoption count alone does
not create authority; this established contract does.

### 4.2 Prohibited owners

In the target architecture, the following modules and module classes may consume a
governed engine, connection, or persistence service but may not construct or own a
SQLAlchemy engine:

- `app.main`;
- analytics, context, and impression loggers;
- market collectors;
- the recommendation pipeline;
- Streamlit and administrative presentation modules;
- generator services;
- domain services, stores, routers, health handlers, scripts, and utilities; and
- tests, except through an explicitly supplied test engine factory governed by the
  later test contract.

Utility-module import must never confer engine ownership.

## 5. Process-local multiplicity contract

### 5.1 Default rule

Each operating-system process may own exactly one canonical synchronous SQLAlchemy
engine for one resolved persistence configuration snapshot.

Classification: `PROPOSED`.

Threads, request handlers, tasks, services, collectors, and UI callbacks inside the
same process must reuse that process-local engine. They may acquire distinct
connections or transactions from it under later dependency and transaction rules.

### 5.2 Exceptional multiple-engine rule

Multiple engines in one process are prohibited by default. An exception requires all
of the following:

1. a separately documented database role that cannot use the canonical engine;
2. an explicit engine key and configuration authority;
3. independent lifecycle and disposal ownership;
4. proof that accidental duplication is impossible;
5. test-isolation coverage; and
6. a separately established architecture decision.

Existing distributed constructors are current-state migration subjects, not
grandfathered exceptions.

## 6. Engine type and factory contract

The Phase 2 target is the synchronous SQLAlchemy `Engine` produced by the governed
equivalent of `sqlalchemy.create_engine`.

Classification: `PROPOSED`.

An asynchronous engine, alternate ORM engine, direct driver pool, or second factory
is outside this contract and requires separate authority.

The lifecycle authority must accept the construction mechanism through a seam that
allows tests to supply a non-networking factory. Production code may bind the real
factory only during authorized bootstrap. Consumers must not receive the factory.

Engine construction and database connectivity are separate states. Successful
construction must not be reported as successful connectivity or readiness unless a
separately governed operation establishes that fact.

## 7. Construction timing contract

Engine construction must occur only after:

1. an authorized process bootstrap has begun;
2. `app.core.config` has returned one validated immutable configuration snapshot;
3. the lifecycle authority is in `UNINITIALIZED`; and
4. the governed engine factory and pool policy have been selected.

Engine construction must not occur:

- at module import time;
- from a route decorator or route import;
- from logger, collector, pipeline, UI, admin, service, store, or utility import;
- on first health-check request;
- as a side effect of reading a configuration value; or
- during test collection without an explicit test bootstrap.

Classification: `PROPOSED`.

Lazy connection checkout by SQLAlchemy does not make module-scope engine construction
acceptable. The governed event is engine-object construction, not only the first
socket connection.

## 8. Lifecycle state machine

The canonical process-local authority must enforce the following semantic states:

```text
UNINITIALIZED
  -> INITIALIZING
  -> READY
  -> DISPOSING
  -> DISPOSED

INITIALIZING -> FAILED
READY        -> FAILED only when the authority explicitly invalidates the engine
DISPOSING    -> FAILED only when disposal reports a non-recoverable lifecycle error
```

Classification: `PROPOSED`.

Required state semantics:

| State | Meaning |
| --- | --- |
| `UNINITIALIZED` | No engine has been constructed or published |
| `INITIALIZING` | One construction attempt owns the transition; consumers cannot acquire the engine |
| `READY` | Exactly one canonical engine identity is published for reuse |
| `DISPOSING` | New acquisition is blocked while the owner disposes resources |
| `DISPOSED` | The lifecycle is closed; the disposed engine cannot be reacquired |
| `FAILED` | No usable engine may be published or returned |

Exact implementation types and synchronization primitives are deferred. The state
semantics are mandatory.

## 9. Initialization and reuse contract

### 9.1 First initialization

The transition from `UNINITIALIZED` to `READY` must be atomic from the perspective of
consumers. A partially constructed engine must never be observable.

### 9.2 Repeated initialization

When the authority is `READY`:

- a repeated initialization request carrying the identical configuration identity
  and identical engine policy must return or confirm the existing engine identity;
- it must not construct a second engine; and
- a request carrying a different configuration identity or engine policy must fail
  closed as a lifecycle conflict.

The comparison must use a non-secret stable identity or fingerprint. Raw database
URLs must not be logged or embedded in errors.

### 9.3 Access before and after readiness

Engine acquisition while `UNINITIALIZED`, `INITIALIZING`, `DISPOSING`, `DISPOSED`, or
`FAILED` must fail with a machine-classifiable lifecycle error. It must not trigger
implicit initialization or fallback construction.

## 10. Pool policy authority

`app.db.database` is the sole owner of SQLAlchemy pool policy.

The initial target baseline requires:

```text
pool_pre_ping = True
```

Classification: `PROPOSED`, grounded in the sole explicit current constructor policy.

All additional pool settings—including pool class, size, overflow, timeout, recycle,
reset behavior, logging, and connection arguments—must be selected by the canonical
engine authority or a later explicit contract. Consumers may not override them.

No implicit production tuning value is decided by this document. Defaults not
explicitly selected remain SQLAlchemy defaults and must be recorded during later
implementation verification.

`pool_pre_ping=True` does not authorize startup connectivity checks and does not prove
database readiness. It governs validation when pooled connections are checked out.

## 11. Connection and transaction boundary

The engine authority owns the engine and its pool. It does not automatically own
every connection or transaction.

The following current compatibility rule is preserved:

- Preference and Session Context service/store boundaries may continue receiving a
  caller-provided execute-capable connection;
- consumer-owned `engine.connect()` and `engine.begin()` behavior is not changed by
  this document; and
- transaction authority remains subject to the Persistence Dependency / Injection
  Map and later migration contracts.

Classification: `PROPOSED COMPATIBILITY PRESERVATION` based on `VERIFIED` seams.

No consumer may retain a connection beyond its authorized scope merely because the
engine is process-local.

## 12. Disposal ownership and ordering

`app.db.database` is the sole owner authorized to dispose the canonical engine.

Classification: `PROPOSED`.

Required shutdown order:

1. the process entry point stops admitting new persistence work;
2. in-flight governed work is allowed to complete or is cancelled by a later runtime
   contract;
3. engine acquisition is blocked;
4. the lifecycle authority invokes engine disposal exactly once;
5. the engine reference is no longer published; and
6. lifecycle state becomes `DISPOSED` if disposal completes.

Consumers, loggers, stores, routes, UI callbacks, collectors, and tests must not
dispose the shared production engine directly.

Process termination outside a graceful shutdown path cannot be made reliable by this
contract. Later runtime mapping must identify which entry points can guarantee the
ordering.

## 13. Disposal idempotency and reinitialization

Repeated disposal requests while `DISPOSING` or after `DISPOSED` must not invoke
engine disposal a second time. They must return an idempotent already-disposing or
already-disposed result.

Disposal before initialization must be a safe no-op that records no engine disposal.

After `DISPOSED`, the same lifecycle authority instance must not construct a new
engine. A new process lifecycle or a newly created explicit lifecycle container is
required. Hot replacement and in-process configuration rotation are not authorized.

Classification: `PROPOSED`.

## 14. Construction and lifecycle failure behavior

If configuration acceptance, engine construction, state publication, or disposal
fails:

- no partial engine may be returned;
- no alternate constructor owner may take over;
- no legacy environment-variable route may be retried independently;
- no automatic infinite or unbounded retry may occur;
- the failure must be machine-classifiable without disclosing the URL or credentials;
- any locally created but unpublished engine must be disposed when safe; and
- the lifecycle must enter `FAILED` unless the operation was an idempotent no-op.

An explicit new bootstrap attempt may be authorized only after the failed lifecycle
container is abandoned and the cause is externally addressed. Ordinary consumers
must never trigger recovery by access.

## 15. Concurrency contract

Initialization, acquisition, and disposal must be safe under concurrent access.

At minimum:

- only one caller may own `UNINITIALIZED -> INITIALIZING`;
- concurrent identical initialization requests must converge on one engine identity;
- disposal cannot race with publication of a new engine;
- acquisition cannot succeed after disposal begins; and
- a different-configuration initialization request cannot replace a ready engine.

The implementation synchronization mechanism is not decided here. Verification must
demonstrate the semantic invariants without relying on timing luck.

## 16. Entry-point lifecycle obligations

Every persistence-capable process entry point must explicitly bind the canonical
lifecycle:

| Entry-point class | Required target behavior |
| --- | --- |
| FastAPI | initialize through governed startup/lifespan; dispose during governed shutdown |
| Streamlit | reuse one process/session-runtime authority; avoid rerun-driven duplicate construction |
| Administrative dashboard | initialize explicitly before queries; dispose under its process lifecycle |
| Generator service | receive governed engine or dependency; do not construct one through imports |
| Recommendation pipeline | receive governed dependency for embedded or standalone execution |
| Market collector | initialize once per worker process; dispose at worker shutdown |
| Direct scripts/workers | wrap work in one explicit lifecycle container |
| Tests | use an isolated lifecycle with a supplied non-real factory unless integration authority says otherwise |

These are target obligations. Wave 2 did not establish current operational launch
definitions, so actual hook locations remain assigned to the Runtime Startup and
Shutdown Resource Map.

## 17. Health and readiness interaction

A health or readiness handler must not:

- initialize the engine;
- acquire a database connection merely to answer liveness;
- read raw persistence environment variables;
- expose engine, pool, URL, credential, or exception representations; or
- dispose or replace the engine.

Basic liveness must remain persistence-independent. A separately defined readiness
surface may read a redacted lifecycle state such as `UNINITIALIZED`, `READY`, or
`FAILED`, but any active connectivity probe requires explicit later authority.

The currently defined `/health` handler has no detected persistence calls, but its
mounting and operational reachability remain unresolved.

## 18. Test substitution requirements

Later implementation must provide an engine-lifecycle test seam that proves behavior
without real database, network, DNS, or file access.

Required test capabilities include:

- injecting a recording or failing engine factory;
- asserting exactly one construction for concurrent or repeated identical
  initialization;
- asserting conflict on different configuration identity;
- asserting no construction during module import or ordinary acquisition;
- asserting no acquisition before readiness or after disposal begins;
- asserting exactly one disposal;
- asserting safe disposal before initialization;
- asserting no reinitialization after `DISPOSED`;
- asserting redacted failures; and
- preserving execute-only fake connection compatibility at existing store tests.

The later Test Configuration and Substitution Contract must define fixture scope,
cleanup, and fail-closed protection against accidentally binding the real factory.

## 19. Migration disposition

| Current owner or behavior | Target disposition |
| --- | --- |
| `app.db.database` constructor | Retain module as authority; migrate construction to governed bootstrap timing |
| `app.main` constructor | Remove ownership under later implementation authority |
| analytics logger constructor | Replace with injected governed dependency |
| context logger constructor | Replace with injected governed dependency |
| impression logger constructor | Replace with injected governed dependency |
| market collector constructor | Replace with process-lifecycle governed dependency |
| recommendation pipeline constructor | Replace with embedded/standalone governed dependency |
| UI import of analytics logger engine | Remove boundary leak through later dependency migration |
| Module-scope engine creation | Prohibit in target state |
| Missing disposal contract | Replace with canonical owner and explicit lifecycle |

The sequence, adapters, rollback units, and temporary compatibility surfaces remain
assigned to the Compatibility and Migration Seam Register. This contract does not
authorize any migration edit.

## 20. Verification obligations

Later implementation cannot be accepted until evidence establishes:

1. `app.db.database` is the only engine factory caller in the authorized target
   boundary;
2. importing migrated modules constructs no engine;
3. each process lifecycle publishes at most one canonical engine identity;
4. repeated identical initialization reuses that identity;
5. differing initialization fails without replacement;
6. `pool_pre_ping=True` is applied by the canonical owner;
7. consumers cannot override pool policy;
8. engine acquisition is state-gated;
9. graceful shutdown invokes disposal exactly once;
10. acquisition after disposal begins fails;
11. lifecycle failures disclose no secret-bearing values;
12. unit tests cannot reach a real database or network accidentally; and
13. caller-provided connection compatibility remains valid where preservation is
    required.

These obligations are acceptance criteria, not production or test write authority.

## 21. Explicit non-decisions

This contract does not decide:

- exact implementation class, function, or synchronization names;
- consumer-by-consumer engine, connection, or service injection form;
- transaction ownership migration;
- concrete startup/shutdown hook locations;
- Streamlit rerun implementation mechanics;
- active database readiness probes;
- deployment process commands;
- asynchronous engine support;
- multi-database exceptions;
- pool size, overflow, timeout, recycle, or pool class; or
- migration order and adapter removal dates.

These questions remain assigned to later Phase 2 deliverables or separate decisions.

## 22. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 2 state | `OPEN` |
| Canonical configuration authority | `app.core.config` |
| Canonical engine authority | `app.db.database` — `PROPOSED TARGET CONTRACT` |
| Default engine multiplicity | `ONE_PER_PROCESS_LIFECYCLE` |
| Construction timing | `EXPLICIT_BOOTSTRAP_ONLY` |
| Pool-policy authority | `app.db.database` |
| Disposal authority | `app.db.database` |
| Engine contract | `DECIDED_AS_TARGET_ARCHITECTURE` |
| Current implementation conformance | `NOT_VERIFIED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this contract, then author the Persistence Dependency / Injection Map |
