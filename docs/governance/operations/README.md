# Governance Operations Package v1.0

## Purpose

This package installs the operational governance layer for the Commerce AI Generator project.

## Contents

- 05_governance_operations_standard.md
- approval_log.md
- release_history.md
- governance_change_log.md
- governance_release_notes.md
- milestone_registry.md
- audit_trail.md
- governance_dashboard.md
- install_governance_operations.sh
- update_governance_operations.sh
- verify_governance_operations.sh
- uninstall_governance_operations.sh
- MANIFEST.sha256

## Default Target

`docs/governance/operations`

## Installation

```bash
chmod +x *.sh
./install_governance_operations.sh --target /Users/mom/commerce_ai_generator
```

## Verification

```bash
./verify_governance_operations.sh --target /Users/mom/commerce_ai_generator
```

## Update

```bash
./update_governance_operations.sh --target /Users/mom/commerce_ai_generator
```

## Uninstall

```bash
./uninstall_governance_operations.sh --target /Users/mom/commerce_ai_generator
```

All destructive operations create a timestamped backup unless `--no-backup` is specified.
