# MA-2026-037 Sauces F6 Exact-Scope Correction Decision

## Decision status

- Lifecycle: `MA-2026-037`
- Subject: `SAUCES`
- Stage: `F6_SHARED_REGISTRY_INTEGRATION`
- Decision: `ESTABLISHED`
- Corrected exact scope: `ESTABLISHED`

## Evidence and correction reason

The Sauce local provider does not implement the shared `FoodKnowledgeProvider` adapter contract: `category_id`, `aliases`, `supports`, and `analyze`. The Compound Seasoning integration demonstrates the separate domain-adapter precedent. F6 therefore requires a distinct Sauce shared-registry adapter.

## Corrected production boundary

The complete prospective F6 production scope is exactly three files:

1. Add `app/services/food/knowledge/sauce/knowledge_provider.py`.
2. Modify `app/services/food/category_registry.py`.
3. Modify `app/services/food/knowledge/registry.py`.

`app/services/food/knowledge/sauce/provider.py` remains the local domain provider and must be preserved. `app/services/food/knowledge/registry_loader.py` remains unchanged.

## Test-contract disposition

The established, unconsumed F6 test-contract authority remains valid because its sole test target, contract dimensions, function count, and case count are unchanged:

- Target: `tests/services/food/knowledge/sauce/test_sauce_registry_integration.py`
- Functions: `12`
- Cases: `32`

The temporary hold is released by this correction decision. The authority may be consumed only to establish that exact test contract. It does not authorize any production write.

## Supersession

The original F6 exact-scope decision is superseded only where it defined two prospective production targets. All unaffected constraints remain in force. This decision is the canonical correction governing the F6 shared-registry integration boundary.

## Exclusions

- No resource or registry-data write.
- No alias-resolution reopening.
- No category-vocabulary expansion.
- No origin-processing expansion.
- No full-suite execution.
- No Phase 4 reopening.

## Next eligible action

`ESTABLISH_MA_2026_037_SAUCES_F6_TEST_CONTRACT`
