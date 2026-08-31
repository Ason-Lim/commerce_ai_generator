# MA-2026-034 Phase 2 Test Configuration and Substitution Contract

## 1. Contract identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Deliverable | `Test Configuration and Substitution Contract` |
| Governing dependency map | `MA-2026-034-PHASE2-PERSISTENCE-DEPENDENCY-INJECTION-MAP` |
| Governing runtime map | `MA-2026-034-PHASE2-RUNTIME-STARTUP-SHUTDOWN-RESOURCE-MAP` |
| Governing HEAD | `748da3efce1c53f515b91aa66038583293728432` |
| Contract version | `v1.0` |
| Contract date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This contract defines how tests substitute persistence configuration, engine
construction, lifecycle, services, connections, and cleanup while failing closed
against unintended real database and network access.

It is a target architecture contract. It does not create fixtures, edit tests,
change pytest configuration, contact a database, mutate environment values, or grant
integration-test authority.

## 3. Evidence basis

The established repository evidence shows:

- `pytest.ini` defines `pythonpath = .` and `testpaths = tests`;
- no `conftest.py` was found in the inspected boundary;
- 21 detected fixtures were unrelated to persistence;
- no test `create_engine` call was detected within the AST boundary;
- no direct test reference to `DATABASE_URL`, `COMMERCE_DB_URL`, or `FRUIT_DB_URL`
  was detected in the Phase 1 text boundary;
- ten tests directly import an established engine-owner module or symbol;
- no module-scope call was detected in those ten importing test modules, but imported
  owners currently construct engines at module scope;
- one execute-only `_FakeConnection` exists in the Preference store test; and
- nine Preference and Session Context functions accept caller-provided connections.

The repository-wide test substitution contract was therefore previously
`UNRESOLVED`. Rules below are `PROPOSED` until implemented and verified.

## 4. Default test safety decision

The default for every unit, contract, parser, scoring, registry, provider, service,
store, UI-boundary, and entry-point test is:

```text
REAL_DATABASE_ACCESS = DENIED
REAL_NETWORK_ACCESS  = DENIED
AMBIENT_LOCAL_DB     = DENIED
IMPLICIT_DB_DEFAULT  = DENIED
```

Classification: `PROPOSED`.

A test that does not explicitly qualify for the integration boundary must fail before
real engine construction, DNS lookup, socket creation, connection checkout, SQL
execution, or schema/data mutation.

The presence of a reachable local PostgreSQL instance is never permission to use it.

## 5. Test classes and allowed substitutions

| Test class | Configuration seam | Persistence seam | Real resources |
| --- | --- | --- | --- |
| Pure unit test | None or explicit mapping | Fake service/value | Denied |
| Resolver unit test | Explicit mapping | No engine | Denied |
| Engine lifecycle unit test | Validated synthetic snapshot | Recording/failing fake factory | Denied |
| Store unit test | None | Fake execute-capable connection | Denied |
| Service unit test | None or synthetic context | Fake service/connection | Denied |
| Transaction adapter test | Synthetic snapshot | Recording fake engine/connection | Denied |
| Entry-point lifecycle test | Synthetic mapping | Sentinel lifecycle with blocked I/O | Denied |
| Explicit persistence integration test | Isolated explicit configuration | Real isolated lifecycle | Conditionally allowed by separate authority |

Test names, locations, or imports do not automatically promote a test to integration
status.

## 6. Canonical configuration substitution

Tests must exercise `app.core.config` through an explicit caller-provided mapping.
Ambient `os.environ` mutation must not be the only supported seam.

Required mapping cases:

1. all accepted variables absent;
2. empty value;
3. whitespace-only value;
4. only `DATABASE_URL` present;
5. only `COMMERCE_DB_URL` present;
6. only `FRUIT_DB_URL` present;
7. duplicate equal values;
8. conflicting distinct values;
9. malformed URL;
10. unsupported dialect or driver;
11. prohibited placeholder/control character; and
12. explicitly permitted local-development default versus denied implicit default.

The mapping and resolved object must be test-local and immutable from the perspective
of the subject under test.

If an environment mutation is necessary for a compatibility test, it must be scoped,
restored automatically, and isolated from concurrent tests. It must not contain a
production credential.

## 7. Engine factory substitution

`app.db.database` must accept a governed test factory seam. The default unit-test
binding is a recording, stub, or failing factory that cannot perform network or DNS
access.

The test factory must support evidence for:

- constructor call count;
- redacted configuration identity received;
- pool-policy options, including `pool_pre_ping=True`;
- returned fake engine identity;
- controlled construction failure;
- disposal call count; and
- acquisition attempts before or after allowed lifecycle states.

The real `sqlalchemy.create_engine` binding must not be reachable accidentally in a
unit-test process.

Supplying a fake factory grants no permission to weaken the production authority
that only `app.db.database` owns factory invocation.

## 8. Connection and store substitution

The existing execute-only `_FakeConnection` behavior is a protected compatibility
seam for the Preference store boundary.

Target rules:

- store unit tests receive the narrowest connection protocol required by the store;
- a fake must implement only methods exercised by the test boundary unless a broader
  protocol is independently justified;
- Preference and Session Context caller-provided connection parameters remain
  supported;
- stores must not detect a fake and switch behavior;
- fake connections must not open sockets or files; and
- test assertions must distinguish executed statement/parameter intent from real SQL
  effects.

Future fake protocols for transaction, cursor, fetch, close, or rollback behavior
must be explicit; they are not inferred from the one execute-only fake.

## 9. Persistence-service substitution

Routers, UI components, handlers, and ordinary application services should receive a
fake or recording `PersistenceService` rather than a raw fake engine.

The fake service must preserve the public result/error contract needed by the
consumer while avoiding database-specific implementation details.

Tests of analytics, context, impression, collector, recommendation, generator,
preference, and session-context behavior must select the lowest sufficient seam:

1. fake service for consumer behavior;
2. fake connection for store behavior;
3. fake transaction boundary for unit-of-work behavior; or
4. fake engine lifecycle only for infrastructure behavior.

Using a more powerful seam solely for convenience is prohibited.

## 10. Pytest fixture topology

The target fixture hierarchy is:

| Fixture capability | Default scope | Cleanup requirement |
| --- | --- | --- |
| Synthetic configuration mapping | function | discard after test |
| Resolved configuration snapshot | function | immutable; no secret output |
| Recording/failing engine factory | function | assert expected calls |
| Isolated engine lifecycle | function | dispose fake exactly once when initialized |
| Fake connection | function | assert bounded use; release records |
| Fake persistence service | function | test-local reset |
| Real-resource denial guard | earliest process/collection boundary | remain active for all non-integration tests |

Function scope is the default to prevent state leakage. Broader scope requires an
explicit reason, immutable state or deterministic reset, and proof that order and
parallel execution cannot change results.

No session-scoped canonical engine is permitted for ordinary unit tests.

## 11. Collection-time and import-time protection

Ordinary pytest fixtures run after test-module import and therefore cannot by
themselves protect against import-time engine construction.

The target contract requires two independent controls:

1. production modules in the migrated boundary must be import-pure with respect to
   configuration resolution, engine construction, connection checkout, queries, and
   persistence mutation; and
2. the test runner must install the real-resource denial boundary before importing
   application test targets.

Ten current test modules import engine-owning modules. Their absence of test-module
scope calls does not remove owner-module import side effects.

The exact early-guard mechanism—pytest plugin, bootstrap wrapper, or another verified
pre-collection mechanism—is deferred. A function-scoped monkeypatch is insufficient
for this requirement.

## 12. Real-resource denial boundary

For all non-integration tests, the guard must fail closed on an attempted:

- real SQLAlchemy engine construction;
- DB-driver connection;
- DNS lookup or socket connection caused by persistence code;
- use of `localhost` or another ambient DB fallback;
- connection checkout from a real pool;
- SQL execution against a real connection;
- schema creation, alteration, or deletion; or
- database data mutation.

Failure must identify the prohibited category and responsible test boundary without
printing URLs, credentials, query parameters, or sensitive SQL parameters.

The guard should block the capability, not depend only on matching one known URL or
environment-variable name.

## 13. Explicit integration-test gate

Real persistence integration testing is outside the current implementation authority.
When separately authorized, a test may enter the integration boundary only when all
of the following are true:

1. it carries the explicit marker `persistence_integration`;
2. the runner receives an explicit opt-in equivalent to
   `ALLOW_PERSISTENCE_INTEGRATION_TESTS=1`;
3. an isolated non-production database identity is supplied explicitly;
4. the local-default policy remains disabled;
5. the target database passes a non-production identity guard;
6. cleanup and data-isolation strategy is declared;
7. network scope is limited to the authorized database target; and
8. the run is invoked through an integration-specific command or job.

Marker alone or opt-in alone is insufficient. Missing any gate must skip or fail
closed before engine construction according to the later verification plan.

This contract does not authorize creating that marker, environment variable, job, or
database.

## 14. Test lifecycle and cleanup

For an isolated fake engine lifecycle:

1. create the test-local configuration snapshot;
2. install the fake factory;
3. initialize one lifecycle container;
4. compose the test subject;
5. run the assertion scope;
6. close fake transaction/connection scopes;
7. dispose the fake lifecycle exactly once; and
8. assert no unexpected calls or retained state.

Cleanup must execute after test failure as well as success. Cleanup failure must not
hide the original assertion failure; both must remain reportable without secrets.

Repeated teardown must be idempotent. A test that never initialized an engine must
not record a disposal.

## 15. Transaction isolation contract

Unit tests use fake transaction/connection scopes and must not rely on rollback of a
real database.

For separately authorized integration tests:

- one transaction per test with rollback is preferred when application behavior and
  DDL permit it;
- committed side effects require an isolated database/schema and deterministic
  cleanup;
- tests must not share mutable data without explicit serialization/reset rules;
- schema migration tests require separate schema-mutation authority; and
- cleanup must be verified, not assumed from process exit.

No integration cleanup strategy may target a production or ambiguously identified
database.

## 16. Parallelism and ordering

Tests must remain correct under reordering. Parallel execution is allowed only when:

- configuration mappings are test-local;
- fake factories and lifecycle containers are not shared mutably;
- ambient environment mutation is absent or serialized and restored;
- fake connection records are test-local;
- integration database scopes are isolated; and
- cleanup ownership is unambiguous.

Tests that require global patching must declare serialization until a process-local
early guard removes the shared mutation.

Order-dependent success is a contract violation.

## 17. Failure and secret-handling contract

Test doubles must exercise and assert machine-classifiable failures for:

- missing, conflicting, and invalid configuration;
- prohibited default use;
- engine construction failure;
- acquisition outside `READY`;
- different-configuration repeated initialization;
- disposal failure; and
- dependency absence.

Captured logs, exception strings, pytest assertion diffs, snapshots, and fixture
representations must not contain complete URLs, credentials, environment values,
query tokens, or raw engine/configuration representations.

Test failure verbosity is not an exception to the production redaction contract.

## 18. Required configuration test matrix

| Case | Expected result |
| --- | --- |
| All variables absent, local default denied | Missing-configuration failure |
| Empty/whitespace value | Treated as absent |
| Canonical variable only | Canonical source selected |
| Each compatibility alias only | Alias accepted with provenance |
| Multiple exact-equal values | Highest-precedence provenance, one effective value |
| Multiple distinct values | Conflict before factory call |
| Malformed/unsupported URL | Validation failure before factory call |
| Local default explicitly allowed | Canonical explicit-port local compatibility route |
| Local default implicitly inferred | Prohibited-default failure |
| Diagnostic rendering | No secret-bearing value |

Every failure-before-factory case must assert factory call count `0`.

## 19. Required lifecycle test matrix

| Case | Expected result |
| --- | --- |
| First valid initialization | One engine constructed and published |
| Repeated identical initialization | Same engine; constructor count remains one |
| Concurrent identical initialization | One published identity |
| Different configuration while ready | Lifecycle conflict; no replacement |
| Acquisition before ready | Failure; no implicit initialization |
| Construction failure | `FAILED`; no engine published |
| Disposal before initialization | Safe no-op |
| First disposal | Exactly one fake dispose call |
| Repeated disposal | No second dispose call |
| Acquisition after quiesce/disposal | Failure |
| Reinitialize disposed container | Failure |
| Import target modules | No factory, connection, query, or mutation calls |

Concurrency tests must use synchronization and observed calls rather than timing-only
sleep assertions.

## 20. Required dependency and runtime test matrix

Later implementation tests must establish:

- routers and UI receive services, not raw engines;
- loggers publish no raw engine and construct none;
- embedded generator, pipeline, and collector paths reuse host dependencies;
- standalone runners create and dispose exactly one lifecycle;
- Preference and Session Context preserve caller connection delegation;
- liveness performs no persistence operation;
- readiness reads only redacted lifecycle state;
- work admission begins after composition and closes before disposal; and
- active scopes close before the engine is disposed.

These are future test requirements, not current test-write authority.

## 21. Compatibility disposition

| Current test behavior | Target disposition |
| --- | --- |
| Execute-only Preference fake connection | Preserve |
| Caller-provided Preference/Session connections | Preserve |
| Direct imports of current engine-owner modules | Preserve test intent; remove import-time persistence side effects |
| Generic monkeypatch usage | No authority implication; use only where seam-specific |
| No persistence `conftest.py` | Replace later with explicit governed fixture/guard topology |
| No test constructor calls detected | Preserve by using injected fake factory |
| Ambient local DB possibility | Deny by default |

## 22. Verification obligations

Later implementation cannot be accepted until evidence establishes:

1. the real-resource denial boundary is active before application test-target import;
2. migrated application imports perform no persistence side effect;
3. resolver tests use explicit mappings and cover all required cases;
4. lifecycle tests use an injected non-networking factory;
5. failure-before-factory cases call the factory zero times;
6. fake lifecycle teardown is exact and idempotent;
7. Preference and Session Context fake-connection tests remain compatible;
8. unit tests cannot use an implicit local default;
9. marker and opt-in are both required for any future integration run;
10. integration targets are guarded as non-production and isolated;
11. parallel and reordered test runs do not leak state; and
12. captured output contains no secret-bearing persistence value.

These are acceptance criteria, not implementation authority.

## 23. Explicit non-decisions

This contract does not decide:

- exact fixture, plugin, hook, or helper names;
- physical `conftest.py` placement;
- pytest command lines or CI job definitions;
- integration database product, host, schema, or credentials;
- network sandbox implementation;
- whether a prohibited integration attempt skips or fails;
- transaction rollback implementation for each integration test;
- schema migration test scope;
- exact fake engine or connection classes; or
- production/test implementation wave sequencing.

Those decisions remain assigned to the Phase 2 Verification Plan, Compatibility and
Migration Seam Register, or later implementation authority.

## 24. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 2 state | `OPEN` |
| Unit-test real DB/network policy | `DENY_BY_DEFAULT` |
| Configuration substitution | `EXPLICIT_MAPPING` |
| Engine substitution | `INJECTED_NON_NETWORKING_FACTORY` |
| Store substitution | `CALLER_PROVIDED_FAKE_CONNECTION` |
| Integration gate | `MARKER_PLUS_EXPLICIT_OPT_IN_PLUS_ISOLATED_TARGET` |
| Test contract | `DECIDED_AS_TARGET_ARCHITECTURE` |
| Current test conformance | `NOT_VERIFIED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this contract, then author the Compatibility and Migration Seam Register |
