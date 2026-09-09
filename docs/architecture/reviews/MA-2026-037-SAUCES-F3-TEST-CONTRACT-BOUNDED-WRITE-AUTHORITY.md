# MA-2026-037 Sauces F3 Test Contract Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized target

This authority permits exactly one new test-contract file:

`tests/services/food/knowledge/sauce/test_sauce_parser.py`

The file shall contain exactly 16 test functions and collect exactly 58 cases.
It shall implement the complete behavioral matrix sealed by the F3 exact-scope
decision, including canonicalization, five-axis classification, Japanese
condiment product-identity routing, cross-domain exclusions, provenance,
conflict preservation, and deterministic output.

## Required expected-fail state

The contract must be test-first and must fail only because the selected parser
production contract is absent:

- `app/services/food/knowledge/sauce/parser.py` does not exist;
- `parse_sauce` is not yet exported by `app/services/food/knowledge/sauce/__init__.py`.

Collection must succeed with 58 cases. The expected-fail execution must not
create or modify production, resource, registry, or integration files.

## Preserved boundaries

- F1 parser-result model and F2 attributes taxonomy remain unchanged.
- Canonical specification v1.1 and its fourteen Japanese-condiment routes are consumed.
- Rules, scoring, evaluation, and provider implementation remain deferred to F4.
- Resources, shared registry, category registry, and Alias Resolution are excluded.
- Compound Seasonings and Herb & Spice remain closed.
- Origin Processing remains deferred.
- Full-suite execution is not authorized.

## Non-authority

This artifact does not authorize production writes, parser implementation,
resource writes, registry mutation, integration writes, or full-suite execution.

## Consumption

This authority is consumed only by creating, verifying the expected-fail state,
committing, tagging, and atomically pushing the exact one-file F3 test contract.
