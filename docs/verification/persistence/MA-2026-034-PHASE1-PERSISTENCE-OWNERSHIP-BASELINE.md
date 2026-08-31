# MA-2026-034 Phase 1 Persistence Ownership Baseline

**Architecture Program:** MA-2026-034

**Authorization:** ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE

**Evidence Baseline:** `e0b18c5e7c455504091a8c84a23c4d45edfe085a`

**Date:** 2026-08-31

**Status:** EVIDENCE BASELINE ESTABLISHED / PHASE 1 NOT COMPLETE

---

## 1. Purpose

This artifact consolidates read-only Evidence Waves 1–3 for the initial
Persistence Ownership Baseline. It records verified repository facts,
bounded interpretations, and unresolved conditions. It does not authorize
production or test modification.

Evidence classifications:

```text
VERIFIED
Direct repository or static-analysis evidence at the authoritative HEAD.

PARTIALLY VERIFIED
Static evidence exists, but runtime behavior or complete coverage is not proven.

UNRESOLVED
Evidence is insufficient for an architecture conclusion.
```

---

## 2. Evidence Acquisition State

```text
Wave 1 — Configuration / Engine / Connection / Transaction Scan
PASS

Wave 2 — Engine Provenance / Transaction Owner / Test Substitution
PASS

Wave 3 — Import-Time Topology / Test Isolation / Disposal Contract
PASS

Repository mutation during acquisition
NONE
```

---

## 3. Engine Constructor Owners — VERIFIED

Seven tracked Python modules construct SQLAlchemy engines at module scope:

```text
app/db/database.py
app/main.py
app/services/analytics_logger.py
app/services/context_logger.py
app/services/impression_logger.py
app/services/market/collector.py
app/services/recommendation_pipeline.py
```

`app/db/database.py` uses `pool_pre_ping=True`. The other six observed
constructors do not declare that option in their constructor expression.

Decision state:

```text
SINGLE REPOSITORY-WIDE ENGINE OWNER
NOT ESTABLISHED

DISTRIBUTED MODULE-SCOPE ENGINE CONSTRUCTION
VERIFIED
```

---

## 4. Configuration Precedence — VERIFIED

| Owner group | Precedence | Default |
| --- | --- | --- |
| `app/db/database.py` via `app/core/config.py` | `DATABASE_URL` | `localhost:5432/dashboard_db` |
| `app/main.py` | `FRUIT_DB_URL` | `localhost/dashboard_db` |
| analytics/context/impression loggers | `COMMERCE_DB_URL → FRUIT_DB_URL` | `localhost:5432/dashboard_db` |
| market collector / recommendation pipeline | `COMMERCE_DB_URL → FRUIT_DB_URL` | `localhost:5432/dashboard_db` |

The application runtime default omits the explicit port used by the other
defaults.

```text
CANONICAL CONFIGURATION PRECEDENCE
NOT ESTABLISHED

DEFAULT URL CONSISTENCY
NOT ESTABLISHED
```

---

## 5. Canonical DB Module Adoption — VERIFIED

`app.db.database.engine` is directly imported by 27 tracked files, including
services, admin presentation, and scripts. `app/db/__init__.py` is empty, so no
package-level engine export contract exists.

`app/ui/streamlit_app.py` imports `engine` from
`app.services.analytics_logger`, not from `app.db.database`.

```text
CANONICAL DB MODULE
WIDELY ADOPTED BUT NOT REPOSITORY-WIDE GOVERNING

LOGGER ENGINE EXPOSED TO PRESENTATION
VERIFIED BOUNDARY LEAK
```

---

## 6. Connection and Transaction Ownership — VERIFIED

Observed read paths primarily use:

```text
with engine.connect() as conn
```

Observed write and schema-adjustment paths primarily use:

```text
with engine.begin() as conn
```

Transaction authority is therefore distributed among consumer functions rather
than centralized in the engine constructor module. Several collectors also
perform `ensure_columns` operations within consumer-owned transactions.

No explicit `.commit()` or `.rollback()` ownership model was established; the
observed model relies mainly on SQLAlchemy context-manager behavior.

---

## 7. Preference and Session Context Boundaries — VERIFIED

Preference and Session Context service/store layers accept a caller-provided
`conn`. They do not construct engines.

Current callers include:

```text
app/services/analytics_logger.py
app/main.py
app/ui/streamlit_app.py
```

Preference store tests use `_FakeConnection`. Service tests verify injected
connection delegation. This establishes bounded store testability without
establishing repository-wide engine substitution.

```text
PREFERENCE / SESSION STORE CONNECTION INJECTION
VERIFIED

LOCAL CONNECTION MIGRATION DEFECT
NOT ESTABLISHED
```

---

## 8. Static Entrypoint Topology — PARTIALLY VERIFIED

Static import reachability found:

| Entrypoint | Reachable constructor modules |
| --- | ---: |
| `app.main` | 5 |
| `app.ui.streamlit_app` | 5 |
| `app.ui.admin_dashboard` | 1 |
| `app.services.generator_service` | 3 |
| `app.services.recommendation_pipeline` | 3 |
| `app.services.market.collector` | 2 |

This proves static import reachability only. It does not prove that every
reachable module is imported or exercised in every deployed process mode.

```text
MULTIPLE ENGINE CONSTRUCTORS REACHABLE FROM PRIMARY ENTRYPOINTS
VERIFIED STATICALLY

ACTUAL RUNTIME ENGINE INSTANCE COUNT
UNRESOLVED
```

---

## 9. Runtime Lifecycle — VERIFIED ABSENCE / RUNTIME UNRESOLVED

No repository match was found for an engine disposal, FastAPI lifespan,
startup/shutdown engine cleanup, or `atexit` persistence lifecycle contract.

```text
DECLARED ENGINE DISPOSAL CONTRACT
NOT FOUND

ACTUAL PROCESS SHUTDOWN RESOURCE BEHAVIOR
UNRESOLVED
```

---

## 10. Test Isolation — PARTIALLY VERIFIED

Ten test files directly import engine-owner modules. Preference uses a fake
connection. Recommendation pipeline tests patch provider execution but do not
establish module-level engine construction substitution.

No direct evidence was found for a repository-wide test fixture that overrides:

```text
DATABASE_URL
COMMERCE_DB_URL
FRUIT_DB_URL
create_engine
all module-level engine instances
```

Absence from these scans is not proof that no indirect fixture exists.

```text
BOUNDED STORE TEST DOUBLES
PRESENT

REPOSITORY-WIDE ENGINE TEST SUBSTITUTION
UNRESOLVED
```

---

## 11. Key Architecture Observations

```text
PAO-001
Configuration authority is distributed across three precedence models.

PAO-002
Engine construction is distributed across seven module-scope owners.

PAO-003
The canonical DB engine has broad adoption but is not universally governing.

PAO-004
Streamlit imports Analytics Logger infrastructure directly.

PAO-005
Transaction boundaries are consumer-owned and function-local.

PAO-006
Preference and Session Context stores already support connection injection.

PAO-007
No declared engine disposal or process lifecycle contract was found.

PAO-008
Static primary entrypoints reach multiple engine constructor modules.

PAO-009
Tests import engine-owner modules without verified repository-wide engine isolation.
```

---

## 12. Candidate Migration Seams — NOT AUTHORIZED

Evidence supports further evaluation of these candidates:

```text
Candidate A
Canonical configuration resolution contract

Candidate B
Canonical engine construction and lifecycle contract

Candidate C
Remove Presentation dependency on Analytics Logger engine

Candidate D
Migrate independent logger engines behind governed infrastructure authority

Candidate E
Preserve connection-injected bounded stores while changing only callers
```

These are candidates, not production write authority.

---

## 13. Protected Contracts

The following remain protected:

```text
Preference models, policy, and service semantics
Session Context models, policy, and service semantics
Recommendation scoring, ranking, and provider semantics
Market Intelligence semantics
Analytics and logging event semantics
Food Knowledge and Product Identity authority
Cross-Border sealed baselines
Provider.aliases runtime contract
```

---

## 14. Unresolved Evidence

```text
actual runtime engine instance count by process mode
connection pool identity and reuse at runtime
engine disposal behavior during process shutdown
complete indirect pytest fixture and environment isolation topology
failure and rollback behavior under database errors
minimum safe production write file set
compatibility behavior when configuration precedence is unified
```

---

## 15. Phase 1 Status

```text
Persistence Consumer and Owner Inventory
PARTIALLY ESTABLISHED

Database Configuration Source and Precedence Map
ESTABLISHED

Engine Construction and Ownership Inventory
ESTABLISHED

Connection Acquisition and Release Map
PARTIALLY ESTABLISHED

Transaction Boundary Map
PARTIALLY ESTABLISHED

Persistence Dependency / Injection Map
PARTIALLY ESTABLISHED

Runtime Startup and Shutdown Resource Map
UNRESOLVED

Test Configuration and Substitution Map
PARTIALLY ESTABLISHED

Minimal Production Write Boundary
NOT YET DETERMINED

PHASE 1
NOT COMPLETE
```

---

## 16. Authority State

```text
ARCHITECTURE EVIDENCE AUTHORING
AUTHORIZED

PRODUCTION WRITE AUTHORIZATION
NONE

TEST WRITE AUTHORIZATION
NONE

NEXT ACTION
REVIEW UNRESOLVED RUNTIME / TEST EVIDENCE ROUTE
```

---

**00_1 Master Architecture**

Commerce AI Generator
