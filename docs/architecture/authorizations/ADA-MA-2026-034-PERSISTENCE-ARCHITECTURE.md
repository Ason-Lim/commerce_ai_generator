# ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE

# Commerce AI Persistence Architecture Development Authorization

**Project:** Commerce AI Generator

**Architecture Program:** MA-2026-034

**Architecture:** Commerce AI Persistence Architecture

**Authorization Authority:** 00_1 Master Architecture

**Decision Basis:** MA-2026-033 Phase 2F Escalation

**Governing Review Decision:** IASM-DECISION-2026-002

**Date:** 2026-08-31

**Status:** AUTHORIZED

---

# 1. Authorization Purpose

This document authorizes governed architecture development for:

```text
MA-2026-034
COMMERCE AI PERSISTENCE ARCHITECTURE
```

The authorization follows the independent architecture decision:

```text
IASM-DECISION-2026-002
```

It establishes the initial development and evidence boundary for the
Persistence Architecture lifecycle.

---

# 2. Previous Approved Architecture Baseline

The Previous Approved Project Architecture Baseline is:

```text
PACD-2026-001

COMMIT
36bf9a77bc165bc1606febef92445ff9d2e4d6f9

TAG
project-architecture-closure-2026-001-v1.0

PROJECT ARCHITECTURE
CLOSED
```

The persistence condition was escalated from the governed MA-2026-033
Experience Architecture lifecycle after Phase 2E completion.

---

# 3. Governing Architecture Review

The governing Architecture Review Decision is:

```text
IASM-DECISION-2026-002

AUTHORITATIVE COMMIT
ff5cbc2f76376db73fbb56cf702b2119d0e4693f

AUTHORITATIVE TAG
iasm-decision-2026-002-v1.0
```

The decision established:

```text
PERSISTENCE ARCHITECTURE CONDITION
ACCEPTED

SEPARATE MASTER ARCHITECTURE LIFECYCLE
REQUIRED

ARCHITECTURE PROGRAM
MA-2026-034

ARCHITECTURE DEVELOPMENT
APPROVED
```

---

# 4. Architecture Need

The verified architecture condition is:

```text
Persistence ownership
CROSS-CUTTING

Existing canonical DB module
PRESENT BUT NOT REPOSITORY-WIDE GOVERNING

Distributed engine ownership
PRESENT

Configuration precedence
DISTRIBUTED / INCONSISTENT
```

This condition crosses Application Runtime, Preference, Session Context,
Analytics, Impression Logging, Market Collection, and Recommendation Runtime.

These concerns shall be investigated through Evidence First architecture
development.

---

# 5. Preferred Architecture Direction

The approved development direction is:

```text
Explicit Persistence Ownership

with

Canonical Configuration / Engine Authority

and

Explicit Connection / Transaction Boundaries
```

This model is a development hypothesis to be validated through repository and
runtime evidence. It does not require every SQL operation to move into one
physical module.

---

# 6. Architecture Development Objective

MA-2026-034 shall determine and establish explicit authority for:

```text
database configuration precedence
configuration resolution
engine creation, reuse, and disposal
connection acquisition and release
transaction initiation, commit, and rollback
dependency / injection direction
test configuration substitution
migration compatibility
```

The objective is structural ownership and lifecycle clarity. It is not a
database vendor or schema redesign by itself.

---

# 7. Phase 1 Authorization

The initial authorized phase is:

```text
PHASE 1
PERSISTENCE OWNERSHIP BASELINE
```

Authorization type:

```text
READ / INSPECTION
ARCHITECTURE EVIDENCE AUTHORING
```

Production and test modification:

```text
NOT AUTHORIZED
```

---

# 8. Phase 1 Read / Inspection Scope

Phase 1 may inspect the following repository surfaces where present and
relevant:

```text
app/main.py
app/core/**
app/db/**
app/services/**
app/models/**
app/api/**
tests/**
scripts/**
alembic/**
config and environment-loading files
dependency manifests
runtime entrypoints
```

Inspection may include imports, call paths, configuration resolution, engine
construction, connection acquisition, transaction behavior, startup and
shutdown behavior, test substitution, failure handling, and effective runtime
contracts.

No production or test modification is authorized by this inspection scope.

---

# 9. Named Initial Evidence Surfaces

Initial evidence shall include, without presuming final ownership:

```text
app/core/config.py
app/db/database.py
app/main.py
app/services/preference/**
app/services/analytics_logger.py
app/services/context_logger.py
app/services/impression_logger.py
app/services/market/collector.py
app/services/recommendation_pipeline.py
```

Additional consumers may be added to the inventory when repository evidence
shows that they own or participate in persistence lifecycle behavior.

---

# 10. Architecture Evidence Write Boundary

Architecture evidence and review artifacts may be created under:

```text
docs/architecture/**
docs/verification/persistence/**
```

for MA-2026-034.

Evidence artifacts may include inventories, dependency maps, lifecycle maps,
contract observations, migration candidates, verification plans, and bounded
scope proposals.

These documents shall not be treated as implementation authorization.

---

# 11. Production Write Boundary

Initial production write authorization is:

```text
NONE
```

No modification is currently authorized to:

```text
app/**
tests/**
scripts/**
alembic/**
dependency manifests
runtime configuration files
```

Any production or test modification requires a subsequent explicit
write-boundary authorization based on Phase 1 evidence.

---

# 12. Configuration Ownership Investigation

Phase 1 shall identify all sources and precedence rules involving, at minimum:

```text
DATABASE_URL
COMMERCE_DB_URL
FRUIT_DB_URL
default connection URLs
environment loading
test overrides
runtime overrides
```

It shall distinguish declared configuration authority from effective runtime
precedence.

No configuration source is declared canonical by this ADA.

---

# 13. Engine Ownership Investigation

Phase 1 shall identify:

```text
every create_engine call
engine module ownership
engine construction arguments
pool configuration
engine reuse behavior
engine disposal behavior
startup-time engine creation
import-time engine creation
test engine replacement
```

The existence of `app/db/database.py` does not by itself establish
repository-wide engine authority.

---

# 14. Connection Lifecycle Investigation

Phase 1 shall determine:

```text
where connections are acquired
where connections are released
context-manager behavior
exception behavior
connection ownership duration
cross-layer connection passing
implicit versus explicit lifecycle ownership
```

Physical proximity to SQL does not by itself establish connection lifecycle
authority.

---

# 15. Transaction Boundary Investigation

Phase 1 shall map:

```text
transaction initiation
autocommit assumptions
explicit commit
explicit rollback
implicit rollback
nested transaction behavior
multi-operation atomicity
failure and retry behavior
consumer-specific transaction semantics
```

No universal transaction policy is authorized before this evidence exists.

---

# 16. Dependency and Injection Direction

Phase 1 shall establish the current effective dependency direction between:

```text
Application Runtime
Persistence Infrastructure
Bounded Services
Domain / Intelligence Logic
Presentation
Tests
```

It shall identify direct engine imports, direct configuration imports,
connection injection, hidden global ownership, and import-time side effects.

Domain and intelligence semantics shall not become subordinate to a database
implementation detail.

---

# 17. Runtime Lifecycle Investigation

Phase 1 shall inspect:

```text
application startup
application shutdown
worker or process initialization
engine initialization timing
resource disposal
health-check interaction
failure during initialization
runtime reconnection behavior
```

Runtime evidence shall be collected only where necessary and through separately
safe, bounded observation.

---

# 18. Test Configuration Investigation

Phase 1 may read tests to determine:

```text
database fixture ownership
engine substitution
connection substitution
transaction rollback fixtures
environment-variable overrides
mock boundaries
integration database assumptions
test isolation behavior
```

Test modification is not authorized during Phase 1.

---

# 19. Preference Boundary Protection

The canonical Preference package is currently a persistence-aware bounded
service. This is not classified as an architecture defect by this ADA.

Phase 1 may inspect its persistence behavior and infrastructure dependencies.

It shall not modify or redesign:

```text
Preference models
Preference policy
Preference service semantics
Preference scoring or affinity behavior
```

Local Preference connection migration is not authorized during Phase 1.

---

# 20. Logger and Analytics Boundary Protection

Phase 1 may inspect persistence participation by analytics, context, and
impression logging components.

It shall distinguish:

```text
event semantics
transport behavior
storage behavior
engine ownership
transaction ownership
failure policy
```

Analytics and logging semantics remain protected. No logger implementation
change is authorized.

---

# 21. Market and Recommendation Boundary Protection

Phase 1 may inspect Market Collection and Recommendation Runtime persistence
dependencies.

It shall not redefine:

```text
Recommendation scoring
Recommendation ranking
Recommendation signal semantics
Market Intelligence semantics
collection policy
domain-specific persistence meaning
```

No Recommendation or Market production change is authorized.

---

# 22. Application Runtime Boundary

Phase 1 may inspect application-level engine construction and dependency
composition in `app/main.py` and other runtime entrypoints.

It shall identify whether runtime code owns configuration, engines,
connections, transactions, dependency injection, or compatibility shims.

Application Runtime modification is not authorized.

---

# 23. Protected Architecture Contracts

The following governed contracts are protected:

```text
Experience contracts
Preference contracts
Recommendation Engine canonical contracts
Market Intelligence canonical contracts
Food Knowledge canonical contracts
Product Identity authority
Price Intelligence authority
Analytics authority
Marketplace Core authority
Cross-Border sealed baselines
Provider.aliases runtime contract
```

MA-2026-034 may inspect persistence dependencies associated with these
authorities. Semantic modification requires separate authorization from the
responsible architecture authority.

---

# 24. Cross-Border Scope Protection

The current Cross-Border terminal state remains preserved.

This ADA does not authorize:

```text
Cross-Border lifecycle reopening
external evidence acquisition
provider admission
canonical Cross-Border mutation
Korea Post EMS reopening
```

Cross-Border persistence participation may be recorded only if it is already
present in repository evidence and relevant to the ownership inventory.

---

# 25. Explicit Non-Goals

The following are not authorized:

```text
database vendor migration
schema redesign
ORM replacement
universal repository abstraction
Product / Domain Affinity redesign
Recommendation scoring redesign
Preference policy redesign
domain-specific SQL semantic redesign
Cross-Border reopening
general repository cleanup
unrelated infrastructure refactoring
dependency upgrades
broad test rewrite
```

Product / Domain Affinity candidates remain deferred and are not abandoned.

---

# 26. Big-Bang Migration Prohibition

MA-2026-034 shall not proceed through a repository-wide database rewrite.

The required lifecycle model is:

```text
inventory ownership
    ↓
establish authority contract
    ↓
characterize consumer behavior
    ↓
authorize bounded migration
    ↓
verify compatibility
    ↓
retire obsolete ownership only with evidence
    ↓
independently verify
```

---

# 27. Evidence First Requirement

No architecture assumption shall become implementation authority solely
because it appears desirable.

Architecture changes shall be justified by:

```text
repository evidence
runtime evidence where required
configuration evidence
dependency evidence
connection lifecycle evidence
transaction evidence
contract evidence
regression evidence
```

---

# 28. Phase 1 Required Deliverables

Phase 1 shall produce an evidence package containing at minimum:

```text
1. Persistence Consumer and Owner Inventory
2. Database Configuration Source and Precedence Map
3. Engine Construction and Ownership Inventory
4. Connection Acquisition and Release Map
5. Transaction Boundary Map
6. Persistence Dependency / Injection Map
7. Runtime Startup and Shutdown Resource Map
8. Test Configuration and Substitution Map
9. Persistence Contract Observation Register
10. Controlled Consumer Migration Candidate Register
11. Compatibility and Regression Verification Plan
12. Proposed Minimal Production Write Boundary
```

Each claim shall distinguish verified evidence, interpretation, and unresolved
condition.

---

# 29. Phase 1 Completion Criteria

Phase 1 is complete when 00_1 can determine:

```text
all known engine construction owners;
the effective database configuration precedence;
the current connection lifecycle ownership;
the current transaction boundary ownership;
the effective persistence dependency direction;
the runtime resource lifecycle;
the test substitution model;
the highest-value structural migration seam;
the minimum safe production write boundary;
the required compatibility and rollback evidence.
```

Unresolved material ownership shall be explicitly recorded rather than
inferred.

---

# 30. Verification Requirements

Phase 1 itself requires:

```text
repository inspection completeness
evidence traceability
no unauthorized production modification
no unauthorized test modification
git diff --check PASS
worktree change inventory
```

Any future implementation phase shall additionally require targeted consumer
tests, protected-contract verification, relevant subsystem regression,
application compile, migration compatibility checks, and `git diff --check`.

The re-entry baseline associated with the governing decision is:

```text
Preference
33 PASSED

Experience
52 PASSED

Recommendation
1099 PASSED

Application compile
PASS
```

---

# 31. Independent Verification Requirement

Architecture implementation performed under MA-2026-034 shall not declare
itself independently complete.

Material persistence migration shall be subject to independent verification by
the appropriate verification authority.

00_1 retains architecture completion authority.

---

# 32. Authorization Boundary Expansion

After Phase 1, any requested production write authorization shall state:

```text
specific files
specific ownership migration
configuration compatibility behavior
connection and transaction behavior
protected contracts
expected runtime behavior
test and regression plan
rollback plan
explicit non-changes
```

Broad directory-level write authorization shall not be assumed.

---

# 33. Current Authorization State

```text
MA-2026-034
COMMERCE AI PERSISTENCE ARCHITECTURE

ARCHITECTURE DEVELOPMENT
AUTHORIZED

PHASE 1
PERSISTENCE OWNERSHIP BASELINE
AUTHORIZED

READ / INSPECTION
AUTHORIZED

ARCHITECTURE EVIDENCE AUTHORING
AUTHORIZED

PRODUCTION CODE MODIFICATION
NOT AUTHORIZED

TEST MODIFICATION
NOT AUTHORIZED

NEXT DECISION
PHASE 1 EVIDENCE REVIEW
```

---

# 34. Final Authorization

00_1 Master Architecture authorizes:

```text
ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE

STATUS
AUTHORIZED

ARCHITECTURE PROGRAM
MA-2026-034

INITIAL PHASE
PHASE 1

PHASE PURPOSE
PERSISTENCE OWNERSHIP BASELINE

READ / INSPECTION AUTHORIZATION
AUTHORIZED

ARCHITECTURE EVIDENCE AUTHORING
AUTHORIZED

PRODUCTION WRITE AUTHORIZATION
NONE

TEST WRITE AUTHORIZATION
NONE

IMPLEMENTATION AUTHORIZATION
PENDING PHASE 1 EVIDENCE

GOVERNING REVIEW DECISION
IASM-DECISION-2026-002

GOVERNING DECISION COMMIT
ff5cbc2f76376db73fbb56cf702b2119d0e4693f

GOVERNING DECISION TAG
iasm-decision-2026-002-v1.0
```

---

**00_1 Master Architecture**

Commerce AI Generator
