# 00_1 Master Architecture

# Architecture Repository Structure Decision

## ARSD-MA-2026-001

**Title**
Canonical Documentation Architecture for Sprint 3 Governance and Evidence

---

## Document Identity

| Item            | Value                               |
| --------------- | ----------------------------------- |
| Document ID     | ARSD-MA-2026-001                    |
| Authority       | 00_1 Master Architecture            |
| Project         | Commerce AI Generator               |
| Scope           | Sprint 3 Documentation Architecture |
| Status          | OFFICIAL ARCHITECTURE DECISION      |
| Effective Date  | 2026-08-06                          |
| Decision Result | APPROVED                            |

---

# 1. Purpose

This decision establishes the canonical repository structure for architecture, verification, integration, handoff, and governance documents within the Commerce AI Generator project.

The purpose is to:

* preserve authority boundaries;
* distinguish governance decisions from technical evidence;
* improve Evidence Chain traceability;
* eliminate inconsistent documentation paths;
* provide a stable repository structure for the remaining Sprint 3 domains;
* support Project-level Cross-domain Validation and Integration Completion.

This decision governs document placement and repository organization. It does not modify runtime architecture or implementation contracts.

---

# 2. Canonical Repository Structure

The following structure is officially approved.

```text
docs/
├── architecture/
│   ├── proposals/
│   ├── approvals/
│   ├── reviews/
│   ├── verification/
│   ├── completion/
│   ├── handoff/
│   └── notices/
│
├── verification/
│   └── <domain>/
│
├── integration/
│   ├── <domain>/
│   └── sprint3/
│
└── governance/
```

This structure becomes the canonical documentation architecture for Sprint 3.

---

# 3. Architectural Ownership

## 3.1 `docs/architecture/`

This directory contains authoritative architecture-governance documents owned or approved by 00_1 Master Architecture.

It shall not be used as a general technical-evidence directory.

### `architecture/proposals/`

Purpose:

* proposed architecture changes;
* architecture governance proposals;
* architecture evolution requests;
* responsibility-boundary proposals.

Expected document types include:

```text
APR
RFC
Architecture Migration Proposal
Architecture Evolution Proposal
```

Example:

```text
docs/architecture/proposals/
└── APR-MA-2026-001_Sprint3_Architecture_Review_Governance.md
```

### `architecture/approvals/`

Purpose:

* official architecture approval decisions;
* approval reports;
* approval of independently produced verification results.

Expected document types include:

```text
OAA
AAR
Architecture Approval Record
```

Example:

```text
docs/architecture/approvals/
└── OAA-MA-2026-016-HERB-SPICE_Official_Architecture_Approval.md
```

### `architecture/reviews/`

Purpose:

* architecture review requests;
* architecture review findings;
* responsibility-boundary reviews;
* review decisions not representing final completion.

Expected document types include:

```text
ARR
Architecture Review Decision
Architecture Assessment
```

Example:

```text
docs/architecture/reviews/
└── ARR-MA-2026-001_Category_Registry_Responsibility_Boundary_Clarification.md
```

### `architecture/verification/`

Purpose:

* architecture verification-completion decisions;
* formal review of whether accumulated evidence satisfies architecture-verification gates.

Expected document types include:

```text
AVCR
Architecture Boundary Verification Review
```

Example:

```text
docs/architecture/verification/
└── AVCR-MA-2026-016-HERB-SPICE.md
```

### `architecture/completion/`

Purpose:

* final domain-level architecture completion decisions;
* records establishing eligibility for Domain Handoff.

Expected document types include:

```text
MACR
Architecture Completion Review
Architecture Closure Decision
```

Example:

```text
docs/architecture/completion/
└── MACR-MA-2026-016-HERB-SPICE.md
```

MACR documents currently stored under `docs/architecture/verification/` shall be migrated to this directory through a controlled documentation-only migration.

### `architecture/handoff/`

Purpose:

* official transfer from Domain Governance to Project-level Integration Governance;
* permanent record of responsibility transition.

Expected document types include:

```text
DHN
Domain Handoff Acknowledgement
Handoff Acceptance
```

Example:

```text
docs/architecture/handoff/
└── herb_spice/
    └── DHN-MA-2026-016-HERB-SPICE.md
```

Domain subdirectories are recommended when more than one handoff-related artifact exists.

### `architecture/notices/`

Purpose:

* official architecture notices;
* operational directives;
* reference-process notices;
* architecture-authority announcements.

Expected document types include:

```text
MAN
ARN
SED
Architecture Directive
```

Example:

```text
docs/architecture/notices/
├── ARN-MA-2026-001_Approved_Sprint3_Reference_Process.md
└── MAN-2026-003_Sprint3_Governance_Operation_Phase.md
```

---

# 4. Technical Verification Evidence

## `docs/verification/<domain>/`

This directory contains reproducible technical evidence.

It is not the location for final architecture approval or completion decisions.

Expected content includes:

* repository baseline;
* implementation inventory;
* registry inventory;
* test output;
* compilation output;
* import-safety evidence;
* architecture-boundary evidence;
* protected-file verification;
* change-scope evidence;
* Git evidence;
* Verification Package;
* machine-readable evidence.

Canonical domain identifiers shall use lowercase snake case.

Examples:

```text
docs/verification/coffee/
docs/verification/cheese/
docs/verification/wine/
docs/verification/tea/
docs/verification/olive_oil/
docs/verification/herb_spice/
docs/verification/seafood/
docs/verification/fruit/
docs/verification/vegetable/
```

---

# 5. Integration Verification Evidence

## `docs/integration/<domain>/`

This directory contains independent Domain Integration Verification records owned by 99_Integration Verification Authority.

Expected document lifecycle:

```text
IVR
        │
        ▼
IPR
        │
        ▼
IPS
        │
        ▼
IRC
        │
        ▼
IRR
        │
        ▼
IRG
        │
        ▼
IVC
```

Example:

```text
docs/integration/herb_spice/
├── IVR-HERB-SPICE-2026-001.md
├── IPR-HERB-SPICE-2026-001.md
├── IPS-HERB-SPICE-2026-001.md
├── IRC-HERB-SPICE-2026-001.md
├── IRR-HERB-SPICE-2026-001.md
├── IRG-HERB-SPICE-2026-001.md
└── IVC-HERB-SPICE-2026-001.md
```

## `docs/integration/sprint3/`

This directory contains Project-level Integration Governance records.

Expected lifecycle:

```text
ICP
        │
        ▼
CDV
        │
        ▼
CDR
        │
        ▼
ICA
        │
        ▼
ICR
```

Project-level Integration Completion shall be declared only through the final ICR.

---

# 6. Governance Documents

## `docs/governance/`

This directory contains project-governance rules and governing registries that are broader than an individual architecture review.

Expected content includes:

* Project Governance Architecture;
* Governance Registry;
* governance operations;
* role and authority definitions;
* Evidence First policy;
* Progressive Maturity policy;
* document-governance rules;
* governance compliance checklists.

Architecture-specific notices and decisions shall remain under `docs/architecture/`, even when they have governance effects.

---

# 7. Canonical Document Placement Matrix

| Document Type                | Canonical Location                    | Primary Authority                  |
| ---------------------------- | ------------------------------------- | ---------------------------------- |
| APR / architecture proposal  | `docs/architecture/proposals/`        | Requesting authority / 00_1 review |
| OAA / AAR                    | `docs/architecture/approvals/`        | 00_1 Master Architecture           |
| ARR / review decision        | `docs/architecture/reviews/`          | 00_1 Master Architecture           |
| AVCR                         | `docs/architecture/verification/`     | 00_1 Master Architecture           |
| MACR                         | `docs/architecture/completion/`       | 00_1 Master Architecture           |
| DHN                          | `docs/architecture/handoff/<domain>/` | Domain and receiving authority     |
| MAN / ARN / SED              | `docs/architecture/notices/`          | 00_1 Master Architecture           |
| VKP and technical evidence   | `docs/verification/<domain>/`         | Verification authority             |
| IVR–IVC                      | `docs/integration/<domain>/`          | 99_Integration                     |
| ICP–ICR                      | `docs/integration/sprint3/`           | 99_Integration                     |
| Project governance documents | `docs/governance/`                    | Project governance authority       |

---

# 8. Domain Completion Evidence Chain

The canonical Sprint 3 Evidence Chain is mapped to the repository as follows.

```text
ADA
docs/architecture/approvals/ or authorizations/
        │
        ▼
Implementation Evidence
docs/verification/<domain>/
        │
        ▼
IVR → IVC
docs/integration/<domain>/
        │
        ▼
OAA
docs/architecture/approvals/
        │
        ▼
AVCR
docs/architecture/verification/
        │
        ▼
MACR
docs/architecture/completion/
        │
        ▼
DHN
docs/architecture/handoff/<domain>/
        │
        ▼
99_Integration Project Governance
docs/integration/sprint3/
```

Existing `docs/architecture/authorizations/` may remain the canonical location for ADA documents.

Accordingly, the full approved architecture tree includes:

```text
docs/architecture/
├── authorizations/
├── proposals/
├── approvals/
├── reviews/
├── verification/
├── completion/
├── handoff/
└── notices/
```

The `authorizations/` directory shall not be removed.

---

# 9. Migration Policy

This decision does not authorize uncontrolled deletion or bulk movement of existing evidence.

Existing documents stored in inconsistent paths shall be migrated under the following rules:

1. Inventory all tracked source and destination paths.
2. Confirm that the destination does not contain a conflicting document.
3. Use `git mv` to preserve history.
4. Update internal document links and governing references.
5. Validate that no duplicate canonical copy remains.
6. Commit migration separately from implementation changes.
7. Tag significant governance migrations where appropriate.
8. Preserve old paths only when required by an explicit archive policy.

Migration shall not modify document meaning or approval status.

---

# 10. Path Naming Rules

The following naming rules are adopted.

* All repository directories shall use lowercase names.
* Domain directory names shall use lowercase snake case.
* Document IDs shall retain their approved uppercase form.
* Spaces should be avoided in new filenames.
* Existing approved filenames containing spaces may remain until controlled migration.
* `docs/Architecture/` shall not be recreated.
* `docs/architecture/handoff/` shall not be used for new Domain Handoff records.
* The canonical handoff root is `docs/architecture/handoff/`.

Examples:

```text
herb_spice
olive_oil
seafood
fruit
vegetable
```

---

# 11. Architecture Boundaries

This repository structure preserves the following responsibility separation:

```text
Architecture decisions
        │
        ▼
docs/architecture/

Technical verification evidence
        │
        ▼
docs/verification/

Independent integration evidence
        │
        ▼
docs/integration/

Project governance
        │
        ▼
docs/governance/
```

A document shall be placed according to its authority and purpose, not merely according to the domain that produced it.

---

# 12. Official Decision

## Review Result

```text
APPROVED
```

## Repository Architecture Status

```text
CANONICAL DOCUMENTATION ARCHITECTURE

ESTABLISHED
```

## Effective Status

```text
OFFICIAL

EFFECTIVE IMMEDIATELY
```

---

# 13. Official Direction

Effective immediately:

* All new Sprint 3 documents shall use the canonical paths established by this decision.
* Existing inconsistent paths shall be migrated through controlled documentation-only commits.
* No duplicate authoritative copy shall remain after migration.
* Architecture, verification, integration, and governance evidence shall remain separated by authority and purpose.
* Deviations require prior approval from 00_1 Master Architecture.

---

# Official Statement

00_1 Master Architecture formally establishes the approved repository structure as the canonical documentation architecture for Commerce AI Generator Sprint 3.

The architecture provides a stable and traceable foundation for the remaining Seafood, Fruit, and Vegetable domains, Project-level Cross-domain Validation, Integration Completion, and the final Sprint 3 Completion Assessment.

This decision establishes an operational repository structure for Sprint 3. Broader adoption as an institution-wide KOP Labs documentation standard remains subject to future independent review.

---

**Approved By**
00_1 Master Architecture
