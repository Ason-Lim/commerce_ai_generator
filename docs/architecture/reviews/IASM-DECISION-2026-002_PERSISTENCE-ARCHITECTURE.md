# IASM-DECISION-2026-002

# Commerce AI Persistence Architecture Review Decision

**Project:** Commerce AI Generator

**Decision Authority:** 00_1 Master Architecture

**Decision Basis:** MA-2026-033 Phase 2F Escalation

**Architecture Program:** MA-2026-034

**Date:** 2026-08-31

**Status:** APPROVED FOR ARCHITECTURE DEVELOPMENT

---

# 1. Decision Purpose

This document records the 00_1 review of the repository-wide persistence
ownership condition escalated from MA-2026-033 Phase 2F.

The review determines whether:

```text
the persistence condition is genuinely cross-cutting;
the condition belongs outside Experience Architecture;
a separate governed architecture lifecycle is required;
the proposed scope preserves existing governed authority;
MA-2026-034 may be assigned;
a new Architecture Development Authorization should be issued.
```

---

# 2. Governing Architecture Baseline

The approved project architecture closure baseline is:

```text
PACD-2026-001
36bf9a77bc165bc1606febef92445ff9d2e4d6f9
project-architecture-closure-2026-001-v1.0
PROJECT ARCHITECTURE CLOSED
```

The governing Experience Architecture chain is:

```text
IASM-DECISION-2026-001
9774d19afd6d475e0277904d0c1c8b6aaaed148b
iasm-decision-2026-001-v1.0

ADA-MA-2026-033-EXPERIENCE-ARCHITECTURE
2e1aaa584b8296023c4faf2a0ba4446fedcacc04
ada-ma-2026-033-experience-architecture-v1.0
```

MA-2026-033 Phase 2E Preference Canonicalization is:

```text
COMPLETE / SEALED
```

The authoritative repository baseline is:

```text
c49a0741b21a95ba73e10bb344256300475490f3
```

---

# 3. Verified Architecture Condition

Read-only repository inspection established:

```text
Persistence ownership
CROSS-CUTTING

Existing canonical DB module
PRESENT BUT NOT REPOSITORY-WIDE GOVERNING

Distributed engine ownership
PRESENT

Configuration precedence
DISTRIBUTED / INCONSISTENT

Existing Persistence Architecture artifact or tag
NOT FOUND
```

The distributed condition crosses:

```text
Application Runtime
Preference
Session Context
Analytics
Impression Logging
Market Collection
Recommendation Runtime
```

Decision:

```text
ARCHITECTURE CONDITION
ACCEPTED
```

---

# 4. Existing Infrastructure Candidate

The repository contains:

```text
app/core/config.py
app/db/database.py
```

These modules are accepted as existing infrastructure evidence. They are not
declared repository-wide canonical authority merely because they exist.

Other consumers use differing configuration precedence, including:

```text
DATABASE_URL
COMMERCE_DB_URL
FRUIT_DB_URL
```

Decision:

```text
EXISTING DB INFRASTRUCTURE
PRESERVED AS CANDIDATE

REPOSITORY-WIDE AUTHORITY
NOT YET ESTABLISHED
```

---

# 5. Alternatives Review

The MA-2026-033 Phase 2F review considered:

```text
ALTERNATIVE A
Local Preference Connection Ownership Migration

ALTERNATIVE B
Separate Persistence Architecture

ALTERNATIVE C
Preserve Current Connection Ownership as Intentional
```

Alternative A would incorrectly absorb a repository-wide condition into
Experience Architecture. Alternative C is not supported by evidence that the
current distribution is an intentional governed architecture.

Decision:

```text
ALTERNATIVE B
SEPARATE PERSISTENCE ARCHITECTURE
ACCEPTED
```

---

# 6. Preferred Architecture Direction

The accepted direction is:

```text
Explicit Persistence Ownership

with

Canonical Configuration / Engine Authority

and

Explicit Connection / Transaction Boundaries
```

This direction does not require every SQL operation to move into one physical
module. It requires authority, lifecycle, dependency direction, and
compatibility rules to become explicit and governed.

Decision:

```text
PERSISTENCE ARCHITECTURE DIRECTION
ACCEPTED AS ARCHITECTURE DEVELOPMENT BASELINE
```

---

# 7. Required Authority Contracts

MA-2026-034 shall establish explicit authority for:

```text
database configuration precedence
configuration resolution
engine construction, reuse, and disposal
connection acquisition and release
transaction initiation, commit, and rollback
test configuration substitution
consumer dependency direction
migration compatibility
```

No existing consumer shall be silently treated as canonical without evidence.
Physical proximity to SQL does not by itself establish ownership of the engine
or transaction lifecycle.

Decision:

```text
CONFIGURATION / ENGINE AUTHORITY CONTRACT
REQUIRED

CONNECTION / TRANSACTION BOUNDARY CONTRACT
REQUIRED
```

---

# 8. Migration Strategy

The following is not authorized as the default strategy:

```text
REPOSITORY-WIDE BIG-BANG DATABASE REWRITE
```

The required migration model is:

```text
inventory ownership
    ↓
establish authority contract
    ↓
characterize consumer behavior
    ↓
migrate bounded consumers
    ↓
verify compatibility
    ↓
retire obsolete ownership only with evidence
```

Decision:

```text
CONTROLLED PROGRESSIVE MIGRATION
REQUIRED
```

---

# 9. Initial Architecture Scope

The approved initial architecture development scope is:

```text
database configuration ownership
engine creation ownership
connection lifecycle ownership
transaction ownership
dependency / injection direction
migration compatibility
consumer ownership inventory
regression preservation
```

This scope may be refined through architecture evidence but shall not be
broadened without explicit authorization.

---

# 10. Protected Existing Authority

MA-2026-034 shall preserve the approved semantic authority of:

```text
Experience
Preference
Recommendation
Analytics
Market Intelligence
Food Knowledge
Product Identity
Price Intelligence
Cross-Border governed baselines
```

Persistence Architecture may govern infrastructure access and lifecycle
contracts. It shall not silently redefine canonical service or domain
semantics.

Decision:

```text
EXISTING GOVERNED AUTHORITY
PROTECTED
```

---

# 11. Explicit Non-Goals

The following are not authorized by this review:

```text
Product / Domain Affinity redesign
Recommendation scoring redesign
Preference policy redesign
Cross-Border lifecycle reopening
Korea Post EMS reopening
domain-specific SQL semantic redesign
general repository cleanup
unrelated infrastructure refactoring
database vendor migration
schema redesign without separate evidence
```

The Product / Domain Affinity candidates remain:

```text
DEFERRED
NOT ABANDONED
```

The current Cross-Border terminal state remains preserved. MA-2026-034 does
not authorize Cross-Border external evidence acquisition, provider admission,
canonical mutation, or lifecycle reopening.

---

# 12. Architecture Program Assignment

00_1 assigns:

```text
MA-2026-034
COMMERCE AI PERSISTENCE ARCHITECTURE
```

Read-only inspection confirmed:

```text
MA-2026-034 collision
ABSENT

Persistence Architecture artifact collision
ABSENT

Persistence Architecture tag collision
ABSENT
```

---

# 13. Implementation Boundary

This Review Decision approves architecture development. It does not by itself
authorize unrestricted production modification.

Production implementation shall be governed by the separate:

```text
ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE
```

with explicit write boundaries, protected contracts, verification
requirements, and completion evidence requirements.

---

# 14. Required Development Principles and Evidence

MA-2026-034 shall follow:

```text
Evidence First
Fail-Closed Mutation Control
Authority Before Migration
Explicit Ownership
Progressive Migration
Dependency Direction Preservation
Transaction Boundary Clarity
Compatibility Preservation
Independent Verification
```

Architecture development shall establish evidence sufficient to review:

```text
all engine construction owners
all database configuration sources and precedence
all connection acquisition and release paths
all transaction initiation / commit / rollback paths
consumer dependency direction
runtime startup and shutdown behavior
test and production configuration compatibility
bounded consumer migration order
rollback and failure behavior
regression integrity
```

Current re-entry regression baseline:

```text
Preference
33 PASSED

Experience
52 PASSED

Recommendation
1099 PASSED

Application compile
PASS

git diff --check
PASS
```

---

# 15. Candidate Lifecycle Shape

```text
Phase 1
Persistence Ownership Baseline

Phase 2
Configuration / Engine Authority Contract

Phase 3
Transaction / Connection Boundary Contract

Phase 4
Controlled Consumer Migration

Phase 5
Regression / Compatibility Verification

Phase 6
Architecture Completion
```

Phase boundaries may be refined by the ADA or later bounded authority. They
shall not be expanded by inference.

---

# 16. Decision

00_1 Master Architecture determines:

```text
PERSISTENCE ARCHITECTURE CONDITION
ACCEPTED

SEPARATE MASTER ARCHITECTURE LIFECYCLE
REQUIRED

PREFERRED GOVERNING ROUTE
SEPARATE PERSISTENCE ARCHITECTURE

ARCHITECTURE PROGRAM
MA-2026-034

ARCHITECTURE DEVELOPMENT
APPROVED

LOCAL MA-2026-033 PERSISTENCE MIGRATION
NOT AUTHORIZED

IMPLEMENTATION AUTHORITY
TO BE GOVERNED BY SEPARATE ADA
```

---

# 17. Next Action

The next governing artifact shall be:

```text
ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE
```

The ADA shall define:

```text
authorized read-only inventory scope
initial write boundary
configuration / engine authority investigation
connection / transaction boundary investigation
protected contracts
explicit non-goals
verification requirements
completion evidence requirements
```

No production implementation is authorized before that ADA is separately
reviewed and issued.

---

# 18. Final Review State

```text
IASM-DECISION-2026-002
ARCHITECTURE REVIEW COMPLETE

PERSISTENCE ARCHITECTURE CONDITION
ACCEPTED

MA-2026-034
ASSIGNED

COMMERCE AI PERSISTENCE ARCHITECTURE
AUTHORIZED FOR ARCHITECTURE DEVELOPMENT

PRODUCTION IMPLEMENTATION
NOT YET AUTHORIZED BY THIS DECISION

MA-2026-033
PERSISTENCE CONDITION ESCALATION RESOLVED BY SEPARATE LIFECYCLE

CROSS-BORDER TERMINAL STATE
PRESERVED

NEXT AUTHORITY ACTION
ISSUE ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE
```

---

**00_1 Master Architecture**

Commerce AI Generator
