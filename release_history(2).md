# Governance Release History

## Document Metadata

| Item | Value |
|---|---|
| Record Type | Append-only release ledger |
| Version | v1.0 |
| Status | ACTIVE OPERATIONAL RECORD |
| Update Model | Immediate for Official releases; reconciled at milestones |
| Last Reconciled Milestone | GOV-MS-2026-001 |
| Last Reconciled Date | 2026-07-29 |

## Release Principles

- Approval and release are separate events.
- An Official release must reference an approval unless an emergency exception is recorded.
- A release bundle may contain multiple approved artifacts.
- Proposed tags are not treated as existing tags until repository verification.
- Withdrawn and superseded releases remain in the ledger.

## Release Ledger

| Release ID | Release Date | Release Unit | Version | Status | Approval Record | Milestone | Included Artifacts | Commit SHA | Git Tag | Evidence Status | Notes | Supersedes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GOV-REL-20260729-001 | 2026-07-29 | Governance Registry | v1.0 RC1 | RELEASE_CANDIDATE | GOV-APR-20260729-001 | GOV-MS-2026-001 | Governance Registry RC1; RC1 Review Consensus Statement | UNVERIFIED | PROPOSED: `governance-registry-v1.0-rc1` | PARTIALLY_VERIFIED | RC1 review completed. This historical RC release is retained even though the Official version is now approved. | — |
| GOV-REL-20260729-002 | 2026-07-29 | Project Governance Architecture | v1.0 Official | OFFICIAL | GOV-APR-20260729-002 | GOV-MS-2026-001 | Project Governance Architecture v1.0 Official | UNVERIFIED | PROPOSED: `governance-architecture-v1.0` | PARTIALLY_VERIFIED | Official architecture baseline established. Repository evidence remains pending. | — |
| GOV-REL-20260729-003 | 2026-07-29 | Governance Registry | v1.0 Official | OFFICIAL | GOV-APR-20260729-003 | GOV-MS-2026-001 | Governance Registry v1.0 Official | UNVERIFIED | PROPOSED: `governance-registry-v1.0` | PARTIALLY_VERIFIED | Official governance registry established. Repository evidence remains pending. | GOV-REL-20260729-001 |
| GOV-REL-20260729-004 | 2026-07-29 | Governance Baseline Bundle | v1.0 | OFFICIAL | GOV-APR-20260729-002; GOV-APR-20260729-003 | GOV-MS-2026-001 | Project Governance Architecture v1.0 Official; Governance Registry v1.0 Official | UNVERIFIED | PROPOSED: `governance-baseline-v1.0` | PARTIALLY_VERIFIED | Logical release bundle representing the first approved governance baseline. Tag creation remains pending verification. | — |

## Next Release ID

```text
GOV-REL-20260729-005
```

## Release ID Rule

```text
GOV-REL-YYYYMMDD-NNN
```

## Release Status Vocabulary

`PLANNED`, `RELEASE_CANDIDATE`, `OFFICIAL`, `WITHDRAWN`, `SUPERSEDED`, `ARCHIVED`

## Reconciliation Checklist

- [x] Every Official artifact release references an approval
- [x] RC and Official releases are distinguished
- [x] Release bundle scope is explicit
- [x] Supersession is explicit
- [ ] Commit SHAs verified
- [ ] Git tags verified
