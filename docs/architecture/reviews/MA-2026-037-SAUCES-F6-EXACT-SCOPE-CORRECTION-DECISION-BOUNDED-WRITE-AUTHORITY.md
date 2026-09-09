# MA-2026-037 Sauces F6 Exact-Scope Correction Decision Bounded Write Authority

## Status

- Lifecycle: `MA-2026-037`
- Subject: `SAUCES`
- Stage: `F6_SHARED_REGISTRY_INTEGRATION`
- Authority: `ESTABLISHED_ONE_USE_BOUNDED`
- Consumption status: `UNCONSUMED`

## Sealed baseline

This authority is rooted at commit `1de743a4348ba11e9db56399e888d0c80eed95aa`. The established F6 test-contract authority remains unconsumed and held; this authority does not consume or replace it.

## Confirmed correction reason

The local Sauce provider does not implement the shared `FoodKnowledgeProvider` contract (`category_id`, `aliases`, `supports`, and `analyze`). The neighboring Compound Seasoning domain uses a distinct shared-registry adapter, establishing the applicable integration precedent.

## Sole authorized write

This one-use authority permits creating exactly one decision file:

`docs/architecture/reviews/MA-2026-037-SAUCES-F6-EXACT-SCOPE-CORRECTION-DECISION.md`

The decision may establish the corrected F6 production boundary as exactly three targets:

1. Add `app/services/food/knowledge/sauce/knowledge_provider.py`.
2. Modify `app/services/food/category_registry.py`.
3. Modify `app/services/food/knowledge/registry.py`.

It must preserve `app/services/food/knowledge/sauce/provider.py`, preserve the intended test target `tests/services/food/knowledge/sauce/test_sauce_registry_integration.py`, and explicitly decide the held test-contract authority's continuing validity or required supersession.

## Prohibitions

- No test, production, resource, registry-data, or integration implementation write.
- No test execution or application import.
- No alias-resolution reopening or category-vocabulary expansion.
- No full-suite execution.
- No consumption of the held F6 test-contract authority.
- No Phase 4 reopening.

## Consumption rule

This authority is consumed only by one commit that adds the sole decision file above and by its corresponding annotated tag. Any other write or target fails closed.

## Next eligible action

`ESTABLISH_MA_2026_037_SAUCES_F6_EXACT_SCOPE_CORRECTION_DECISION`
