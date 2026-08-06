# 1. 운영 선언 문서 저장 위치

권장 위치

```text
/Users/mom/commerce_ai_generator/docs/architecture/notices/
```

권장 파일명

```text
MAN-2026-003_Sprint3_Governance_Operation_Phase.md
```

(기존 MAN-2026-002가 00_1 권한 확대 공지이므로, 운영 단계 전환은 MAN-2026-003으로 관리하는 것이 문서 계층상 자연스럽습니다.)

---

# 2. 커밋 명령어

```bash
cd ~/commerce_ai_generator

git add \
docs/architecture/notices/MAN-2026-003_Sprint3_Governance_Operation_Phase.md

git commit -m "docs(architecture): commence Sprint 3 governance operation phase"

git push origin main
```

권장 태그

```bash
git tag -a man-2026-003 \
-m "Sprint 3 Governance Operation Phase"

git push origin man-2026-003
```

---

# 3. 15_Herb & Spice Domain 개발 승인 문서

---

# Architecture Development Authorization

## ADA-MA-2026-016-HERB-SPICE

**Title**

Architecture Development Authorization — Herb & Spice Knowledge Domain

---

## Document Identity

| Item        | Value                                           |
| ----------- | ----------------------------------------------- |
| Document ID | ADA-MA-2026-016-HERB-SPICE                      |
| Authority   | 00_1 Master Architecture                        |
| Project     | Commerce AI Generator                           |
| Domain      | 15_Herb & Spice                                 |
| Status      | OFFICIAL ARCHITECTURE DEVELOPMENT AUTHORIZATION |
| Date        | 2026-08-06                                      |

---

# 1. Purpose

This Architecture Development Authorization (ADA) authorizes implementation of the Herb & Spice Knowledge Domain within the approved Sprint 3 operational governance.

Implementation shall reproduce the approved Sprint 3 Reference Process and shall remain within the authorized architectural scope.

No architectural expansion is authorized by this document.

---

# 2. Governing References

* ARN-MA-2026-001 Revision 1 — Approved Sprint 3 Reference Process
* MAN-2026-003 — Sprint 3 Governance Operation Phase
* SED-2026-001 Sprint 3 Domain Completion Directive
* MA-2026-011 Commerce AI Platform Architecture
* Commerce AI Generator Architecture Handbook v1.1
* Evidence First Principle
* Progressive Maturity Model

---

# 3. Authorized Scope

The following components are authorized.

### Registry Layer

* Herb Registry
* Spice Registry
* Origin Registry
* Form Registry
* Usage Registry
* Registry YAML

### Domain Logic

* Parser
* Parser Models
* Attribute Builder
* Scoring Engine
* Rule Engine

### Provider Layer

* Herb & Spice Knowledge Provider
* Provider Registration
* Provider Selection Integration

### Test Layer

* Registry Tests
* Parser Tests
* Attribute Tests
* Scoring Tests
* Rule Tests
* Provider Tests
* Registry Integration Tests

---

# 4. Mandatory Sprint 3 Evidence Chain

Implementation shall follow the approved Sprint 3 Domain Evidence Chain without modification.

```text
ADA
        ↓
Implementation
        ↓
IVR
        ↓
IPR
        ↓
IPS
        ↓
IRC
        ↓
IRR
        ↓
IRG
        ↓
IVC
        ↓
OAA
        ↓
AVCR
        ↓
MACR
        ↓
DHN
```

Deviation from this lifecycle is not authorized.

---

# 5. Architecture Constraints

The following constraints remain mandatory throughout Sprint 3.

* No Category Registry redesign
* No Knowledge Registry redesign
* No Resolver redesign
* No shared runtime contract modification
* No Alias Resolution Layer implementation
* No Provider responsibility expansion

Any identified improvements shall be recorded as **Architecture Observations** and deferred to Sprint 4 unless separately authorized.

---

# 6. Development Objectives

Implementation shall demonstrate:

* Food Knowledge Architecture compliance
* Shared runtime contract preservation
* Provider compatibility
* Registry compatibility
* Reproducible Evidence Chain
* Independent Verification readiness

---

# 7. Expected Deliverables

The Herb & Spice Domain shall produce:

* Complete implementation
* Verification Package
* Integration Verification evidence
* Architecture Verification Completion Report
* Master Architecture Completion Review
* Domain Handoff Notice

These deliverables shall satisfy the approved Sprint 3 Reference Process.

---

# 8. Completion Criteria

The domain shall be considered complete only after:

* Authorized implementation completed
* All verification activities completed
* AVCR approved
* MACR approved
* DHN accepted by 99_Integration

Implementation completion alone shall not constitute architecture completion.

---

# 9. Official Authorization

```text
APPROVED
```

```text
HERB & SPICE

DOMAIN DEVELOPMENT

AUTHORIZED
```

---

# Official Direction

The Herb & Spice Knowledge Domain is hereby authorized to begin implementation under the approved Sprint 3 Operational Governance.

All implementation, verification, architecture review, and domain completion activities shall follow the approved Sprint 3 Reference Process established by ARN-MA-2026-001 Revision 1.

No architectural expansion beyond the authorized scope is permitted during Sprint 3.

---

**Approved By**

**00_1 Master Architecture**
