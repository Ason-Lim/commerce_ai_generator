# Architecture Boundary Verifier v1.0

## Document Identity

- Project: Commerce AI Generator
- Platform Area: 40_Development Platform
- Platform Asset: Verification Framework
- Architecture Reference: MA-2026-021
- Version: 1.0
- Status: Initial Implementation

## Purpose

Architecture Boundary Verifier validates source-layer dependency
boundaries using the Python abstract syntax tree.

It replaces grep-based source checks that can incorrectly identify
comments, docstrings, and ordinary string literals as violations.

## Verification Inputs

- Domain source directory
- Optional domain identity
- Optional architecture identity

## Inspected AST Nodes

- Import
- ImportFrom
- Call
- ClassDef
- FunctionDef
- AsyncFunctionDef

## Ignored Content

- Comments
- Docstrings
- Ordinary string literals
- Formatting and whitespace

## Layer Policies

### Parser

Parser must not import or call Scoring, Rules, Provider,
FoodKnowledgeResult, or external runtime dependencies.

### Attributes

Attributes may project Parser and Registry data but must not calculate
scores, execute Rules, construct FoodKnowledgeResult, or orchestrate
Providers.

### Scoring

Scoring must not parse products, execute Rules, construct Results, or
orchestrate Providers.

### Rules

Rules must not reparse products, recalculate scores, construct Results,
or orchestrate Providers.

### Provider

Provider must inherit FoodKnowledgeProvider and preserve this ordered
orchestration sequence:

    parse_product
    build_cheese_attributes
    calculate_cheese_scores
    apply_cheese_rules
    calculate_cheese_final_score
    FoodKnowledgeResult

## External Dependency Policy

The domain layers must not directly import:

- requests
- httpx
- sqlalchemy
- streamlit

## Result Contract

The Verifier returns the common VerificationResult defined by
Verification Framework Core v1.0.

Each independently evaluated condition is represented by a
VerificationCheck with PASS, FAIL, ERROR, WARNING, or SKIPPED status.

## CLI

Example invocation:

    python -m tools.verification.boundary.cli \
      app/services/food/knowledge/cheese \
      --domain-id 10_Cheese \
      --architecture-id MA-2026-012

JSON output is available through the --json option.

## Governance Interpretation

A PASS result is reproducible architecture verification evidence.
It does not replace Master Architecture review, Documentation
Governance review, or Project Owner approval.
