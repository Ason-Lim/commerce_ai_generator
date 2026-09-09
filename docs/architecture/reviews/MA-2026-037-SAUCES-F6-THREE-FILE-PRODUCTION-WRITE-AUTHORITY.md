# MA-2026-037 Sauces F6 Three-File Production Write Authority

## Status

- Lifecycle: `MA-2026-037`
- Stage: `F6_SHARED_REGISTRY_INTEGRATION`
- Authority: `ESTABLISHED_ONE_USE_BOUNDED`
- Implementation: `NOT_IMPLEMENTED`

## Sealed prerequisites

The corrected F6 exact scope and the exact 12-function, 32-case expected-fail test contract are sealed. The test contract must remain byte-identical during implementation.

## Exact authorized production writes

This one-use authority permits exactly three production targets:

1. Add `app/services/food/knowledge/sauce/knowledge_provider.py` as the shared `FoodKnowledgeProvider` adapter.
2. Modify `app/services/food/category_registry.py` only to register the Sauce category and its bounded aliases.
3. Modify `app/services/food/knowledge/registry.py` only to import and register the Sauce shared adapter.

## Required verification

- The exact F6 test file must collect 32 cases and pass all 32.
- The test file must remain byte-identical.
- `app/services/food/knowledge/sauce/provider.py` must remain byte-identical.
- `app/services/food/knowledge/registry_loader.py` must remain byte-identical.

## Exclusions

- No other production or test write.
- No resource or registry-data write.
- No alias-resolution implementation change.
- No category-vocabulary expansion beyond the sealed Sauce aliases.
- No origin-processing expansion or full-suite execution.
- No Phase 4 reopening.

## Consumption rule

This authority is consumed only by one commit containing exactly the three authorized production changes and by its corresponding annotated tag and atomic push.

## Next eligible action

`IMPLEMENT_MA_2026_037_SAUCES_F6_THREE_FILE_PRODUCTION`
