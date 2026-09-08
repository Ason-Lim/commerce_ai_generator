# MA-2026-036 Compound Seasonings Bounded Integration Exact-Scope Decision

## Decision identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F6 Bounded Integration`
- Decision: `EXACT_SCOPE_ESTABLISHED`
- Baseline commit: `72bda57301589f94da23814b855ad63a21177696`

## Evidence basis

F5 is sealed at 314/314 passing cases. The F6 read-only inventory found two
known shared anchors, 74 broad registry/routing candidates, zero adapter
candidates, 21 integration-test candidates, and zero existing Compound
Seasonings references outside its own package. Those counts are inventory
evidence only and do not authorize wholesale integration changes.

## Exact integration decision

F6 shall use the existing shared Food Knowledge Registry as the sole production
registration boundary:

`app/services/food/knowledge/registry.py`

The exact production change type is `MODIFY`. It may register and route the
existing Compound Seasonings provider through the existing registry contract.
It may not change provider scoring, resource data, parser behavior, aliases, or
the registry's public contract beyond the minimal registration entry.

The Category Registry is explicitly excluded:

`app/services/food/category_registry.py`

Compound Seasonings integration must not expand Category Registry
responsibilities. No adapter file is selected or authorized.

## Exact integration-test decision

F6A may establish a test contract in exactly one future new file:

`tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py`

The exact change type is `ADD`. The contract shall contain exactly four tests:

1. the shared Knowledge Registry exposes the Compound Seasonings provider;
2. canonical Compound Seasonings routing resolves to that provider;
3. the resolved provider preserves the existing domain provider identity and
   result contract; and
4. Herb & Spice routing remains independent and unchanged.

These four cases are prospective until a separate F6A test-write authority is
established and consumed. No existing test file is selected for modification.

## Selected regression boundary

After implementation, bounded verification shall execute:

- the new four-case shared-registry integration contract;
- the existing six Compound Seasonings files and 112 cases;
- `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py`;
- `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py`; and
- the existing shared-registry integration tests whose registry API is directly
  exercised by the selected one-file production diff, selected by a later
  read-only collection preflight before execution.

The remaining broad inventory candidates are not implementation targets. The
full repository suite remains unauthorized unless a later independent decision
explicitly authorizes it.

## Ordered bounded subwaves

1. `F6A`: establish four-case integration test contract authority, then add the
   exact one test file and confirm its intended pre-implementation failure;
2. `F6B`: establish one-file production write authority, then minimally modify
   the shared Knowledge Registry;
3. `F6C`: run the exact bounded integration and regression verification set
   established by a separate read-only collection preflight; and
4. `F6D`: conduct bounded-integration completion review without implying
   MA-2026-036 lifecycle completion.

Each subwave requires separate authority. No authority carries forward.

## Deferred and excluded scope

Origin Registry, Processing Registry, Ingredient Role Registry, Category
Registry expansion, provider alias changes, Alias Resolution reopening, Herb &
Spice reopening, adapters, scoring, resource changes, database/network work,
DDL, migration, deployment, Sauces, Cross-Border, Recommendation/Ranking, and
new MA allocation remain excluded.

## Established state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f5_verification_status=ESTABLISHED
compound_seasonings_f5_verification_result=SATISFIED_314_PASS
compound_seasonings_f6_stage=BOUNDED_INTEGRATION
compound_seasonings_f6_exact_scope_status=ESTABLISHED
compound_seasonings_f6_exact_scope_decision_status=ESTABLISHED
compound_seasonings_f6_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_f6_selected_production_target_count=1
compound_seasonings_f6_selected_production_target=app/services/food/knowledge/registry.py
compound_seasonings_f6_selected_test_target_count=1
compound_seasonings_f6_selected_test_target=tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py
compound_seasonings_f6_selected_test_case_count=4
compound_seasonings_f6_adapter_scope=NONE_SELECTED
compound_seasonings_f6_category_registry_scope=EXCLUDED
compound_seasonings_f6_test_write_authority=NONE
compound_seasonings_f6_production_write_authority=NONE
compound_seasonings_f6_integration_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
alias_resolution_reopening_authority=NONE
herb_spice_reopening_authority=NONE
origin_registry_status=DEFERRED_NOT_SELECTED
processing_registry_status=DEFERRED_NOT_SELECTED
ingredient_role_registry_status=DEFERRED_NOT_SELECTED
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_F6A_SHARED_REGISTRY_INTEGRATION_TEST_CONTRACT_BOUNDED_WRITE_AUTHORITY
```

## Decision statement

The F6 exact scope is limited to one future shared-registry production
modification and one future four-case integration-test addition, executed in
separately authorized subwaves. This decision itself grants no test execution,
test write, production write, or integration implementation authority.
