# MA-2026-034 Phase 2 Compatibility and Migration Seam Register

## 1. Register identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Deliverable | `Compatibility and Migration Seam Register` |
| Governing test contract | `MA-2026-034-PHASE2-TEST-CONFIGURATION-SUBSTITUTION-CONTRACT` |
| Governing architecture chain | Configuration → Engine → Dependency → Runtime → Test |
| Governing HEAD | `006706f6274c9704ca7fe4d1b9645aa31f44ca8d` |
| Register version | `v1.0` |
| Register date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This register decomposes the current distributed persistence architecture into
bounded migration seams. Each seam records its compatibility obligation,
prerequisites, acceptance evidence, rollback boundary, and removal condition.

The register defines future sequencing constraints. It does not authorize edits to
production code, tests, deployment configuration, environment values, database
schema, or data.

## 3. Governing target state

The registered seams must converge on the established target architecture:

- `app.core.config` is the sole configuration authority;
- `DATABASE_URL` is canonical, while `COMMERCE_DB_URL` and `FRUIT_DB_URL` are
  compatibility aliases;
- `app.db.database` is the sole engine factory and lifecycle authority;
- each process lifecycle owns one canonical synchronous engine by default;
- module import performs no persistence initialization or work;
- UI and routers receive higher-level services;
- stores may receive caller-provided connections;
- startup precedes work admission and shutdown quiesces before disposal; and
- unit tests deny real database and network access by default.

Current conformance to this target is `NOT_VERIFIED`.

## 4. Register state model

Each seam moves through these future states:

```text
REGISTERED
  -> AUTHORIZED
  -> IMPLEMENTED_BEHIND_COMPATIBILITY
  -> VERIFIED
  -> LEGACY_PATH_DISABLED
  -> LEGACY_PATH_REMOVED
  -> CLOSED
```

This document establishes seams only in `REGISTERED` state. No seam becomes
`AUTHORIZED` for implementation without a later explicit authority artifact.

Rollback may return an implemented seam to the last verified compatibility state; it
must not fabricate authority or silently reactivate an unverified path.

## 5. Register summary

| ID | Seam | Current state | Target disposition | Risk |
| --- | --- | --- | --- | --- |
| `CMS-001` | Canonical resolver introduction | Distributed inline resolution | Centralize in `app.core.config` | High |
| `CMS-002` | Environment aliases and default divergence | Three names; inconsistent empty/default behavior | Preserve aliases; unify semantics | High |
| `CMS-003` | Canonical engine lifecycle introduction | Module-scope global engine | Explicit bootstrap lifecycle | High |
| `CMS-004` | `app.main` independent engine | Own constructor | FastAPI composition consumer | High |
| `CMS-005` | Three logger-owned engines | Independent constructors | Inject logging persistence capabilities | High |
| `CMS-006` | Market collector engine | Independent constructor | Embedded/worker governed dependency | High |
| `CMS-007` | Recommendation pipeline engine | Independent constructor | Embedded/standalone governed dependency | High |
| `CMS-008` | Streamlit analytics-engine leak | UI imports logger engine | Query/command and analytics services | Critical |
| `CMS-009` | Admin global engine/query paths | UI imports canonical engine | Administrative query service | Critical |
| `CMS-010` | Canonical global-engine importers | 27 direct imports | Injection or state-gated temporary adapter | High |
| `CMS-011` | Preference/Session connection seam | Caller-provided `conn` | Preserve | Medium |
| `CMS-012` | FastAPI startup/shutdown | No established lifecycle contract | Governed lifespan per worker | High |
| `CMS-013` | Streamlit rerun lifecycle | Runtime behavior unobserved | Process-scoped reuse | High |
| `CMS-014` | Test collection safety | Imports can trigger owner side effects | Pre-collection real-resource denial | Critical |
| `CMS-015` | Transaction semantics | Consumer-owned contexts | Preserve while dependencies migrate | High |
| `CMS-016` | Operational launch definitions | Unresolved | Verify before binding concrete hooks | Medium |

## 6. `CMS-001` — canonical resolver introduction

| Field | Registration |
| --- | --- |
| Current boundary | Inline resolution across seven constructor owners |
| Target boundary | `app.core.config` resolves one immutable snapshot |
| Compatibility | Existing accepted variable names remain usable |
| Prerequisite | Configuration unit-test matrix and redaction tests |
| Acceptance evidence | One resolver owns precedence; failure-before-factory cases call factory zero times |
| Rollback unit | Resolver implementation plus its isolated tests, before consumer migration |
| Removal condition | No migrated consumer independently reads persistence variables |

Migration rule: introduce and verify the resolver before changing any consumer. Its
initial existence must not change engine ownership or cause import-time resolution.

## 7. `CMS-002` — aliases and default divergence

| Field | Registration |
| --- | --- |
| Current boundary | `DATABASE_URL`; `COMMERCE_DB_URL → FRUIT_DB_URL`; direct `FRUIT_DB_URL`; two defaults |
| Target boundary | `DATABASE_URL > COMMERCE_DB_URL > FRUIT_DB_URL`; conflicts fail closed |
| Compatibility | Both aliases retained temporarily |
| Behavior change | Empty/whitespace becomes absent; port-omitting default retired |
| Acceptance evidence | Alias matrix, duplicate/conflict tests, explicit-local-default tests |
| Rollback unit | Consumer cohort binding, not removal of verified canonical resolver |
| Removal condition | Alias usage telemetry/evidence is zero and separate removal authority exists |

Alias removal must not occur in the same migration unit that first centralizes
resolution. No compatibility warning may disclose raw values.

## 8. `CMS-003` — canonical engine lifecycle introduction

| Field | Registration |
| --- | --- |
| Current boundary | `app.db.database.engine` constructed at module scope |
| Target boundary | Explicit lifecycle container; one engine per process |
| Compatibility | Temporary state-gated accessor may bridge verified callers |
| Prerequisite | Fake factory, lifecycle state tests, import-purity tests |
| Acceptance evidence | One construction, idempotent init/dispose, `pool_pre_ping=True` |
| Rollback unit | Lifecycle implementation before any consumer cohort cutover |
| Removal condition | All callers use governed composition; accessor usage is zero |

Any temporary accessor must fail before readiness and after quiesce. It may return the
published engine but may never construct one implicitly.

## 9. `CMS-004` — `app.main` independent engine

| Field | Registration |
| --- | --- |
| Current boundary | `app.main` reads `FRUIT_DB_URL` and constructs its own engine |
| Target boundary | FastAPI composition root binds canonical lifecycle/services |
| Compatibility | Preserve endpoint and response behavior; retire independent default |
| Prerequisite | `CMS-001–003`, pre-collection guard, FastAPI lifecycle tests |
| Acceptance evidence | Import creates zero engines; worker startup creates one; shutdown disposes once |
| Rollback unit | FastAPI composition/lifespan cohort |
| Removal condition | No `create_engine`, raw DB env read, or fallback URL remains in `app.main` |

Router mounting and operational launch commands must be verified separately; this seam
must not combine unrelated route repair with engine migration without explicit scope.

## 10. `CMS-005` — logger-owned engines

| Field | Registration |
| --- | --- |
| Current boundary | Analytics, context, and impression loggers construct engines |
| Target boundary | Inject logging persistence service/transaction capability |
| Compatibility | Preserve logging call and event semantics |
| Prerequisite | Canonical lifecycle and fake service/connection seams |
| Acceptance evidence | Zero logger constructors; no raw engine export; behavior regressions pass |
| Rollback unit | One logger at a time unless shared adapter proves atomic need |
| Removal condition | All callers bind governed logging services |

Logging durability, buffering, retry, and event-loss policies are not to be changed as
an incidental part of this seam.

## 11. `CMS-006` — market collector engine

| Field | Registration |
| --- | --- |
| Current boundary | Market collector resolves config and constructs engine |
| Target boundary | Embedded host injection or standalone worker lifecycle |
| Compatibility | Preserve collection, schema-adjustment, and transaction semantics |
| Prerequisite | Mode-explicit runner contract and transaction evidence |
| Acceptance evidence | One host/worker engine; no import constructor; bounded cleanup |
| Rollback unit | Collector composition binding, separate from business logic |
| Removal condition | No collector env read, factory call, or global engine ownership |

No collector data or schema operation is authorized by this register.

## 12. `CMS-007` — recommendation pipeline engine

| Field | Registration |
| --- | --- |
| Current boundary | Recommendation pipeline resolves config and constructs engine |
| Target boundary | Embedded host or standalone lifecycle supplies dependency |
| Compatibility | Preserve ranking, scoring, normalization, and response behavior |
| Prerequisite | Pipeline mode selection and regression baseline |
| Acceptance evidence | No import constructor; embedded identity reuse; standalone exact disposal |
| Rollback unit | Pipeline dependency adapter only |
| Removal condition | No raw config/factory/global engine remains in pipeline |

Recommendation semantics are protected and must not be refactored in this seam.

## 13. `CMS-008` — Streamlit analytics-engine leak

| Field | Registration |
| --- | --- |
| Current boundary | Streamlit imports `analytics_logger.engine`; direct connect/begin paths exist |
| Target boundary | Query/command services and analytics event service |
| Compatibility | Preserve UI outputs, caching behavior, events, and transactions |
| Prerequisite | Safe runtime harness, service seams, rerun lifecycle design |
| Acceptance evidence | No raw engine import; reruns create zero additional engines; UI regression pass |
| Rollback unit | One presentation service binding at a time |
| Removal condition | All DB-capable module-level paths removed or composition-gated |

This critical seam must not be probed by blind import before its confirmed
module-level database paths are isolated.

## 14. `CMS-009` — administrative dashboard global engine

| Field | Registration |
| --- | --- |
| Current boundary | Admin imports canonical engine; module-level query paths exist |
| Target boundary | Administrative query service after lifecycle readiness |
| Compatibility | Preserve displayed results and query semantics |
| Prerequisite | Safe runner harness and query-service boundary |
| Acceptance evidence | Import performs no query; refresh reuses engine; bounded scopes close |
| Rollback unit | Administrative query adapter and one caller cohort |
| Removal condition | No raw engine import or module-level DB query remains |

Admin runtime verification must use sentinel or fake resources until separate real
integration authority exists.

## 15. `CMS-010` — canonical global-engine importers

| Field | Registration |
| --- | --- |
| Current boundary | 27 tracked files directly import `app.db.database.engine` |
| Target boundary | Explicit injected connection, transaction boundary, or service |
| Compatibility | Preserve per-consumer query and transaction semantics |
| Prerequisite | Exact consumer inventory and cohort classification |
| Acceptance evidence | Direct-import count decreases monotonically; cohort regressions pass |
| Rollback unit | Small consumer cohort with one dependency form |
| Removal condition | No ordinary consumer imports a raw engine |

Migration must not replace one global engine import with another global service
locator. The Naver Shopping API collector's current canonical reuse is compatible in
identity but still requires an explicit target dependency.

## 16. `CMS-011` — Preference and Session Context connection seam

| Field | Registration |
| --- | --- |
| Current boundary | Nine functions accept caller `conn`; four stores call `conn.execute` |
| Target boundary | Preserve caller-provided connection and unit-of-work ownership |
| Compatibility | Execute-only Preference fake remains valid |
| Prerequisite | Existing contract tests remain green |
| Acceptance evidence | Delegation and fake tests unchanged or equivalently verified |
| Rollback unit | Caller binding only; store signatures protected |
| Removal condition | None in MA-2026-034 unless separate migration decision exists |

This seam is a preservation anchor, not technical debt to remove during engine
centralization.

## 17. `CMS-012` — FastAPI startup and shutdown

| Field | Registration |
| --- | --- |
| Current boundary | No established persistence lifespan/disposal contract |
| Target boundary | Resolve → initialize → compose → admit; quiesce → drain → dispose |
| Compatibility | Preserve API behavior and worker isolation |
| Prerequisite | `CMS-003–004`, work-admission and lifecycle sentinel tests |
| Acceptance evidence | Per-worker single identity; failure blocks admission; dispose exactly once |
| Rollback unit | Lifespan integration separate from consumer cohorts |
| Removal condition | Legacy startup construction paths absent |

Preload and multi-worker behavior must be verified before production acceptance.

## 18. `CMS-013` — Streamlit rerun lifecycle

| Field | Registration |
| --- | --- |
| Current boundary | Runtime identity/reuse not safely observed |
| Target boundary | One process lifecycle reused across reruns |
| Compatibility | Preserve Streamlit rerun/cache semantics |
| Prerequisite | Sentinel runner and no-real-resource guard |
| Acceptance evidence | Multiple reruns, one engine construction, no session engine multiplication |
| Rollback unit | Process resource binding isolated from UI service migration |
| Removal condition | Rerun topology independently verified |

If reliable shutdown hooks are unavailable, the limitation must be documented rather
than hidden behind a false disposal guarantee.

## 19. `CMS-014` — test collection safety

| Field | Registration |
| --- | --- |
| Current boundary | Ten tests import engine-owner modules; no pre-collection guard established |
| Target boundary | Real-resource denial active before application import |
| Compatibility | Preserve test discovery and intent |
| Prerequisite | Early guard design and import-purity target |
| Acceptance evidence | Collection triggers zero real constructors/connections; full regression passes |
| Rollback unit | Guard bootstrap plus its self-tests |
| Removal condition | Guard remains permanent; seam closes when import-purity is verified |

A function-scoped fixture alone cannot close this seam.

## 20. `CMS-015` — transaction semantics preservation

| Field | Registration |
| --- | --- |
| Current boundary | Consumer-owned `connect`/`begin` context managers |
| Target boundary | Explicit outer unit of work passes one connection to stores |
| Compatibility | Commit/rollback/query ordering preserved by default |
| Prerequisite | Per-consumer transaction characterization |
| Acceptance evidence | Behavior tests prove identical boundaries and failure effects |
| Rollback unit | One unit-of-work cohort |
| Removal condition | Target transaction boundaries independently verified |

Engine centralization must not silently centralize or relocate transaction ownership.

## 21. `CMS-016` — operational launch definitions

| Field | Registration |
| --- | --- |
| Current boundary | No high-precision launch command found; 26 main guards only |
| Target boundary | Each deployed process binds an explicit lifecycle root |
| Compatibility | Preserve supported invocation modes |
| Prerequisite | Deployment/process evidence under separate read authority |
| Acceptance evidence | Every supported entry point maps to one startup/shutdown root |
| Rollback unit | Process definition or runner binding, separate from domain logic |
| Removal condition | Launch inventory and lifecycle bindings are established |

No main guard is presumed to be a production deployment command.

## 22. Dependency order

The mandatory dependency order is:

```text
CMS-014 test safety foundation
  -> CMS-001 / CMS-002 configuration authority
  -> CMS-003 canonical engine lifecycle
  -> CMS-004 / CMS-012 FastAPI first composition path
  -> CMS-005 logger cohort
  -> CMS-006 / CMS-007 worker and pipeline cohorts
  -> CMS-008 / CMS-009 presentation cohorts
  -> CMS-010 remaining canonical importers
  -> compatibility-path disablement and removal
```

`CMS-011` and `CMS-015` are preservation constraints across all waves.
`CMS-013` is coordinated with `CMS-008`. `CMS-016` must be resolved before concrete
deployment hook implementation is declared complete.

This dependency order is a design constraint, not implementation authorization.

## 23. Proposed future implementation waves

| Wave | Intended scope | Entry condition | Exit evidence |
| --- | --- | --- | --- |
| `I0` | Early real-resource denial and characterization tests | Separate test-write authority | Guard self-test and unchanged baseline |
| `I1` | Canonical resolver and fake-backed lifecycle core | `I0` verified | Unit matrices and import purity |
| `I2` | FastAPI composition/lifecycle | `I1` verified | Sentinel startup/shutdown and API regressions |
| `I3` | Logger constructors | `I2` stable | Logger behavior and no constructor evidence |
| `I4` | Collector and pipeline constructors | Worker modes characterized | Embedded/standalone lifecycle evidence |
| `I5` | Streamlit and admin presentation seams | Safe sentinel harnesses | Rerun/refresh and presentation regressions |
| `I6` | Remaining canonical importers | Exact cohort inventory | Direct-import reduction and transaction evidence |
| `I7` | Disable/remove legacy paths | All cohorts verified | Zero usage and rollback readiness |

Each wave requires separate exact file scope, regression baseline, rollback procedure,
and authority. Waves may not be inferred as approved from this register.

## 24. Compatibility-window rules

During any future compatibility window:

- canonical and legacy paths must never construct two engines for one process role;
- legacy aliases may feed only the canonical resolver;
- a temporary engine accessor may expose only the ready canonical identity;
- adapters must fail if composition is missing rather than construct a fallback;
- warnings and metrics must be redacted;
- transaction behavior must remain characterized;
- usage evidence must identify code path, not secret values; and
- removal requires zero-use evidence plus explicit authority.

Compatibility code is temporary governed infrastructure, not a permanent second
architecture.

## 25. Rollback rules

A valid rollback must:

1. target one bounded seam or cohort;
2. restore the last verified caller binding or adapter behavior;
3. preserve one-engine-per-process identity;
4. preserve canonical configuration conflict and redaction rules;
5. avoid reintroducing import-time engine construction when a state-gated adapter can
   restore compatibility;
6. preserve Preference and Session Context connection seams;
7. run the cohort and baseline regressions; and
8. leave worktree, lifecycle state, and external database state known.

Rollback must not delete data, revert schema, rotate secrets, or force-push history
without separately granted authority.

## 26. Protected behavior

Migration must preserve unless separately authorized:

- API request and response contracts;
- recommendation ranking, scoring, parsing, provider, and result semantics;
- market collection and intelligence semantics;
- analytics, context, and impression event semantics;
- UI-visible results and administrative query semantics;
- Preference and Session Context models and caller-connection behavior;
- current transaction commit/rollback intent;
- Food Knowledge, Product Identity, Cross-Border, and `Provider.aliases` authority;
- secret redaction; and
- fail-closed test protection.

## 27. Register verification obligations

Before Phase 2 readiness can be accepted, evidence must establish that:

1. every known independent constructor owner has a registered seam;
2. both UI engine leaks have registered safe-observation and migration boundaries;
3. configuration aliases and default divergence have explicit compatibility rules;
4. the 27 direct-import boundary has a cohort strategy;
5. caller-provided connection seams are protected;
6. transaction behavior is a preservation constraint;
7. test collection protection precedes risky imports;
8. each proposed wave has entry, exit, and rollback criteria;
9. no compatibility path permits duplicate or fallback construction; and
10. no seam is mislabeled as implementation-authorized.

## 28. Explicit non-decisions

This register does not decide:

- implementation file lists or commit identities;
- exact adapter, protocol, fixture, or lifecycle names;
- production deployment commands;
- per-cohort time estimates;
- alias deprecation dates;
- concrete telemetry system;
- rollback execution commands;
- schema/data migration;
- active database readiness probes; or
- Phase 3 scope.

These require later authority and evidence.

## 29. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 2 state | `OPEN` |
| Registered seams | `16` |
| Proposed implementation waves | `I0–I7` |
| Compatibility aliases | `PRESERVE_UNTIL_ZERO_USE_AND_REMOVAL_AUTHORITY` |
| Caller-provided connection seams | `PROTECTED` |
| Migration register | `DECIDED_AS_TARGET_ARCHITECTURE` |
| Implementation authorization | `NOT_ISSUED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this register, then author the Phase 2 Verification Plan |
