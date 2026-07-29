# Commerce AI Generator Governance Documents

이 디렉터리는 Commerce AI Generator 프로젝트의 공식 거버넌스 문서와 승인 증적을 관리한다.

## Source of Truth

이 디렉터리에 커밋된 문서와 Git 이력을 공식 원본(Source of Truth)으로 사용한다.
ChatGPT 대화는 작성·검토·합의 지원 기록이며, 공식 문서 저장소를 대체하지 않는다.

## Directory Structure

```text
docs/governance/
├── README.md
├── 00_project_charter.md
├── 01_master_document_governance_standard.md
├── 02_project_governance_architecture.md
├── 03_governance_registry_v1.0_rc1.md
├── 04_governance_registry_v1.0_rc1_review_consensus.md
├── approvals/
│   └── approval_log.md
└── releases/
    └── release_history.md
```

## Naming Rules

- 파일명은 소문자 `snake_case`를 사용한다.
- 정렬이 필요한 핵심 문서는 두 자리 순번을 사용한다.
- 문서 버전은 파일명과 문서 본문 메타데이터에 함께 기록한다.
- Release Candidate는 `_rc1`, `_rc2` 형식으로 표시한다.
- Official 버전은 `_official` 또는 확정된 버전 번호를 사용한다.
- 기존 승인 문서는 덮어쓰지 않고 새 버전 파일을 추가한다.

## Document Status

권장 상태값:

- `DRAFT`
- `REVIEW`
- `RELEASE CANDIDATE`
- `APPROVED`
- `SUPERSEDED`
- `RETIRED`

## Change and Approval Rules

1. 문서 변경은 Git commit으로 기록한다.
2. 승인된 문서는 Approval Log에 기록한다.
3. RC 또는 Official Release는 Release History에 기록한다.
4. 승인 기록과 릴리스 기록은 삭제하거나 덮어쓰지 않는다.
5. Official 문서 변경은 새 버전 또는 후속 RC로 진행한다.
