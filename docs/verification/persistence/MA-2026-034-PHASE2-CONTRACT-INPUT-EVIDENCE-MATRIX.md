# MA-2026-034 Phase 2 Contract-Input Evidence Matrix

## 1. Matrix identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Governing Phase 2 ADA | `ADA-MA-2026-034-PHASE2-CONFIGURATION-ENGINE-AUTHORITY-CONTRACT` |
| Verified repository HEAD | `0ab2b9d2a94b96241df24d59f3f52e55bd049a1a` |
| Matrix type | Read-only architecture contract input |
| Matrix date | `2026-08-31` |
| Production or test mutation | `NONE` |

## 2. Purpose

This matrix maps every required Phase 2 decision to established Phase 1 evidence, the
remaining gap, and the method required to verify or decide the target contract.

It distinguishes current repository facts from proposed architecture. A target
contract must not be labeled `VERIFIED` until it is supported by current-state
evidence; a future-state decision remains `PROPOSED` until implemented and separately
verified under later authority.

## 3. Evidence classification

| Classification | Meaning in this matrix |
| --- | --- |
| `VERIFIED` | Directly supported by established repository or controlled runtime evidence |
| `PARTIALLY_VERIFIED` | Supported only within an explicit entry point, pattern, or scan boundary |
| `PROPOSED` | Target architecture decision to be made during Phase 2 |
| `UNRESOLVED` | Existing evidence does not determine the answer |

## 4. Established evidence sources

| Source ID | Established artifact |
| --- | --- |
| `P1-BASELINE` | `MA-2026-034-PHASE1-PERSISTENCE-OWNERSHIP-BASELINE` |
| `P1-RUNTIME` | `MA-2026-034-PHASE1-APP-MAIN-SENTINEL-IMPORT-OBSERVATION` |
| `P1-GAPS` | `MA-2026-034-PHASE1-CLOSURE-READINESS-GAP-CLASSIFICATION` |
| `P1-SCOPE` | `MA-2026-034-PHASE1-CLOSURE-SCOPE-DECISION` |
| `P1-COMPLETE` | `MA-2026-034-PHASE1-COMPLETION` |
| `P2-ADA` | `ADA-MA-2026-034-PHASE2-CONFIGURATION-ENGINE-AUTHORITY-CONTRACT` |

## 5. Configuration authority inputs

| Decision input | Current classification | Established evidence | Remaining gap | Phase 2 verification or decision method |
| --- | --- | --- | --- | --- |
| Existing configuration routes | `VERIFIED` | `P1-BASELINE`: `DATABASE_URL`; `COMMERCE_DB_URL → FRUIT_DB_URL → default`; direct `FRUIT_DB_URL` | None for inventoried owners | Preserve exact owner-to-route map in Configuration Authority Contract |
| Existing precedence behavior | `VERIFIED` for inventoried owners | `P1-BASELINE` | No canonical repository-wide precedence exists | Compare compatibility impact and select one `PROPOSED` precedence contract |
| Default URL divergence | `VERIFIED` | `P1-BASELINE`: canonical default includes `:5432`; `app.main` default omits the port | Whether omission is intentional or accidental | Byte-exact source review plus PostgreSQL-equivalence analysis; record compatibility decision |
| Canonical configuration resolver | `UNRESOLVED` | Fragmented inline resolution in `P1-BASELINE` | No selected resolver owner | Evaluate minimal dependency direction and select one `PROPOSED` owner |
| Conflicting variables | `UNRESOLVED` | Multiple precedence routes verified | No conflict policy | Define fail-fast, precedence, and diagnostic contract without reading secret values |
| Missing or invalid URL behavior | `PARTIALLY_VERIFIED` | Existing defaults visible in `P1-BASELINE` | No repository-wide validation/failure contract | Static call-path review and proposed error contract |
| Secret-handling boundary | `UNRESOLVED` | No Phase 1 secret-output contract | Logging and diagnostic exposure not classified | Inspect configuration logging paths without printing values; author redaction contract |
| Resolution timing | `PARTIALLY_VERIFIED` | Seven module-scope constructors in `P1-BASELINE`; five reached during `P1-RUNTIME` | Later conditional/callback timing remains unknown | Static reachability map plus safe sentinel probes only where side effects are blocked |

## 6. Engine authority inputs

| Decision input | Current classification | Established evidence | Remaining gap | Phase 2 verification or decision method |
| --- | --- | --- | --- | --- |
| Constructor-owner inventory | `VERIFIED` | Seven owners in `P1-BASELINE` and `P1-GAPS` | Constructors outside inspected `app/**` boundary not asserted | Retain repository-boundary statement |
| `app.main` import graph | `VERIFIED` within sentinel boundary | Five distinct constructors in `P1-RUNTIME` | Real engine operation not observed | Use as topology evidence, not connectivity evidence |
| Canonical engine owner | `UNRESOLVED` | `app.db.database.engine` has 27 direct imports, but other owners exist | Popularity does not itself grant authority | Compare dependency direction, compatibility, and lifecycle suitability; select `PROPOSED` owner |
| Permitted engine count per process | `UNRESOLVED` | Five identities reached under `app.main` sentinel | Desired multiplicity not decided | Define single-owner and exceptional multi-engine rules |
| Construction timing | `PARTIALLY_VERIFIED` | Module-scope creation verified | Target startup/lazy timing not decided | Specify import-time prohibition or exception policy |
| Reuse semantics | `PARTIALLY_VERIFIED` | Naver collector reuses canonical engine; other services construct engines | Repository-wide intended reuse unknown | Produce identity and consumer map; define requested target reuse |
| Pool configuration authority | `PARTIALLY_VERIFIED` | Canonical owner supplies `pool_pre_ping=True`; others observed without it | Target pool policy absent | Inventory constructor kwargs and specify one policy owner |
| Disposal ownership | `PARTIALLY_VERIFIED_NEGATIVE_EVIDENCE` | Zero inspected lifecycle/disposal signals in `P1-GAPS` | Semantic lifecycle may use other indirection; target contract absent | Complete targeted symbol/call-path review; specify owner and disposal events |
| Repeated initialization/disposal | `UNRESOLVED` | No idempotency contract established | Re-entry behavior unknown | Define state machine and failure/idempotency requirements |
| Construction failure behavior | `UNRESOLVED` | No repository-wide contract established | Startup vs request-time failure policy unknown | Map entry-point expectations and author fail-closed behavior |

## 7. Dependency and injection inputs

| Decision input | Current classification | Established evidence | Remaining gap | Phase 2 verification or decision method |
| --- | --- | --- | --- | --- |
| Canonical engine consumer graph | `VERIFIED` within direct-import boundary | 27 direct imports in `P1-BASELINE` | Dynamic or indirect access not fully classified | Generate static dependency map and preserve boundary label |
| Logger-owned engine boundary | `VERIFIED` | Analytics, context, and impression loggers construct engines | Target ownership rule absent | Decide whether loggers receive connection/engine/service dependency |
| Collector-owned engine boundary | `VERIFIED` | Market collector constructs engine | Target ownership rule absent | Decide injected dependency and process-lifecycle applicability |
| Pipeline-owned engine boundary | `VERIFIED` | Recommendation pipeline constructs engine | Target ownership rule absent | Decide injected dependency and transaction boundary preservation |
| UI analytics-logger boundary leak | `VERIFIED` statically | `streamlit_app.py` imports `analytics_logger.engine` | Safe runtime binding not observed | Define prohibited utility ownership and future migration seam |
| Admin canonical-engine import | `VERIFIED` statically | `admin_dashboard.py` imports `app.db.database.engine` | Safe runtime binding not observed | Define future injection seam; defer runtime validation until safe |
| Caller-provided connection compatibility | `VERIFIED` | Preference and Session Context service/store accept caller connections | Whether engine injection should replace connection passing | Preserve explicit connection compatibility unless later migration is authorized |
| Consumer transaction ownership | `VERIFIED` | `engine.connect` and `engine.begin` contexts in consumers | Target transaction authority not yet decided | Separate engine authority from transaction authority; record preserved boundaries |
| Allowed dependency form | `UNRESOLVED` | Current code mixes engine import and caller connection | Engine vs connection vs service injection target absent | Evaluate per consumer class and define permitted forms |

## 8. Runtime entry-point inputs

| Entry point | Current classification | Established evidence | Remaining gap | Phase 2 verification or decision method |
| --- | --- | --- | --- | --- |
| FastAPI `app.main` | `VERIFIED` within sentinel import boundary | Five constructors and bindings in `P1-RUNTIME` | Real startup/shutdown behavior and disposal absent | Define lifespan contract; later verify using sentinel lifecycle harness |
| Streamlit application | `PARTIALLY_VERIFIED` | Static engine import and module-level DB-capable paths in `P1-GAPS` | Safe runtime topology absent | Design configuration/lifecycle seam before any import probe |
| Admin dashboard | `PARTIALLY_VERIFIED` | Canonical import and multiple module-level `load_df` calls | Safe runtime topology absent | Design query and engine seam before any import probe |
| Generator service | `PARTIALLY_VERIFIED` | Static constructor reachability in `P1-BASELINE` | Process lifecycle and disposal unknown | Map executable entry and dependency graph without execution first |
| Recommendation pipeline | `PARTIALLY_VERIFIED` | Static owner and `app.main` sentinel reachability | Standalone process behavior unknown | Separate import and standalone execution contracts |
| Market collector | `PARTIALLY_VERIFIED` | Static owner and `app.main` sentinel reachability | Scheduled/worker lifecycle unknown | Identify launch mechanisms and specify per-process ownership |
| Health checks | `UNRESOLVED` | No Phase 1 health-check interaction contract | Whether health checks acquire persistence resources | Static endpoint/call-path inspection and proposed no-side-effect policy |

## 9. Test substitution inputs

| Decision input | Current classification | Established evidence | Remaining gap | Phase 2 verification or decision method |
| --- | --- | --- | --- | --- |
| Direct `create_engine` use in tests | `VERIFIED` absent for inspected text signal | 0 of 257 `test_*.py` files in `P1-GAPS` | Aliases or indirect construction not excluded | AST import/call resolution across tests |
| DB environment-variable substitution | `VERIFIED` absent for inspected names | 0 matches for three known variables in `P1-GAPS` | Other fixture/config mechanisms not excluded | Inspect fixtures and test configuration files |
| Generic monkeypatch use | `VERIFIED` | 14 matching test files in `P1-GAPS` | DB-specific substitution not established | Classify patched symbols, not only the keyword |
| Engine-owner imports in tests | `VERIFIED` for inspected pattern | 11 matching files in `P1-GAPS` | Import-time side effects per test not classified | Map collection-time imports and isolation behavior |
| Fake-connection compatibility | `VERIFIED` for known Preference test boundary | `_FakeConnection` evidence in `P1-BASELINE` | Repository-wide fake contract absent | Inventory fake connection protocols and required methods |
| Canonical injection seam | `UNRESOLVED` | No repository-wide seam established | Target fixture mechanism absent | Propose fixture/provider boundary consistent with canonical owner |
| Real DB/network fail-closed guard | `UNRESOLVED` repository-wide | Sentinel probe demonstrates one bounded technique | No universal test protection | Define guard fixture/process policy and later verification suite |
| Cleanup and disposal in tests | `UNRESOLVED` | No disposal contract | Isolation/leak behavior unknown | Define fixture scope, cleanup ordering, and assertions |

## 10. Migration and compatibility inputs

| Decision input | Current classification | Established evidence | Remaining gap | Phase 2 verification or decision method |
| --- | --- | --- | --- | --- |
| Highest-value first seam | `UNRESOLVED` | Seven owners and reachability are established | Risk/benefit ordering not decided | Compare fan-out, side effects, compatibility, and testability |
| Environment compatibility | `PARTIALLY_VERIFIED` | Existing variables and precedence known | Deprecation/alias duration absent | Define compatibility table and migration stages |
| Import compatibility | `PARTIALLY_VERIFIED` | Direct engine imports inventoried | Re-export or adapter policy absent | Map consumers and propose bounded adapter seam |
| Transaction compatibility | `PARTIALLY_VERIFIED` | Current consumer-owned contexts established | Future ownership split absent | Preserve existing semantics unless explicitly changed later |
| Rollback boundary | `UNRESOLVED` | No implementation plan authorized | Reversible unit not selected | Define document-level migration sequence only; implementation later |

## 11. Decision sequencing

The evidence supports the following Phase 2 decision order:

1. Configuration Authority Contract.
2. Engine Ownership and Lifecycle Contract.
3. Persistence Dependency / Injection Map.
4. Runtime Startup and Shutdown Resource Map.
5. Test Configuration and Substitution Contract.
6. Compatibility and Migration Seam Register.
7. Phase 2 Verification Plan.
8. Phase 2 Completion Readiness Review.

Configuration authority precedes engine authority because constructor identity and
lifecycle cannot be specified safely while configuration precedence remains
ambiguous. Engine authority precedes dependency and runtime maps because those maps
must name an explicit owner rather than infer one from current import popularity.

## 12. Immediate evidence gaps

Before selecting the canonical contracts, Phase 2 should obtain bounded read-only
evidence for:

1. exact constructor keyword arguments and configuration expressions for all seven
   owners;
2. configuration logging and diagnostic exposure;
3. executable launch mechanisms for API, UI, collector, pipeline, and worker paths;
4. health-check persistence interaction;
5. test fixture, conftest, and indirect engine-construction behavior; and
6. fake-connection protocol coverage.

These inspections may be grouped into a single read-only evidence wave if the output
preserves file, line, and classification boundaries.

## 13. Authority result

| Authority | Result |
| --- | --- |
| Phase 2 state | `OPEN` |
| Contract-input matrix | `AUTHORED` |
| Current-state claims | Classified by evidence boundary |
| Target architecture decisions | `NOT_YET_MADE` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Perform the bounded read-only Phase 2 evidence wave listed in Section 12 |
