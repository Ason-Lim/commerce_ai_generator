# MA-2026-037 Sauces F6 Test Contract Bounded Write Authority

## Status

- Lifecycle: `MA-2026-037`
- Stage: `F6_SHARED_REGISTRY_INTEGRATION`
- Authority: `ESTABLISHED_ONE_USE_BOUNDED`
- Delivery order: `TEST_FIRST`
- Test contract: `NOT_ESTABLISHED`

## Exact authorized target

Exactly one new test file may be created:

`tests/services/food/knowledge/sauce/test_sauce_registry_integration.py`

The file must contain exactly 12 test functions collecting exactly 32 cases.

## Required contract dimensions

The 32 cases must collectively cover Sauce registration visibility; canonical category lookup; provider routing; repeated idempotent registration; same-identity duplicates; conflicting identity rejection; transaction rollback and recovery; preservation of existing domain registrations; Japanese-condiment included identities; excluded raw, dry, solid, broth, spread, and preserve identities; registry-loader non-reopening; and stable public lookup results.

The initial contract must fail for the absence of F6 production integration while remaining collectible without changing production files.

## Prohibitions

- no production-file modification;
- no resource or registry-data write;
- no alias-resolution reopening;
- no category-vocabulary expansion;
- no application import outside pytest collection/execution required to establish expected failure;
- no full-suite execution.

## Consumption

This authority is consumed by one commit adding only the exact test target, with exactly 12 functions and 32 collected cases, followed by one annotated tag and atomic push. A separate authority is required before modifying `app/services/food/category_registry.py` or `app/services/food/knowledge/registry.py`.

## Next eligible action

`ESTABLISH_MA_2026_037_SAUCES_F6_TEST_CONTRACT`
