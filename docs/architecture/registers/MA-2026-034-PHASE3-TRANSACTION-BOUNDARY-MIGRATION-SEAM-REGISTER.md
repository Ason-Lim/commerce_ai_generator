# MA-2026-034 Phase 3 Transaction Boundary Migration Seam Register

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Register: `MA-2026-034-PHASE3-TRANSACTION-BOUNDARY-MIGRATION-SEAM-REGISTER`
- Register version: `1.0`
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Immediate predecessor: `MA-2026-034-PHASE3-CALLER-PROVIDED-CONNECTION-COMPATIBILITY-MAP`

## 2. Purpose

This register converts the Phase 3 evidence and established contracts into bounded migration seams. It identifies current acquisition groups, target ownership, compatibility obligations, risk, prerequisites, rollback conditions, and proposed implementation waves.

The register is a design artifact only. It does not authorize code changes, tests, database activity, migration execution, or verification execution.

## 3. Governing rules

Every registered seam is governed by these established rules:

- the scope that acquires a connection owns release;
- a supplied connection is borrowed;
- consumers cannot acquire, close, commit, roll back, or dispose;
- one write business operation has one transaction owner;
- click preference and session-context writes share one UoW;
- independent batch records default to per-item atomicity;
- external network waits do not occur inside DB transactions;
- DDL does not execute as an ordinary runtime UoW;
- nested transactions and savepoints are denied by default;
- unknown commit outcome is never blindly retried;
- failed or uncertain connections are never reused.

## 4. Evidence inventory

Wave 4 identified 70 persistence-relevant acquisition calls under `app/`:

| Mode | Count |
|---|---:|
| `engine.connect()` | 29 |
| `engine.begin()` | 41 |
| Total | 70 |

The same evidence identified nine required caller-connection functions and 25 bounded application/test calls. The Caller-Provided Connection Compatibility Map registered `CP-01` through `CP-10` as compatibility inputs.

## 5. Risk vocabulary

| Risk | Meaning |
|---|---|
| `LOW` | Localized borrowed-connection or test-surface change |
| `MEDIUM` | Acquisition relocation or read-scope behavior may change |
| `HIGH` | Atomicity, DDL, external I/O, or multi-consumer transaction behavior may change |
| `CRITICAL` | Potential schema mutation, unknown commit outcome, or cross-cutting lifecycle impact |

## 6. Migration-state vocabulary

Every seam begins as `REGISTERED_NOT_AUTHORIZED`.

Later authorized execution may advance a seam only through:

1. `AUTHORIZED`
2. `IMPLEMENTED_IN_ISOLATION`
3. `STATICALLY_VERIFIED`
4. `NON_NETWORKING_TEST_VERIFIED`
5. `REGRESSION_VERIFIED`
6. `MIGRATED`
7. `LEGACY_PATH_REMOVED`

No status in this register implies that any transition has occurred.

## 7. Acquisition-group census

| Group | Paths | Connect | Begin | Primary role |
|---|---|---:|---:|---|
| G-01 API application | `app/main.py` | 5 | 0 | request reads |
| G-02 Interaction logging | `analytics_logger.py`, `context_logger.py`, `impression_logger.py` | 0 | 4 | request/event writes |
| G-03 Simple DB readers | `coupang_review_matcher.py`, `db_product_collector.py`, `market/collector.py` | 3 | 0 | bounded reads |
| G-04 Collector read/write pairs | `collector_v4_runner.py`, Kurly collectors, `price_detail_enricher.py` | 5 | 5 | per-item collection |
| G-05 Market intelligence engines | market collector/signal/cluster/price modules | 5 | 10 | DDL, fetch, update |
| G-06 Product intelligence engines | attribute, cluster, family, identity, quality, variety, recommendation modules | 8 | 17 | DDL, fetch, update |
| G-07 Naver services | `naver_datalab_service.py`, `naver_shopping_api_collector.py` | 0 | 4 | read/write and DDL/write |
| G-08 Admin UI | `app/ui/admin_dashboard.py` | 2 | 0 | pandas reads |
| G-09 Streamlit UI | `app/ui/streamlit_app.py` | 1 | 1 | preference read/write |
| Total | 70 acquisition calls | 29 | 41 | — |

The grouping is a migration unit abstraction. Each underlying acquisition remains independently subject to verification.

## 8. Core migration seam register

| ID | Current seam | Target boundary | Risk | Dependencies | State |
|---|---|---|---|---|---|
| TB-01 | `app.main` has five direct read acquisitions | request composition-owned read scopes | `MEDIUM` | CP-02, acquisition contract | `REGISTERED_NOT_AUTHORIZED` |
| TB-02 | `analytics_logger.log_search` owns a local transaction | explicit search interaction UoW owner | `HIGH` | UoW and failure contracts | `REGISTERED_NOT_AUTHORIZED` |
| TB-03 | `analytics_logger.log_product_click` owns click transaction | explicit click UoW preserving shared connection | `CRITICAL` | CP-03, CP-04, CP-05 | `REGISTERED_NOT_AUTHORIZED` |
| TB-04 | context and impression loggers own local transactions | explicit event UoW composition | `HIGH` | failure semantics | `REGISTERED_NOT_AUTHORIZED` |
| TB-05 | simple reader services acquire directly | injected read connection or read-owner adapter | `MEDIUM` | acquisition contract | `REGISTERED_NOT_AUTHORIZED` |
| TB-06 | collector fetch functions acquire directly | bounded read phase outside external I/O | `HIGH` | batch UoW contract | `REGISTERED_NOT_AUTHORIZED` |
| TB-07 | collector update functions open per-call transactions | explicit per-item UoW owner | `HIGH` | idempotency and retry rules | `REGISTERED_NOT_AUTHORIZED` |
| TB-08 | market intelligence modules mix DDL, fetch, update entry points | DDL removed from runtime; fetch/read and update/UoW separated | `CRITICAL` | TB-15, migration authority | `REGISTERED_NOT_AUTHORIZED` |
| TB-09 | product intelligence modules mix DDL, fetch, update entry points | DDL removed; per-item update UoWs | `CRITICAL` | TB-15, batch tests | `REGISTERED_NOT_AUTHORIZED` |
| TB-10 | `naver_datalab_service` uses `begin` for cached read and write | read uses read scope; write uses explicit UoW | `HIGH` | behavior verification | `REGISTERED_NOT_AUTHORIZED` |
| TB-11 | shopping collector combines DDL and inserts | DDL migration separated from insert UoW | `CRITICAL` | TB-15 | `REGISTERED_NOT_AUTHORIZED` |
| TB-12 | admin dashboard acquires for pandas calls | injected/read-owner connection with full materialization | `MEDIUM` | pandas SQL input classification | `REGISTERED_NOT_AUTHORIZED` |
| TB-13 | Streamlit owns one read and one write acquisition | UI composition adapter preserving behavior | `HIGH` | CP-06, CP-07 | `REGISTERED_NOT_AUTHORIZED` |
| TB-14 | nine `Any` connection parameters | minimal borrowed structural protocols | `MEDIUM` | CP-01, CP-08, CP-09 | `REGISTERED_NOT_AUTHORIZED` |
| TB-15 | 14 runtime DDL sites / 124 DDL statements | separately authorized migration system only | `CRITICAL` | DB/migration authority | `REGISTERED_NOT_AUTHORIZED` |
| TB-16 | no transaction-capable test double | bounded non-networking owner fake/factory | `HIGH` | CP-10, test authority | `REGISTERED_NOT_AUTHORIZED` |
| TB-17 | no persistence failure semantics tests identified | staged failure/cancellation test suite | `HIGH` | failure contract, test authority | `REGISTERED_NOT_AUTHORIZED` |
| TB-18 | explicit engine disposal not identified | canonical shutdown composition disposal | `HIGH` | Phase 2 runtime map | `REGISTERED_NOT_AUTHORIZED` |
| TB-19 | module-scope engine construction remains distributed | canonical engine authority binding | `CRITICAL` | Phase 2 contracts, implementation ADA | `REGISTERED_NOT_AUTHORIZED` |
| TB-20 | no runtime conformance evidence | sentinel then authorized bounded integration verification | `HIGH` | verification plan | `REGISTERED_NOT_AUTHORIZED` |

## 9. Compatibility cross-reference

| Compatibility seam | Migration seam | Preservation rule |
|---|---|---|
| CP-01 | TB-14 | replace `Any` without breaking current callers |
| CP-02 | TB-01 | preserve request read behavior and lifetime |
| CP-03 | TB-03 | click transaction moves as one owner boundary |
| CP-04 | TB-03, TB-14 | preference same-connection forwarding preserved |
| CP-05 | TB-03, TB-14 | session-context same-connection forwarding preserved |
| CP-06 | TB-13 | Streamlit read behavior preserved |
| CP-07 | TB-13 | Streamlit preference write occurs exactly once |
| CP-08 | TB-14, TB-16 | execution-only store tests stay minimal |
| CP-09 | TB-14, TB-16 | opaque service substitutions remain non-networking |
| CP-10 | TB-16, TB-17 | transaction-owner fake added without widening store protocol |

## 10. DDL seam subregister

The following evidence-classified `ensure_columns` families are governed by TB-15:

| DDL seam | Module family | Current mode | Target |
|---|---|---|---|
| DDL-01 | market collector v5 | runtime `begin` | migration artifact |
| DDL-02 | market collector v51 | runtime `begin` | migration artifact |
| DDL-03 | market identity cluster v53 | runtime `begin` | migration artifact |
| DDL-04 | market representative price v54 | runtime `begin` | migration artifact |
| DDL-05 | market signal propagation v52 | runtime `begin` | migration artifact |
| DDL-06 | Naver shopping collector | runtime `begin` | migration artifact |
| DDL-07 | product attribute v8 | runtime `begin` | migration artifact |
| DDL-08 | product cluster representative v5 | runtime `begin` | migration artifact |
| DDL-09 | product family variant v6 | runtime `begin` | migration artifact |
| DDL-10 | product identity cluster v4 | runtime `begin` | migration artifact |
| DDL-11 | product quality v9 | runtime `begin` | migration artifact |
| DDL-12 | product quality v10 runner | runtime `begin` | migration artifact |
| DDL-13 | product variety v7 | runtime `begin` | migration artifact |
| DDL-14 | recommendation intelligence v55 | runtime `begin` | migration artifact |

All 124 statements remain execution-prohibited without explicit migration and database-mutation authority.

## 11. Proposed implementation waves

The following waves are planning labels only.

### I0 — Test and protocol foundation

- TB-14 minimal connection protocols
- TB-16 transaction-owner fake/factory
- TB-17 failure and cancellation seam tests

Exit condition: no real engine, DB, or network; existing test compatibility preserved.

### I1 — Canonical composition primitives

- TB-19 canonical engine binding
- reusable read-owner and UoW-owner composition primitives
- TB-18 shutdown disposal seam in testable form

Exit condition: ownership can be substituted and observed without consumer migration.

### I2 — Borrowed-connection services

- preference and session-context functions under TB-14
- same-connection identity assertions
- no consumer lifecycle action

Exit condition: CP-01, CP-04, CP-05, CP-08, and CP-09 verified.

### I3 — Interaction UoWs

- TB-02, TB-03, TB-04
- click atomicity as one indivisible migration

Exit condition: success, rollback, cancellation, and unknown-outcome tests pass in isolation.

### I4 — API and UI read/write boundaries

- TB-01, TB-12, TB-13
- materialized reads and UI compatibility adapters

Exit condition: API/UI behavior remains compatible without duplicate acquisition.

### I5 — Collector per-item boundaries

- TB-05, TB-06, TB-07, TB-10
- external I/O outside transaction

Exit condition: per-item atomicity, bounded retry, and partial batch outcome verified.

### I6 — Intelligence pipeline boundaries

- TB-08, TB-09, TB-11 excluding DDL execution
- fetch/compute/update separation

Exit condition: no external wait or DDL inside runtime UoW.

### I7 — DDL extraction

- TB-15 and DDL-01 through DDL-14

Exit condition: runtime paths contain no self-migrating DDL; separate migration authority is still required for execution.

### I8 — Lifecycle and conformance verification

- TB-18, TB-20
- shutdown, invalidation, cancellation, regression, and runtime sentinel evidence

Exit condition: Phase 3 verification gates satisfied under separately issued authority.

## 12. Wave-order constraints

- I0 precedes all production migrations.
- I1 precedes I3 through I6.
- I2 precedes I3.
- TB-03 must migrate atomically; it may not be split between preference and session-context waves.
- DDL extraction design may proceed early, but DDL execution remains separately authorized.
- Old and new acquisition owners SHALL NOT both be active for one operation.
- I8 cannot establish Phase 3 completion by itself.

## 13. Per-seam preflight

Before any seam receives implementation authority, its preflight SHALL establish:

1. exact parent commit and governing authorization;
2. clean worktree and empty index;
3. exact files permitted to change;
4. current caller and test surface;
5. target owner and atomicity set;
6. rollback method for source changes;
7. non-networking verification commands;
8. regression scope;
9. absence of DB/network execution unless separately authorized;
10. no overlapping active migration seam.

## 14. Per-seam rollback rule

Implementation rollback SHALL restore the previous code path without changing database state. If a seam cannot be rolled back without schema or data action, it must be reclassified under migration authority before implementation.

Feature flags or compatibility adapters MAY support rollback only when they cannot activate two acquisition owners simultaneously.

## 15. Verification matrix

| Seam class | Minimum later verification |
|---|---|
| Read owner | one acquisition, materialized result, one release |
| Write owner | same connection, one success exit, rollback on failure |
| Click UoW | preference + session context atomicity |
| Batch item | per-item isolation and fresh context after failure |
| Protocol | compatible real adapter and minimal fake |
| DDL extraction | no runtime DDL reachability |
| Shutdown | quiesce, drain, release, dispose ordering |
| Failure | primary/cleanup preservation and no blind retry |

## 16. Register invariants

- `REGISTERED` is not `AUTHORIZED`.
- Documentation commits do not change runtime conformance.
- No seam may claim completion from static evidence alone.
- No migration may introduce a real DB dependency into unit tests.
- No seam may weaken caller-provided connection compatibility without a separate decision.
- No seam may widen the atomicity set silently.
- No DDL seam may run under ordinary application authority.

## 17. Authority limits

This register does not authorize:

- source or test writes;
- type, engine, connection, or UoW implementation;
- database or network execution;
- DDL or data migration;
- any I0–I8 implementation wave;
- consumer migration;
- verification execution;
- Phase 3 completion.

## 18. Register result

- `FINAL_RESULT=APPROVED_FOR_ESTABLISHMENT`
- `register=MA-2026-034-PHASE3-TRANSACTION-BOUNDARY-MIGRATION-SEAM-REGISTER`
- `phase_3=OPEN`
- `persistence_acquisition_sites=70`
- `connect_sites=29`
- `begin_sites=41`
- `core_migration_seams=TB_01_THROUGH_TB_20`
- `compatibility_seams=CP_01_THROUGH_CP_10`
- `DDL_seams=DDL_01_THROUGH_DDL_14`
- `proposed_implementation_waves=I0_THROUGH_I8`
- `migration_authorization=NOT_ISSUED`
- `runtime_conformance=NOT_VERIFIED`
- `implementation_authorization=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=PHASE3_VERIFICATION_PLAN`

## 19. Establishment rule

This register shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment must include no production or test code, no application import, no test execution, no database or application-network execution, and no unrelated repository mutation.
