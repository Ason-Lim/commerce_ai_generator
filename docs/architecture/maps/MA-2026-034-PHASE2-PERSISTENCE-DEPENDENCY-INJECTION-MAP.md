# MA-2026-034 Phase 2 Persistence Dependency / Injection Map

## 1. Map identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Deliverable | `Persistence Dependency / Injection Map` |
| Governing configuration contract | `MA-2026-034-PHASE2-CONFIGURATION-AUTHORITY-CONTRACT` |
| Governing engine contract | `MA-2026-034-PHASE2-ENGINE-OWNERSHIP-LIFECYCLE-CONTRACT` |
| Governing HEAD | `7d49ac93bdcd90493ea12110a1a36ab1081d3c4d` |
| Map version | `v1.0` |
| Map date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This map decides how persistence authority may flow from process entry points to
consumers. It distinguishes ownership from possession and assigns an allowed
dependency form to each architectural boundary.

The map does not implement injection, change transaction semantics, alter public
service behavior, or authorize production and test writes. Every target rule is
`PROPOSED` until implemented and independently verified.

## 3. Governing decisions

The following decisions are already established as target architecture:

- `app.core.config` is the sole persistence-configuration authority;
- `app.db.database` is the sole SQLAlchemy engine lifecycle authority;
- the default is one canonical synchronous engine per process lifecycle;
- engine construction occurs only during explicit governed bootstrap;
- engine factory and pool policy belong only to `app.db.database`; and
- engine disposal belongs only to `app.db.database`.

This map may route those authorities but may not weaken or duplicate them.

## 4. Dependency capability model

The target architecture recognizes six persistence capabilities:

| Capability | Meaning | Permitted holder |
| --- | --- | --- |
| `ConfigurationResolver` | Resolves and validates one immutable configuration snapshot | `app.core.config` only |
| `EngineFactory` | Constructs the SQLAlchemy engine | `app.db.database` lifecycle authority only |
| `EngineLifecycle` | Initializes, publishes, state-gates, and disposes the canonical engine | Process composition root through `app.db.database` |
| `TransactionBoundary` | Opens and closes a connection or transaction scope using the canonical engine | Explicit process/application adapter |
| `Connection` | Executes persistence work inside one caller-owned scope | Store/repository or bounded service function |
| `PersistenceService` | Domain- or use-case-level query/command interface | Router, UI, handler, orchestration, and domain consumers |

Exact Python protocols and names are deferred. The capability separation is
authoritative.

## 5. Canonical dependency direction

The only permitted authority direction is:

```text
Process Composition Root
  -> app.core.config / ConfigurationResolver
  -> app.db.database / EngineLifecycle + EngineFactory
  -> TransactionBoundary
  -> Connection
  -> Store or Repository
  -> PersistenceService result
  -> Router, UI, Handler, or Orchestrator
```

Classification: `PROPOSED`.

Dependencies must not flow upward from a store to the engine factory, laterally from
a UI into a logger-owned engine, or indirectly through a utility module that happens
to expose an engine object.

## 6. Ownership versus possession

The map uses the following strict distinction:

- `app.core.config` owns configuration interpretation;
- `app.db.database` owns engine construction and lifecycle;
- a composition root may hold the lifecycle capability but does not become its
  owner;
- a transaction boundary may hold the canonical engine for the purpose of opening a
  bounded scope but may not construct, replace, tune, or dispose it;
- a store may hold a connection for one call or unit of work but may not retain it;
  and
- a UI, router, handler, or ordinary service may hold a higher-level persistence
  service but not an engine factory or raw configuration.

Possession never grants authority to create a second instance or bypass lifecycle
state checks.

## 7. Allowed injection forms by layer

| Layer | Default injected form | Prohibited forms |
| --- | --- | --- |
| Process composition root | `EngineLifecycle`, resolved configuration | Independent `create_engine`, inline env precedence |
| Transaction adapter | Canonical `Engine` or governed `TransactionBoundary` | `EngineFactory`, disposal authority, raw DB URL |
| Application orchestration | `PersistenceService` or `TransactionBoundary` | Module-global engine lookup, raw env access |
| Domain/service function | `PersistenceService` or caller-provided `Connection` | Engine construction, pool tuning |
| Store/repository | Caller-provided `Connection` | Engine construction, engine disposal, env access |
| Router/HTTP handler | Use-case or persistence service | Engine, connection, DB URL, engine factory |
| UI/presentation | Query/command service | Engine, connection, logger-owned infrastructure |
| Health/liveness | Redacted lifecycle-readiness view only | Engine creation, connection checkout, raw configuration |
| Unit test | Fake service, fake connection, or isolated lifecycle/factory | Unintended real engine factory or ambient DB fallback |

An exception requires an explicit row in a later established contract; convenience
or existing imports are not exceptions.

## 8. Canonical authority modules

| Module | Current evidence | Target dependency role |
| --- | --- | --- |
| `app.core.config` | Existing canonical `DATABASE_URL` route | Sole configuration resolver; no engine ownership |
| `app.db.database` | Broadly imported engine; unique explicit `pool_pre_ping=True` | Sole engine factory and lifecycle authority |
| `app.db.__init__` | Empty; no export contract | Must not become an accidental service locator |

The target map does not require a package-level global `engine` re-export. Any future
package surface must preserve lifecycle state gating and may not expose construction
authority.

## 9. FastAPI boundary

### Current evidence

`app.main` currently constructs an engine and statically reaches several other
constructor owners. The instrumented import graph reached five distinct engine
constructor identities. The repository defines a persistence-independent `/health`
handler, but router mounting was not established.

### Target map

| Component | Injected dependency | Authority rule |
| --- | --- | --- |
| FastAPI process bootstrap | configuration resolver and engine lifecycle | May initialize and shut down lifecycle; may not construct independently |
| Application/request composition | persistence services or transaction boundary | Binds dependencies after readiness |
| Routes and handlers | use-case services | No engine, connection, factory, or raw configuration |
| Liveness handler | no persistence dependency | Must remain side-effect free |
| Future readiness handler | redacted lifecycle-state view | Must not create or check out a connection without separate authority |

`app.main` must cease being an engine owner under later implementation authority.

## 10. Streamlit and administrative presentation boundaries

### Current evidence

- `app.ui.streamlit_app` imports `app.services.analytics_logger.engine`;
- the Streamlit module contains direct `engine.connect` and `engine.begin` usage;
- `app.ui.admin_dashboard` imports `app.db.database.engine`; and
- the administrative module contains multiple module-level query calls.

Classification: `VERIFIED` or `PARTIALLY_VERIFIED` within established static
boundaries.

### Target map

| Presentation boundary | Target injected form | Prohibition |
| --- | --- | --- |
| Streamlit UI | query/command services plus analytics event service | No logger engine import; no raw engine or connection ownership |
| Administrative dashboard | administrative query service | No global canonical-engine import; no module-level query side effect |

Streamlit reruns must reuse a process-governed dependency rather than reconstructing
an engine. Exact cache/session mechanics remain assigned to the Runtime Startup and
Shutdown Resource Map.

## 11. Logger boundaries

The analytics, context, and impression logger modules currently construct independent
engines. Analytics infrastructure is also exposed to presentation code.

Target roles:

| Logger | Target injected form | Target ownership |
| --- | --- | --- |
| Analytics logger | analytics persistence service or bounded transaction capability | none |
| Context logger | context persistence service or bounded transaction capability | none |
| Impression logger | impression persistence service or bounded transaction capability | none |

Logger APIs may remain convenient functional surfaces during migration, but their
implementation must receive a governed dependency from composition. They may not
resolve environment variables, call the engine factory, publish a raw engine, or
dispose the shared engine.

Logging failure policy is outside this map except that no logger may create a fallback
engine after dependency failure.

## 12. Collector and pipeline boundaries

### Current evidence

`app.services.market.collector` and `app.services.recommendation_pipeline` each
construct an engine. The Naver Shopping API collector reuses the existing canonical
engine by import. Standalone operational launch definitions remain unresolved.

### Target map

| Execution mode | Target dependency form |
| --- | --- |
| Embedded collector or pipeline | Receive transaction/persistence capability from host composition root |
| Standalone worker process | Its bootstrap initializes one canonical process lifecycle, then injects a transaction/persistence capability |
| Collector/pipeline inner function | Receive `Connection`, `TransactionBoundary`, or higher-level store/service according to unit-of-work needs |

Collector and pipeline modules may not construct, configure, tune, replace, or
dispose engines. Schema-adjustment operations observed in collectors remain
consumer-owned transaction behavior until a later contract explicitly changes them.

## 13. Generator and ordinary service boundaries

`app.services.generator_service` is statically able to reach multiple current
constructor owners. In the target architecture it is an orchestrator, not a
persistence authority.

Generator, recommendation, market-intelligence, preference, session-context, and
ordinary application services must receive one of:

- a use-case-specific `PersistenceService`;
- a bounded `TransactionBoundary`; or
- a caller-provided `Connection` where the existing contract already supports it.

They must not import a module-global engine as an implicit dependency. Domain scoring,
ranking, parser, provider, registry, and Cross-Border semantics remain protected and
outside this map.

## 14. Preference and Session Context preservation map

Wave 2 verified nine caller-provided `conn` consumers:

- three Preference service functions;
- two Preference store functions;
- two Session Context service functions; and
- two Session Context store functions.

The four store functions directly require `conn.execute`; the service wrappers
delegate without directly using the connection.

Target decision:

| Boundary | Disposition |
| --- | --- |
| Preference service/store connection parameter | Preserve |
| Session Context service/store connection parameter | Preserve |
| Execute-only fake connection compatibility | Preserve |
| Caller connection-scope ownership | Preserve until separately decided |
| Replacement with module-global engine | Prohibited |

This existing seam is the reference pattern for low-level store testability. It does
not require every higher-level service to expose a raw connection publicly.

## 15. Transaction boundary rules

The engine authority does not automatically become transaction authority.

Target rules:

1. the outermost function that defines one atomic unit of work selects read
   (`connect`) or transaction (`begin`) scope;
2. that boundary passes one connection to participating stores;
3. stores execute but do not commit, roll back, close, or retain caller-owned
   connections unless their existing explicit contract says otherwise;
4. nested services must reuse the supplied scope instead of opening an unrelated
   engine connection; and
5. engine disposal is never a transaction-cleanup mechanism.

Classification: `PROPOSED COMPATIBILITY TARGET`.

Exact unit-of-work locations require consumer-by-consumer verification during later
implementation planning. This map does not change existing transaction behavior.

## 16. Direct scripts and worker processes

A directly executable script or worker that performs persistence work is a process
composition root only for the lifetime of that process.

It must:

1. resolve configuration through `app.core.config`;
2. initialize `app.db.database` lifecycle exactly once;
3. inject a transaction or persistence service into the work function;
4. stop new work before shutdown;
5. dispose through the lifecycle authority; and
6. return a failure status without constructing a fallback engine if initialization
   fails.

The script must not pass raw environment mappings or URLs beyond the configuration
boundary.

## 17. Test dependency map

| Test scope | Preferred dependency form | Real-resource rule |
| --- | --- | --- |
| Pure service test | Fake `PersistenceService` | No engine factory available |
| Store unit test | Execute-capable fake `Connection` | No network-capable connection |
| Transaction adapter test | Recording fake engine/connection | No real factory binding |
| Lifecycle unit test | Injected recording/failing `EngineFactory` | Real factory fail-closed |
| Authorized integration test | Explicit isolated configuration and lifecycle | Requires separate integration authority |

Importing engine-owner modules during test collection must not construct an engine.
Ambient local defaults must not make a unit test silently connect to a real local
database.

Fixture scope and cleanup details remain assigned to the Test Configuration and
Substitution Contract.

## 18. Dependency lifetime map

| Dependency | Target lifetime |
| --- | --- |
| Resolved configuration snapshot | One process lifecycle; immutable |
| Canonical engine | One process lifecycle |
| Transaction boundary provider | Process/application adapter |
| Connection or transaction | One bounded unit of work |
| Persistence service | Request, callback, task, or explicit application scope |
| Store object, if any | Must not outlive dependencies it holds |
| Redacted readiness view | Read-only projection of current lifecycle state |

Longer-lived components may depend on shorter-lived capabilities only through an
explicit provider or factory that creates the bounded scope; they must not cache a
connection.

## 19. Import and lookup prohibitions

The target architecture prohibits:

- `from ... import engine` in ordinary consumers;
- importing an engine from a logger, collector, pipeline, UI, or utility module;
- calling `create_engine` outside `app.db.database`;
- reading persistence environment variables outside `app.core.config`;
- a mutable global service locator that allows arbitrary engine replacement;
- circular imports used to obtain persistence infrastructure;
- hidden fallback construction when injection is absent; and
- import-time query, transaction, or schema mutation.

A state-gated compatibility accessor may exist temporarily only if separately listed
in the Compatibility and Migration Seam Register. It must never construct implicitly.

## 20. Failure propagation

Missing injection must fail clearly at composition time. Consumers must not respond
by:

- importing a legacy global engine;
- resolving a URL independently;
- constructing a local engine;
- using a local default without explicit policy;
- suppressing lifecycle conflicts; or
- continuing with a partially initialized persistence service.

Failure messages may identify the missing capability and consumer boundary but must
not disclose raw configuration or engine representations.

## 21. Migration classes

| Migration class | Members | Intended seam |
| --- | --- | --- |
| `M1 — authority owner` | `app.core.config`, `app.db.database` | Implement canonical resolver and lifecycle first |
| `M2 — independent constructors` | `app.main`, three loggers, market collector, recommendation pipeline | Replace construction with injection |
| `M3 — presentation leaks` | Streamlit, admin dashboard | Introduce query/command and analytics service boundaries |
| `M4 — existing canonical importers` | Naver collector and 27 direct-import boundary | Replace global imports with state-gated composition or injected capability |
| `M5 — preserved connection seams` | Preference and Session Context | Keep caller-provided connection behavior |
| `M6 — tests` | Ten engine-owner import tests and fake connection tests | Establish isolated fixtures and no-real-resource guards |

These classes describe future migration surfaces. They are not an implementation
sequence authorization.

## 22. Verification obligations

Later implementation cannot be accepted until evidence establishes:

1. only `app.core.config` interprets accepted persistence environment variables;
2. only `app.db.database` calls the real engine factory and owns disposal;
3. ordinary consumers contain no direct engine import or fallback constructor in the
   authorized migrated boundary;
4. UI and routers receive higher-level services rather than engines or connections;
5. logger modules publish no raw engine;
6. embedded collectors and pipelines reuse their host process lifecycle;
7. standalone workers create only one governed process lifecycle;
8. Preference and Session Context caller-connection contracts still pass;
9. transaction boundaries pass one connection to participating stores;
10. no connection is cached beyond its unit of work;
11. health/liveness does not initialize or check out persistence resources;
12. unit tests fail closed against real database and network access; and
13. dependency absence cannot trigger hidden construction.

These are acceptance criteria, not write authority.

## 23. Explicit non-decisions

This map does not decide:

- exact protocol, class, function, parameter, or provider names;
- concrete files for new adapters or composition roots;
- detailed FastAPI dependency-provider syntax;
- Streamlit caching or session implementation;
- transaction migration for each of the 27 direct importers;
- active readiness probe behavior;
- fixture implementation and pytest hook details;
- adapter deprecation dates;
- rollback commit boundaries; or
- production implementation wave scope.

Those questions remain assigned to later Phase 2 deliverables.

## 24. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 2 state | `OPEN` |
| Dependency direction | `COMPOSITION_ROOT_TO_SERVICE_TO_CONNECTION_TO_STORE` |
| Engine factory exposure | `APP_DB_DATABASE_ONLY` |
| Raw engine in presentation | `PROHIBITED_TARGET_STATE` |
| Caller-provided connection seams | `PRESERVED` |
| Dependency / injection map | `DECIDED_AS_TARGET_ARCHITECTURE` |
| Current implementation conformance | `NOT_VERIFIED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this map, then author the Runtime Startup and Shutdown Resource Map |
