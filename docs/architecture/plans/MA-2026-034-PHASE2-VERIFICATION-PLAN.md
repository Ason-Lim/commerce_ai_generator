# MA-2026-034 Phase 2 Verification Plan

## 1. Plan identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Deliverable | `Phase 2 Verification Plan` |
| Governing register | `MA-2026-034-PHASE2-COMPATIBILITY-MIGRATION-SEAM-REGISTER` |
| Governing HEAD | `fdd5b6e1f540e5ee585c14f15b3c0e72c7891b94` |
| Plan version | `v1.0` |
| Plan date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This plan defines the evidence required to verify later implementation of the Phase 2
configuration, engine, dependency, runtime, test, and migration contracts.

The plan separates:

- architectural completeness needed to close Phase 2 design;
- offline implementation acceptance evidence;
- controlled runtime evidence; and
- separately authorized real-database integration evidence.

Establishing this plan does not execute tests, import application modules, access a
database or network, modify code, or authorize implementation.

## 3. Verification principles

All future verification must follow these principles:

1. evidence is tied to an exact repository HEAD;
2. the worktree and index state are recorded before and after execution;
3. target statements remain `PROPOSED` until their exact implementation is observed;
4. static evidence cannot prove runtime identity, connectivity, or cleanup;
5. sentinel evidence cannot be promoted beyond the instrumented boundary;
6. unit tests deny real database and network access by default;
7. secret-bearing values never appear in output or evidence artifacts;
8. every migration cohort has independent entry, exit, and rollback gates;
9. a failing mandatory gate blocks acceptance; and
10. documentation-only Phase 2 closure does not imply implementation conformance.

## 4. Verification levels

| Level | Name | Purpose | Resource authority |
| --- | --- | --- | --- |
| `L0` | Architecture-chain verification | Verify documents, tags, decisions, and internal consistency | Read-only |
| `L1` | Static implementation verification | Verify ownership, imports, call sites, and prohibited patterns | Read-only |
| `L2` | Offline unit/contract verification | Verify resolver, lifecycle, injection, guards, and redaction | No real DB/network |
| `L3` | Instrumented entry-point verification | Verify startup/shutdown identity with sentinel resources | No real DB/network |
| `L4` | Regression and compatibility verification | Verify protected behavior across cohorts/full suite | No real DB/network unless separately classified |
| `L5` | Controlled persistence integration | Verify real construction/connectivity/cleanup against isolated target | Separate authority required |

`L0` is required for Phase 2 design readiness. `L1–L4` apply after authorized
implementation. `L5` is not authorized by Phase 2 and is required only when a later
production-readiness decision makes it an explicit gate.

## 5. Gate summary

| Gate | Verification subject | Primary level | Mandatory for implementation acceptance |
| --- | --- | --- | --- |
| `V-000` | Exact repository and authority baseline | `L0` | Yes |
| `V-010` | Architecture-chain integrity | `L0` | Yes |
| `V-020` | Canonical configuration authority | `L1/L2` | Yes |
| `V-030` | Engine ownership and lifecycle | `L1/L2` | Yes |
| `V-040` | Import purity and collection safety | `L1/L2` | Yes |
| `V-050` | Dependency and injection conformance | `L1/L2` | Yes |
| `V-060` | Runtime startup/shutdown ordering | `L3` | Yes for migrated entry point |
| `V-070` | Test real-resource denial | `L2` | Yes |
| `V-080` | Compatibility and transaction preservation | `L2/L4` | Yes for migrated cohort |
| `V-090` | Secret/redaction safety | `L1/L2/L3` | Yes |
| `V-100` | Cohort regression | `L4` | Yes for each wave |
| `V-110` | Full repository regression | `L4` | Yes before implementation completion |
| `V-120` | Controlled real persistence | `L5` | Only under later authority |
| `V-130` | Evidence package and rollback readiness | all applicable | Yes |

## 6. `V-000` — exact baseline

Before any verification execution, record and require:

- current branch identity;
- exact `HEAD`, `origin/main`, and remote `main` identities;
- clean tracked and untracked worktree as required by the authorized wave;
- empty staged index;
- governing annotated-tag object and peeled target identities;
- authorized implementation file list;
- authorized test file list;
- expected regression baseline; and
- explicit real-resource authority state.

If any identity or scope differs, verification must stop before application import or
mutation.

## 7. `V-010` — architecture-chain integrity

The Phase 2 design chain must contain independently established artifacts for:

1. Configuration Authority Contract;
2. Engine Ownership and Lifecycle Contract;
3. Persistence Dependency / Injection Map;
4. Runtime Startup and Shutdown Resource Map;
5. Test Configuration and Substitution Contract;
6. Compatibility and Migration Seam Register; and
7. this Verification Plan.

Pass criteria:

- each artifact exists at its governed path;
- each annotated tag targets the expected document-only commit;
- ownership and dependency rules do not conflict;
- all target rules are distinguished from current implementation facts;
- production/test/database authority remains explicit; and
- all eight ADA-required deliverables are accounted for, with the Completion
  Readiness Review remaining the next document.

## 8. `V-020` — configuration authority

### Static checks

- only `app.core.config` interprets `DATABASE_URL`, `COMMERCE_DB_URL`, and
  `FRUIT_DB_URL` in the migrated boundary;
- no migrated consumer has an inline fallback URL or precedence chain;
- the port-omitting `app.main` default is not independently active; and
- configuration values are not formatted into diagnostics.

### Offline behavioral matrix

| Case | Required result |
| --- | --- |
| All absent; local default denied | Missing failure; factory calls `0` |
| Empty/whitespace | Absent semantics |
| Canonical only | Canonical source selected |
| Each alias only | Compatibility source accepted |
| Exact-equal duplicates | Highest-precedence provenance; one value |
| Distinct values | Conflict; factory calls `0` |
| Malformed/unsupported URL | Validation failure; factory calls `0` |
| Explicit local default | Explicit-port local route only |
| Implicit local default | Prohibited-default failure |
| Diagnostic rendering | No URL, credential, token, or raw value |

Pass requires deterministic results under reordered and repeated execution.

## 9. `V-030` — engine ownership and lifecycle

### Static checks

- only `app.db.database` calls the real engine factory in the migrated boundary;
- migrated modules contain no module-scope engine construction;
- consumers cannot set pool policy or call shared-engine disposal; and
- `pool_pre_ping=True` is owned by the canonical authority.

### Offline lifecycle matrix

| Case | Required result |
| --- | --- |
| First initialization | One fake engine published |
| Repeated identical initialization | Same identity; constructor count one |
| Concurrent identical initialization | One published identity |
| Different configuration/policy | Conflict; no replacement |
| Acquire before ready | Failure; no implicit init |
| Constructor failure | `FAILED`; no published engine |
| Dispose before init | Safe no-op |
| First dispose | Exactly one dispose call |
| Repeated dispose | No second call |
| Acquire after quiesce/dispose | Failure |
| Reinitialize disposed container | Failure |

Concurrency evidence must use barriers/events and call records, not timing-only sleep.

## 10. `V-040` — import purity and collection safety

Required targets include every migrated constructor owner and each entry-point module
within the authorized wave.

The sentinel must block and count:

- engine-factory calls;
- DB-driver connections;
- DNS/network attempts;
- file writes;
- subprocess execution;
- connection checkout;
- SQL execution; and
- schema or data mutation.

Pass criteria:

- ordinary module import produces zero persistence side effects;
- pytest collection imports produce zero real-resource attempts;
- the denial boundary is active before application test-target import;
- importing tests do not rely on a function-scoped patch for collection safety; and
- the repository remains unchanged.

## 11. `V-050` — dependency and injection conformance

Static and behavioral evidence must establish:

- process composition roots hold lifecycle authority without factory ownership;
- routers and UI receive use-case/query/command services;
- logger modules publish no raw engine;
- stores receive caller-provided connections where specified;
- missing injection fails rather than triggering a global lookup or constructor;
- embedded generator, pipeline, and collector paths reuse the host lifecycle;
- standalone paths initialize one lifecycle; and
- no replacement mutable global service locator has been introduced.

Direct raw-engine imports must be counted before and after each cohort. The count must
decrease as authorized and must never increase elsewhere.

## 12. `V-060` — runtime startup and shutdown

Each migrated entry point requires an instrumented lifecycle trace.

Expected startup order:

```text
resolve configuration
-> initialize one engine
-> compose services
-> mark lifecycle ready
-> open work admission
```

Expected shutdown order:

```text
mark non-ready / close admission
-> drain or cancel bounded work
-> close connections and transactions
-> release services
-> dispose engine exactly once
```

Entry-point cases:

| Boundary | Required evidence |
| --- | --- |
| FastAPI | Import purity, per-worker identity, startup failure, graceful shutdown |
| Streamlit | Repeated rerun with one engine identity; no session multiplication |
| Admin dashboard | Import without query; refresh reuses process engine |
| Generator | Embedded host reuse and standalone ownership |
| Recommendation pipeline | Embedded and standalone mode behavior |
| Market collector | Embedded/worker/one-shot lifecycle behavior |
| Direct runner | Outer cleanup on success and failure |

Sentinel verification proves ordering and identity only. It does not prove real
connectivity.

## 13. `V-070` — real-resource denial

The test safety guard must be self-tested by controlled attempts to reach each
prohibited capability. Each attempt must fail before external access.

Pass criteria:

- non-integration tests cannot bind the real engine factory;
- local defaults cannot silently enable a DB;
- DB-driver, DNS, socket, pool checkout, and SQL attempts are blocked;
- blocked output identifies category without secret values;
- protection remains active under test reorder and supported parallelism; and
- integration marker alone or opt-in alone does not bypass the guard.

No real database is required to prove denial.

## 14. `V-080` — compatibility and transaction preservation

For each seam/cohort, record the existing behavior before migration and compare the
target result after migration.

Mandatory protected contracts include:

- API request/response behavior;
- recommendation ranking, scoring, parsing, provider, and result behavior;
- market collection/intelligence behavior;
- analytics, context, and impression event behavior;
- UI-visible and administrative query behavior;
- Preference and Session Context caller-connection delegation;
- execute-only fake connection behavior;
- transaction begin/connect scope and commit/rollback intent;
- Food Knowledge, Product Identity, Cross-Border, and `Provider.aliases` boundaries;
  and
- secret redaction and real-resource denial.

Any intentional behavior change requires separate authority and cannot be accepted as
an incidental migration difference.

## 15. `V-090` — secret and diagnostic safety

Verification must scan and exercise:

- configuration error messages;
- conflict errors;
- engine construction failures;
- lifecycle state failures;
- readiness output;
- logs and captured pytest output;
- object representations used in assertions; and
- migration warnings or usage evidence.

Inject synthetic unique credential/token sentinels and require zero occurrence in all
captured output. Do not use real credentials for redaction testing.

Passing substring checks alone is insufficient if structured fields can retain raw
values; both rendered and structured outputs must be inspected where applicable.

## 16. `V-100` — cohort regression

Every future migration wave must define an exact affected-test cohort before code
changes. The cohort must cover:

- directly modified modules;
- importers and callers;
- protected public contracts;
- failure and rollback paths;
- entry-point or worker mode affected; and
- tests for the temporary compatibility adapter, if present.

Pass requires all selected tests to pass at the exact candidate HEAD with the
real-resource denial guard active. Test deletions, skips, expected-failure additions,
or assertion weakening require explicit review and cannot silently satisfy the gate.

## 17. `V-110` — full repository regression

Before implementation completion or legacy-path removal:

- record the authoritative current test inventory and baseline at the pre-change
  parent;
- run the full supported regression suite at the candidate HEAD;
- record pass, fail, skip, xfail, warning, duration, and environment identity;
- account for any test-count change by exact file/scope change;
- run compilation or syntax verification for changed Python/shell artifacts; and
- verify clean repository state after execution.

Historical counts are evidence context, not a substitute for an exact future
baseline. A lower count without an authorized explanation fails the gate.

## 18. `V-120` — controlled real persistence integration

This gate is `NOT_AUTHORIZED` by Phase 2.

If later authorized, it requires:

- `persistence_integration` marker;
- explicit runner opt-in;
- isolated non-production target verification;
- local-default disabled;
- scoped network authority;
- schema/data cleanup strategy;
- bounded connection and operation timeouts;
- lifecycle disposal evidence; and
- proof that no production credential or target is used.

Real connectivity cannot be inferred from engine construction, `pool_pre_ping`, or
sentinel success.

## 19. `V-130` — evidence package and rollback readiness

Each future implementation wave must produce one evidence package containing:

1. exact parent and candidate HEAD;
2. governing authority and seam IDs;
3. exact changed file list and diff summary;
4. static verification results;
5. focused test commands and results;
6. sentinel/runtime trace where applicable;
7. cohort and full regression results required by the wave;
8. redaction and real-resource-denial results;
9. compatibility-path usage evidence;
10. known limitations;
11. rollback target and procedure; and
12. final synchronized repository state.

Evidence must distinguish `PASS`, `FAIL`, `NOT_RUN`, `NOT_APPLICABLE`, and
`NOT_AUTHORIZED`. Missing evidence must not be represented as `PASS`.

## 20. Wave-to-gate matrix

| Proposed wave | Required gates before exit |
| --- | --- |
| `I0` test safety | `V-000`, `V-040`, `V-070`, `V-090`, `V-100` |
| `I1` resolver/lifecycle core | `V-020`, `V-030`, `V-040`, `V-070`, `V-090`, `V-100` |
| `I2` FastAPI | `V-040`, `V-050`, `V-060`, `V-080`, `V-100` |
| `I3` loggers | `V-040`, `V-050`, `V-080`, `V-090`, `V-100` |
| `I4` collector/pipeline | `V-040`, `V-050`, `V-060`, `V-080`, `V-100` |
| `I5` Streamlit/admin | `V-040`, `V-050`, `V-060`, `V-080`, `V-100` |
| `I6` remaining importers | `V-040`, `V-050`, `V-080`, `V-100` |
| `I7` legacy disable/removal | All prior gates plus `V-110` and `V-130` |

Every wave also requires `V-000`. `V-120` is included only by separate authority.

## 21. Fail-closed rules

Verification stops and the candidate is not accepted when:

- baseline identity or authority scope differs;
- a real-resource attempt escapes the guard;
- a secret sentinel appears in output;
- more than one engine identity is created for one process role;
- import or collection performs persistence work;
- transaction or protected behavior changes without authority;
- disposal count/order is wrong;
- a mandatory test fails or is silently skipped;
- full regression count is unaccountably lower;
- a compatibility path constructs a fallback engine; or
- rollback state is undefined.

Failure evidence must be preserved without proceeding to broader or riskier gates.

## 22. Evidence artifact naming

Future verification evidence should use stable identifiers under
`docs/verification/persistence/**` and include:

- program and implementation-wave identity;
- verification gate IDs;
- exact candidate HEAD;
- execution date;
- resource authority boundary; and
- result classification.

One evidence artifact may cover multiple gates only when each gate remains separately
reported and independently reviewable.

## 23. Phase 2 design-closure interpretation

For Phase 2 design closure:

- this plan must be established;
- its gates need not be executed because no implementation is authorized;
- the Completion Readiness Review must verify that every required architecture
  deliverable exists and every mandatory decision is explicit;
- current implementation conformance remains `NOT_VERIFIED`; and
- later implementation authority remains a separate decision.

Phase 2 completion therefore means “implementation-ready architecture contract,” not
“persistence centralization implemented.”

## 24. Explicit non-decisions

This plan does not decide:

- implementation authority or file scope;
- exact future test commands, fixture names, or CI jobs;
- real integration database identity;
- deployment commands;
- migration schedule;
- telemetry system;
- active readiness probes;
- schema/data migration; or
- Phase 3 content.

## 25. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 2 state | `OPEN` |
| Verification gates | `V-000–V-130` |
| Offline mandatory gates | `DEFINED` |
| Controlled real persistence gate | `DEFINED_BUT_NOT_AUTHORIZED` |
| Verification plan | `DECIDED_AS_TARGET_ARCHITECTURE` |
| Verification execution | `NOT_RUN_BY_DESIGN` |
| Implementation authorization | `NOT_ISSUED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this plan, then author the Phase 2 Completion Readiness Review |
