# MA-2026-036 Compound Seasonings Corrected F6B Two-File Production Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `Corrected F6B Adapter and Shared Registry Implementation`
- Authority: `ONE_USE_BOUNDED_TWO_FILE_PRODUCTION_WRITE_AUTHORITY`
- Baseline commit: `aa4f40b55eb330678a497e97fd64eba52c0b4202`

## Sealed test-first state

The corrected F6A contract contains exactly six collected tests and currently
produces exactly six expected failures attributable to the absent adapter and
shared registration. Its test-write authority is consumed.

## Exact authorized production targets

Exactly two production changes are authorized:

1. `ADD app/services/food/knowledge/compound_seasoning/knowledge_provider.py`
2. `MODIFY app/services/food/knowledge/registry.py`

No other file may be created, modified, renamed, or deleted.

## Adapter contract

The adapter must inherit `FoodKnowledgeProvider`, expose canonical category
identity, retain tuple aliases, implement bounded `supports()` behavior, and
translate `Provider.evaluate()` output into `FoodKnowledgeResult`. The original
domain `Provider`, parser, registries, attributes, rules, scoring, resources,
and aliases contract must remain unchanged.

## Shared Registry contract

The Registry modification is limited to importing the new adapter and
registering exactly one instance in the established provider order. Category
Registry remains excluded. No registry public API or Alias Resolution behavior
may be changed.

## Required implementation verification

- corrected F6A contract: exactly `6 passed`;
- existing Compound Seasonings suite: exactly `118 passed` including F6A;
- no failure, error, skip, or xfail;
- exact two-file production diff;
- original domain Provider and Category Registry blob identities unchanged.

Any additional regression execution requires a later F6C decision or authority.

## Exclusions

No test modification, Category Registry expansion, direct domain Provider
change, resource/parser/rule/scoring change, Provider.aliases change, Alias
Resolution or Herb & Spice reopening, full-suite execution, database/network
operation, DDL, migration, deployment, deferred registry work, Sauces,
Cross-Border, Recommendation/Ranking, or lifecycle completion is authorized.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6a_corrected_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f6a_corrected_test_case_count=6
compound_seasonings_f6a_corrected_test_write_authority=CONSUMED
compound_seasonings_f6b_stage=CORRECTED_ADAPTER_AND_SHARED_REGISTRY_IMPLEMENTATION
compound_seasonings_f6b_production_target_count=2
compound_seasonings_f6b_adapter_change_type=ADD
compound_seasonings_f6b_registry_change_type=MODIFY
compound_seasonings_f6b_production_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f6b_implementation_status=NOT_IMPLEMENTED
test_write_authority=NONE
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=IMPLEMENT_MA_2026_036_COMPOUND_SEASONINGS_F6B_CORRECTED_TWO_FILE_PRODUCTION
```

## Authority statement

Only the one-use authority for the exact two-file corrected F6B production
implementation is established. This authority document performs no production
write and grants no authority beyond its stated targets and verification.
