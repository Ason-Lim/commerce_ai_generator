# Integration Verification Tool v1.0

## Document Identity

- Project: Commerce AI Generator
- Platform Area: 40_Development Platform
- Platform Asset: Verification Framework
- Architecture Reference: MA-2026-021
- Version: 1.0
- Status: Initial Implementation

## Purpose

Integration Verification Tool provides reusable project-level
verification for Food Knowledge domain integration.

## Verification Phases

- registration: Provider Registration Verification
- selection: Provider Selection Verification
- contract: Result Contract Verification
- routing: Runtime Routing Verification
- regression: Cross-domain Regression Verification
- all: Execute all supported phases

## Registry Order Policy

The Tool records the current Provider Registry order as evidence.

It does not fail merely because new Providers were added before or
after the target Provider, unless a separately approved governance
policy defines an exact order constraint.

Provider membership, single registration, category uniqueness,
retrieval, and contract conformance remain mandatory checks.

## Profile Model

Domain-specific expectations are defined through IntegrationProfile.

Profiles contain Provider identity, routing examples, expected Result
attributes and scores, and the regression target.

## CLI

Registration verification:

    python -m tools.verification.integration.cli cheese \
      --phase registration

Complete integration verification:

    python -m tools.verification.integration.cli cheese \
      --phase all

JSON evidence:

    python -m tools.verification.integration.cli cheese \
      --phase registration \
      --json \
      --output docs/verification/cheese/provider-registration.json

## Governance Interpretation

Tool PASS results constitute reproducible technical evidence.

They do not independently issue IPR, IPS, IRC, IRR, IRG, or ICR
approval. Formal reports remain subject to 99_Integration review.
