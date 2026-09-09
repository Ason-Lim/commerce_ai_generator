# MA-2026-037 Sauces F6 Exact-Scope Decision Bounded Write Authority

## Status

- Lifecycle: `MA-2026-037`
- Subject: `SAUCES`
- Stage: `F6_SHARED_REGISTRY_INTEGRATION`
- Authority: `ESTABLISHED_ONE_USE_BOUNDED`
- Exact-scope decision: `NOT_ESTABLISHED`

## Sealed basis

- F5 independent-domain verification is sealed at `67b7158cd78824ec2e3e7d16a2def28437ca2a70`.
- The selected F5 verification result is `SATISFIED_486_PASS` across 24 test files.
- The corrected canonical Sauces specification v1.1 remains an ancestor.
- The sealed read-only F6 preflight reported three shared-registry anchors, 81 registry-routing candidates, 23 integration-test candidates, and four external Sauce references.
- This authority establishment independently revalidates the three exact shared-registry anchor blobs, the exact four external Sauce references, and the absence or presence of each proposed target. The broad discovery counts are retained as preflight evidence and are not recomputed under a different path predicate.

## One-use authorization

This authority may be consumed exactly once to create only:

`docs/architecture/reviews/MA-2026-037-SAUCES-F6-EXACT-SCOPE-DECISION.md`

That decision may select, narrow, or reject the candidate F6 boundary consisting of:

1. prospective test addition: `tests/services/food/knowledge/sauce/test_sauce_registry_integration.py`;
2. prospective production modification: `app/services/food/category_registry.py`;
3. prospective production modification: `app/services/food/knowledge/registry.py`.

The decision must preserve the existing `registry_loader.py` anchor unless separately authorized and must keep registry data, resources, alias-resolution reopening, category-vocabulary expansion, and origin/processing outside scope.

## Prohibitions

This authority does not authorize:

- creation or modification of any test or production file;
- test execution or application imports;
- resource or registry-data writes;
- shared-registry integration implementation;
- alias-resolution reopening;
- category-vocabulary expansion;
- origin or processing changes;
- full-suite execution.

## Consumption rule

The authority is consumed only by one commit that adds the sole F6 exact-scope decision file, followed by one annotated tag and an atomic push. Any different path, additional file, implementation change, or pre-existing target fails closed.

## Next eligible action

`ESTABLISH_MA_2026_037_SAUCES_F6_EXACT_SCOPE_DECISION`
