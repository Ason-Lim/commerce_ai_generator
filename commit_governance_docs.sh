#!/usr/bin/env bash
set -euo pipefail

# Run this script from the Commerce AI Generator repository root.
# Example:
#   cd /Users/mom/commerce_ai_generator
#   bash commit_governance_docs.sh

git status --short

git add docs/governance

git diff --cached --check
git diff --cached --stat

git commit -m "docs(governance): add Governance Registry v1.0 RC1 consensus"

# Optional RC1 tag:
git tag -a governance-registry-v1.0-rc1 \
  -m "Governance Registry v1.0 RC1 review consensus approved on 2026-07-29"

echo
echo "Local commit and annotated tag created."
echo "Review with: git log -1 --stat && git tag --list 'governance-registry-*'"
echo "Push with: git push origin HEAD && git push origin governance-registry-v1.0-rc1"
