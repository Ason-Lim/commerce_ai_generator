# MA-2026-037 Sauces F4 Test Contract Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized target

This authority permits exactly three new test-contract files:

- `tests/services/food/knowledge/sauce/test_sauce_rules.py`
- `tests/services/food/knowledge/sauce/test_sauce_scoring.py`
- `tests/services/food/knowledge/sauce/test_sauce_provider.py`

Together they shall contain exactly 24 test functions and collect exactly 64
cases: rules 8 functions/24 cases, scoring 8 functions/20 cases, and provider
8 functions/20 cases. They shall consume the F2 five-axis taxonomy, the F3
parser behavior, and all fourteen Japanese-condiment routes from specification
v1.1 without reopening those sealed contracts.

## Required expected-fail state

The contract must be test-first and must fail only because the selected F4
production contracts are absent:

- `app/services/food/knowledge/sauce/rules.py` does not exist;
- `app/services/food/knowledge/sauce/scoring.py` does not exist;
- `app/services/food/knowledge/sauce/provider.py` does not exist;
- the F4 public contracts are not yet exported by the package.

Collection must succeed with 64 cases. The expected-fail execution must not
create or modify production, resource, registry, or integration files.

## Preserved boundaries

- F1 through F3 production and test contracts remain unchanged.
- Canonical specification v1.1 and its fourteen Japanese-condiment routes are consumed.
- Scoring weights are fixed at family 0.30, texture 0.15, heat 0.15,
  intended use 0.25, and provenance 0.15.
- Raw and dry condiment identities remain outside Sauces unless sealed product-form evidence qualifies them.
- Resources, shared registry, category registry, and Alias Resolution are excluded.
- Compound Seasonings and Herb & Spice remain closed.
- Origin Processing remains deferred.
- Full-suite execution is not authorized.

## Non-authority

This artifact does not authorize production writes, F4 implementation,
resource writes, registry mutation, integration writes, or full-suite execution.

## Consumption

This authority is consumed only by creating, verifying the expected-fail state,
committing, tagging, and atomically pushing the exact three-file F4 test contract.
