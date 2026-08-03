# Governance Operations Package

## Package Metadata

| Item | Value |
|---|---|
| Package | Governance Operations Package |
| Version | v1.0 |
| Status | READY FOR PROJECT OWNER APPROVAL |
| Prepared Date | 2026-07-29 |
| Operational Model | Milestone-based batch update |
| Default Install Path | `docs/governance/operations` |
| Approval Authority | Project Owner |
| Documentation Governance | 00_0 Master Document Governance |
| Architecture Review | 00_1 Master Architecture |

## Purpose

This package establishes the operational records and procedures used to preserve governance approval, release, change, milestone, and audit evidence for the Commerce AI Generator project.

The package does not replace normative governance documents. It operates beneath the Project Charter, Master Document Governance Standard, Project Governance Architecture, and Governance Registry.

## Included Files

| File | Purpose |
|---|---|
| `05_governance_operations_standard.md` | Governing operating standard |
| `approval_log.md` | Append-only approval ledger |
| `release_history.md` | Release and release-bundle history |
| `governance_change_log.md` | Material governance change history |
| `governance_release_notes.md` | Human-readable milestone release notes |
| `milestone_registry.md` | Governance milestone lifecycle registry |
| `audit_trail.md` | Evidence and traceability ledger |
| `governance_dashboard.md` | Current operational summary |
| `install_governance_operations.sh` | One-command installer |
| `MANIFEST.sha256` | Package integrity manifest |

## Installation

From the extracted package directory:

```bash
chmod +x install_governance_operations.sh
./install_governance_operations.sh --target /Users/mom/commerce_ai_generator
```

Default destination:

```text
docs/governance/operations
```

Use a custom destination relative to the target repository:

```bash
./install_governance_operations.sh \
  --target /Users/mom/commerce_ai_generator \
  --dest governance/operations
```

Preview without writing:

```bash
./install_governance_operations.sh \
  --target /Users/mom/commerce_ai_generator \
  --dry-run
```

Existing destination files are backed up automatically unless `--no-backup` is supplied. Existing files are not replaced unless `--force` is supplied.

## Operating Rule

Operational records are updated at governance milestones rather than after every individual activity. Immediate recording is required only when an approval, release, emergency governance decision, or compliance exception would otherwise lose authoritative evidence.
