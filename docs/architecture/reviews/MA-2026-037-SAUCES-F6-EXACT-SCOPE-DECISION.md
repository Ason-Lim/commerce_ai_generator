# MA-2026-037 Sauces F6 Exact-Scope Decision

## Decision

- Lifecycle: `MA-2026-037`
- Stage: `F6_SHARED_REGISTRY_INTEGRATION`
- Status: `ESTABLISHED`
- Delivery order: `TEST_FIRST`
- Result: `ONE_TEST_ADDITION_AND_TWO_SHARED_REGISTRY_MODIFICATIONS`

## Exact test target

Exactly one test file may be added in the subsequent test-contract subwave:

`tests/services/food/knowledge/sauce/test_sauce_registry_integration.py`

Its contract shall cover Sauce registration visibility, canonical lookup and provider routing, idempotent registration, duplicate/conflict behavior, transaction safety, preservation of existing domains, and consumption of the canonical Japanese-condiment boundary. Test function and parametrized case counts must be fixed by the subsequent test-contract authority before the test file is written.

## Exact prospective production targets

Subject to a later production-write authority, implementation may modify exactly:

1. `app/services/food/category_registry.py`
2. `app/services/food/knowledge/registry.py`

No production write is authorized by this decision.

## Preserved boundary

- `app/services/food/knowledge/registry_loader.py` remains unchanged.
- Existing Herb & Spice and Compound Seasoning behavior remains regression-protected.
- Sauce classification consumes the canonical specification v1.1 and does not reopen its Japanese-condiment route matrix.
- Shared registration must be deterministic, idempotent, and fail safely on conflicting identity.

## Exclusions

- no registry-data or resource file;
- no alias-resolution reopening;
- no category-vocabulary expansion;
- no parser, attributes, rules, scoring, provider, or parser-model reopening;
- no origin or processing change;
- no full-suite execution;
- no production or test write under this decision.

## Sequential authorization

1. establish one-use F6 test-contract bounded write authority;
2. establish the exact expected-fail test contract;
3. establish a separate exact two-file production-write authority;
4. implement only the two production targets and run only the authorized contract;
5. perform separately authorized regression and lifecycle completion review.

## Next eligible action

`ESTABLISH_MA_2026_037_SAUCES_F6_TEST_CONTRACT_BOUNDED_WRITE_AUTHORITY`
