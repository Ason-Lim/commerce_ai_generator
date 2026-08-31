# MA-2026-034 Phase 2 Runtime Startup and Shutdown Resource Map

## 1. Map identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Deliverable | `Runtime Startup and Shutdown Resource Map` |
| Governing engine contract | `MA-2026-034-PHASE2-ENGINE-OWNERSHIP-LIFECYCLE-CONTRACT` |
| Governing dependency map | `MA-2026-034-PHASE2-PERSISTENCE-DEPENDENCY-INJECTION-MAP` |
| Governing HEAD | `6ead4ded577650b668faf680565349fbcccf264d` |
| Map version | `v1.0` |
| Map date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This map assigns persistence-resource startup, readiness, work-admission, shutdown,
and disposal responsibilities to each runtime entry-point class.

The repository's effective operational launch commands remain `UNRESOLVED`. The map
therefore defines target lifecycle obligations without claiming that current
deployment or execution already implements them.

This document authorizes no production, test, deployment, environment, or database
mutation.

## 3. Evidence boundary

The established evidence supports these current-state conclusions:

- seven module-scope engine constructors exist;
- several primary entry points statically reach multiple constructor owners;
- an instrumented `app.main` import reached five constructor identities;
- no exact detectable disposal, lifespan, startup, shutdown, or persistence `atexit`
  contract was established;
- no high-precision operational launch command was found in the bounded scope;
- 26 Python main guards establish local direct-execution surfaces but not deployment
  lifecycle definitions;
- Streamlit and admin contain database-capable module-level paths;
- the `/health` handler contains no detected persistence call; and
- its mounting and operational reachability remain unresolved.

The following target maps are `PROPOSED` until implemented and verified.

## 4. Runtime resource inventory

| Resource | Canonical owner | Target lifetime | Shutdown obligation |
| --- | --- | --- | --- |
| Configuration source mapping | Process composition root | Startup input only | Do not retain raw mapping beyond resolution need |
| Resolved configuration snapshot | `app.core.config` contract | One process lifecycle; immutable | Release reference; never log raw URL |
| Engine lifecycle state | `app.db.database` | One process lifecycle | Transition through `DISPOSING` to `DISPOSED` |
| Canonical SQLAlchemy engine and pool | `app.db.database` | One process lifecycle | Dispose exactly once |
| Transaction boundary provider | Application/process adapter | Application lifecycle | Reject new scopes after quiesce begins |
| Connection or transaction | Caller-defined unit of work | Bounded work scope | Close/exit before engine disposal |
| Persistence services | Composition root/application scope | Request, callback, task, or application scope | Stop admission and release dependencies |
| Redacted readiness projection | Lifecycle authority view | Process lifecycle | Report non-ready after quiesce begins |

Ownership remains governed by the configuration, engine, and dependency contracts.

## 5. Canonical startup sequence

Every persistence-capable process must follow this logical order:

```text
S0  Process entry begins
S1  Bind explicit execution policy and configuration source
S2  Resolve and validate immutable persistence configuration
S3  Create the process-local engine lifecycle container
S4  Construct exactly one canonical engine through app.db.database
S5  Publish READY only after atomic lifecycle publication
S6  Compose transaction boundaries and persistence services
S7  Begin accepting persistence-dependent work
```

Classification: `PROPOSED`.

Required invariants:

- imports may occur before `S1` only if they do not resolve configuration, construct
  engines, open connections, execute queries, or mutate schema/data;
- no persistence-dependent work may be accepted before `S5` and `S6` complete;
- failed configuration or construction must prevent `S7`;
- engine construction is not itself proof of connectivity; and
- a later readiness policy must distinguish lifecycle readiness from database
  connectivity if both are required.

## 6. Canonical shutdown sequence

Every graceful persistence-capable process must follow this logical order:

```text
D0  Shutdown or quiesce requested
D1  Mark readiness non-ready and stop admitting new persistence work
D2  Wait for, cancel, or bound in-flight work under entry-point policy
D3  Close or exit active connection and transaction scopes
D4  Release persistence services and transaction providers
D5  Invoke app.db.database disposal exactly once
D6  Publish DISPOSED and complete process shutdown
```

Classification: `PROPOSED`.

The engine must not be disposed before active governed scopes complete or are
explicitly cancelled. New acquisition must fail after `D1`. Consumer modules may not
dispose the shared engine during `D2` or `D3`.

## 7. Startup failure map

| Failure point | Required state | Required behavior |
| --- | --- | --- |
| Configuration missing/conflicting/invalid | No engine | Fail before construction; redact values |
| Lifecycle container creation | No published engine | Fail process bootstrap |
| Engine construction | `FAILED` | Publish no partial engine; dispose unpublished engine if safely created |
| Service composition | Not work-ready | Dispose initialized engine before bootstrap exits |
| Entry-point registration | Not work-ready | Tear down composed resources in reverse order |

No failure permits fallback to a module-owned engine, a different environment route,
an implicit local default, or unbounded automatic retry.

## 8. Shutdown trigger map

| Trigger class | Target lifecycle response |
| --- | --- |
| Framework graceful shutdown | Run `D0–D6` through framework lifecycle integration |
| Worker completion | Stop new work and dispose after the final unit of work |
| Controlled script completion | Dispose in a guaranteed outer cleanup boundary |
| Initialization failure after engine creation | Reverse initialized resources and dispose |
| Test teardown | Dispose isolated test lifecycle and assert cleanup |
| Process interrupt handled by runner | Begin bounded graceful shutdown when execution model permits |
| Forced kill, interpreter crash, host loss | No guaranteed Python cleanup; rely on OS/database recovery |

This map does not claim that every external process manager delivers a catchable
signal or sufficient shutdown time.

## 9. FastAPI runtime map

### Current classification

- `app.main` exists as a FastAPI application owner;
- `app.main` currently constructs an engine;
- no repository-defined lifespan/startup/shutdown persistence contract was found;
- the defined `/health` router is not statically established as mounted; and
- explicit operational launch commands remain unresolved.

### Target lifecycle

| Phase | FastAPI obligation |
| --- | --- |
| Import | Define application structure only; no persistence initialization |
| Lifespan startup | Perform `S1–S6` once per worker process |
| Ready | Admit persistence-dependent requests only after service composition |
| Quiesce | Mark readiness non-ready before rejecting or draining new work |
| Lifespan shutdown | Perform `D2–D6` once per worker process |

Each server worker is a separate process lifecycle and therefore owns one canonical
engine through `app.db.database`. Preload or parent-process imports must not construct
the engine before worker creation.

Exact FastAPI dependency-provider and lifespan syntax is deferred to implementation
planning.

## 10. Streamlit runtime map

### Current classification

Streamlit imports a logger-owned engine and contains database-capable module-level
paths. Its safe runtime topology was not observed.

### Target lifecycle

| Event | Streamlit obligation |
| --- | --- |
| Module import | No engine construction or query |
| First governed app execution in process | Initialize or obtain one process-scoped lifecycle container |
| Script rerun | Reuse the same ready engine; never construct per rerun |
| User interaction | Receive query/command and analytics services, not raw engine ownership |
| Process shutdown | Dispose once if the runner exposes a reliable process-lifecycle hook |

If the Streamlit runner cannot guarantee a shutdown hook, implementation must record
that limitation and still prevent rerun-driven duplication. It must not introduce
session-scoped engines as a substitute for process-scoped lifecycle ownership.

Exact cache-resource or runner integration is deferred.

## 11. Administrative dashboard runtime map

### Current classification

The admin dashboard imports the canonical engine and contains multiple module-level
query paths. Safe runtime behavior was not observed.

### Target lifecycle

- module import defines presentation and query functions only;
- the dashboard composition root obtains an administrative query service after the
  engine lifecycle reaches `READY`;
- queries execute only through bounded connection/transaction scopes;
- refresh or rerender does not construct another engine; and
- process shutdown follows `D0–D6` when supported by the runner.

Module-level database reads are prohibited in the target state.

## 12. Generator service runtime map

The generator service may execute embedded in another application process or through
a standalone process boundary.

| Mode | Startup owner | Dependency rule | Shutdown owner |
| --- | --- | --- | --- |
| Embedded | Host composition root | Receive persistence services; no lifecycle ownership | Host process |
| Standalone | Generator process composition root | Perform `S1–S7` once | Generator process performs `D0–D6` |

The service module itself must not infer which mode applies by constructing an engine
on import. The caller must select the mode explicitly.

## 13. Recommendation pipeline runtime map

| Mode | Startup behavior | Work behavior | Shutdown behavior |
| --- | --- | --- | --- |
| Embedded pipeline | Reuse host lifecycle | Receive transaction/persistence capability | Host disposes |
| Standalone batch/worker | Initialize one process lifecycle | Reuse engine across bounded work items | Stop admission, close scopes, dispose once |
| One-shot direct execution | Initialize in outer runner | Run one bounded unit | Dispose in outer cleanup boundary |

The pipeline must not retain its current independent constructor ownership in the
target state. Failure to receive a dependency must fail; it must not construct a
fallback engine.

## 14. Market collector runtime map

| Mode | Startup behavior | Work behavior | Shutdown behavior |
| --- | --- | --- | --- |
| Embedded collector | Host supplies persistence capability | Reuse host transaction policy | Host disposes |
| Scheduled/worker process | Initialize once per worker process | Reuse engine across collection items; bound transactions | Drain/cancel work, close scopes, dispose once |
| One-shot script | Outer runner initializes | Execute bounded collection | Outer runner disposes in cleanup |

Collector schema-adjustment and data-write operations remain governed by existing
consumer transaction behavior and later implementation authority. This map does not
authorize their execution.

## 15. Logger resource map

Analytics, context, and impression loggers are consumers, not runtime roots.

They must:

- receive an analytics/context/impression persistence service or bounded transaction
  capability from the host composition root;
- stop accepting events when the host enters quiesce;
- complete, reject, or explicitly drop queued work according to a later logging
  policy before engine disposal; and
- never construct, replace, or dispose an engine.

This map does not decide buffering, durability, retry, or event-loss policy. It only
requires that any such policy complete before `D5` or explicitly report abandonment.

## 16. Direct scripts and main-guard map

Wave 2 found 26 Python main guards and one tracked `.py` file containing non-Python
shell content. A main guard establishes a possible direct-execution surface but not a
production launch definition.

Every persistence-capable direct runner must use this outer shape:

```text
enter process lifecycle
  resolve configuration
  initialize engine lifecycle
  compose work dependency
  run bounded work
finally
  stop new work
  close active scopes
  dispose lifecycle once
```

Non-persistence scripts do not need an engine lifecycle and must not initialize one
preemptively.

## 17. Liveness and readiness resource map

### Liveness

Basic liveness reports whether the application process can answer. It must not:

- read database configuration;
- initialize the engine;
- check out a connection;
- execute SQL;
- expose pool or URL state; or
- change lifecycle state.

### Readiness

A future readiness projection may expose only redacted lifecycle information:

| Lifecycle state | Readiness projection |
| --- | --- |
| `UNINITIALIZED`, `INITIALIZING` | not ready |
| `READY` | lifecycle ready; connectivity not implied |
| `DISPOSING`, `DISPOSED`, `FAILED` | not ready |

An active database probe is not authorized by this map. If later required, it must
have a bounded timeout, no mutation, redacted failure, and separate authority.

The current `/health` handler's persistence-independent body is compatible with the
liveness target, but its mounting and runtime reachability are not established.

## 18. Work-admission and drain contract

Each entry-point adapter must maintain a work-admission boundary distinct from engine
availability.

Target rules:

1. admission opens only after lifecycle `READY` and service composition;
2. shutdown closes admission before waiting for in-flight work;
3. no new connection or transaction may start after admission closes;
4. in-flight work receives a bounded drain or cancellation policy appropriate to the
   entry point;
5. all connection scopes end before engine disposal; and
6. readiness changes to non-ready no later than admission closure.

Drain timeout values are deployment decisions and are not selected here.

## 19. Connection and transaction cleanup map

| Scope result | Required cleanup |
| --- | --- |
| Successful read scope | Exit/close connection context |
| Successful transaction | Exit context and apply existing commit semantics |
| Failed transaction | Exit context and apply existing rollback semantics |
| Cancelled work | Exit or cancel scope before disposal |
| Shutdown timeout | Record bounded failure; do not open replacement scopes |

The engine authority must not reach into consumers to commit or roll back their
transactions. Consumers must not use engine disposal as a substitute for scope
cleanup.

## 20. Repeated startup and shutdown

- identical repeated startup requests in `READY` reuse the published engine;
- different configuration or policy requests in `READY` fail closed;
- concurrent startup converges on one initialization;
- repeated shutdown is idempotent and invokes disposal no more than once;
- shutdown before initialization is a safe no-op; and
- the same disposed lifecycle container cannot restart.

Framework reloaders and development hot reloads create new process lifecycles; they
must not mutate a disposed container in place.

## 21. Observability boundary

Permitted runtime lifecycle observations are:

- lifecycle state;
- non-secret stable process/worker identity when required;
- whether initialization, readiness, quiesce, and disposal completed;
- stable redacted error code; and
- counts of active governed scopes if implemented without leaking query or user data.

Prohibited observations include raw URLs, credentials, connection representations,
SQL parameters, secrets, and full exception representations that contain them.

Logging the Python `Engine`, pool, URL, or configuration object directly is not a
valid redaction strategy.

## 22. Test lifecycle map

| Test class | Startup | Shutdown |
| --- | --- | --- |
| Resolver unit test | No engine lifecycle | None |
| Engine lifecycle unit test | Inject recording/failing factory | Assert exactly one fake disposal |
| Store unit test | Supply fake connection | End fake scope; no engine |
| Service unit test | Supply fake persistence service | Release test-local service |
| Entry-point lifecycle test | Use sentinel lifecycle and blocked real I/O | Assert order `S0–S7` and `D0–D6` |
| Authorized integration test | Explicit isolated configuration | Close scopes and dispose isolated engine |

Unit and entry-point tests must fail closed if the real engine factory, network, DNS,
or ambient local database becomes reachable unexpectedly.

## 23. Runtime verification obligations

Later implementation cannot be accepted until evidence establishes:

1. imports perform no configuration resolution, engine construction, connection
   checkout, query, or persistence mutation in the migrated boundary;
2. each process entry point initializes at most one engine lifecycle;
3. work admission remains closed until lifecycle and service composition are ready;
4. startup failure prevents work admission and cleans initialized resources;
5. quiesce closes admission before disposal;
6. active scopes end before disposal;
7. disposal occurs exactly once on every controllable graceful path;
8. embedded pipeline, collector, generator, and logger paths reuse host resources;
9. standalone paths own and close exactly one process lifecycle;
10. Streamlit reruns and dashboard refreshes do not duplicate engines;
11. liveness performs no persistence operation;
12. readiness reveals no secret and does not imply unverified connectivity; and
13. forced-termination limitations are documented rather than mislabeled as graceful
    cleanup guarantees.

These are acceptance criteria, not implementation authority.

## 24. Explicit non-decisions

This map does not decide:

- actual production launch commands or process-manager definitions;
- exact FastAPI lifespan code;
- Streamlit cache or shutdown-hook implementation;
- admin runner integration;
- signal numbers, drain timeouts, or retry budgets;
- active database readiness probing;
- logger buffering and loss policy;
- concrete dependency-provider names;
- test fixture implementation;
- deployment environment or secret storage; or
- production migration sequence.

Those questions remain assigned to later Phase 2 deliverables or later implementation
authority.

## 25. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 2 state | `OPEN` |
| Canonical startup order | `RESOLVE_CONFIG_THEN_INITIALIZE_THEN_COMPOSE_THEN_ADMIT` |
| Canonical shutdown order | `QUIESCE_THEN_DRAIN_THEN_CLOSE_SCOPES_THEN_DISPOSE` |
| Liveness persistence access | `PROHIBITED` |
| Active readiness probe | `NOT_AUTHORIZED` |
| Runtime resource map | `DECIDED_AS_TARGET_ARCHITECTURE` |
| Current runtime conformance | `NOT_VERIFIED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this map, then author the Test Configuration and Substitution Contract |
