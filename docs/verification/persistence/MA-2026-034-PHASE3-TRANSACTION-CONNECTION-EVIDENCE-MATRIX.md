# MA-2026-034 Phase 3 Transaction / Connection Evidence Matrix

## 1. Matrix identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 3 — Transaction / Connection Boundary Contract` |
| Artifact | `Transaction / Connection Evidence Matrix` |
| Governing ADA | `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT` |
| Governing ADA commit | `d5c032f17db797154dfa31050e9ae1e36e9ea03f` |
| Matrix date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This matrix defines the evidence inputs, unknowns, and inspection waves required to
design the Phase 3 transaction and connection boundary contracts.

It records only facts already established by the Phase 1 and Phase 2 evidence chain.
It does not infer transaction ownership from function names, signatures, or engine
imports. It does not make target architecture decisions.

## 3. Evidence classification

| Classification | Meaning |
| --- | --- |
| `VERIFIED_STATIC` | Directly established through source inspection |
| `VERIFIED_INSTRUMENTED` | Established through non-resource instrumentation |
| `TEST_CONTRACT` | Present as a test or fake expectation only |
| `REPORTED` | Present in an established document but not independently verified |
| `UNKNOWN` | Evidence is insufficient |
| `NOT_APPLICABLE` | Boundary does not participate in persistence |

Target rules from Phase 2 are labeled `TARGET_CONTRACT`, not current facts.

## 4. Governing evidence chain

| Evidence | Commit | Relevance |
| --- | --- | --- |
| Phase 1 Persistence Ownership Baseline | `df4d07459ec9733afeb6311412178aa85f50bf26` | Static ownership and consumer inventory |
| App.main Sentinel Import Observation | `eb74b7557630ae63e1fe48385a1c66844581a8fb` | Import graph and engine binding observation |
| Phase 1 Gap Classification | `e1b67c0eae3267821e4c2db23a666eb2a743fb20` | Closure gaps and unresolved ownership |
| Phase 2 Contract-Input Evidence Matrix | `7fd7cec5355b0fad5c90e861d37949108d666840` | Initial configuration and engine inputs |
| Phase 2 Wave 1 Classification | `23d958c3ad2e4b3dfcb44fe507cf7e9c1d1bb475` | Static configuration/engine classification |
| Phase 2 Wave 2 Classification | `2ab61bfbc1d9d2609e69573094bbf3fbbfefef46` | Router, launch, test seam, and caller-connection evidence |
| Phase 2 Dependency / Injection Map | `6ead4ded577650b668faf680565349fbcccf264d` | Target dependency direction |
| Phase 2 Test Substitution Contract | `006706f6274c9704ca7fe4d1b9645aa31f44ca8d` | Target offline substitution rules |
| Phase 2 Migration Seam Register | `fdd5b6e1f540e5ee585c14f15b3c0e72c7891b94` | 16 seams and proposed `I0–I7` waves |
| Phase 2 Completion | `6182a2ad5cc81db86dba55e3e500bc8aae34fba2` | Phase 2 closure and carry-forward obligations |

## 5. Established current facts

### 5.1 Instrumented engine facts

An instrumented `app.main` import observed five `create_engine` calls while blocking
real engine creation, database access, network access, filesystem writes, and
subprocess execution.

| Ordinal | Observed owner | Classification |
| ---: | --- | --- |
| 1 | `app/db/database.py:4` | `VERIFIED_INSTRUMENTED` |
| 2 | `app/services/market/collector.py:28` | `VERIFIED_INSTRUMENTED` |
| 3 | `app/services/recommendation_pipeline.py:22` | `VERIFIED_INSTRUMENTED` |
| 4 | `app/services/analytics_logger.py:14` | `VERIFIED_INSTRUMENTED` |
| 5 | `app/main.py:21` | `VERIFIED_INSTRUMENTED` |

This proves engine-construction multiplicity in the observed import graph. It does not
prove connection acquisition, transaction ownership, commit, rollback, or release.

### 5.2 Caller-provided connection consumers

Phase 2 Wave 2 statically identified nine functions with a `conn` parameter.

| Path | Function | Observed direct connection calls | Classification |
| --- | --- | --- | --- |
| `app/services/preference/service.py:17` | `update_user_preference` | None in the function body | `VERIFIED_STATIC` |
| `app/services/preference/service.py:39` | `get_user_preference` | None in the function body | `VERIFIED_STATIC` |
| `app/services/preference/service.py:63` | `get_preference_profile` | None in the function body | `VERIFIED_STATIC` |
| `app/services/preference/store.py:12` | `update_preference` | `conn.execute` | `VERIFIED_STATIC` |
| `app/services/preference/store.py:123` | `get_preference` | `conn.execute` | `VERIFIED_STATIC` |
| `app/services/session_context/service.py:14` | `update_session_context` | None in the function body | `VERIFIED_STATIC` |
| `app/services/session_context/service.py:40` | `get_session_context` | None in the function body | `VERIFIED_STATIC` |
| `app/services/session_context/store.py:12` | `update_session_context_record` | `conn.execute` | `VERIFIED_STATIC` |
| `app/services/session_context/store.py:75` | `get_session_context_record` | `conn.execute` | `VERIFIED_STATIC` |

The absence of a direct call in a service function does not establish transaction
ownership or non-participation. Call propagation requires further inspection.

### 5.3 Existing connection-like test double

| Path | Class | Observed protocol | Classification |
| --- | --- | --- | --- |
| `tests/services/preference/test_store.py:42` | `_FakeConnection` | `execute` | `TEST_CONTRACT` |

The fake proves an `execute` seam for that test only. It does not prove production
connection lifecycle, commit, rollback, close, context-manager, or transaction
protocols.

### 5.4 Test import seams

Phase 2 Wave 2 identified ten tests importing current engine-owning modules and no
module-scope calls in that inspection. This is `VERIFIED_STATIC` for the inspected
syntax and does not prove pytest collection safety under future changes.

## 6. Target contracts carried from Phase 2

| Target rule | Classification |
| --- | --- |
| Configuration owner is `app.core.config` | `TARGET_CONTRACT` |
| Engine owner is `app.db.database` | `TARGET_CONTRACT` |
| Engine construction occurs at explicit bootstrap | `TARGET_CONTRACT` |
| Dependency direction is composition root → service → connection → store | `TARGET_CONTRACT` |
| Preference and Session Context caller-connection seams are preserved | `TARGET_CONTRACT` |
| Unit tests deny real resources by default | `TARGET_CONTRACT` |

Phase 3 must define transaction and connection rules consistent with these targets.

## 7. Initial boundary matrix

| Boundary family | Acquisition owner | Release owner | Begin owner | Commit owner | Rollback owner | Current evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Preference service/store | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `conn` propagation and `execute` verified |
| Session Context service/store | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `conn` propagation and `execute` verified |
| Recommendation pipeline | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Engine construction observed |
| Analytics logger | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Engine construction observed |
| Market collector | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Engine construction observed |
| FastAPI `app.main` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Engine construction observed |
| Streamlit UI | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Runtime topology not safely proven |
| Administrative dashboard | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Runtime topology not safely proven |
| Direct workers/scripts | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Main guards inventoried; execution not inspected |
| Tests and fixtures | Test-specific | Test-specific | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | One `execute`-only fake verified |

## 8. Mandatory unknowns

The following remain `UNKNOWN` until bounded inspection establishes evidence:

- all `connect`, `begin`, `begin_nested`, `commit`, `rollback`, and `close` call sites;
- context-manager and generator-based connection scopes;
- session or ORM transaction use, if any;
- DB-API cursor and implicit transaction behavior;
- autocommit or isolation-level configuration;
- transaction propagation through service-to-store calls;
- nested service call behavior;
- repeated, re-entrant, and concurrent use;
- exception, retry, cancellation, timeout, and partial-failure behavior;
- read-only versus mutating operation classification;
- commit-after-write assumptions;
- rollback and cleanup guarantees;
- connection leakage or pool return behavior;
- actual Streamlit and admin runtime composition;
- fixture and monkeypatch ordering before risky imports; and
- transaction compatibility across the 27 direct engine-import cohorts.

## 9. Bounded evidence waves

### Wave 1 — Static transaction primitive census

Collect syntax-aware evidence for:

- connection acquisition and context-manager calls;
- transaction begin, commit, rollback, close, and disposal calls;
- SQLAlchemy and DB-API imports;
- functions receiving or returning connection-like values;
- explicit exception, retry, finally, and cleanup structures; and
- module-scope persistence operations.

No module import or code execution is authorized.

### Wave 2 — Call-path and mutation classification

Trace bounded call paths for Preference, Session Context, recommendation pipeline,
analytics logger, market collector, FastAPI, Streamlit, admin, and direct workers.
Classify read-only and mutating operations without executing them.

### Wave 3 — Safe sentinel protocol observation

Where static evidence is insufficient, use non-networking sentinel engines,
connections, transactions, and context managers. Block real engines, database
connections, network access, writes, and subprocess execution.

### Wave 4 — Test and compatibility seam classification

Inspect fixtures, fakes, monkeypatch ordering, collection safety, transaction protocol
coverage, and compatibility risks. No test implementation is authorized.

Each wave requires separate bounded authority or a script fully within this ADA.

## 10. Required evidence output fields

Every classified boundary must record:

```text
path
line
symbol
caller
callee
operation_kind
read_or_write
connection_source
acquisition_owner
release_owner
transaction_begin_owner
commit_owner
rollback_owner
scope_lifetime
propagation_method
exception_behavior
cancellation_behavior
retry_behavior
nested_behavior
test_substitution_seam
evidence_classification
compatibility_risk
```

Unknown values must be emitted as `UNKNOWN`.

## 11. Decision boundary

This matrix does not decide:

- the canonical transaction or unit-of-work owner;
- whether services or composition roots own scopes;
- whether stores may commit or roll back;
- nested-transaction policy;
- migration order or implementation scope;
- concrete adapters, protocols, fixtures, or hooks; or
- Phase 3 completion eligibility.

Those decisions require the authorized evidence waves and separately established
architecture contracts.

## 12. Non-mutation and authority result

```text
PHASE_3 = OPEN
TRANSACTION_CONNECTION_EVIDENCE_MATRIX = ESTABLISHED_UPON_SEAL
TARGET_ARCHITECTURE_DECISIONS = NOT_YET_MADE
PRODUCTION_WRITE_AUTHORITY = NONE
TEST_WRITE_AUTHORITY = NONE
DATABASE_MUTATION_AUTHORITY = NONE
DATABASE_NETWORK_EXECUTION_AUTHORITY = NONE
CONSUMER_MIGRATION_AUTHORITY = NONE
PHASE_3_COMPLETION_AUTHORITY = NOT_ISSUED
```

The next action is a bounded read-only Phase 3 Evidence Wave 1 static transaction
primitive census.
