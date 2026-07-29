# Commerce AI Generator

# Governance Registry v1.0 (Release Candidate 1)

**Document Type**  
Governance Registry

**Registry Version**  
1.0 (RC1)

**Schema Version**  
1.0

**Status**  
RELEASE CANDIDATE

**Draft Date**  
2026-07-29

**Prepared By**  
00_0 Master Document Governance *(Project Governance 체계와의 최종 정합성 확인 후 Official v1.0에서 확정)*

**Review Partner**  
00_1 Master Architecture *(Project Governance 체계와의 최종 정합성 확인 후 Official v1.0에서 확정)*

**Approval Authority**  
Project Owner *(Official v1.0 승인 시 최종 확정)*

**Approval Status**  
PENDING PROJECT OWNER APPROVAL

**Effective Date**  
PENDING PROJECT OWNER APPROVAL

**Approval Record**  
PENDING PROJECT OWNER APPROVAL

---

# Part 1. Registry Specification

## Purpose

Governance Registry는 Commerce AI Generator 프로젝트의 Governance Domain 운영 메타데이터를 관리하는 공식 Registry이다.

Registry는 Governance Domain의 운영 상태를 기록하고 추적하기 위한 기준점이며, Project Charter, Master Document Governance Standard(MDGS), Project Governance Architecture 및 Domain Standards를 대체하지 않는다.

## Registry Classification

| Component | Classification |
|---|---|
| Registry Specification | Registry-level Normative |
| Registry Schema | Registry-level Normative |
| Registry Operating Rules | Registry-level Normative |
| Registry Entries | Operational Data |
| Appendix A | Operational Reference |

Registry-level Normative는 Registry 내부 운영 규칙을 의미하며, Project Charter, MDGS 또는 Project Governance Architecture와 동일한 규범 수준을 의미하지 않는다.

---

# Part 2. Registry Schema

본 절에서 정의하는 Required Field는 **ACTIVE Registry Entry**에 적용한다.

다른 Lifecycle Status의 Entry는 해당 상태에 적합한 필드 집합을 사용할 수 있다.

| Field | Requirement |
|---|---|
| Domain ID | Required |
| Governance Domain | Required |
| Status | Required |
| Current Version | Required |
| Domain Owner | Required |
| Approval Authority | Required |
| Normative Reference | Required |
| Effective Date | Required |
| Approval Record | Required |
| Last Updated | Required |
| Change History | Required |
| Remarks | Optional |

Purpose Summary와 Scope Summary는 Optional이며 비규범적 메타데이터이다.

---

# Part 3. Initial Registry Entries

## GOV-DOC

| Field | Value |
|---|---|
| Domain ID | GOV-DOC |
| Governance Domain | Documentation Governance |
| Status | ACTIVE |
| Current Version | 1.0 |
| Domain Owner | 00_0 Master Document Governance |
| Approval Authority | 00_0 Master Document Governance |
| Normative Reference | Project Governance Architecture v1.0 |
| Effective Date | PENDING PROJECT OWNER APPROVAL |
| Approval Record | PENDING PROJECT OWNER APPROVAL |
| Last Updated | 2026-07-29 |
| Change History | Version 1.0 · 2026-07-29 · Initial Registration |
| Remarks | None |

## GOV-ARCH

| Field | Value |
|---|---|
| Domain ID | GOV-ARCH |
| Governance Domain | System Architecture & Development Governance |
| Status | ACTIVE |
| Current Version | 1.0 |
| Domain Owner | 00_1 Master Architecture |
| Approval Authority | 00_1 Master Architecture |
| Normative Reference | Project Governance Architecture v1.0 |
| Effective Date | PENDING PROJECT OWNER APPROVAL |
| Approval Record | PENDING PROJECT OWNER APPROVAL |
| Last Updated | 2026-07-29 |
| Change History | Version 1.0 · 2026-07-29 · Initial Registration |
| Remarks | None |

## Proposed Domains

| Domain ID | Governance Domain | Status | Current Version | Domain Owner | Approval Authority | Remarks |
|---|---|---|---|---|---|---|
| GOV-SEC | Security Governance | PROPOSED | 1.0 | UNASSIGNED | UNASSIGNED | Initial Registration |
| GOV-QUAL | Quality Governance | PROPOSED | 1.0 | UNASSIGNED | UNASSIGNED | Initial Registration |
| GOV-AI | AI Governance | PROPOSED | 1.0 | UNASSIGNED | UNASSIGNED | Initial Registration |
| GOV-DATA | Data Governance | PROPOSED | 1.0 | UNASSIGNED | UNASSIGNED | Initial Registration |
| GOV-MKT | Marketplace Governance | PROPOSED | 1.0 | UNASSIGNED | UNASSIGNED | Initial Registration |
| GOV-OPS | Operations Governance | PROPOSED | 1.0 | UNASSIGNED | UNASSIGNED | Initial Registration |

`UNASSIGNED`는 해당 Registry Field에 필요한 공식 주체, 역할 또는 권한이 아직 지정되지 않았음을 나타내는 명시적 Registry 값이다.

`UNASSIGNED`는 Null 또는 정보 누락을 의미하지 않는다.

---

# Part 4. Registry Operating Rules

## Version Management

Registry Version은 Registry 문서와 운영 데이터 집합의 버전을 의미한다.

Schema Version은 Registry Entry 공통 메타데이터 계약의 버전을 의미한다.

두 버전은 독립적으로 관리한다.

## Approval Rules

- 신규 Domain 등록은 승인된 거버넌스 절차를 따른다.
- `PROPOSED → ACTIVE` 전환은 Project Owner 또는 공식 위임된 승인 권한의 승인을 필요로 한다.
- Approval Authority 변경은 Project Owner 또는 상위 승인 권한의 승인을 필요로 한다.
- Schema 변경은 00_0 Master Document Governance와 00_1 Master Architecture의 검토 후 Project Owner 승인을 거친다.

## Lifecycle Rules

- 기본 Lifecycle은 `PROPOSED → ACTIVE → DEPRECATED → RETIRED`를 따른다.
- `PROPOSED → RETIRED`는 승인 절차에 따라 허용될 수 있다.
- `RETIRED → ACTIVE`는 기본적으로 허용하지 않는다.
- Domain 명칭이 변경되어도 Domain ID는 변경하지 않는다.
- RETIRED Domain ID는 재사용하지 않는다.

## Evidence and Change Management

모든 Registry 변경은 **Approval Record**와 Change History를 함께 기록한다.

Change History는 다음 형식을 권장한다.

- Version
- Date
- Change Summary
- Approval Record

기존 승인 기록과 변경 이력은 삭제하거나 덮어쓰지 않는다.

---

# Appendix A. Domain ID Registry

| Domain ID | Governance Domain |
|---|---|
| GOV-DOC | Documentation Governance |
| GOV-ARCH | System Architecture & Development Governance |
| GOV-SEC | Security Governance |
| GOV-QUAL | Quality Governance |
| GOV-AI | AI Governance |
| GOV-DATA | Data Governance |
| GOV-MKT | Marketplace Governance |
| GOV-OPS | Operations Governance |

---

# Release Candidate Status

본 문서는 **Governance Registry v1.0 Release Candidate 1 (RC1)** 이다.

RC1은 설계 검토를 완료하고 Official v1.0 승인을 위한 최종 후보 문서이다.

Official v1.0 승인 시에는 다음 사항을 실제 승인 정보로 갱신한다.

- Approval Authority
- Approval Status
- Effective Date
- Approval Record

또한 Project Governance 체계와의 정합성을 확인하여 Prepared By 및 Review Partner를 최종 확정한다.
